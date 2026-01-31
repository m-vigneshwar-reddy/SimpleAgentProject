from tool import estimate_budget, suggest_places
class TravelPlannerAgent:
    def __init__(self, memory):
        self.memory = memory
        self.itinerary = {}

    def create_itinerary(self):
        daily_budget = estimate_budget(
            self.memory["budget"],
            self.memory["days"]
        )
        used_places = set()
        for day in range(1, self.memory["days"] + 1):
            places = suggest_places(
                self.memory["destination"],
                self.memory["style"]
            )
            unique_places = []
            for p in places:
                if p not in used_places:
                    unique_places.append(p)
                    used_places.add(p)
            # fallback if repetition occurs
            while len(unique_places) < 3:
                unique_places.append("Leisure / Exploration time")
            self.itinerary[f"Day {day}"] = {
                "Morning": unique_places[0],
                "Afternoon": unique_places[1],
                "Evening": unique_places[2],
                "Transport": "Walking / Public transport",
                "Estimated Cost (€)": daily_budget
            }
        return self.itinerary

    def refine_itinerary(self, feedback):
        self.memory["feedback"] = feedback
        text = feedback.lower()
        for day in self.itinerary:
            if day.lower() in text and "busy" in text:
                self.itinerary[day]["Afternoon"] = "Free time / Cafe visit"
        return self.itinerary