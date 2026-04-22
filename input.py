import json 

class Uma:
    def __init__(self):
        with open("character.json", "r") as b:
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
        self.sprint = "E"
        self.mile = "E"
        self.medium = "E"
        self.long = "E"

    def isi_distance(self):
        list_distance = ["sprint","mile","medium","long"]
        for t in list_distance:
            while True:
                input_distance = input(f"Insert the {t} Grade Distance of Your Uma (S/A/B/C/D/E):").strip().upper()
                if input_distance in ["S","A","B","C","D","E"]:
                    setattr(self, t, input_distance)
                    break
                else:
                    print("Distance must be S/A/B/C/D/E") 

class Track:
    def __init__(self):
        self.dirt = "E" 
        self.turf = "E"

    def isi_track(self):
        list_track = ["dirt", "turf"]
        for u in list_track:
            while True:
                input_track = input(f"Insert the {u} Grade Track of Your Uma (S/A/B/C/D/E):").strip().upper()
                if input_track in ["S","A","B","C","D","E"]:
                    setattr(self, u, input_track)
                    break
                else:
                    print("Track must be S/A/B/C/D/E")

class Style:
    def __init__(self):
        self.front_runner = "E"
        self.pace_chaser = "E"
        self.late_surger = "E" 
        self.end_closer = "E"

    def isi_style(self):
        list_style = ["front_runner", "pace_chaser", "late_surger", "end_closer"]
        for v in list_style:
            while True:
                input_style = input(f"Insert the {v} grade Style of Your Uma (S/A/B/C/D/E):").strip().upper()
                if input_style in ["S","A","B","C","D","E"]:
                    setattr(self, v, input_style)
                    break
                else:
                    print("Track must be S/A/B/C/D/E")

class Skills():
    def __init__(self):
        with open("skills.json", "r") as f:
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

class UmaMusume(Uma):
    def __init__(self):
        super().__init__()
        self.distance = Distance()
        self.track = Track()
        self.style = Style()
        self.stats = Stats()
        self.skills = Skills()

    def setup(self):
        self.isi_identitas()
        self.skills.selected_skills.append({"name": self.unique_skill})
        self.distance.isi_distance()
        self.track.isi_track()
        self.style.isi_style()
        self.stats.isi_stats()
        self.skills.isi_skills()

    def to_dict(self):
        return {
            "name": self.name,
            "unique_skill": self.unique_skill,
            "skill_level": self.level_skill,
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
            "skills": self.skills.selected_skills
        }

my_uma = UmaMusume()
my_uma.setup()
uma_stats = my_uma.to_dict()