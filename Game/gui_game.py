import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os
import random
import time
import threading # To run the fight without freezing the window
# --- CONFIGURATION ---
UPDATE_RECORDS = False  # Set to True when you are ready for the real career mode

# --- 1. THE LOGIC BACKEND (Reused from your previous code) ---
WEIGHT_CLASSES = ["Heavyweight", "Light Heavyweight", "Middleweight", "Welterweight", 
                  "Lightweight", "Featherweight", "Bantamweight", "Flyweight"]

class Fighter:
    def __init__(self, data):
        self.id = data['id']
        self.name = data['name']
        self.nickname = data.get('nickname', "")
        self.weight_class = data['weight_class']
        stats = data['stats']
        self.striking = stats['striking']
        self.grappling = stats['grappling']
        self.tdd = stats['tdd']
        self.sub_off = stats['sub_off']
        self.sub_def = stats['sub_def']
        self.chin = stats['chin']
        self.cardio = stats['cardio']
        self.traits = data['traits']
        self.record = data['record']
        self.is_champion = data['is_champion']
        self.rank = 999 
        self.total_damage_taken = 0

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "nickname": self.nickname,
            "weight_class": self.weight_class,
            "stats": {"striking": self.striking, "grappling": self.grappling, "tdd": self.tdd,
                      "sub_off": self.sub_off, "sub_def": self.sub_def, "chin": self.chin, "cardio": self.cardio},
            "traits": self.traits, "record": self.record, "is_champion": self.is_champion
        }

def load_roster_objects():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, 'roster.json')
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            roster = [Fighter(f) for f in data]
            update_rankings_logic(roster) # Auto-rank on load
            return roster
    except FileNotFoundError:
        messagebox.showerror("Error", "roster.json not found!")
        return []

