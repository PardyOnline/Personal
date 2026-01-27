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

# --- CONSTANTS ---
WEIGHT_CLASSES = ["Heavyweight", "Light Heavyweight", "Middleweight", "Welterweight", 
                  "Lightweight", "Featherweight", "Bantamweight", "Flyweight"]
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
CARD_SLOTS_KEYS = ["Main Event", "Co-Main", "Main Card 3", "Main Card 4", "Main Card 5", "Prelim 1", "Prelim 2", "Prelim 3"]

# Name Database (For random regens)
FIRST_NAMES = ["Mike", "Joe", "Kevin", "Liam", "Thiago", "Magomed", "Khabib", "Conor", "Dustin", "Max", "Israel", "Kamaru", "Jorge", "Nate", "Nick", "Sean", "Justin", "Charles", "Francis", "Stipe", "Ciryl", "Tom", "Paddy", "Ian", "Shavkat", "Islam", "Alex", "Glover", "Jan", "Jiri", "Jamahal", "Aljamain", "Merab", "Cory", "Petr", "Henry", "Deiveson", "Brandon", "Kai", "Amir", "Movsar", "Ilia", "Arman", "Beneil", "Rafael", "Gilbert", "Belal", "Colby", "Robert", "Jared", "Paulo", "Marvin", "Dricus", "Khamzat", "Bo", "Raul"]
LAST_NAMES = ["Smith", "Silva", "Johnson", "Jones", "Pereira", "Oliveira", "Magomedov", "Nurmagomedov", "McGregor", "Poirier", "Holloway", "Adesanya", "Usman", "Masvidal", "Diaz", "O'Malley", "Gaethje", "Ngannou", "Miocic", "Gane", "Aspinall", "Pimblett", "Garry", "Rakhmonov", "Makhachev", "Teixeira", "Blachowicz", "Prochazka", "Hill", "Sterling", "Dvalishvili", "Sandhagen", "Yan", "Cejudo", "Figueiredo", "Moreno", "Kara-France", "Albazi", "Evloev", "Topuria", "Tsarukyan", "Dariush", "Fiziev", "Burns", "Muhammad", "Covington", "Whittaker", "Cannonier", "Costa", "Vettori", "Du Plessis", "Chimaev", "Nickal", "Rosas"]
NICKNAMES = ["The Eraser", "The Eagle", "Notorious", "Diamond", "Blessed", "Stylebender", "Nigerian Nightmare", "Gamebred", "Suga", "Highlight", "Predator", "Bon Gamin", "The Baddy", "The Future", "Nomad", "Poatan", "Polish Power", "Samurai", "Sweet Dreams", "Funk Master", "The Machine", "Sandman", "No Mercy", "The Messenger", "God of War", "Assassin Baby", "Don't Blink", "The Prince", "Matador", "Ahalkalakets", "Benny", "Ataman", "Durinho", "Remember the Name", "Chaos", "The Reaper", "Killa Gorilla", "The Italian Dream", "Stillknocks", "Borz"]

# --- COMMENTARY ENGINE ---
COMMENTARY_DB = {
    "strike_light": ["lands a jab.", "pops the jab.", "connects with a quick left.", "touches them with a right.", "lands a glancing blow.", "nice 1-2 combo."],
    "leg_kick": ["CHOPS the leg!", "lands a heavy leg kick.", "invests in a low kick.", "kicks the lead leg.", "that leg kick echoed!"],
    "body_shot": ["digs to the body!", "lands a knee to the ribs.", "rips a left hook to the liver.", "teep kick to the gut."],
    "strike_heavy": ["HUGE RIGHT HAND!", "LANDS A BOMB!", "BIG KNEE TO THE HEAD!", "HEAD KICK CONNECTS!", "THEY ARE WOBBLED!", "CRUSHING overhand!", "massive elbow!"],
    "knockdown": ["OH! HE DROPPED HIM!", "DOWN GOES THE OPPONENT!", "A HUGE KNOCKDOWN!", "HE'S HURT BADLY!"],
    "takedown": ["shoots and SCORES the double leg.", "trips them to the mat.", "beautiful blast double leg.", "dumps them on their head!", "drags them down."],
    "takedown_stuff": ["stuffs the takedown.", "shrugs them off.", "nice sprawl.", "defends the shot easily."],
    "ko": ["OUT COLD!", "FACE PLANT!", "IT IS ALL OVER!", "JUST LIKE THAT!", "SENT TO THE SHADOW REALM!"],
    "sub": ["HE TAPS! HE TAPS!", "IT IS TIGHT! IT'S OVER!", "GOES TO SLEEP!", "GETS THE SUBMISSION!"]
}

def get_commentary(category): return random.choice(COMMENTARY_DB[category])

