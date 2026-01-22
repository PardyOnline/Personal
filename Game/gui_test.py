import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

# --- LOAD DATA (Reusing your logic) ---
def load_roster():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, 'roster.json')
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            # Sort by rank logic (Champion -> Rank)
            # Simple sort for demo: Champs first
            data.sort(key=lambda x: (not x.get('is_champion', False))) 
            return data
    except FileNotFoundError:
        return []

roster_data = load_roster()

# --- GUI APP ---
class MatchmakerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("UFC Matchmaker 2012 (GUI Mode)")
        self.root.geometry("900x600")

        # 1. THE LEFT PANEL (ROSTER)
        # Treeview is basically a detailed list/excel sheet
        self.left_frame = tk.Frame(root, width=400)
        self.left_frame.pack(side="left", fill="y", padx=10, pady=10)
        
        tk.Label(self.left_frame, text="ROSTER", font=("Arial", 12, "bold")).pack()
        
        # Table Columns
        self.tree = ttk.Treeview(self.left_frame, columns=("Rank", "Name", "Rec"), show='headings', height=25)
        self.tree.heading("Rank", text="Rank")
        self.tree.heading("Name", text="Name")
        self.tree.heading("Rec", text="Record")
        
        self.tree.column("Rank", width=50)
        self.tree.column("Name", width=150)
        self.tree.column("Rec", width=80)
        self.tree.pack()

        # Populate List
        self.refresh_roster()

        # 2. THE RIGHT PANEL (THE CARD)
        self.right_frame = tk.Frame(root, bg="#f0f0f0")
        self.right_frame.pack(side="right", expand=True, fill="both", padx=10, pady=10)

        tk.Label(self.right_frame, text="UFC 152: FIGHT CARD", font=("Arial", 14, "bold"), bg="#f0f0f0").pack(pady=10)

        # Slots for fights
        self.main_event_frame = self.create_fight_slot("Main Event")
        self.comain_frame = self.create_fight_slot("Co-Main Event")
        
        # Action Buttons
        tk.Button(self.right_frame, text="Book Selected vs Selected", command=self.book_fight, bg="#d9534f", fg="white", font=("Arial", 10, "bold")).pack(pady=20)
        
        # Instruction Label
        self.lbl_instruction = tk.Label(self.right_frame, text="Select 2 fighters from the left list, then click Book!", bg="#f0f0f0")
        self.lbl_instruction.pack()

    def create_fight_slot(self, title):
        frame = tk.Frame(self.right_frame, bd=2, relief="groove", bg="white")
        frame.pack(fill="x", pady=5, padx=10)
        tk.Label(frame, text=title, font=("Arial", 10, "bold"), bg="#ddd").pack(fill="x")
        lbl = tk.Label(frame, text="[ Empty ]   vs   [ Empty ]", font=("Arial", 12), pady=10, bg="white")
        lbl.pack()
        return lbl # Return label so we can update text later

    def refresh_roster(self):
        # Clear old
        for i in self.tree.get_children():
            self.tree.delete(i)
            
        # Add Rows
        for f in roster_data:
            rank = "C" if f['is_champion'] else "NR"
            rec = f"{f['record']['wins']}-{f['record']['losses']}"
            self.tree.insert("", "end", values=(rank, f['name'], rec))

    def book_fight(self):
        # Get selected items
        selected_items = self.tree.selection()
        
        if len(selected_items) != 2:
            messagebox.showwarning("Booking Error", "Please select exactly TWO fighters (Hold Ctrl to select multiple).")
            return

        # Get Names
        item1 = self.tree.item(selected_items[0])
        item2 = self.tree.item(selected_items[1])
        name1 = item1['values'][1]
        name2 = item2['values'][1]
        
        # Update Main Event Label
        self.main_event_frame.config(text=f"🔴 {name1}  vs  🔵 {name2}")
        self.lbl_instruction.config(text="Fight Booked! (This is just a visual demo)")

# --- RUN ---
root = tk.Tk()
app = MatchmakerApp(root)
root.mainloop()
