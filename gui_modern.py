import customtkinter as ctk
from tkinter import ttk, messagebox
import json
import os
import random
import time
import threading

# --- CONFIGURATION ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")
UPDATE_RECORDS = True
TEXT_SPEED = 1.0

# --- DATA CLASSES ---
WEIGHT_CLASSES = ["Heavyweight", "Light Heavyweight", "Middleweight", "Welterweight", 
                  "Lightweight", "Featherweight", "Bantamweight", "Flyweight"]
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
CARD_SLOTS_KEYS = ["Main Event", "Co-Main", "Main Card 3", "Main Card 4", "Main Card 5", "Prelim 1", "Prelim 2", "Prelim 3"]

class GameData:
    def __init__(self):
        self.month_index = 0
        self.year = 2012
        self.event_number = 142
        self.news_feed = [] 
        self.event_history = [] 
        
    def get_date_str(self):
        return f"{MONTHS[self.month_index]} {self.year}"
    
    def get_event_name(self):
        return f"UFC {self.event_number}"

    def advance_time(self):
        self.month_index += 1
        self.event_number += 1
        if self.month_index > 11:
            self.month_index = 0
            self.year += 1
            
    def add_news(self, message):
        date = self.get_date_str()
        self.news_feed.insert(0, f"[{date}] {message}") 
        
    def archive_event(self, event_name, date_str, results_list, total_buys, event_rating):
        self.event_history.append({
            "name": event_name,
            "date": date_str,
            "buys": total_buys,
            "rating": event_rating,
            "results": results_list
        })

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
        self.injury_months = data.get('injury_months', 0)
        self.popularity = data.get('popularity', 10)
        self.age = data.get('age', 25) # Default 25 if missing

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "nickname": self.nickname,
            "weight_class": self.weight_class,
            "stats": {"striking": self.striking, "grappling": self.grappling, "tdd": self.tdd,
                      "sub_off": self.sub_off, "sub_def": self.sub_def, "chin": self.chin, "cardio": self.cardio},
            "traits": self.traits, "record": self.record, "is_champion": self.is_champion,
            "injury_months": self.injury_months,
            "popularity": self.popularity,
            "age": self.age
        }

def load_roster_objects():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, 'roster.json')
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            roster = [Fighter(f) for f in data]
            update_rankings_logic(roster)
            return roster
    except FileNotFoundError: return []

def save_roster_objects(roster):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, 'roster.json')
    data = [f.to_dict() for f in roster]
    with open(file_path, 'w') as f: json.dump(data, f, indent=4)

def update_rankings_logic(roster):
    for div in WEIGHT_CLASSES:
        div_roster = [f for f in roster if f.weight_class == div]
        if not div_roster: continue
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

# --- LOGIC: AGING, REGRESSION & INJURIES ---
def process_monthly_events(roster, game_data):
    events_log = []
    
    # Check if it's January (New Year Update)
    is_january = (game_data.month_index == 0)
    
    if is_january:
        game_data.add_news("🎆 HAPPY NEW YEAR! All fighters have aged 1 year.")
        events_log.append("Happy New Year! Fighters Aged.")

    for f in roster:
        # 1. AGE UPDATE & REGRESSION
        if is_january:
            f.age += 1
            # Regression Logic (Over 35s)
            if f.age > 34:
                # 30% chance to regress each year past 34
                if random.randint(1, 100) <= 30:
                    stat_hit = random.choice(["chin", "cardio", "striking"])
                    current_val = getattr(f, stat_hit)
                    if current_val > 50:
                        setattr(f, stat_hit, current_val - 2)
                        msg = f"REGRESSION: {f.name} ({f.age}) looks slower in training (-2 {stat_hit.title()})."
                        game_data.add_news(msg)

        # 2. INJURY RECOVERY
        if f.injury_months > 0:
            f.injury_months -= 1
            if f.injury_months == 0:
                msg = f"MEDICAL: {f.name} cleared to fight."
                game_data.add_news(msg)
                events_log.append(msg)
            continue 
            
        # 3. RANDOM INJURIES
        chance = 2
        if "Fragile" in f.traits: chance = 5
        if "Hard to Kill" in f.traits: chance = 1
        if random.randint(1, 100) <= chance:
            severity_roll = random.randint(1, 10)
            if severity_roll <= 6: duration = random.randint(1, 2); injury_type = "Minor Injury"
            elif severity_roll <= 9: duration = random.randint(3, 5); injury_type = "Moderate Injury"
            else: duration = random.randint(6, 12); injury_type = "Major Injury"
            f.injury_months = duration
            msg = f"INJURY: {f.name} suffered a {injury_type} ({duration} mo)."
            game_data.add_news(msg)
            events_log.append(msg)

    return events_log