# --- GAME LOGIC CLASSES ---
class GameData:
    def __init__(self):
        self.month_index = 0
        self.year = 2012
        self.event_number = 142
        self.news_feed = [] 
        self.event_history = []
        self.free_agents = [] 
        self.spawned_legends = [] # Track names of prospects already spawned
        
    def get_date_str(self): return f"{MONTHS[self.month_index]} {self.year}"
    def get_event_name(self): return f"UFC {self.event_number}"

    def advance_time(self):
        self.month_index += 1
        self.event_number += 1
        if self.month_index > 11:
            self.month_index = 0
            self.year += 1
            
    def add_news(self, message):
        date = self.get_date_str()
        self.news_feed.insert(0, f"[{date}] {message}") 
        
    def archive_event(self, event_name, date_str, results_list, total_buys, event_rating, awards):
        self.event_history.append({"name": event_name, "date": date_str, "buys": total_buys, "rating": event_rating, "results": results_list, "awards": awards})

class Fighter:
    def __init__(self, data):
        self.id = data.get('id', 0)
        self.name = data['name']
        self.nickname = data.get('nickname', "")
        self.weight_class = data['weight_class']
        self.stats = data['stats']
        self.striking = self.stats['striking']
        self.grappling = self.stats['grappling']
        self.tdd = self.stats['tdd']
        self.sub_off = self.stats['sub_off']
        self.sub_def = self.stats['sub_def']
        self.chin = self.stats['chin']
        self.cardio = self.stats['cardio']
        
        self.traits = data.get('traits', [])
        self.record = data.get('record', {"wins": 0, "losses": 0, "draws": 0})
        self.is_champion = data.get('is_champion', False)
        self.rank = 999 
        self.total_damage_taken = 0
        self.injury_months = data.get('injury_months', 0)
        self.popularity = data.get('popularity', 10)
        self.age = data.get('age', 25)
        self.history = data.get('history', []) 
        
        self.annual_stats = data.get('annual_stats', {'wins': 0, 'finishes': 0})
        
        # Rankings Init (Squashed)
        raw_score = (self.record['wins'] * 50) - (self.record['losses'] * 10)
        self.ranking_score = data.get('ranking_score', min(raw_score, 1500))
        if self.is_champion: self.ranking_score = 2000

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "nickname": self.nickname, "weight_class": self.weight_class,
            "stats": {"striking": self.striking, "grappling": self.grappling, "tdd": self.tdd, "sub_off": self.sub_off, "sub_def": self.sub_def, "chin": self.chin, "cardio": self.cardio},
            "traits": self.traits, "record": self.record, "is_champion": self.is_champion,
            "injury_months": self.injury_months, "popularity": self.popularity, "age": self.age,
            "history": self.history, "ranking_score": self.ranking_score,
            "annual_stats": self.annual_stats
        }
    
    def get_scout_grade(self):
        avg_stat = (self.striking + self.grappling + self.tdd + self.chin + self.cardio) / 5
        potential_bonus = 0
        if self.age < 25: potential_bonus = 10
        elif self.age < 29: potential_bonus = 5
        elif self.age > 35: potential_bonus = -10
        score = avg_stat + potential_bonus
        if score >= 95: return "A+"
        if score >= 90: return "A"
        if score >= 85: return "B+"
        if score >= 80: return "B"
        if score >= 75: return "C+"
        if score >= 70: return "C"
        if score >= 60: return "D"
        return "F"

def load_roster_objects():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, 'roster.json')
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            roster = []
            seen_names = set()
            for fighter_data in data:
                if fighter_data['name'] not in seen_names:
                    roster.append(Fighter(fighter_data))
                    seen_names.add(fighter_data['name'])
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
            if f.is_champion: return 999999
            return f.ranking_score
        div_roster.sort(key=sort_key, reverse=True)
        rank_counter = 1
        for f in div_roster:
            if f.is_champion: f.rank = 0
            else:
                f.rank = rank_counter
                rank_counter += 1

def generate_rookie(roster_for_id):
    max_id = 0
    for f in roster_for_id:
        if f.id > max_id: max_id = f.id
    new_id = max_id + random.randint(1, 1000)
    
    f_name = random.choice(FIRST_NAMES); l_name = random.choice(LAST_NAMES)
    full_name = f"{f_name} {l_name}"
    nick = random.choice(NICKNAMES) if random.randint(0,1) else ""
    wc = random.choice(WEIGHT_CLASSES)
    
    style = random.choice(["Striker", "Grappler", "Balanced"])
    stats = {}
    if style == "Striker":
        stats = {"striking": random.randint(70, 88), "grappling": random.randint(50, 70), "tdd": random.randint(60, 80),
                 "sub_off": random.randint(40, 60), "sub_def": random.randint(60, 75), "chin": random.randint(80, 95), "cardio": random.randint(70, 90)}
        traits = ["Head Hunter"]
    elif style == "Grappler":
        stats = {"striking": random.randint(50, 70), "grappling": random.randint(75, 92), "tdd": random.randint(70, 85),
                 "sub_off": random.randint(70, 90), "sub_def": random.randint(70, 90), "chin": random.randint(80, 95), "cardio": random.randint(75, 90)}
        traits = ["Submission Magician"]
    else:
        stats = {"striking": random.randint(65, 82), "grappling": random.randint(65, 82), "tdd": random.randint(65, 80),
                 "sub_off": random.randint(60, 80), "sub_def": random.randint(65, 80), "chin": random.randint(85, 95), "cardio": random.randint(75, 90)}
        traits = ["Well Rounded"]
        
    data = {
        "id": new_id, "name": full_name, "nickname": nick, "weight_class": wc,
        "stats": stats, "traits": traits, "record": {"wins": 0, "losses": 0, "draws": 0},
        "is_champion": False, "age": random.randint(19, 25), "popularity": random.randint(5, 15),
        "injury_months": 0, "history": [], "annual_stats": {'wins': 0, 'finishes': 0}
    }
    return Fighter(data)

