import json
import random
import time
import os

# --- CONFIGURATION ---
TEXT_SPEED = 1.0

# --- WEIGHT CLASSES ---
WEIGHT_CLASSES = {
    "Flyweight": 125, "Bantamweight": 135, "Featherweight": 145, 
    "Lightweight": 155, "Welterweight": 170, "Middleweight": 185, 
    "Light Heavyweight": 205, "Heavyweight": 265
}

class Fighter:
    def __init__(self, data):
        self.id = data['id']
        self.name = data['name']
        self.nickname = data['nickname']
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
        
        # NEW: Load rank if it exists, otherwise default to 999 (Unranked)
        self.rank = data.get('rank', 999) 
        
        self.total_damage_taken = 0 

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "nickname": self.nickname,
            "weight_class": self.weight_class,
            "stats": {
                "striking": self.striking, "grappling": self.grappling,
                "tdd": self.tdd, "sub_off": self.sub_off,
                "sub_def": self.sub_def, "chin": self.chin,
                "cardio": self.cardio
            },
            "traits": self.traits,
            "record": self.record,
            "is_champion": self.is_champion,
            "rank": self.rank # <--- SAVE RANK
        }

# --- SYSTEM FUNCTIONS ---
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_script_path():
    return os.path.dirname(os.path.abspath(__file__))

def load_roster():
    path = os.path.join(get_script_path(), 'roster.json')
    try:
        with open(path, 'r') as f:
            data = json.load(f)
            return [Fighter(f) for f in data]
    except FileNotFoundError:
        print("❌ ERROR: roster.json not found!")
        return []

def save_roster(roster):
    """Writes the current state of fighters back to the file"""
    path = os.path.join(get_script_path(), 'roster.json')
    data = [f.to_dict() for f in roster]
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)
    print("\n💾 Game Data Saved Automatically.")

def update_rankings(roster):
    """
    Sorts fighters in every division based on a 'Score' and assigns ranks.
    Score = (Wins * 5) - (Losses * 3) + (Overall_Stat / 2)
    """
    # 1. Reset everyone to 999 (Unranked) first
    for f in roster:
        f.rank = 999

    # 2. Process each division separately
    divisions = list(WEIGHT_CLASSES.keys())
    
    for div in divisions:
        div_roster = [f for f in roster if f.weight_class == div]
        if not div_roster: continue

        # 3. Calculate Score
        def sort_key(f):
            if f.is_champion: return 10000 # Champion is always top
            
            # Formula: Win Record is most important, Stats are tie-breaker
            ovr = (f.striking + f.grappling) // 2
            score = (f.record['wins'] * 10) - (f.record['losses'] * 3) + ovr
            return score

        # Sort descending (Highest score first)
        div_roster.sort(key=sort_key, reverse=True)

        # 4. Assign Ranks
        current_rank = 0 
        for f in div_roster:
            if f.is_champion:
                f.rank = 0 # 0 = Champion
            else:
                current_rank += 1
                f.rank = current_rank

def get_time_string(seconds_left):
    mins = seconds_left // 60
    secs = seconds_left % 60
    return f"[{mins}:{secs:02d}]"

def get_commentary(action, f1, f2, sub_type=None):
    if action == "heavy_strike":
        return random.choice([
            f"💥 MASSIVE shot from {f1.name}!",
            f"{f1.name} wobbles {f2.name} with a hook!",
            f"CRACK! High kick lands flush for {f1.name}!"
        ])
    elif action == "takedown":
        return random.choice([
            f"{f1.name} blasts a double leg!",
            f"Beautiful trip takedown by {f1.name}.",
            f"{f1.name} drags the fight to the floor."
        ])
    elif action == "sub_attempt":
        return f"⚠️ {f1.name} is looking for the {sub_type}!"
    elif action == "sub_escape":
        return f"...but {f2.name} defends successfully."
    return f"{f1.name} lands a strike."

