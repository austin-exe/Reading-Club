import sqlite3
import os
import datetime

DB_PATH = "library.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row 
    return conn

def init_db():
    # Only create tables if the DB file doesn't exist
    new_db = not os.path.exists(DB_PATH)
    
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                creator TEXT,
                category TEXT,
                date TEXT,
                description TEXT,
                available INTEGER DEFAULT 1,
                borrower TEXT,
                borrow_date TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER,
                action TEXT,
                borrower TEXT,
                date TEXT
            )
        """)
        conn.commit()

    # If we just created the DB, fill it with data
    if new_db:
        seed_sample()

def seed_sample():
    print("Seeding library collection...")
    
    # --- BOOKS ---
    add_item("The Great Gatsby", "F. Scott Fitzgerald", "Book", "1925", "A story of the Jazz Age, wealth, and one man's obsession with the past.")
    add_item("1984", "George Orwell", "Book", "1949", "A dystopian social science fiction novel and cautionary tale about totalitarianism.")
    add_item("To Kill a Mockingbird", "Harper Lee", "Book", "1960", "A novel about the serious issues of rape and racial inequality in the American South.")
    add_item("Sapiens", "Yuval Noah Harari", "Book", "2011", "A brief history of humankind, exploring how biology and history have defined us.")
    add_item("Harry Potter and the Sorcerer's Stone", "J.K. Rowling", "Book", "1997", "A young wizard discovers his magical heritage and attends a school of witchcraft.")

    # --- FILMS ---
    add_item("The Godfather", "Francis Ford Coppola", "Film", "1972", "The aging patriarch of an organized crime dynasty transfers control to his reluctant son.")
    add_item("Inception", "Christopher Nolan", "Film", "2010", "A thief who steals corporate secrets through the use of dream-sharing technology.")
    add_item("Parasite", "Bong Joon-ho", "Film", "2019", "Greed and class discrimination threaten the newly formed symbiotic relationship between two families.")
    add_item("Pulp Fiction", "Quentin Tarantino", "Film", "1994", "The lives of two mob hitmen, a boxer, and a gangster intertwine in four tales of violence and redemption.")
    add_item("Spirited Away", "Hayao Miyazaki", "Film", "2001", "A young girl wanders into a world ruled by gods, witches, and spirits, and where humans are changed into beasts.")

    # --- MAGAZINES ---
    add_item("National Geographic", "NatGeo Society", "Magazine", "May 2024", "Special issue on Ocean Conservation and deep-sea exploration.")
    add_item("Time Magazine", "Time USA", "Magazine", "Dec 2023", "Person of the Year edition featuring Taylor Swift.")
    add_item("Vogue", "Condé Nast", "Magazine", "Sept 2024", "The September Issue: Trends defining the upcoming fashion season.")
    add_item("Wired", "Condé Nast", "Magazine", "Jan 2024", "The Future of Artificial Intelligence and its impact on silicon valley.")
    add_item("The New Yorker", "Condé Nast", "Magazine", "Feb 2024", "Commentary, criticism, essays, fiction, satire, cartoons, and poetry.")

def get_all_items():
    with get_conn() as conn:
        return [dict(row) for row in conn.execute("SELECT * FROM items ORDER BY id DESC")]

def search_items(q):
    qlike = f"%{q}%"
    with get_conn() as conn:
        return [dict(row) for row in conn.execute("SELECT * FROM items WHERE title LIKE ? OR creator LIKE ? OR category LIKE ?", (qlike, qlike, qlike))]

def get_item_by_id(item_id):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
    return dict(row) if row else None

def add_item(title, creator, category, date, description):
    with get_conn() as conn:
        cur = conn.execute("INSERT INTO items (title,creator,category,date,description,available) VALUES (?,?,?,?,?,1)", 
                           (title, creator, category, date, description))
        conn.commit()
        return get_item_by_id(cur.lastrowid)

def update_item(item_id, data):
    allowed = ["title", "creator", "category", "date", "description"]
    updates = [f"{k}=?" for k in data if k in allowed]
    if not updates: return False
    vals = [data[k] for k in data if k in allowed] + [item_id]
    with get_conn() as conn:
        conn.execute(f"UPDATE items SET {', '.join(updates)} WHERE id=?", vals)
        conn.commit()
    return True

def delete_item(item_id):
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM items WHERE id=?", (item_id,))
        conn.commit()
    return cur.rowcount > 0

def borrow_item(item_id, borrower):
    item = get_item_by_id(item_id)
    if not item or not item['available']: return False, "Unavailable"
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    with get_conn() as conn:
        conn.execute("UPDATE items SET available=0, borrower=?, borrow_date=? WHERE id=?", (borrower, now, item_id))
        conn.execute("INSERT INTO history (item_id, action, borrower, date) VALUES (?, 'Borrowed', ?, ?)", (item_id, borrower, now))
        conn.commit()
    return True, "Borrowed"

def return_item(item_id):
    item = get_item_by_id(item_id)
    if not item or item['available']: return False, "Not borrowed"
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    with get_conn() as conn:
        conn.execute("UPDATE items SET available=1, borrower=NULL, borrow_date=NULL WHERE id=?", (item_id,))
        conn.execute("INSERT INTO history (item_id, action, borrower, date) VALUES (?, 'Returned', ?, ?)", (item_id, item['borrower'], now))
        conn.commit()
    return True, "Returned"

def get_history(item_id):
    with get_conn() as conn:
        return [dict(row) for row in conn.execute("SELECT * FROM history WHERE item_id=? ORDER BY id DESC", (item_id,))]