import json 

class Uma:
    def __init__(self):
        self.name = ""
        self.star = 0

    def isi_identitas(self):
        while True:
            self.name = input(f"your Uma's Name:").strip().title()

            if self.name.replace(" ", "").isalpha():    
                break
            else:
                print("Name must be a string and not empty")

        while True:
            try:
                input_star = int(input(f"Limit Break star:"))

                if 0<=input_star<=4:
                    self.star = input_star
                    break
                else:
                    print("Star must be between 1-4") 
            except ValueError:
                print("Star must be an integer and between 1-4")
    
        print(f"Halo {self.name}, Your Current Star {self.star}!")

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
                    print("Stats must be integers and between 0-1200")
                    continue #continue digunakan untuk mengulang kembali ke awal loop saat terjadi error, sehingga tidak perlu menggunakan else untuk memisahkan antara input yang benar dan salah
                if 0<=hasil_input<=1200:
                    setattr(self, s, hasil_input) #setattr(object, attribute, value) diusahakan ditaruh di bawah saat input sudah benar, agar tidak menyimpan nilai yang salah duluan ke dalam class Stats
                    break
                else:
                    print("Stats must be between 0-1200")
               
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
            if selected in self.selected_skills:
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
        self.distance.isi_distance()
        self.track.isi_track()
        self.style.isi_style()
        self.stats.isi_stats()
        self.skills.isi_skills()

            
my_uma = UmaMusume()
my_uma.setup()


#buat data skills
#buat sistem input skills