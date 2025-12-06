import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import requests

# --- CONFIGURATION ---
API_BASE = "http://127.0.0.1:5000/api/items"

# --- CUSTOM PALETTE ("Noir & Taupe") ---
COLORS = {
    "bg": "#121212",             # Deep Black Background
    "panel": "#1E1E1E",          # Sidebar Panel
    "header": "#000000",         # Header
    
    "white": "#FFFFFF",          # Text High Contrast
    "cream": "#FFFDD0",          # Accent Text
    "silver": "#C0C0C0",         # Muted Text / Borders
    "charcoal": "#36454F",       # Secondary Buttons
    "taupe": "#483C32",          # Primary Buttons
    "row_even": "#121212",       # List Stripe 1
    "row_odd": "#181818",        # List Stripe 2
    "grid_line": "#333333"       # Column Dividers
}

# --- FONTS ---
FONT_MAIN = ("Segoe UI", 11)
FONT_HEADER = ("Segoe UI", 22, "bold")
FONT_TITLE = ("Segoe UI", 24, "bold")  # Sidebar Title
FONT_BOLD = ("Segoe UI", 12, "bold")
FONT_BTN = ("Segoe UI", 10, "bold")

class ReadingClubApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Reading Club")
        self.geometry("1280x800")
        self.configure(bg=COLORS["bg"])
        self.state("zoomed") 

        self.selected_item = None
        self.current_table_data = [] # Stores real data to map visual IDs to real IDs
        self.search_var = tk.StringVar()

        self._setup_styles()
        self._build_layout()
        self.load_data()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        # General Panels
        style.configure("TFrame", background=COLORS["bg"])
        style.configure("Panel.TFrame", background=COLORS["panel"])
        style.configure("Header.TFrame", background=COLORS["header"])
        
        # Labels
        style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["white"], font=FONT_MAIN)
        style.configure("Panel.TLabel", background=COLORS["panel"], foreground=COLORS["white"], font=FONT_MAIN)
        style.configure("Header.TLabel", background=COLORS["header"], foreground=COLORS["cream"], font=FONT_HEADER)
        style.configure("Muted.TLabel", background=COLORS["panel"], foreground=COLORS["silver"], font=("Segoe UI", 10))
        
        # --- TREEVIEW (THE LIST) ---
        style.configure("Treeview", 
            background=COLORS["bg"], 
            fieldbackground=COLORS["bg"], 
            foreground=COLORS["silver"], 
            font=("Segoe UI", 12), 
            rowheight=50,
            borderwidth=0
        )
        style.configure("Treeview.Heading", 
            background=COLORS["panel"], 
            foreground=COLORS["cream"], 
            font=("Segoe UI", 11, "bold"),
            relief="flat"
        )
        style.map("Treeview", background=[("selected", COLORS["taupe"])], foreground=[("selected", COLORS["white"])])

    def _build_layout(self):
        # 1. Header
        header = ttk.Frame(self, style="Header.TFrame", padding=(40, 25))
        header.pack(fill="x")
        
        ttk.Label(header, text="🍀 Reading Club", style="Header.TLabel").pack(side="left")

        # Search Bar Area
        search_frame = ttk.Frame(header, style="Header.TFrame")
        search_frame.pack(side="right")
        
        self.entry_search = tk.Entry(search_frame, textvariable=self.search_var, font=("Segoe UI", 13), width=35, 
                                     bg=COLORS["panel"], fg=COLORS["white"], insertbackground=COLORS["white"], 
                                     relief="flat")
        self.entry_search.pack(side="left", padx=15, ipady=8)
        self.entry_search.bind("<Return>", lambda e: self.search())

        # Header Buttons
        tk.Button(search_frame, text="SEARCH", bg=COLORS["taupe"], fg=COLORS["cream"], 
                  font=FONT_BTN, relief="flat", padx=20, pady=6, command=self.search).pack(side="left")
        
        tk.Button(search_frame, text="RESET", bg=COLORS["charcoal"], fg=COLORS["white"], 
                  font=FONT_BTN, relief="flat", padx=20, pady=6, command=self.load_data).pack(side="left", padx=15)

        # 2. Main Content
        main_content = ttk.Frame(self, style="TFrame")
        main_content.pack(fill="both", expand=True, padx=40, pady=40)

        # Left: Inventory List
        left_frame = ttk.Frame(main_content, style="TFrame")
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 40))

        # Toolbar
        toolbar = ttk.Frame(left_frame, style="TFrame")
        toolbar.pack(fill="x", pady=(0, 20))
        ttk.Label(toolbar, text="LIBRARY COLLECTION", font=("Segoe UI", 14, "bold"), foreground=COLORS["silver"]).pack(side="left", pady=5)
        
        # Add Button
        btn_add = tk.Button(toolbar, text="+ ADD NEW ITEM", bg=COLORS["taupe"], fg=COLORS["cream"], 
                            font=FONT_BTN, relief="flat", padx=25, pady=8, command=self.open_add_modal)
        btn_add.pack(side="right")

        # Table Setup
        cols = ("ID", "Title", "Category", "Status")
        self.tree = ttk.Treeview(left_frame, columns=cols, show="headings", selectmode="browse")
        
        # --- FIXED ALIGNMENT SETTINGS (Perfect Left Alignment) ---
        self.tree.heading("ID", text="NO.", anchor="center")      # Center Number
        self.tree.heading("Title", text="TITLE", anchor="w")      # Left Align Header
        self.tree.heading("Category", text="GENRE", anchor="w")   # Left Align Header
        self.tree.heading("Status", text="STATUS", anchor="w")    # Left Align Header
        
        self.tree.column("ID", width=60, anchor="center")         # Center Data
        self.tree.column("Title", width=450, anchor="w")          # Left Align Data
        self.tree.column("Category", width=180, anchor="w")       # Left Align Data
        self.tree.column("Status", width=150, anchor="w")         # Left Align Data

        # Setup Scrollbar
        sb = ttk.Scrollbar(left_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=sb.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        # Configure Row Stripes
        self.tree.tag_configure("odd", background=COLORS["row_odd"])
        self.tree.tag_configure("even", background=COLORS["row_even"])

        # Right: Details Sidebar
        self.sidebar = ttk.Frame(main_content, style="Panel.TFrame", width=500)
        self.sidebar.pack(side="right", fill="y")
        self.sidebar.pack_propagate(False)

        self._build_sidebar()

    def _build_sidebar(self):
        # Master container for sidebar
        container = ttk.Frame(self.sidebar, style="Panel.TFrame", padding=30)
        container.pack(fill="both", expand=True)

        # Empty State Label
        self.lbl_empty = ttk.Label(container, text="Select an item to see actions", style="Muted.TLabel", font=("Segoe UI", 14, "italic"))
        self.lbl_empty.place(relx=0.5, rely=0.4, anchor="center")

        # --- Sidebar Layout: Split into Top (Info) and Bottom (Buttons) ---
        
        # Bottom Frame (Buttons) - Packed FIRST to ensure they stay at bottom
        self.sidebar_bottom = ttk.Frame(container, style="Panel.TFrame")
        self.sidebar_bottom.pack(side="bottom", fill="x", pady=(20, 0))

        # Top Frame (Content) - Takes remaining space
        self.detail_frame = ttk.Frame(container, style="Panel.TFrame")
        
        # --- CONTENT SECTION (Top) ---
        # 1. Header (Big Title)
        self.det_title = ttk.Label(self.detail_frame, text="", style="Panel.TLabel", font=FONT_TITLE, wraplength=420)
        self.det_title.pack(anchor="w", pady=(0, 8))
        
        self.det_meta = ttk.Label(self.detail_frame, text="", style="Muted.TLabel", font=("Segoe UI", 12))
        self.det_meta.pack(anchor="w", pady=(0, 15))

        # 2. Status Pill
        self.det_status_box = tk.Label(self.detail_frame, text="AVAILABLE", bg=COLORS["taupe"], fg=COLORS["cream"], 
                                       font=("Segoe UI", 11, "bold"), padx=15, pady=8)
        self.det_status_box.pack(anchor="w", pady=(0, 20))

        # 3. Description
        ttk.Label(self.detail_frame, text="SYNOPSIS", style="Muted.TLabel", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.det_desc = tk.Text(self.detail_frame, height=10, bg=COLORS["bg"], fg=COLORS["silver"], 
                                bd=0, font=("Segoe UI", 12), wrap="word", padx=15, pady=15)
        self.det_desc.pack(fill="both", expand=True, pady=(5, 0))
        self.det_desc.config(state="disabled")

        # --- BUTTON SECTION (Bottom - Guaranteed Visible) ---
        
        # BORROW BUTTON
        self.btn_action = tk.Button(self.sidebar_bottom, text="BORROW ITEM", bg=COLORS["taupe"], fg=COLORS["cream"], 
                                    font=FONT_BTN, relief="flat", pady=12, cursor="hand2",
                                    command=self.action_borrow_return)
        self.btn_action.pack(fill="x", pady=(0, 10))

        # ROW FOR EDIT / DELETE
        row_admin = ttk.Frame(self.sidebar_bottom, style="Panel.TFrame")
        row_admin.pack(fill="x", pady=(0, 10))

        # EDIT BUTTON
        tk.Button(row_admin, text="EDIT", bg=COLORS["charcoal"], fg=COLORS["white"], 
                  font=FONT_BTN, relief="flat", pady=12, width=15, cursor="hand2",
                  command=self.open_edit_modal).pack(side="left", fill="x", expand=True, padx=(0, 5))

        # DELETE BUTTON
        tk.Button(row_admin, text="DELETE", bg=COLORS["white"], fg=COLORS["bg"], 
                  font=FONT_BTN, relief="flat", pady=12, width=15, cursor="hand2",
                  command=self.action_delete).pack(side="left", fill="x", expand=True, padx=(5, 0))

        # HISTORY BUTTON (UPDATED COLOR)
        # Using Silver background with Dark Text for distinction
        tk.Button(self.sidebar_bottom, text="VIEW HISTORY", bg=COLORS["silver"], fg=COLORS["bg"], 
                  font=("Segoe UI", 10, "bold"), relief="flat", pady=8, cursor="hand2",
                  command=self.view_history).pack(fill="x", pady=(15, 0))

    # --- LOGIC ---

    def safe_api(self, method, endpoint, payload=None, params=None):
        try:
            url = f"{API_BASE}{endpoint}"
            if method == "GET": r = requests.get(url, params=params)
            elif method == "POST": r = requests.post(url, json=payload)
            elif method == "PUT": r = requests.put(url, json=payload)
            elif method == "DELETE": r = requests.delete(url)
            return r
        except:
            messagebox.showerror("Connection Error", "Ensure server.py is running.")
            return None

    def load_data(self):
        r = self.safe_api("GET", "")
        if r:
            self.populate_tree(r.json())
            self.hide_sidebar()

    def search(self):
        q = self.search_var.get()
        if not q: return self.load_data()
        r = self.safe_api("GET", "", params={"q": q})
        if r: self.populate_tree(r.json())

    def populate_tree(self, data):
        self.current_table_data = data # Store actual data reference
        
        for item in self.tree.get_children(): self.tree.delete(item)
        
        # KEY CHANGE: using 'i + 1' for Visual ID
        for i, item in enumerate(data):
            status = "Available" if item['available'] else "Borrowed"
            tag = "even" if i % 2 == 0 else "odd"
            
            # Display i+1 as the ID, but we track the real item via self.current_table_data
            self.tree.insert("", "end", values=(i + 1, item['title'], item['category'], status), tags=(tag,))

    def on_select(self, event):
        sel = self.tree.focus()
        if not sel: return
        
        # Find which row index was clicked (0, 1, 2...)
        # We need to map this back to the REAL database ID
        item_index = self.tree.index(sel)
        
        if item_index < len(self.current_table_data):
            real_item = self.current_table_data[item_index]
            real_id = real_item['id']
            
            # Fetch fresh details using REAL ID
            r = self.safe_api("GET", f"/{real_id}")
            if r and r.status_code == 200:
                self.selected_item = r.json()
                self.show_sidebar()

    # --- SIDEBAR DISPLAY ---

    def hide_sidebar(self):
        self.detail_frame.pack_forget()
        self.sidebar_bottom.pack_forget() # Hide buttons
        self.lbl_empty.place(relx=0.5, rely=0.4, anchor="center")

    def show_sidebar(self):
        self.lbl_empty.place_forget()
        
        # Pack order matters!
        self.sidebar_bottom.pack(side="bottom", fill="x", pady=(20, 0)) # Buttons at bottom
        self.detail_frame.pack(side="top", fill="both", expand=True) # Info fills rest
        
        item = self.selected_item

        self.det_title.config(text=item['title'])
        self.det_meta.config(text=f"{item['creator']}  •  {item['category']}  •  {item['date']}")
        
        self.det_desc.config(state="normal")
        self.det_desc.delete("1.0", "end")
        self.det_desc.insert("1.0", item.get('description', ''))
        self.det_desc.config(state="disabled")

        if item['available']:
            self.det_status_box.config(text="AVAILABLE", bg=COLORS["taupe"], fg=COLORS["cream"])
            self.btn_action.config(text="BORROW ITEM", bg=COLORS["taupe"], fg=COLORS["cream"])
        else:
            self.det_status_box.config(text=f"BORROWED BY {item.get('borrower','').upper()}", bg=COLORS["charcoal"], fg=COLORS["silver"])
            self.btn_action.config(text="RETURN ITEM", bg=COLORS["charcoal"], fg=COLORS["white"])

    # --- ACTIONS ---

    def action_borrow_return(self):
        if not self.selected_item: return
        item_id = self.selected_item['id']
        
        if self.selected_item['available']:
            name = simpledialog.askstring("Reading Club", "Enter Borrower Name:")
            if name:
                r = self.safe_api("POST", f"/{item_id}/borrow", payload={"borrower": name})
                if r and r.status_code == 200: 
                    self.load_data() # Reload full list to update status
                    # Re-select the item to update sidebar
                    self.refresh_selection_by_id(item_id)
        else:
            if messagebox.askyesno("Return", "Confirm return of item?"):
                r = self.safe_api("POST", f"/{item_id}/return")
                if r and r.status_code == 200: 
                    self.load_data()
                    self.refresh_selection_by_id(item_id)

    def action_delete(self):
        if not self.selected_item: return
        if messagebox.askyesno("Delete", "Remove this item from collection?"):
            self.safe_api("DELETE", f"/{self.selected_item['id']}")
            self.selected_item = None
            self.hide_sidebar()
            self.load_data()

    def refresh_selection_by_id(self, target_id):
        # Helper to find the visual row for a specific ID after reload
        for i, item in enumerate(self.current_table_data):
            if item['id'] == target_id:
                # We found the index in the new data
                children = self.tree.get_children()
                if i < len(children):
                    self.tree.selection_set(children[i])
                    self.tree.focus(children[i])
                    self.on_select(None) # Trigger update
                break

    def view_history(self):
        if not self.selected_item: return
        r = self.safe_api("GET", f"/{self.selected_item['id']}/history")
        if r: HistoryWindow(self, r.json())

    # --- MODALS ---
    def open_add_modal(self):
        ItemModal(self, "Add Item", on_submit=self._submit_add)

    def open_edit_modal(self):
        if not self.selected_item: return
        ItemModal(self, "Edit Item", data=self.selected_item, on_submit=self._submit_edit)

    def _submit_add(self, data):
        r = self.safe_api("POST", "", payload=data)
        if r and r.status_code == 201:
            self.load_data()
            messagebox.showinfo("Success", "Item Added")

    def _submit_edit(self, data):
        r = self.safe_api("PUT", f"/{self.selected_item['id']}", payload=data)
        if r and r.status_code == 200:
            self.load_data()
            self.refresh_selection_by_id(self.selected_item['id'])
            messagebox.showinfo("Success", "Item Updated")


class ItemModal(tk.Toplevel):
    def __init__(self, parent, title, data=None, on_submit=None):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=COLORS["bg"])
        self.geometry("500x600")
        self.on_submit = on_submit
        
        pad = 30
        labels = ["Title", "Creator", "Category", "Date"]
        self.entries = {}

        for lbl in labels:
            key = lbl.split()[0].lower()
            ttk.Label(self, text=lbl.upper(), font=("Segoe UI", 9, "bold"), foreground=COLORS["silver"]).pack(anchor="w", padx=pad, pady=(15, 5))
            ent = tk.Entry(self, bg=COLORS["panel"], fg=COLORS["white"], insertbackground=COLORS["white"], relief="flat", font=("Segoe UI", 12))
            ent.pack(fill="x", padx=pad, ipady=8)
            if data: ent.insert(0, data.get(key, ""))
            self.entries[key] = ent

        ttk.Label(self, text="SYNOPSIS", font=("Segoe UI", 9, "bold"), foreground=COLORS["silver"]).pack(anchor="w", padx=pad, pady=(15, 5))
        self.desc = tk.Text(self, height=5, bg=COLORS["panel"], fg=COLORS["white"], relief="flat", font=("Segoe UI", 12))
        self.desc.pack(fill="both", padx=pad, expand=True)
        if data: self.desc.insert("1.0", data.get("description", ""))

        btn_box = ttk.Frame(self, style="TFrame")
        btn_box.pack(fill="x", padx=pad, pady=30)
        
        tk.Button(btn_box, text="SAVE", bg=COLORS["taupe"], fg=COLORS["cream"], font=FONT_BTN, relief="flat", pady=10, width=15, command=self.save).pack(side="right")
        tk.Button(btn_box, text="CANCEL", bg=COLORS["panel"], fg=COLORS["silver"], font=FONT_BTN, relief="flat", pady=10, width=12, command=self.destroy).pack(side="right", padx=15)

    def save(self):
        d = {k: v.get() for k,v in self.entries.items()}
        d["description"] = self.desc.get("1.0", "end").strip()
        if not d["title"]: return messagebox.showerror("Error", "Title Required")
        self.on_submit(d)
        self.destroy()

class HistoryWindow(tk.Toplevel):
    def __init__(self, parent, data):
        super().__init__(parent)
        self.title("History")
        self.geometry("650x500")
        self.configure(bg=COLORS["bg"])
        
        tree = ttk.Treeview(self, columns=("Date","User","Action"), show="headings")
        tree.heading("Date", text="DATE")
        tree.heading("User", text="MEMBER")
        tree.heading("Action", text="ACTIVITY")
        
        style = ttk.Style()
        style.configure("Treeview", rowheight=35, background=COLORS["bg"], foreground=COLORS["silver"])
        
        tree.pack(fill="both", expand=True, padx=30, pady=30)
        
        for row in data:
            tree.insert("", "end", values=(row['date'], row['borrower'], row['action']))

if __name__ == "__main__":
    app = ReadingClubApp()
    app.mainloop()