# --- GUI CLASS ---
class UFCGameGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("UFC Matchmaker Pro 2012")
        self.root.geometry("1400x900")
        
        self.roster = load_roster_objects()
        self.game_data = GameData()
        self.current_fights = {key: [None, None] for key in CARD_SLOTS_KEYS}
        self.selected_fighter_obj = None 

        # HEADER
        self.header = ctk.CTkFrame(root, height=80, corner_radius=0, fg_color="#111")
        self.header.pack(fill="x", side="top")
        self.lbl_event_title = ctk.CTkLabel(self.header, text=self.game_data.get_event_name(), font=("Impact", 32), text_color="#D32F2F")
        self.lbl_event_title.pack(side="left", padx=25, pady=5)
        self.lbl_date = ctk.CTkLabel(self.header, text=self.game_data.get_date_str(), font=("Arial", 20, "bold"), text_color="#eee")
        self.lbl_date.pack(side="right", padx=25, pady=10)

        # NAV BAR
        self.nav_bar = ctk.CTkFrame(root, height=40, corner_radius=0, fg_color="#222")
        self.nav_bar.pack(fill="x", side="top")
        self.btn_nav_dashboard = ctk.CTkButton(self.nav_bar, text="DASHBOARD", width=150, fg_color="#333", corner_radius=0, command=lambda: self.show_view("dashboard"))
        self.btn_nav_dashboard.pack(side="left", padx=1)
        self.btn_nav_history = ctk.CTkButton(self.nav_bar, text="EVENT HISTORY", width=150, fg_color="#222", corner_radius=0, command=lambda: self.show_view("history"))
        self.btn_nav_history.pack(side="left", padx=1)
        self.btn_nav_news = ctk.CTkButton(self.nav_bar, text="NEWS & INBOX", width=150, fg_color="#222", corner_radius=0, command=lambda: self.show_view("news"))
        self.btn_nav_news.pack(side="left", padx=1)

        # CONTENT AREA
        self.content_area = ctk.CTkFrame(root, corner_radius=0, fg_color="transparent")
        self.content_area.pack(fill="both", expand=True)

        self.view_dashboard = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.build_dashboard_view(self.view_dashboard)
        self.view_history = ctk.CTkFrame(self.content_area, fg_color="#1a1a1a")
        self.build_history_view(self.view_history)
        self.view_news = ctk.CTkFrame(self.content_area, fg_color="#1a1a1a")
        ctk.CTkLabel(self.view_news, text="NEWS FEED", font=("Impact", 30), text_color="#555").pack(pady=20)
        self.txt_news = ctk.CTkTextbox(self.view_news, font=("Consolas", 14), width=800, height=500, state="disabled", fg_color="#222")
        self.txt_news.pack(pady=10)

        self.show_view("dashboard")

    def show_view(self, view_name):
        self.view_dashboard.pack_forget()
        self.view_history.pack_forget()
        self.view_news.pack_forget()
        self.btn_nav_dashboard.configure(fg_color="#222")
        self.btn_nav_history.configure(fg_color="#222")
        self.btn_nav_news.configure(fg_color="#222")
        if view_name == "dashboard":
            self.view_dashboard.pack(fill="both", expand=True)
            self.btn_nav_dashboard.configure(fg_color="#444")
        elif view_name == "history":
            self.view_history.pack(fill="both", expand=True)
            self.btn_nav_history.configure(fg_color="#444")
            self.refresh_history_list()
        elif view_name == "news":
            self.view_news.pack(fill="both", expand=True)
            self.btn_nav_news.configure(fg_color="#444")
            self.update_news_display()

    def update_news_display(self):
        self.txt_news.configure(state="normal")
        self.txt_news.delete("0.0", "end")
        for item in self.game_data.news_feed:
            self.txt_news.insert("end", item + "\n\n")
        self.txt_news.configure(state="disabled")

    def build_history_view(self, parent):
        left_panel = ctk.CTkFrame(parent, width=300, corner_radius=0, fg_color="#222")
        left_panel.pack(side="left", fill="y")
        ctk.CTkLabel(left_panel, text="PAST EVENTS", font=("Impact", 20)).pack(pady=20)
        self.history_listbox = ctk.CTkScrollableFrame(left_panel, width=280, fg_color="transparent")
        self.history_listbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.history_details = ctk.CTkFrame(parent, fg_color="#1a1a1a")
        self.history_details.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        self.lbl_hist_title = ctk.CTkLabel(self.history_details, text="SELECT AN EVENT", font=("Impact", 36), text_color="#444")
        self.lbl_hist_title.pack(pady=20)
        self.hist_textbox = ctk.CTkTextbox(self.history_details, font=("Arial", 14), width=600, height=500, state="disabled", fg_color="#222")
        self.hist_textbox.pack(pady=10)

    def refresh_history_list(self):
        for widget in self.history_listbox.winfo_children(): widget.destroy()
        for i, event in enumerate(reversed(self.game_data.event_history)):
            btn = ctk.CTkButton(self.history_listbox, text=f"{event['name']} ({event['date']})", 
                                fg_color="#333", hover_color="#444", 
                                command=lambda e=event: self.show_event_details(e))
            btn.pack(fill="x", pady=2)

    def show_event_details(self, event):
        self.lbl_hist_title.configure(text=f"{event['name']} RESULTS")
        self.hist_textbox.configure(state="normal")
        self.hist_textbox.delete("0.0", "end")
        self.hist_textbox.insert("end", f"DATE: {event['date']}\n")
        self.hist_textbox.insert("end", f"PPV BUYS: {event['buys']:,}\n")
        self.hist_textbox.insert("end", f"EVENT RATING: {'★' * event['rating']}\n")
        self.hist_textbox.insert("end", "="*50 + "\n\n")
        for fight in event['results']:
            w_icon = "👑 " if fight['title_fight'] else ""
            stars = "★" * fight['stars']
            self.hist_textbox.insert("end", f"{fight['slot'].upper()} | Rating: {stars}\n")
            self.hist_textbox.insert("end", f"{fight['winner']} def. {fight['loser']}\n")
            self.hist_textbox.insert("end", f"Method: {fight['method']} (R{fight['round']})\n")
            if fight['new_champ']: self.hist_textbox.insert("end", ">>> AND NEW CHAMPION! <<<\n")
            elif fight['still_champ']: self.hist_textbox.insert("end", ">>> AND STILL CHAMPION! <<<\n")
            self.hist_textbox.insert("end", "-"*30 + "\n")
        self.hist_textbox.configure(state="disabled")

    def build_dashboard_view(self, parent):
        col_roster = ctk.CTkFrame(parent, width=320, corner_radius=0, fg_color="#222")
        col_roster.pack(side="left", fill="y")
        self.filter_var = ctk.StringVar(value="All")
        ctk.CTkOptionMenu(col_roster, variable=self.filter_var, values=["All"] + WEIGHT_CLASSES, command=self.refresh_list, fg_color="#333", button_color="#444").pack(fill="x", padx=10, pady=15)
        self.tree_frame = ctk.CTkFrame(col_roster, fg_color="transparent")
        self.tree_frame.pack(fill="both", expand=True, padx=10, pady=(0,10))
        cols = ("Rank", "Name", "Rec", "Pop")
        self.tree = ttk.Treeview(self.tree_frame, columns=cols, show='headings', selectmode="extended")
        self.tree.heading("Rank", text="#")
        self.tree.heading("Name", text="FIGHTER")
        self.tree.heading("Rec", text="REC")
        self.tree.heading("Pop", text="POP")
        self.tree.column("Rank", width=30, anchor="center")
        self.tree.column("Name", width=140)
        self.tree.column("Rec", width=70, anchor="center")
        self.tree.column("Pop", width=40, anchor="center")
        vsb = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_fighter_select)
        self.tree.tag_configure('injured', foreground='#e74c3c')

        col_details = ctk.CTkFrame(parent, fg_color="#1a1a1a")
        col_details.pack(side="left", fill="both", expand=True, padx=2)
        self.lbl_det_name = ctk.CTkLabel(col_details, text="SELECT FIGHTER", font=("Impact", 36), text_color="#444")
        self.lbl_det_name.pack(pady=(60, 5))
        # NEW: Age Label (Dynamic Color)
        self.lbl_age = ctk.CTkLabel(col_details, text="AGE: -", font=("Arial", 14, "bold"), text_color="#aaa")
        self.lbl_age.pack()
        
        self.lbl_status_alert = ctk.CTkLabel(col_details, text="", font=("Arial", 14, "bold"), text_color="#e74c3c")
        self.lbl_status_alert.pack()
        self.lbl_det_record = ctk.CTkLabel(col_details, text="", font=("Arial", 18, "bold"), text_color="#ddd")
        self.lbl_det_record.pack(pady=15)
        self.stats_frame = ctk.CTkFrame(col_details, fg_color="transparent")
        self.stats_frame.pack(pady=20, padx=40, fill="x")
        self.stat_labels = {}
        stat_keys = ["Striking", "Grappling", "Chin", "Cardio", "Sub Off", "Sub Def"]
        for i, key in enumerate(stat_keys):
            row = i // 2; col = i % 2
            f = ctk.CTkFrame(self.stats_frame, fg_color="#2a2a2a", height=50)
            f.grid(row=row, column=col, padx=8, pady=8, sticky="ew")
            ctk.CTkLabel(f, text=key.upper(), font=("Arial", 11, "bold"), text_color="#888", width=80, anchor="w").pack(side="left", padx=15)
            lbl_v = ctk.CTkLabel(f, text="-", font=("Arial", 18, "bold"), text_color="#3498db")
            lbl_v.pack(side="right", padx=15)
            self.stat_labels[key] = lbl_v
            self.stats_frame.columnconfigure(col, weight=1)
        self.lbl_pop = ctk.CTkLabel(col_details, text="POPULARITY: -", font=("Impact", 18), text_color="#f1c40f")
        self.lbl_pop.pack(pady=10)
        ctk.CTkLabel(col_details, text="TRAITS", font=("Arial", 12, "bold"), text_color="#666").pack(pady=(20, 5))
        self.lbl_traits = ctk.CTkLabel(col_details, text="-", font=("Arial", 14), wraplength=250)
        self.lbl_traits.pack()

        self.col_card = ctk.CTkFrame(parent, width=450, corner_radius=0, fg_color="#111")
        self.col_card.pack(side="right", fill="y", padx=(2,0))
        self.col_card.pack_propagate(False)
        ctk.CTkLabel(self.col_card, text="FULL FIGHT CARD", font=("Impact", 22), text_color="#eee").pack(pady=(20, 10))
        self.scroll_card = ctk.CTkScrollableFrame(self.col_card, width=420, height=600, fg_color="#111")
        self.scroll_card.pack(fill="both", expand=True, padx=5)
        self.card_slots = {}
        for key in CARD_SLOTS_KEYS:
            color = "#C62828" if key == "Main Event" else ("#444" if key == "Co-Main" else "#222")
            h = 110 if key == "Main Event" else 90
            self.card_slots[key] = self.create_slot_ui(self.scroll_card, key.upper(), key, h, color)
        self.btn_run = ctk.CTkButton(self.col_card, text="RUN EVENT (0/8 Filled)", fg_color="#555", hover_color="#555", height=60, font=("Impact", 18), state="disabled", command=self.run_event_window)
        self.btn_run.pack(side="bottom", pady=20, padx=30, fill="x")
        self.refresh_list("All")

    def create_slot_ui(self, parent, label_text, slot_key, height, color):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="x", padx=5, pady=5)
        header = ctk.CTkFrame(container, height=24, fg_color=color, corner_radius=4)
        header.pack(fill="x")
        ctk.CTkLabel(header, text=label_text, font=("Arial", 11, "bold"), text_color="white").place(relx=0.5, rely=0.5, anchor="center")
        body = ctk.CTkFrame(container, height=height, fg_color="#1a1a1a", border_color=color, border_width=1, corner_radius=4)
        body.pack(fill="x"); body.pack_propagate(False)
        content_frame = ctk.CTkFrame(body, fg_color="transparent")
        content_frame.place(relx=0.5, rely=0.5, anchor="center")
        red_lbl = ctk.CTkLabel(content_frame, text="Empty", font=("Impact", 16), text_color="#777")
        red_lbl.pack()
        ctk.CTkLabel(content_frame, text="vs", font=("Arial", 10, "italic"), text_color="#555").pack(pady=0)
        blue_lbl = ctk.CTkLabel(content_frame, text="Empty", font=("Impact", 16), text_color="#777")
        blue_lbl.pack()
        btn = ctk.CTkButton(body, text="+", width=30, height=20, fg_color="#333", hover_color="#555", command=lambda s=slot_key, r=red_lbl, b=blue_lbl: self.book_selected_to_slot(s, r, b))
        btn.place(relx=0.92, rely=0.85, anchor="center")
        return {"red": red_lbl, "blue": blue_lbl}

    def on_fighter_select(self, event):
        selected = self.tree.selection()
        if not selected: return
        item = self.tree.item(selected[0])
        name = item['values'][1]
        f = next((x for x in self.roster if x.name == name), None)
        if f: self.selected_fighter_obj = f; self.update_details_panel(f)

    def update_details_panel(self, f):
        self.lbl_det_name.configure(text=f.name.upper(), text_color="#e74c3c" if f.injury_months > 0 else "white")
        if f.injury_months > 0: self.lbl_status_alert.configure(text=f"⚠️ INJURED (Out {f.injury_months} Mo)")
        else: self.lbl_status_alert.configure(text="")
        
        # Age Color Logic
        age_col = "#2ecc71" if f.age < 29 else ("#e74c3c" if f.age > 35 else "#aaa")
        self.lbl_age.configure(text=f"AGE: {f.age}", text_color=age_col)

        self.lbl_det_record.configure(text=f"Record: {f.record['wins']}-{f.record['losses']}")
        self.stat_labels["Striking"].configure(text=f.striking); self.stat_labels["Grappling"].configure(text=f.grappling)
        self.stat_labels["Chin"].configure(text=f.chin); self.stat_labels["Cardio"].configure(text=f.cardio)
        self.stat_labels["Sub Off"].configure(text=f.sub_off); self.stat_labels["Sub Def"].configure(text=f.sub_def)
        self.lbl_pop.configure(text=f"POPULARITY: {f.popularity}")
        self.lbl_traits.configure(text=", ".join(f.traits) if f.traits else "None")

    def refresh_list(self, choice=None):
        if choice is None: choice = self.filter_var.get()
        for item in self.tree.get_children(): self.tree.delete(item)
        display_list = self.roster
        if choice != "All": display_list = [f for f in self.roster if f.weight_class == choice]
        display_list.sort(key=lambda x: x.rank)
        for f in display_list:
            rank_str = "C" if f.is_champion else f"{f.rank}" if f.rank <= 15 else "-"
            status_str = f"INJ({f.injury_months})" if f.injury_months > 0 else "OK"
            rec_str = f"{f.record['wins']}-{f.record['losses']}"
            self.tree.insert("", "end", values=(rank_str, f.name, rec_str, f.popularity), tags=('injured',) if f.injury_months > 0 else ())
        self.tree.tag_configure('injured', foreground='#e74c3c')

    def check_card_complete(self):
        filled_count = 0
        total = len(CARD_SLOTS_KEYS)
        for k in CARD_SLOTS_KEYS:
            if self.current_fights[k][0] is not None:
                filled_count += 1
        if filled_count == total:
            self.btn_run.configure(state="normal", text="RUN EVENT (Ready!)", fg_color="#2ecc71")
        else:
            self.btn_run.configure(state="disabled", text=f"RUN EVENT ({filled_count}/{total} Filled)", fg_color="#555")

    def book_selected_to_slot(self, slot_name, red_lbl, blue_lbl):
        selected_items = self.tree.selection()
        if len(selected_items) != 2: messagebox.showwarning("Select Fighters", "Please hold CTRL and select exactly 2 fighters."); return
        n1 = self.tree.item(selected_items[0])['values'][1]; n2 = self.tree.item(selected_items[1])['values'][1]
        f1 = next((x for x in self.roster if x.name == n1), None); f2 = next((x for x in self.roster if x.name == n2), None)
        if f1.injury_months > 0 or f2.injury_months > 0: messagebox.showerror("Injury", "Cannot book injured fighter!"); return
        if f1.weight_class != f2.weight_class:
             if not messagebox.askyesno("Weight Mismatch", f"Book {f1.weight_class} vs {f2.weight_class}?"): return
        self.current_fights[slot_name] = [f1, f2]
        c1 = "👑 " if f1.is_champion else ""; c2 = "👑 " if f2.is_champion else ""
        red_lbl.configure(text=f"{c1}{f1.name}", text_color="white"); blue_lbl.configure(text=f"{c2}{f2.name}", text_color="white")
        self.check_card_complete()

    def run_event_window(self):
        for k in CARD_SLOTS_KEYS:
            if not self.current_fights[k][0]: messagebox.showerror("Incomplete Card", "You must fill all 8 slots!"); return
        sim_win = ctk.CTkToplevel(self.root)
        sim_win.title("Live Simulation")
        sim_win.geometry("700x600")
        txt_area = ctk.CTkTextbox(sim_win, font=("Consolas", 12), state="disabled", fg_color="#111", text_color="#0f0")
        txt_area.pack(fill="both", expand=True, padx=5, pady=5)
        def log(text): txt_area.configure(state="normal"); txt_area.insert("end", text + "\n"); txt_area.see("end"); txt_area.configure(state="disabled")
        
        def run_thread():
            log("🔥 EVENT STARTING... 🔥\n")
            reverse_order = list(reversed(CARD_SLOTS_KEYS))
            event_results = []
            total_card_stars = 0
            main_event_pop = 0
            
            for slot in reverse_order:
                f1, f2 = self.current_fights[slot]
                is_main = (slot == "Main Event")
                if is_main: main_event_pop = (f1.popularity + f2.popularity)
                result_data = self.simulate_fight_logic(f1, f2, is_main, slot, log)
                total_card_stars += result_data['stars']
                event_results.append(result_data)
            
            avg_stars = total_card_stars / 8
            base_buys = 100000 
            pop_buys = main_event_pop * 4000
            quality_bonus = avg_stars * 25000
            total_buys = int(base_buys + pop_buys + quality_bonus + random.randint(-20000, 20000))
            event_rating = int(avg_stars)
            if event_rating < 1: event_rating = 1
            if event_rating > 5: event_rating = 5

            log("\n" + "="*30)
            log(f"💰 PPV BUYS: {total_buys:,}")
            log(f"⭐ EVENT RATING: {event_rating}/5 Stars")
            log("="*30)

            self.game_data.archive_event(self.game_data.get_event_name(), self.game_data.get_date_str(), event_results, total_buys, event_rating)

            log("\n🏁 Event Over.")
            log(f"📅 Advancing Date to Next Month...")
            self.game_data.advance_time()
            self.reset_card_slots()
            injury_logs = process_monthly_events(self.roster, self.game_data)
            for msg in injury_logs: log(f" > {msg}")
            if UPDATE_RECORDS: save_roster_objects(self.roster)
            update_rankings_logic(self.roster)
            self.refresh_list()
            self.root.after(0, self.update_header_info)

        threading.Thread(target=run_thread, daemon=True).start()

    def update_header_info(self):
        self.lbl_event_title.configure(text=self.game_data.get_event_name())
        self.lbl_date.configure(text=self.game_data.get_date_str())

    def reset_card_slots(self):
        self.current_fights = {key: [None, None] for key in CARD_SLOTS_KEYS}
        for slot in self.card_slots:
            self.card_slots[slot]["red"].configure(text="Empty", text_color="#777")
            self.card_slots[slot]["blue"].configure(text="Empty", text_color="#777")
        self.check_card_complete()

    def simulate_fight_logic(self, f1, f2, is_main, slot_name, log_func):
        is_title = is_main and (f1.is_champion or f2.is_champion)
        if f2.is_champion and not f1.is_champion: f1, f2 = f2, f1
        rounds = 5 if is_title or is_main else 3
        log_func(f"\n>> {f1.name} vs {f2.name} <<"); time.sleep(1.0)
        judge_scores = [[0,0], [0,0], [0,0]]; winner = None; method = "Decision"; finish_round = 0
        fight_stars = 2 
        damage_exchanged = 0
        
        for r in range(1, rounds+1):
            log_func(f"🔔 R{r}..."); time.sleep(TEXT_SPEED * 0.3); stats = {f1.name: 0, f2.name: 0}
            for _ in range(5):
                attacker = f1 if random.choice([True, False]) else f2
                defender = f2 if attacker == f1 else f1
                if attacker.grappling > defender.striking:
                     if attacker.grappling + random.randint(-20, 20) > defender.tdd:
                        log_func(f"  > {attacker.name} Takedown!"); stats[attacker.name] += 10
                        if attacker.sub_off + random.randint(0,20) > defender.sub_def + 30: winner = attacker; method = "SUBMISSION"; finish_round = r; break 
                     else: log_func(f"  > {attacker.name} shoots, stuffed.")
                else:
                     if attacker.striking + random.randint(-20,20) > defender.striking:
                        log_func(f"  > {attacker.name} Lands!"); stats[attacker.name] += 10; defender.total_damage_taken += 10
                        damage_exchanged += 10
                        if random.randint(0,100) > (defender.chin - (defender.total_damage_taken*0.5)): winner = attacker; method = "KNOCKOUT"; finish_round = r; break
                time.sleep(TEXT_SPEED * 0.1)
            if winner: break
            s1, s2 = stats[f1.name], stats[f2.name]
            for j in range(3):
                 if s1 > s2: judge_scores[j][0]+=10; judge_scores[j][1]+=9
                 elif s2 > s1: judge_scores[j][0]+=9; judge_scores[j][1]+=10
                 else: judge_scores[j][0]+=10; judge_scores[j][1]+=10
        if not winner:
            votes_f1 = sum(1 for s in judge_scores if s[0] > s[1])
            winner = f1 if votes_f1 >= 2 else f2; method = "DECISION"; finish_round = rounds
            
        loser = f2 if winner == f1 else f1
        log_func(f"🏆 {winner.name} via {method}")
        
        if method == "KNOCKOUT": fight_stars += 2
        elif method == "SUBMISSION": fight_stars += 1
        if finish_round == 1: fight_stars += 1
        if damage_exchanged > 100: fight_stars += 1
        if damage_exchanged < 30 and method == "DECISION": fight_stars -= 1 
        if is_title: fight_stars += 1
        if fight_stars > 5: fight_stars = 5
        if fight_stars < 1: fight_stars = 1

        new_champ = False; still_champ = False
        if is_title:
            if winner.is_champion: log_func("👑 AND STILL!"); still_champ = True
            else: log_func("👑 AND NEW!"); new_champ = True; winner.is_champion = True; f1.is_champion = False if winner == f2 else f1.is_champion; f2.is_champion = False if winner == f1 else f2.is_champion
        
        if UPDATE_RECORDS:
            winner.record['wins'] += 1; loser.record['losses'] += 1
            if winner.popularity < 90: winner.popularity += random.randint(1, 3)
            # PROGESSION LOGIC
            if winner.age < 28 and random.randint(1,100) < 50:
                stat = random.choice(["striking", "grappling", "tdd"])
                curr = getattr(winner, stat)
                if curr < 95:
                    setattr(winner, stat, curr + 1)
                    log_func(f"📈 DEVELOPMENT: {winner.name} improved {stat} (+1)!")
            # DAMAGE LOGIC
            if method == "KNOCKOUT":
                loser.chin -= 1
                log_func(f"📉 DAMAGE: {loser.name}'s chin degraded (-1).")
            
        return {"slot": slot_name, "winner": winner.name, "loser": loser.name, "method": method, "round": finish_round, "title_fight": is_title, "new_champ": new_champ, "still_champ": still_champ, "stars": fight_stars}

if __name__ == "__main__":
    app = ctk.CTk()
    gui = UFCGameGUI(app)
    app.mainloop()