# --- FIGHT ENGINE ---
def simulate_fight(f1, f2, is_title_fight=False):
    # Champion Logic
    if f2.is_champion and not f1.is_champion:
        f1, f2 = f2, f1
        
    rounds = 5 if is_title_fight else 3
    f1.total_damage_taken = 0
    f2.total_damage_taken = 0
    
    clear_screen()
    print("\n==================================================")
    print("🔥  UFC FIGHT NIGHT  🔥")
    print("==================================================")
    c1 = "🏆 " if f1.is_champion else ""
    c2 = "🏆 " if f2.is_champion else ""
    print(f"🔴 {c1}{f1.name} ({f1.record['wins']}-{f1.record['losses']})")
    print(f"       vs")
    print(f"🔵 {c2}{f2.name} ({f2.record['wins']}-{f2.record['losses']})")
    print("==================================================\n")
    time.sleep(2)
    
    judge_scores = [[0,0], [0,0], [0,0]]
    winner = None
    method = "Decision"

    # Fight Loop
    for round_num in range(1, rounds + 1):
        print(f"\n🔔 ROUND {round_num} 🔔")
        time.sleep(1)
        clock = 300
        stats = {f1.name: {'dmg':0,'td':0,'sub':0}, f2.name: {'dmg':0,'td':0,'sub':0}}
        
        while clock > 10:
            clock -= random.randint(20, 40)
            if clock < 0: clock = 10
            timestamp = get_time_string(clock)
            
            attacker = f1 if random.choice([True, False]) else f2
            defender = f2 if attacker == f1 else f1
            
            # Action Logic
            td_threshold = 30
            if "Wrestler" in attacker.traits: td_threshold = 60
            
            wants_takedown = (attacker.grappling > defender.striking) or (random.randint(0,100) < td_threshold)
            is_ground = False
            
            if wants_takedown:
                att_roll = attacker.grappling + random.randint(-15, 15)
                def_roll = defender.tdd + random.randint(-15, 15)
                if att_roll > def_roll:
                    print(f"{timestamp} > {get_commentary('takedown', attacker, defender)}")
                    stats[attacker.name]['td'] += 1
                    is_ground = True
                else:
                    print(f"{timestamp} > {attacker.name} shoots, but gets stuffed.")
            
            if is_ground:
                # Sub Logic
                sub_pool = ["Rear Naked Choke", "Armbar", "Guillotine"]
                sub_type = random.choice(sub_pool)
                att_sub = attacker.sub_off + random.randint(-10, 10)
                def_sub = defender.sub_def + random.randint(-10, 10)
                
                if att_sub > def_sub + 15:
                    print(f"{timestamp} > {get_commentary('sub_attempt', attacker, defender, sub_type)}")
                    time.sleep(1)
                    if att_sub > def_sub + 30: # Finish
                        winner = attacker
                        method = f"SUBMISSION ({sub_type})"
                        break # Break While Loop
                    else:
                        print(f"       > {get_commentary('sub_escape', attacker, defender)}")
                
                dmg = 10
                stats[attacker.name]['dmg'] += dmg
                defender.total_damage_taken += dmg
                print(f"       > {attacker.name} lands ground strikes.")

            else:
                # Strike Logic
                att_str = attacker.striking + random.randint(-20, 20)
                def_str = defender.striking + random.randint(-20, 20)
                if att_str > def_str:
                    is_heavy = (att_str - def_str) > 25
                    if is_heavy:
                        print(f"{timestamp} > {get_commentary('heavy_strike', attacker, defender)}")
                        ko_resist = defender.chin - (defender.total_damage_taken * 0.4)
                        if random.randint(0, 100) > ko_resist:
                            winner = attacker
                            method = "KNOCKOUT"
                            break # Break While Loop
                        dmg = 20
                    else:
                        print(f"{timestamp} > {attacker.name} lands a strike.")
                        dmg = 5
                    stats[attacker.name]['dmg'] += dmg
                    defender.total_damage_taken += dmg
            
            time.sleep(TEXT_SPEED)
        
        if winner: break # Break Round Loop

        # Scoring
        s1 = stats[f1.name]['dmg'] + (stats[f1.name]['td']*15)
        s2 = stats[f2.name]['dmg'] + (stats[f2.name]['td']*15)
        for i in range(3):
            sc1, sc2 = s1, s2
            if i==1: sc1 += random.randint(-10, 10)
            if sc1 > sc2: judge_scores[i][0]+=10; judge_scores[i][1]+=9
            elif sc2 > sc1: judge_scores[i][0]+=9; judge_scores[i][1]+=10
            else: judge_scores[i][0]+=10; judge_scores[i][1]+=10

    # Decision Logic
    if not winner:
        votes_f1 = 0
        for s in judge_scores:
            if s[0] > s[1]: votes_f1 += 1
        winner = f1 if votes_f1 >= 2 else f2
        loser = f2 if winner == f1 else f1
        print(f"\n🏆 Winner: {winner.name} via Decision!")
    else:
        loser = f2 if winner == f1 else f1
        print(f"\n🏆 Winner: {winner.name} via {method} in Round {round_num}!")

    # --- UPDATE RECORDS ---
    # print("\n📝 Updating Records...")
    # winner.record['wins'] += 1
    # loser.record['losses'] += 1
    
    # Title Change Logic
    if is_title_fight and winner == f1 and f2.is_champion: # Challenger beat Champ
        print(f"👑 AND NEW! {winner.name} is the new Champion!")
        f1.is_champion = True
        f2.is_champion = False
    elif is_title_fight and winner.is_champion:
        print("👑 AND STILL! The Champion retains!")

    return True # Fight Completed successfully