def save_roster_objects(roster):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, 'roster.json')
    data = [f.to_dict() for f in roster]
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def update_rankings_logic(roster):
    for div in WEIGHT_CLASSES:
        div_roster = [f for f in roster if f.weight_class == div]
        if not div_roster: continue
        
        # Scoring Formula
        def sort_key(f):
            if f.is_champion: return 10000
            score = (f.record['wins'] * 10) - (f.record['losses'] * 3) + ((f.striking+f.grappling)//2)
            return score

        div_roster.sort(key=sort_key, reverse=True)
        
        rank_counter = 1
        for f in div_roster:
            if f.is_champion: f.rank = 0
            else:
                f.rank = rank_counter
                rank_counter += 1

# --- 2. THE GUI FRONTEND ---
class UFCGameGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("UFC Matchmaker: Career Mode")
        self.root.geometry("1000x700")
        
        # Load Data
        self.roster = load_roster_objects()
        self.current_fights = {"Main Event": [None, None], "Co-Main": [None, None]}

        # --- LAYOUT ---
        # Left Panel (Roster)
        self.left_frame = tk.Frame(root, width=400, padx=10, pady=10)
        self.left_frame.pack(side="left", fill="y")
        
        # Filter Dropdown
        tk.Label(self.left_frame, text="Weight Class:", font=("Arial", 10, "bold")).pack(anchor="w")
        self.filter_var = tk.StringVar(value="All")
        self.combo_filter = ttk.Combobox(self.left_frame, textvariable=self.filter_var, state="readonly")
        self.combo_filter['values'] = ["All"] + WEIGHT_CLASSES
        self.combo_filter.pack(fill="x", pady=5)
        self.combo_filter.bind("<<ComboboxSelected>>", self.refresh_list)

        # Roster Table (Treeview)
        cols = ("Rank", "Name", "Rec", "OVR")
        self.tree = ttk.Treeview(self.left_frame, columns=cols, show='headings', height=30)
        self.tree.heading("Rank", text="Rank")
        self.tree.heading("Name", text="Name")
        self.tree.heading("Rec", text="Rec")
        self.tree.heading("OVR", text="OVR")
        
        self.tree.column("Rank", width=40)
        self.tree.column("Name", width=140)
        self.tree.column("Rec", width=60)
        self.tree.column("OVR", width=40)
        self.tree.pack(fill="both", expand=True)

        # Right Panel (Card Management)
        self.right_frame = tk.Frame(root, bg="#eaeaea", padx=20, pady=20)
        self.right_frame.pack(side="right", fill="both", expand=True)

        tk.Label(self.right_frame, text="UFC FIGHT NIGHT", font=("Impact", 20), bg="#eaeaea").pack(pady=10)

        # Slot 1: Main Event
        self.frame_main = self.create_fight_slot("MAIN EVENT", "Main Event")
        # Slot 2: Co-Main
        self.frame_comain = self.create_fight_slot("CO-MAIN EVENT", "Co-Main")

        # Run Button
        self.btn_run = tk.Button(self.right_frame, text="RUN EVENT", bg="green", fg="white", font=("Arial", 14, "bold"), state="disabled", command=self.run_event_window)
        self.btn_run.pack(pady=30, fill="x")

        # Initial Load
        self.refresh_list()

    def create_fight_slot(self, label_text, slot_key):
        frame = tk.Frame(self.right_frame, bd=2, relief="groove", bg="white", pady=10)
        frame.pack(fill="x", pady=10)
        
        tk.Label(frame, text=label_text, font=("Arial", 12, "bold"), bg="#ddd").pack(fill="x")
        
        lbl_vs = tk.Label(frame, text="[ Empty ]   vs   [ Empty ]", font=("Arial", 12), bg="white", pady=10)
        lbl_vs.pack()
        
        # Buttons
        btn_frame = tk.Frame(frame, bg="white")
        btn_frame.pack(pady=5)
        
        btn_book = tk.Button(btn_frame, text="Book Selected (2 Fighters)", command=lambda: self.book_fight(slot_key, lbl_vs))
        btn_book.pack()
        
        return frame

    def refresh_list(self, event=None):
        # Clear Tree
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        selected_div = self.filter_var.get()
        
        # Filter Logic
        display_list = self.roster
        if selected_div != "All":
            display_list = [f for f in self.roster if f.weight_class == selected_div]
            
        # Sort Logic (Rank)
        display_list.sort(key=lambda x: x.rank)

        for f in display_list:
            rank_str = "C" if f.is_champion else f"#{f.rank}" if f.rank <= 15 else "NR"
            ovr = (f.striking + f.grappling) // 2
            rec = f"{f.record['wins']}-{f.record['losses']}"
            
            # Store ID in tags or hidden values if needed, here we rely on object lookup
            self.tree.insert("", "end", values=(rank_str, f.name, rec, ovr), tags=(str(f.id),))

    def book_fight(self, slot_key, label_widget):
        selected_items = self.tree.selection()
        if len(selected_items) != 2:
            messagebox.showwarning("Booking", "Select exactly 2 fighters from the list (Hold CTRL or Shift).")
            return

        # Find fighters by Name (Simplified for demo) or use ID mapping
        # Let's grab the names from the tree columns
        row1 = self.tree.item(selected_items[0])['values']
        row2 = self.tree.item(selected_items[1])['values']
        
        name1 = row1[1]
        name2 = row2[1]
        
        # Find objects
        f1 = next((f for f in self.roster if f.name == name1), None)
        f2 = next((f for f in self.roster if f.name == name2), None)
        
        # Validation
        if f1.weight_class != f2.weight_class:
            if not messagebox.askyesno("Catchweight", f"Different weights ({f1.weight_class} vs {f2.weight_class}). Allow?"):
                return

        # Book it
        self.current_fights[slot_key] = [f1, f2]
        label_widget.config(text=f"🔴 {f1.name}   vs   🔵 {f2.name}")
        
        # Enable Run Button if Main Event is booked
        if self.current_fights["Main Event"][0] is not None:
            self.btn_run.config(state="normal")

    # --- 3. THE FIGHT SIMULATION POPUP ---
    def run_event_window(self):
        # Create Popup
        sim_win = tk.Toplevel(self.root)
        sim_win.title("Live Fight Simulation")
        sim_win.geometry("600x500")
        
        # Text Area
        txt_area = scrolledtext.ScrolledText(sim_win, font=("Courier", 10), state="disabled")
        txt_area.pack(fill="both", expand=True)
        
        # Helper to print to GUI
        def log(text):
            txt_area.config(state="normal")
            txt_area.insert("end", text + "\n")
            txt_area.see("end")
            txt_area.config(state="disabled")

        # Run logic in a thread so GUI doesn't freeze
        def run_thread():
            log("🔥 EVENT STARTING... 🔥\n")
            
            # Run Co-Main
            if self.current_fights["Co-Main"][0]:
                f1, f2 = self.current_fights["Co-Main"]
                self.simulate_fight_gui(f1, f2, False, log)
            
            # Run Main Event
            if self.current_fights["Main Event"][0]:
                f1, f2 = self.current_fights["Main Event"]
                self.simulate_fight_gui(f1, f2, True, log)
            
            log("\n🏁 Event Over.")
            
            if UPDATE_RECORDS:
                log("💾 Saving Data...")
                save_roster_objects(self.roster)
            
            # Re-rank and Refresh GUI
            update_rankings_logic(self.roster)
            self.root.after(0, self.refresh_list)
            
            # Run Main Event
            if self.current_fights["Main Event"][0]:
                f1, f2 = self.current_fights["Main Event"]
                self.simulate_fight_gui(f1, f2, True, log) # True = Title logic capable
            
            log("\n💾 Event Over. Saving Records...")
            save_roster_objects(self.roster)
            # Re-rank and Refresh GUI main window
            update_rankings_logic(self.roster)
            self.root.after(0, self.refresh_list)

        threading.Thread(target=run_thread, daemon=True).start()

    def simulate_fight_gui(self, f1, f2, is_main, log_func):
        # Determine if title fight (If it's main event AND one holds a belt)
        is_title = False
        if is_main and (f1.is_champion or f2.is_champion):
            is_title = True
        
        # Walkout Logic: Ensure Champion is always F1 (Red Corner) for display
        if f2.is_champion and not f1.is_champion:
             f1, f2 = f2, f1
        
        rounds = 5 if is_title or is_main else 3
        
        log_func("\n" + "="*40)
        log_func(f"FIGHT: {f1.name} vs {f2.name}")
        if is_title: log_func("🏆 FOR THE CHAMPIONSHIP 🏆")
        log_func("="*40 + "\n")
        time.sleep(1.5)
        
        judge_scores = [[0,0], [0,0], [0,0]]
        winner = None
        method = "Decision"
        finish_round = 0

        # --- FIGHT LOOP ---
        for r in range(1, rounds+1):
            log_func(f"\n🔔 Round {r} begins...")
            time.sleep(1)
            
            stats = {f1.name: 0, f2.name: 0} # Round Scoring
            
            # 5 'Exchanges' per round
            for i in range(5):
                attacker = f1 if random.choice([True, False]) else f2
                defender = f2 if attacker == f1 else f1
                
                # Logic: Grapple or Strike?
                wants_grapple = (attacker.grappling > defender.striking)
                
                if wants_grapple:
                    if attacker.grappling + random.randint(-20, 20) > defender.tdd:
                        log_func(f"  > {attacker.name} scores a TAKEDOWN!")
                        stats[attacker.name] += 10
                        # Submission Check
                        if attacker.sub_off + random.randint(0,20) > defender.sub_def + 30:
                            winner = attacker
                            method = "SUBMISSION"
                            finish_round = r
                            log_func(f"  > ⚠️ {attacker.name} locks in a choke!! TAPS!")
                            break 
                    else:
                        log_func(f"  > {attacker.name} shoots, stuffed.")
                else:
                    # Strike Check
                    if attacker.striking + random.randint(-20,20) > defender.striking:
                        log_func(f"  > {attacker.name} lands a clean strike.")
                        stats[attacker.name] += 10
                        defender.total_damage_taken += 10
                        # KO Check
                        if random.randint(0,100) > (defender.chin - (defender.total_damage_taken*0.5)):
                            winner = attacker
                            method = "KNOCKOUT"
                            finish_round = r
                            log_func(f"  > 💥 BIG SHOT! {defender.name} IS OUT COLD!")
                            break
            
            if winner: break
            
            # End of Round Scoring
            s1 = stats[f1.name]
            s2 = stats[f2.name]
            for j in range(3):
                 if s1 > s2: judge_scores[j][0]+=10; judge_scores[j][1]+=9
                 elif s2 > s1: judge_scores[j][0]+=9; judge_scores[j][1]+=10
                 else: judge_scores[j][0]+=10; judge_scores[j][1]+=10
            time.sleep(0.5)

        # --- RESULT PROCESSING ---
        log_func("\n" + "-"*20)
        
        # 1. Determine Winner
        if not winner:
            votes_f1 = 0
            for s in judge_scores:
                if s[0] > s[1]: votes_f1 += 1
            
            winner = f1 if votes_f1 >= 2 else f2
            method = "DECISION"
            log_func(f"🏆 WINNER via {method}: {winner.name}")
        else:
            log_func(f"🏆 WINNER: {winner.name} via {method} (R{finish_round})")

        loser = f2 if winner == f1 else f1

        # 2. TITLE CHANGE LOGIC (The Fixed Part)
        if is_title:
            if winner.is_champion:
                log_func(f"👑 AND STILL! {winner.name} retains the title!")
            else:
                log_func(f"👑 AND NEW! {winner.name} captures the belt!")
                # Immediate Swap in memory
                winner.is_champion = True
                loser.is_champion = False

        # 3. RECORD UPDATES (Only if Sandbox Mode is OFF)
        # if UPDATE_RECORDS:
        #     winner.record['wins'] += 1
        #     loser.record['losses'] += 1
        #     log_func("📝 Records Updated.")
        # else:
        #     log_func("🚫 Sandbox Mode: Records not saved.")

# --- RUN APP ---
if __name__ == "__main__":
    root = tk.Tk()
    app = UFCGameGUI(root)
    root.mainloop()
