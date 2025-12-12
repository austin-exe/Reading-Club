import json
import os
import datetime

DB_PATH = "library.json"

# --- JSON HELPERS ---
def load_data():
    """Reads the JSON file and returns the data dictionary."""
    if not os.path.exists(DB_PATH):
        return {"items": [], "history": []}
    try:
        with open(DB_PATH, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"items": [], "history": []}

def save_data(data):
    """Writes the data dictionary back to the JSON file."""
    with open(DB_PATH, 'w') as f:
        json.dump(data, f, indent=4)

def init_db():
    """Creates the JSON file with seed data if it doesn't exist."""
    if not os.path.exists(DB_PATH):
        seed_sample()

def seed_sample():
    print("Seeding library collection (JSON)...")
    # We use a temporary wrapper to force the file creation
    data = {"items": [], "history": []}
    save_data(data)
    
    # Add items using the standard add_item function
    add_item("The Great Gatsby", "F. Scott Fitzgerald", "Book", "1925", "A story of the Jazz Age.")
    add_item("1984", "George Orwell", "Book", "1949", "A dystopian social science fiction novel.")
    add_item("The Godfather", "Francis Ford Coppola", "Film", "1972", "The aging patriarch of an organized crime dynasty.")
    add_item("National Geographic", "NatGeo Society", "Magazine", "May 2024", "Special issue on Ocean Conservation.")

# --- CRUD OPERATIONS ---

def get_all_items():
    data = load_data()
    # Sort by ID descending to match previous behavior
    return sorted(data["items"], key=lambda x: x['id'], reverse=True)

def search_items(q):
    data = load_data()
    q = q.lower()
    return [
        item for item in data["items"] 
        if q in item["title"].lower() or q in item["creator"].lower() or q in item["category"].lower()
    ]

def get_item_by_id(item_id):
    data = load_data()
    for item in data["items"]:
        if item["id"] == item_id:
            return item
    return None

def add_item(title, creator, category, date, description):
    data = load_data()
    
    # Auto-increment ID logic
    if data["items"]:
        new_id = max(item["id"] for item in data["items"]) + 1
    else:
        new_id = 1
        
    new_item = {
        "id": new_id,
        "title": title,
        "creator": creator,
        "category": category,
        "date": date,
        "description": description,
        "available": 1,
        "borrower": None,
        "borrow_date": None
    }
    
    data["items"].append(new_item)
    save_data(data)
    return new_item

def update_item(item_id, updates):
    data = load_data()
    for item in data["items"]:
        if item["id"] == item_id:
            # Update only allowed fields
            allowed = ["title", "creator", "category", "date", "description"]
            for k in allowed:
                if k in updates:
                    item[k] = updates[k]
            save_data(data)
            return True
    return False

def delete_item(item_id):
    data = load_data()
    original_count = len(data["items"])
    data["items"] = [item for item in data["items"] if item["id"] != item_id]
    
    if len(data["items"]) < original_count:
        save_data(data)
        return True
    return False

# --- BORROW / RETURN LOGIC ---

def borrow_item(item_id, borrower):
    data = load_data()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    for item in data["items"]:
        if item["id"] == item_id:
            if item["available"] == 0:
                return False, "Item unavailable"
            
            # Update Item
            item["available"] = 0
            item["borrower"] = borrower
            item["borrow_date"] = now
            
            # Add to History
            new_hist_id = 1
            if data["history"]:
                new_hist_id = max(h["id"] for h in data["history"]) + 1
                
            data["history"].append({
                "id": new_hist_id,
                "item_id": item_id,
                "action": "Borrowed",
                "borrower": borrower,
                "date": now
            })
            
            save_data(data)
            return True, "Borrowed"
            
    return False, "Item not found"

def return_item(item_id):
    data = load_data()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    for item in data["items"]:
        if item["id"] == item_id:
            if item["available"] == 1:
                return False, "Item not borrowed"
            
            borrower_name = item["borrower"]
            
            # Update Item
            item["available"] = 1
            item["borrower"] = None
            item["borrow_date"] = None
            
            # Add to History
            new_hist_id = 1
            if data["history"]:
                new_hist_id = max(h["id"] for h in data["history"]) + 1
                
            data["history"].append({
                "id": new_hist_id,
                "item_id": item_id,
                "action": "Returned",
                "borrower": borrower_name,
                "date": now
            })
            
            save_data(data)
            return True, "Returned"
            
    return False, "Item not found"

def get_history(item_id):
    data = load_data()
    # Filter history for this item and sort by ID desc
    item_history = [h for h in data["history"] if h["item_id"] == item_id]
    return sorted(item_history, key=lambda x: x['id'], reverse=True)