# --- NEW DATA LOADING FUNCTIONS ---
def load_free_agents_from_json(existing_roster_ids):
    # Load Free Agents file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    fa_path = os.path.join(script_dir, 'data', 'free_agents.json')
    loaded_agents = []
    
    if os.path.exists(fa_path):
        try:
            with open(fa_path, 'r') as f:
                data = json.load(f)
                max_id = max(existing_roster_ids) if existing_roster_ids else 1000
                for item in data:
                    max_id += 1
                    item['id'] = max_id
                    loaded_agents.append(Fighter(item))
        except Exception as e:
            print(f"Error loading free_agents.json: {e}")
    return loaded_agents

def get_prospects_database():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    p_path = os.path.join(script_dir, 'data', 'prospects.json')
    if os.path.exists(p_path):
        try:
            with open(p_path, 'r') as f:
                return json.load(f)
        except: return []
    return []

def process_monthly_events(roster, game_data):
    events_log = []
    is_january = (game_data.month_index == 0)
    is_december = (game_data.month_index == 11)
    
    if is_january:
        game_data.add_news("🎆 HAPPY NEW YEAR! Contracts reviewed.")
        events_log.append("Happy New Year!")

    # 1. HISTORICAL SPAWNS (REAL FIGHTERS from prospects.json)
    prospects_db = get_prospects_database()
    for prospect in prospects_db:
        if prospect['name'] in game_data.spawned_legends: continue
        
        # Check if debut date is passed
        if game_data.year > prospect['debut_year'] or (game_data.year == prospect['debut_year'] and game_data.month_index >= prospect['debut_month']):
            
            # Create the fighter
            max_id = 0
            for f in roster + game_data.free_agents:
                if f.id > max_id: max_id = f.id
            
            new_data = prospect.copy()
            new_data['id'] = max_id + 1
            new_data['record'] = {"wins": 0, "losses": 0, "draws": 0}
            new_data['is_champion'] = False
            new_data['age'] = 22 # Generic debut age
            new_data['injury_months'] = 0
            new_data['popularity'] = 20
            new_data['history'] = []
            
            new_fighter = Fighter(new_data)
            game_data.free_agents.insert(0, new_fighter) 
            game_data.spawned_legends.append(prospect['name'])
            game_data.add_news(f"🔥 PROSPECT ALERT: {new_fighter.name} has made their pro debut and is now scountable!")

    # 2. SCOUTING REFRESH (Randoms)
    if len(game_data.free_agents) < 10:
        num_new = random.randint(2, 4)
        for _ in range(num_new):
            fa = generate_rookie(roster + game_data.free_agents)
            game_data.free_agents.append(fa)
    
    # 3. YEAR-END AWARDS (December)
    if is_december:
        best_fighter = None; max_wins = -1
        best_rookie = None; max_rookie_wins = -1
        
        for f in roster:
            w = f.annual_stats['wins']
            if w > max_wins:
                max_wins = w
                best_fighter = f
            if f.age <= 25 and w > max_rookie_wins:
                max_rookie_wins = w
                best_rookie = f
            # Reset for next year
            f.annual_stats = {'wins': 0, 'finishes': 0}
            
        msg = "🏆 AWARDS SEASON:\n"
        if best_fighter: 
            msg += f"Fighter of the Year: {best_fighter.name} ({max_wins} Wins)\n"
            best_fighter.popularity += 10
        if best_rookie: 
            msg += f"Rookie of the Year: {best_rookie.name}"
            best_rookie.popularity += 10
        
        game_data.add_news(msg)

    # 4. RETIREMENT
    retirees = []
    for f in roster:
        should_retire = False; reason = ""
        if is_january:
            f.age += 1
            if f.age >= 42: should_retire = True; reason = "Age"
            elif f.age >= 38 and f.record['losses'] > f.record['wins']: should_retire = True; reason = "Decline"
            if f.age > 34 and not should_retire:
                if random.randint(1, 100) <= 35:
                    stat_hit = random.choice(["chin", "cardio", "striking"])
                    current_val = getattr(f, stat_hit)
                    if current_val > 50:
                        setattr(f, stat_hit, current_val - 3)
                        game_data.add_news(f"REGRESSION: {f.name} (-3 {stat_hit.title()}) due to age.")
        if f.chin < 40: should_retire = True; reason = "Medical (Chin)"
        if should_retire and not f.is_champion: retirees.append((f, reason))
        
    for f, reason in retirees:
        roster.remove(f)
        game_data.add_news(f"👋 RETIREMENT: {f.name} has retired ({reason}).")
        if len([x for x in roster if x.weight_class == f.weight_class]) < 10:
            rookie = generate_rookie(roster)
            roster.append(rookie)
            game_data.add_news(f"✍️ AUTO-SIGNING: UFC signs prospect {rookie.name} to fill gap.")

    # 5. RANDOM NARRATIVE EVENTS
    for f in roster:
        if random.randint(1, 1000) <= 3: 
            f.injury_months = 6
            f.popularity = max(0, f.popularity - 10)
            game_data.add_news(f"💊 SCANDAL: {f.name} flagged by USADA! Suspended 6 months.")
            
        if random.randint(1, 500) <= 5: 
            gain = random.randint(10, 20)
            f.popularity = min(100, f.popularity + gain)
            game_data.add_news(f"📈 VIRAL: {f.name} blows up on social media! Popularity +{gain}.")

        if random.randint(1, 300) <= 5:
            f.striking += random.randint(-3, 3)
            f.grappling += random.randint(-3, 3)
            game_data.add_news(f"CAMP SWITCH: {f.name} moves to a new gym.")

    # 6. INJURIES
    for f in roster:
        if f.injury_months > 0:
            f.injury_months -= 1
            if f.injury_months == 0:
                msg = f"MEDICAL: {f.name} cleared to fight."
                game_data.add_news(msg)
            continue 
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

