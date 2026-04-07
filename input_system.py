class Uma:
    def __init__(self):
        self.name = ""
        self.star = 0

    def perkenalan(self):
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
                    continue
                if 0<=hasil_input<=1200:
                    setattr(self, s, hasil_input)
                    break
                else:
                    print("Stats must be between 0-1200")
               
my_uma = Uma()
my_stats = Stats()

my_uma.perkenalan()
my_stats.isi_stats()

print(my_stats.speed)