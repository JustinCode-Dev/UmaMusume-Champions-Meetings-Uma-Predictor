import json 
import datetime
import os

class Uma:
    def __init__(self):
        with open("data/raw/character.json", "r") as b:
            self.char_data = json.load(b)

        self.name = ""
        self.star = 0
        self.unique_skill = ""
        self.level_skill = 0

    def isi_identitas(self):
        while True:
            keyword = input(f"your Uma's Name:").strip().lower()

            if not keyword:
                print("don't leave the input empty!")
                continue 
            
            result = [x for x in self.char_data if keyword in x["name"].lower()]
            if len(result) == 0:
                print("Enter a valid character name")
                continue

            for i, name in enumerate(result):
                print(i, name["name"])

            try:
                number = int(input("Insert your option:").strip())
            except ValueError:
                print("Option must be integers")
                continue

            if number >= len(result) or number < 0:
                print("Insert the number based on the options")
                continue

            selected = result[number]
            self.name = selected["name"]
            
            break

        while True:
            try:
                star = int(input("Insert the Limit Break/star:"))
            except ValueError:
                print("Limit break/star must be integers")
                continue
            if star >= int(selected["base_star"]) and star <= 5:
                self.star = star
                break
            else:
                print("Limit break cannot be lower than the base star")
                continue

        if int(selected["base_star"]) < 3 and self.star >= 3:
            self.unique_skill = selected["unique_skill_evolved"]
        else:
            self.unique_skill = selected["unique_skill"]

        if int(selected["base_star"]) < 3 and star < 3:
            max_level = star + 3
            min_level = star
        elif int(selected["base_star"]) < 3 and star >= 3:
            max_level = (star - 2) + 3
            min_level = star - 2
        else:  
            max_level = (star - 2) + 3
            min_level = star - 2
            
        while True:
            try:
                level_skill = int(input("insert the level of the unique skill:"))
            except ValueError:
                print("level must be integers")
                continue
            if min_level <= level_skill <= max_level:
                self.level_skill = level_skill
                break
            else:
                print("Insert valid level")
                continue
            
        print(f"\nHalo {self.name}, Your Current Star {self.star}!\n")

class Stats:
    def __init__(self):
        self.speed = 0
        self.stamina = 0
        self.power = 0
        self.guts = 0
        self.wit = 0

    def isi_stats(self):
        list_stats = ["speed","stamina","power","guts","wit"]
        for s in list_stats:
            while True:
                try:
                    hasil_input = int(input(f"Insert the {s} of Your Uma:" ))
                except ValueError:
                    print("Stats must be integers")
                    continue 
                if 0<=hasil_input<=1200:
                    setattr(self, s, hasil_input) #setattr(object, attribute, value) 
                    break
                else:
                    print("Stats must be between 0-1200")
                    continue
               
class Distance:
    def __init__(self):
        self.sprint = "G"
        self.mile = "G"
        self.medium = "G"
        self.long = "G"

    def isi_distance(self):
        list_distance = ["sprint","mile","medium","long"]
        for t in list_distance:
            while True:
                input_distance = input(f"Insert the {t} Grade Distance of Your Uma (S/A/B/C/D/E/F/G):").strip().upper()
                if input_distance in ["S","A","B","C","D","E","F","G"]:
                    setattr(self, t, input_distance)
                    break
                else:
                    print("Distance must be S/A/B/C/D/E/G") 

class Track:
    def __init__(self):
        self.dirt = "G" 
        self.turf = "G"

    def isi_track(self):
        list_track = ["dirt", "turf"]
        for u in list_track:
            while True:
                input_track = input(f"Insert the {u} Grade Track of Your Uma (S/A/B/C/D/E/F/G):").strip().upper()
                if input_track in ["S","A","B","C","D","E","F","G"]:
                    setattr(self, u, input_track)
                    break
                else:
                    print("Track must be S/A/B/C/D/E/F/G")

class Style:
    def __init__(self):
        self.front_runner = "G"
        self.pace_chaser = "G"
        self.late_surger = "G" 
        self.end_closer = "G"

    def isi_style(self):
        list_style = ["front_runner", "pace_chaser", "late_surger", "end_closer"]
        for v in list_style:
            while True:
                input_style = input(f"Insert the {v} grade Style of Your Uma (S/A/B/C/D/E/F/G):").strip().upper()
                if input_style in ["S","A","B","C","D","E","F","G"]:
                    setattr(self, v, input_style)
                    break
                else:
                    print("Track must be S/A/B/C/D/E/F/G")