# --- MENUS ---
def select_fighter_menu(roster, weight_class=None, exclude_id=None):
    # 1. Update rankings immediately so the list is fresh
    if weight_class:
        update_rankings(roster)

    # Filter and Sort by Rank
    candidates = [f for f in roster if f.weight_class == weight_class] if weight_class else roster
    if exclude_id is not None:
        candidates = [f for f in candidates if f.id != exclude_id]
    
    # Sort: Champ (0) -> Rank 1 -> Rank 2 -> ... -> Unranked (999)
    candidates.sort(key=lambda x: x.rank)

    print(f"\n--- SELECT FIGHTER: {weight_class if weight_class else 'ALL'} ---")
    if not candidates:
        print(f"⚠️  No fighters found in {weight_class}!")
        input("Press Enter to go back...")
        return None

    # Header
    print(f"{'Rank':<4} | {'Name':<22} | {'Rec':<6} | {'ID':<3}")
    print("-" * 50)
    
    for f in candidates:
        # Display Logic
        if f.is_champion:
            rank_str = "C"
            name_str = f"👑 {f.name}"
        elif f.rank <= 15:
            rank_str = f"#{f.rank}"
            name_str = f.name
        else:
            rank_str = "NR"
            name_str = f.name
            
        print(f"{rank_str:<4} | {name_str:<22} | {f.record['wins']}-{f.record['losses']:<3} | {f.id:<3}")
    print("-" * 50)
    print("Type 'C' for Champ, '1' for #1, or Enter ID")
    print("0    | CANCEL")

    # --- NEW INPUT LOGIC ---
    while True:
        choice = input("\nSelect Rank (e.g. C, 1, 5) or ID: ").strip().upper()
        
        if choice == '0': return None
        if not choice: continue

        selected = None

        # Option A: User typed "C" (Champion)
        if choice == 'C':
            selected = next((f for f in candidates if f.is_champion), None)
            if not selected: print("❌ No champion in this list.")

        # Option B: User typed a Rank Number (e.g. "1", "5")
        # We check if input is a digit AND it's small (likely a rank, not an ID like 99)
        elif choice.isdigit() and int(choice) <= 15:
            rank_num = int(choice)
            # Find the fighter with this specific rank
            selected = next((f for f in candidates if f.rank == rank_num), None)
            
            # Fallback: If no fighter has that rank (rare), check if it matches an ID
            if not selected:
                selected = next((f for f in candidates if f.id == rank_num), None)

        # Option C: User typed a large number (ID) or Name
        else:
            # Try ID first
            if choice.isdigit():
                id_num = int(choice)
                selected = next((f for f in candidates if f.id == id_num), None)
            
            # Try Name last
            if not selected:
                selected = next((f for f in candidates if choice.lower() in f.name.lower()), None)

        if selected:
            return selected
        else:
            print(f"❌ Could not find fighter '{choice}'. Try again.")
def main_menu():
    roster = load_roster()
    if not roster: return

    while True:
        clear_screen()
        print(f"UFC MATCHMAKER v2.0")
        print("---------------------------------------")
        print("1. Book a Fight (By Weight Class)")
        print("2. Save & Exit")
        
        choice = input("\nSelect Option: ")
        
        if choice == '1':
            # 1. Pick Division
            print("\nSelect Division:")
            divs = list(WEIGHT_CLASSES.keys())
            for i, d in enumerate(divs):
                print(f"{i+1}. {d}")
            
            try:
                div_idx = int(input("Choice: ")) - 1
                selected_div = divs[div_idx]
                
                # 2. Pick Fighter A (Red Corner)
                print("\n--- RED CORNER ---")
                f1 = select_fighter_menu(roster, selected_div)
                if not f1: continue
                
                # 3. Pick Fighter B (Blue Corner)
                # LOGIC: Pass f1.id so they don't appear in the list!
                print("\n--- BLUE CORNER ---")
                f2 = select_fighter_menu(roster, selected_div, exclude_id=f1.id)
                if not f2: continue
                
                # 4. Confirm
                is_title = False
                if f1.is_champion or f2.is_champion:
                    chk = input("\nIs this for the Title? (y/n): ")
                    if chk.lower() == 'y': is_title = True
                
                fight_result = simulate_fight(f1, f2, is_title)
                
                if fight_result:
                    # Auto-Save after every fight
                    save_roster(roster)
                    input("\nPress Enter to return to menu...")
                    
            except (ValueError, IndexError):
                print("Invalid Selection")
                time.sleep(1)

        elif choice == '2':
            save_roster(roster)
            print("Goodbye!")
            break

if __name__ == "__main__":
    main_menu()