def generate_post_fight_news(winner, loser, method, game_data):
    chance = 20
    if "Trash Talker" in winner.traits: chance = 70
    if "Showman" in winner.traits: chance = 50
    if random.randint(1, 100) <= chance:
        target = "the Champion" if not winner.is_champion else "the #1 Contender"
        msgs = [f"MIC SKILLS: {winner.name} demands a title shot!", f"CALLOUT: {winner.name} says {target} is ducking them!", f"POST-FIGHT: {winner.name} claims they are the GOAT."]
        game_data.add_news(random.choice(msgs))
    if loser.age >= 36 and loser.record['losses'] >= 10:
        if random.randint(1,100) <= 30: game_data.add_news(f"RUMOR: {loser.name} hints at retirement.")
    if method == "SPLIT DECISION": game_data.add_news(f"CONTROVERSY: Fans booing the decision in {winner.name} vs {loser.name}.")

# --- GUI CLASS ---
class UFCGameGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("UFC Matchmaker Pro 2012 (Legacy Edition)")
        self.root.geometry("1400x900")
        self.roster = load_roster_objects()
        self.game_data = GameData()
        
        # Load Free Agents (Real Ones First)
        existing_ids = [f.id for f in self.roster]
        real_fas = load_free_agents_from_json(existing_ids)
        self.game_data.free_agents.extend(real_fas)
        
        # Fill rest with randoms if needed
        while len(self.game_data.free_agents) < 5:
            self.game_data.free_agents.append(generate_rookie(self.roster + self.game_data.free_agents))
        
        self.current_fights = {key: [None, None] for key in CARD_SLOTS_KEYS}
        self.selected_fighter_obj = None 
        self.selected_scout_obj = None

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
        self.btn_nav_scouting = ctk.CTkButton(self.nav_bar, text="SCOUTING", width=150, fg_color="#222", corner_radius=0, command=lambda: self.show_view("scouting"))
        self.btn_nav_scouting.pack(side="left", padx=1)
        self.btn_nav_history = ctk.CTkButton(self.nav_bar, text="EVENT HISTORY", width=150, fg_color="#222", corner_radius=0, command=lambda: self.show_view("history"))
        self.btn_nav_history.pack(side="left", padx=1)
        self.btn_nav_news = ctk.CTkButton(self.nav_bar, text="NEWS & INBOX", width=150, fg_color="#222", corner_radius=0, command=lambda: self.show_view("news"))
        self.btn_nav_news.pack(side="left", padx=1)

        # CONTENT AREA
        self.content_area = ctk.CTkFrame(root, corner_radius=0, fg_color="transparent")
        self.content_area.pack(fill="both", expand=True)

        self.view_dashboard = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.build_dashboard_view(self.view_dashboard)
        self.view_scouting = ctk.CTkFrame(self.content_area, fg_color="#1a1a1a")
        self.build_scouting_view(self.view_scouting)
        self.view_history = ctk.CTkFrame(self.content_area, fg_color="#1a1a1a")
        self.build_history_view(self.view_history)
        self.view_news = ctk.CTkFrame(self.content_area, fg_color="#1a1a1a")
        ctk.CTkLabel(self.view_news, text="NEWS FEED", font=("Impact", 30), text_color="#555").pack(pady=20)
        self.txt_news = ctk.CTkTextbox(self.view_news, font=("Consolas", 14), width=800, height=500, state="disabled", fg_color="#222")
        self.txt_news.pack(pady=10)

        self.show_view("dashboard")

    def show_view(self, view_name):
        self.view_dashboard.pack_forget(); self.view_scouting.pack_forget(); self.view_history.pack_forget(); self.view_news.pack_forget()
        self.btn_nav_dashboard.configure(fg_color="#222"); self.btn_nav_scouting.configure(fg_color="#222"); self.btn_nav_history.configure(fg_color="#222"); self.btn_nav_news.configure(fg_color="#222")
        
        if view_name == "dashboard":
            self.view_dashboard.pack(fill="both", expand=True)
            self.btn_nav_dashboard.configure(fg_color="#444")
        elif view_name == "scouting":
            self.view_scouting.pack(fill="both", expand=True)
            self.btn_nav_scouting.configure(fg_color="#444")
            self.refresh_scouting_list()
        elif view_name == "history":
            self.view_history.pack(fill="both", expand=True)
            self.btn_nav_history.configure(fg_color="#444")
            self.refresh_history_list()
        elif view_name == "news":
            self.view_news.pack(fill="both", expand=True)
            self.btn_nav_news.configure(fg_color="#444")
            self.update_news_display()

    # --- VIEWS ---
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
        self.hist_textbox.insert("end", f"RATING: {'★' * event['rating']}\n")
        awards = event.get('awards', {})
        if awards:
            self.hist_textbox.insert("end", f"FIGHT OF THE NIGHT: {awards.get('fotn', 'N/A')}\n")
            self.hist_textbox.insert("end", f"PERFORMANCE: {awards.get('potn', 'N/A')}\n")
        self.hist_textbox.insert("end", "="*50 + "\n\n")
        for fight in event['results']:
            stars = "★" * fight['stars']
            self.hist_textbox.insert("end", f"{fight['slot'].upper()} | {stars}\n")
            self.hist_textbox.insert("end", f"{fight['winner']} def. {fight['loser']}\n")
            self.hist_textbox.insert("end", f"Method: {fight['method']} (R{fight['round']})\n")
            if fight['method'] in ["DECISION", "SPLIT DECISION"] and 'scores' in fight:
                s = fight['scores']
                sc_str = f"Scores: {s[0][0]}-{s[0][1]} | {s[1][0]}-{s[1][1]} | {s[2][0]}-{s[2][1]}"
                self.hist_textbox.insert("end", f"{sc_str}\n")
            if fight['new_champ']: self.hist_textbox.insert("end", ">>> AND NEW CHAMPION! <<<\n")
            elif fight['still_champ']: self.hist_textbox.insert("end", ">>> AND STILL CHAMPION! <<<\n")
            self.hist_textbox.insert("end", "-"*30 + "\n")
        self.hist_textbox.configure(state="disabled")

    def build_scouting_view(self, parent):
        left = ctk.CTkFrame(parent, width=400, corner_radius=0, fg_color="#222")
        left.pack(side="left", fill="y")
        ctk.CTkLabel(left, text="FREE AGENTS", font=("Impact", 24)).pack(pady=20)
        cols = ("Grade", "Name", "Age", "Class")
        self.scout_tree = ttk.Treeview(left, columns=cols, show='headings', selectmode="browse")
        self.scout_tree.heading("Grade", text="Grade"); self.scout_tree.column("Grade", width=50, anchor="center")
        self.scout_tree.heading("Name", text="Name"); self.scout_tree.column("Name", width=150)
        self.scout_tree.heading("Age", text="Age"); self.scout_tree.column("Age", width=40, anchor="center")
        self.scout_tree.heading("Class", text="Class"); self.scout_tree.column("Class", width=100)
        self.scout_tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.scout_tree.bind("<<TreeviewSelect>>", self.on_scout_select)
        right = ctk.CTkFrame(parent, fg_color="#1a1a1a")
        right.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        self.lbl_scout_name = ctk.CTkLabel(right, text="SELECT FIGHTER", font=("Impact", 36), text_color="#444")
        self.lbl_scout_name.pack(pady=30)
        self.lbl_scout_grade = ctk.CTkLabel(right, text="", font=("Arial", 24, "bold"))
        self.lbl_scout_grade.pack(pady=10)
        self.scout_stats_txt = ctk.CTkLabel(right, text="", font=("Consolas", 14), justify="left")
        self.scout_stats_txt.pack(pady=20)
        self.btn_sign = ctk.CTkButton(right, text="SIGN FIGHTER", fg_color="green", height=50, state="disabled", command=self.sign_fighter)
        self.btn_sign.pack(pady=20)

    def refresh_scouting_list(self):
        for item in self.scout_tree.get_children(): self.scout_tree.delete(item)
        for fa in self.game_data.free_agents:
            grade = fa.get_scout_grade()
            self.scout_tree.insert("", "end", values=(grade, fa.name, fa.age, fa.weight_class))

    def on_scout_select(self, event):
        sel = self.scout_tree.selection()
        if not sel: return
        item = self.scout_tree.item(sel[0])
        name = item['values'][1]
        fa = next((f for f in self.game_data.free_agents if f.name == name), None)
        if fa:
            self.selected_scout_obj = fa
            self.lbl_scout_name.configure(text=fa.name.upper(), text_color="white")
            grade = fa.get_scout_grade()
            col = "#2ecc71" if "A" in grade else ("#f1c40f" if "B" in grade else "#e74c3c")
            self.lbl_scout_grade.configure(text=f"SCOUT GRADE: {grade}", text_color=col)
            stats_text = f"Class: {fa.weight_class}\nAge: {fa.age}\n\nStriking: {fa.striking}\nGrappling: {fa.grappling}\nChin: {fa.chin}\nCardio: {fa.cardio}"
            self.scout_stats_txt.configure(text=stats_text)
            self.btn_sign.configure(state="normal")

    def sign_fighter(self):
        if not self.selected_scout_obj: return
        self.game_data.free_agents.remove(self.selected_scout_obj)
        self.roster.append(self.selected_scout_obj)
        messagebox.showinfo("Signed", f"{self.selected_scout_obj.name} has joined the roster!")
        self.game_data.add_news(f"✍️ SIGNING: You signed free agent {self.selected_scout_obj.name}.")
        self.selected_scout_obj = None
        self.lbl_scout_name.configure(text="SELECT FIGHTER", text_color="#444")
        self.btn_sign.configure(state="disabled")
        self.refresh_scouting_list()
        update_rankings_logic(self.roster)

    def update_news_display(self):
        self.txt_news.configure(state="normal")
        self.txt_news.delete("0.0", "end")
        for item in self.game_data.news_feed:
            self.txt_news.insert("end", item + "\n\n")
        self.txt_news.configure(state="disabled")

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
        
        self.btn_view_log = ctk.CTkButton(col_details, text="VIEW FIGHT LOG", fg_color="#555", command=self.open_fight_log_window)
        self.btn_view_log.pack(pady=10)

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
        age_col = "#2ecc71" if f.age < 29 else ("#e74c3c" if f.age > 35 else "#aaa")
        self.lbl_age.configure(text=f"AGE: {f.age}", text_color=age_col)
        self.lbl_det_record.configure(text=f"Record: {f.record['wins']}-{f.record['losses']}")
        self.stat_labels["Striking"].configure(text=f.striking); self.stat_labels["Grappling"].configure(text=f.grappling)
        self.stat_labels["Chin"].configure(text=f.chin); self.stat_labels["Cardio"].configure(text=f.cardio)
        self.stat_labels["Sub Off"].configure(text=f.sub_off); self.stat_labels["Sub Def"].configure(text=f.sub_def)
        self.lbl_pop.configure(text=f"POPULARITY: {f.popularity}")
        self.lbl_traits.configure(text=", ".join(f.traits) if f.traits else "None")

    def open_fight_log_window(self):
        if not self.selected_fighter_obj: return
        f = self.selected_fighter_obj
        
        log_win = ctk.CTkToplevel(self.root)
        log_win.title(f"{f.name} Fight History")
        log_win.geometry("500x500")
        
        ctk.CTkLabel(log_win, text=f"CAREER LOG: {f.name.upper()}", font=("Impact", 20)).pack(pady=10)
        
        txt_frame = ctk.CTkScrollableFrame(log_win, width=450, height=400)
        txt_frame.pack(pady=10, padx=10, fill="both", expand=True)
        
        if not f.history:
            ctk.CTkLabel(txt_frame, text="No recorded fights yet.", font=("Arial", 12)).pack()
        else:
            for fight in reversed(f.history):
                color = "#2ecc71" if fight['result'] == "Win" else "#e74c3c"
                row_txt = f"[{fight['result'].upper()}] vs {fight['opponent']}\n{fight['method']} (R{fight['round']}) @ {fight['event']}"
                f_row = ctk.CTkFrame(txt_frame, fg_color="#333")
                f_row.pack(fill="x", pady=2)
                ctk.CTkLabel(f_row, text=row_txt, font=("Consolas", 12), text_color=color, anchor="w", justify="left").pack(fill="x", padx=10, pady=5)

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
        
        # RIVALRY CHECK
        rivalry_text = "vs"
        fights_against = [x for x in f1.history if x['opponent'] == f2.name]
        if len(fights_against) == 1: rivalry_text = "REMATCH"
        elif len(fights_against) >= 2: rivalry_text = "TRILOGY"

        self.current_fights[slot_name] = [f1, f2]
        c1 = "👑 " if f1.is_champion else ""; c2 = "👑 " if f2.is_champion else ""
        red_lbl.configure(text=f"{c1}{f1.name}", text_color="white")
        blue_lbl.configure(text=f"{c2}{f2.name}", text_color="white")
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
            best_fight_name = "None"; max_stars = 0
            potn_name = "None"; fastest_win = 999
            
            for slot in reverse_order:
                f1, f2 = self.current_fights[slot]
                is_main = (slot == "Main Event")
                if is_main: main_event_pop = (f1.popularity + f2.popularity)
                
                fights_against = [x for x in f1.history if x['opponent'] == f2.name]
                if len(fights_against) > 0:
                    log(f"⚔️ RIVALRY ALERT: This is fight #{len(fights_against)+1} between them!")

                res = self.simulate_fight_logic(f1, f2, is_main, slot, log)
                if res['stars'] > max_stars:
                    max_stars = res['stars']; best_fight_name = f"{res['winner']} vs {res['loser']}"
                elif res['stars'] == max_stars and is_main: best_fight_name = f"{res['winner']} vs {res['loser']}"
                if res['method'] in ["KNOCKOUT", "SUBMISSION"]:
                    if res['round'] < fastest_win: fastest_win = res['round']; potn_name = res['winner']
                generate_post_fight_news(next(f for f in self.roster if f.name == res['winner']), 
                                         next(f for f in self.roster if f.name == res['loser']), res['method'], self.game_data)
                total_card_stars += res['stars']
                event_results.append(res)
            
            if UPDATE_RECORDS:
                for f in self.roster:
                    if f.name == potn_name: f.popularity += 5
                    if best_fight_name and (f.name in best_fight_name): f.popularity += 5

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
            log(f"⚔️ FIGHT OF THE NIGHT: {best_fight_name}")
            log(f"⚡ PERFORMANCE OF THE NIGHT: {potn_name}")
            log("="*30)

            awards = {"fotn": best_fight_name, "potn": potn_name}
            self.game_data.archive_event(self.game_data.get_event_name(), self.game_data.get_date_str(), event_results, total_buys, event_rating, awards)

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
        
        fighters = {
            f1.name: {"obj": f1, "stamina": 100, "damage_head": 0, "damage_legs": 0, "damage_body": 0, "is_gassed": False, "total_damage_dealt": 0},
            f2.name: {"obj": f2, "stamina": 100, "damage_head": 0, "damage_legs": 0, "damage_body": 0, "is_gassed": False, "total_damage_dealt": 0}
        }
        
        judge_scores = [[0,0] for _ in range(3)]
        winner = None; method = "Decision"; finish_round = 0; fight_stars = 2; damage_exchanged = 0
        
        for r in range(1, rounds+1):
            log_func(f"🔔 R{r}..."); time.sleep(TEXT_SPEED * 0.3)
            r_stats = {f1.name: 0, f2.name: 0}; knockdown_scored = {f1.name: False, f2.name: False}
            for fname, state in fighters.items():
                rec = 10 + (state["obj"].cardio * 0.1)
                state["stamina"] = min(100, state["stamina"] + rec)
                if state["stamina"] < 40: 
                    state["is_gassed"] = True
                    log_func(f"⚠️ {fname} looks EXHAUSTED!")
            
            for _ in range(5):
                att_name = f1.name if random.choice([True, False]) else f2.name
                def_name = f2.name if att_name == f1.name else f1.name
                att = fighters[att_name]; defe = fighters[def_name]
                att_skill_pen = 0.6 if att["is_gassed"] else 1.0; def_skill_pen = 0.6 if defe["is_gassed"] else 1.0
                att["stamina"] -= 8
                
                if att["obj"].grappling > att["obj"].striking:
                    off = att["obj"].grappling * att_skill_pen; defn = defe["obj"].tdd * def_skill_pen
                    if defe["damage_legs"] > 30: defn -= 15
                    if off + random.randint(-20, 20) > defn:
                        log_func(f"  > {att_name} {get_commentary('takedown')}")
                        r_stats[att_name] += 10; att["stamina"] -= 5; att["total_damage_dealt"] += 5
                        if att["obj"].sub_off + random.randint(0,20) > defe["obj"].sub_def + 30: 
                            winner = att["obj"]; method = "SUBMISSION"; finish_round = r
                            log_func(f"  > {get_commentary('sub')}"); break 
                    else: 
                        log_func(f"  > {att_name} shoots... {get_commentary('takedown_stuff')}")
                        att["stamina"] -= 12
                else:
                    off = att["obj"].striking * att_skill_pen; defn = defe["obj"].striking * def_skill_pen
                    if off + random.randint(-20, 20) > defn:
                        roll = random.randint(1, 10)
                        damage_val = 0
                        if roll <= 2: 
                            log_func(f"  > {att_name} {get_commentary('leg_kick')}")
                            defe["damage_legs"] += 15; r_stats[att_name] += 5; damage_val = 5
                        elif roll <= 4:
                            log_func(f"  > {att_name} {get_commentary('body_shot')}")
                            defe["damage_body"] += 15; defe["stamina"] -= 15; r_stats[att_name] += 8; damage_val = 8
                        elif roll <= 8:
                            log_func(f"  > {att_name} {get_commentary('strike_light')}")
                            defe["damage_head"] += 8; r_stats[att_name] += 5; damage_val = 5
                        else:
                            log_func(f"  > {att_name} {get_commentary('strike_heavy')}")
                            defe["damage_head"] += 20; r_stats[att_name] += 15; damage_val = 20
                            damage_exchanged += 20
                            chin_stat = defe["obj"].chin - (defe["damage_head"] * 0.5)
                            if random.randint(0, 100) > chin_stat:
                                winner = att["obj"]; method = "KNOCKOUT"; finish_round = r
                                log_func(f"  > {get_commentary('ko')}"); break
                            if random.randint(0, 100) > (chin_stat + 15):
                                log_func(f"  > {get_commentary('knockdown')}")
                                r_stats[att_name] += 20; knockdown_scored[att_name] = True
                        att["total_damage_dealt"] += damage_val
                time.sleep(TEXT_SPEED * 0.1)
            if winner: break
            
            s1 = r_stats[f1.name]; s2 = r_stats[f2.name]
            for j in range(3):
                 variance = random.randint(-2, 2)
                 j_s1 = s1 + variance; j_s2 = s2
                 if j_s1 > j_s2: p1 = 10; p2 = 8 if knockdown_scored[f1.name] or (j_s1 - j_s2 > 25) else 9
                 elif j_s2 > j_s1: p2 = 10; p1 = 8 if knockdown_scored[f2.name] or (j_s2 - j_s1 > 25) else 9
                 else: p1 = 10; p2 = 10
                 judge_scores[j][0] += p1; judge_scores[j][1] += p2

        if not winner:
            finish_round = rounds
            votes_f1 = 0; votes_f2 = 0
            for s in judge_scores:
                if s[0] > s[1]: votes_f1 += 1
                elif s[1] > s[0]: votes_f2 += 1
            if votes_f1 > votes_f2: winner = f1; method = "DECISION" if votes_f2 == 0 else "SPLIT DECISION"
            elif votes_f2 > votes_f1: winner = f2; method = "DECISION" if votes_f1 == 0 else "SPLIT DECISION"
            else:
                if fighters[f1.name]["total_damage_dealt"] > fighters[f2.name]["total_damage_dealt"]: winner = f1; method = "SPLIT DECISION"
                else: winner = f2; method = "SPLIT DECISION"
            log_func(f"\n📝 OFFICIAL SCORECARDS:")
            for i, s in enumerate(judge_scores):
                j_res = f1.name if s[0] > s[1] else (f2.name if s[1] > s[0] else "Draw")
                log_func(f"   Judge {i+1}: {s[0]} - {s[1]} ({j_res})")

        loser = f2 if winner == f1 else f1
        log_func(f"🏆 {winner.name} via {method}")
        
        if method == "KNOCKOUT": fight_stars += 2
        elif method == "SUBMISSION": fight_stars += 1
        if finish_round == 1: fight_stars += 1
        if damage_exchanged > 100: fight_stars += 1
        if damage_exchanged < 30 and "DECISION" in method: fight_stars -= 1 
        if is_title: fight_stars += 1
        fight_stars = max(1, min(5, fight_stars))

        new_champ = False; still_champ = False
        if is_title:
            if winner.is_champion: log_func("👑 AND STILL!"); still_champ = True
            else: log_func("👑 AND NEW!"); new_champ = True; winner.is_champion = True; loser.is_champion = False 
        
        if UPDATE_RECORDS:
            winner.record['wins'] += 1; loser.record['losses'] += 1
            winner.annual_stats['wins'] += 1
            if method in ["KNOCKOUT", "SUBMISSION"]: winner.annual_stats['finishes'] += 1
            
            points_gained = 150 
            if winner.ranking_score < loser.ranking_score:
                diff = loser.ranking_score - winner.ranking_score
                upset_bonus = int(diff * 0.40) 
                points_gained += upset_bonus
                log_func(f"🚀 RANKINGS: Upset! {winner.name} takes {upset_bonus} bonus points!")
            
            if method in ["KNOCKOUT", "SUBMISSION"]: points_gained += 50
            winner.ranking_score += points_gained
            loss_penalty = 50
            if loser.ranking_score > 1000: loss_penalty = 150
            if loser.ranking_score > 2000: loss_penalty = 300 
            loser.ranking_score = max(0, loser.ranking_score - loss_penalty)
            
            if winner.popularity < 90: winner.popularity += random.randint(1, 3)
            if winner.age < 28 and random.randint(1,100) < 50:
                stat = random.choice(["striking", "grappling", "tdd"])
                curr = getattr(winner, stat)
                if curr < 95: setattr(winner, stat, curr + 1); log_func(f"📈 DEVELOPMENT: {winner.name} improved {stat} (+1)!")
            if method == "KNOCKOUT":
                loser.chin -= 1
                log_func(f"📉 DAMAGE: {loser.name}'s chin degraded (-1).")
            
            ev_name = self.game_data.get_event_name()
            hist_scores = judge_scores if "DECISION" in method else []
            winner.history.append({"result": "Win", "opponent": loser.name, "method": method, "round": finish_round, "event": ev_name, "scores": hist_scores})
            loser.history.append({"result": "Loss", "opponent": winner.name, "method": method, "round": finish_round, "event": ev_name, "scores": hist_scores})
            
        return {"slot": slot_name, "winner": winner.name, "loser": loser.name, "method": method, "round": finish_round, "title_fight": is_title, "new_champ": new_champ, "still_champ": still_champ, "stars": fight_stars, "scores": judge_scores}

if __name__ == "__main__":
    app = ctk.CTk()
    gui = UFCGameGUI(app)
    app.mainloop()