class Skills():
    def __init__(self):
        with open("data/raw/skills.json", "r") as f:
            self.skills = json.load(f)
        self.selected_skills = []

    def isi_skills(self):
        while True:
            keyword = input("Insert the Skills that your uma have (write done if you're done): ").strip() .lower()

            if not keyword:
                print("don't leave the input empty!")
                continue

            if keyword == "done":
                break
            
            result = [x for x in self.skills if keyword in x["name"].lower()]
            if len(result) == 0:
                print("Enter a valid skill name")
                continue

            for i, skill in enumerate(result):
                print(i, skill["name"])

            try:
                number = int(input("Insert your option:").strip())
            except ValueError:
                print("Option must be integers")
                continue

            if number >= len(result) or number < 0:
                print("Insert the number based on the options")
                continue

            selected = result[number]
            if selected["name"] in [x["name"] for x in self.selected_skills]:
                print(f"You already added {selected['name']}!")
            else:
                self.selected_skills.append(result[number])
        
        if self.selected_skills:
            print("\nYour Uma has these skills:") 
            for a in self.selected_skills:
                print(f"- {a['name']}") 
        else:
            print("\nYour Uma has no skills yet.")
        
class mood: 
    def __init__(self):
        self.mood = ""

    def input_mood(self):
        while True:
            mood = input("masukan mood:").strip()
            if mood not in ["awful", "bad", "normal", "good", "great"]:
                print("wrong")
                continue
            else:
                self.mood = mood
                break

class rank: 
    def __init__(self):
        self.rank = 0

    def input_rank(self):
        while True:
            try:
                rank = int(input("masukan rank:"))
            except ValueError:
                print("where's the number?")
                continue

            if rank < 1 or rank > 9:
                print("no")
                continue
                
            else:
                self.rank = rank
                break

class UmaMusume(Uma):
    def __init__(self):
        super().__init__()
        self.distance = Distance()
        self.track = Track()
        self.style = Style()
        self.stats = Stats()
        self.skills = Skills()
        self.mood = mood()
        self.rank = rank()

    def setup(self):
        self.isi_identitas()
        self.skills.selected_skills.append({"name": self.unique_skill})
        self.distance.isi_distance()
        self.track.isi_track()
        self.style.isi_style()
        self.stats.isi_stats()
        self.skills.isi_skills()
        self.mood.input_mood()
        self.rank.input_rank()

    def to_dict(self):
        return {
            "name": self.name,
            "unique_skill": self.unique_skill,
            "skill_level": self.level_skill,
            "mood": self.mood.mood,
            "distance":{
                "sprint": self.distance.sprint,
                "mile": self.distance.mile,
                "medium": self.distance.medium,
                "long": self.distance.long
            },
            "track":{
                "dirt": self.track.dirt,
                "turf": self.track.turf
            },
            "style":{
                "front_runner": self.style.front_runner,
                "pace_chaser": self.style.pace_chaser,
                "late_surger": self.style.late_surger,
                "end_closer": self.style.end_closer
            },
            "stats": {
                "speed": self.stats.speed,
                "stamina": self.stats.stamina,
                "power": self.stats.power,
                "guts": self.stats.guts,
                "wit": self.stats.wit
            },
            "skills": self.skills.selected_skills,
            "rank": self.rank.rank
        }

def fetch_data():
    my_uma = UmaMusume()
    my_uma.setup()
    return my_uma.to_dict()

if __name__ == "__main__":
    latest_data = fetch_data()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    clean_name = latest_data["name"].lower().replace(" ", "_")[:20]
    filename = f"input_{clean_name}_{timestamp}.json"

    save_path = "data/raw/input" 
    
    os.makedirs(save_path, exist_ok=True)
    
    full_path = os.path.join(save_path, filename)

    with open(full_path, "w") as f:
        json.dump(latest_data, f, indent=4)

    print(f"\n[SUCCESS] Data saved to: {full_path}")