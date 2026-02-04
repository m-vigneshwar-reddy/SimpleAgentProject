from tool import (
    suggest_hotels, 
    suggest_transport, 
    suggest_places, 
    suggest_restaurants,
    suggest_important_tips,
    calculate_budget_breakdown
)


class TravelPlannerAgent:
    def __init__(self, memory):
        self.memory = memory
        self.itinerary = {}
        self.hotels = []
        self.transport = []
        self.restaurants = []
        self.tips = []
        self.budget_breakdown = {}

    def create_itinerary(self):
        """Create a comprehensive travel itinerary"""
        destination = self.memory["destination"]
        days = self.memory["days"]
        budget = self.memory["budget"]
        purpose = self.memory.get("purpose", "leisure")
        style = self.memory.get("style", "relaxed")
        
        # Calculate budget breakdown
        self.budget_breakdown = calculate_budget_breakdown(budget, days)
        
        # Get hotel suggestions
        hotel_budget_per_night = self.budget_breakdown["hotel_per_night"]
        self.hotels = suggest_hotels(destination, hotel_budget_per_night, purpose)
        
        # Get transport suggestions
        self.transport = suggest_transport(destination, days, purpose)
        
        # Get restaurant suggestions
        meal_budget = self.budget_breakdown["food_per_day"] / 3  # 3 meals per day
        self.restaurants = suggest_restaurants(destination, purpose, meal_budget)
        
        # Get important tips
        self.tips = suggest_important_tips(destination, days, purpose)
        
        # Create daily itinerary
        activity_budget_per_day = self.budget_breakdown["activities_per_day"]
        
        for day in range(1, days + 1):
            # Get places for this specific day
            daily_places = suggest_places(destination, day, purpose, style)
            
            # Ensure we have 3 activities (morning, afternoon, evening)
            while len(daily_places) < 3:
                daily_places.append({
                    "activity": "Free time / Leisure",
                    "cost": 0,
                    "duration": "Flexible",
                    "description": "Explore at your own pace"
                })
            
            # Calculate daily costs
            daily_activity_cost = sum(place.get("cost", 0) for place in daily_places[:3])
            
            self.itinerary[f"Day {day}"] = {
                "morning": {
                    "activity": daily_places[0]["activity"],
                    "cost": daily_places[0].get("cost", 0),
                    "duration": daily_places[0].get("duration", "2-3 hours"),
                    "description": daily_places[0].get("description", "")
                },
                "afternoon": {
                    "activity": daily_places[1]["activity"],
                    "cost": daily_places[1].get("cost", 0),
                    "duration": daily_places[1].get("duration", "2-3 hours"),
                    "description": daily_places[1].get("description", "")
                },
                "evening": {
                    "activity": daily_places[2]["activity"],
                    "cost": daily_places[2].get("cost", 0),
                    "duration": daily_places[2].get("duration", "2 hours"),
                    "description": daily_places[2].get("description", "")
                },
                "estimated_daily_cost": round(daily_activity_cost, 2)
            }
        
        return self.itinerary

    def refine_itinerary(self, feedback):
        """Refine itinerary based on user feedback"""
        self.memory["feedback"] = feedback
        text = feedback.lower()
        
        # Handle different types of feedback
        if "busy" in text or "too much" in text:
            for day in self.itinerary:
                if day.lower() in text:
                    # Make the afternoon more relaxed
                    self.itinerary[day]["afternoon"] = {
                        "activity": "Free time / Cafe visit",
                        "cost": 10,
                        "duration": "2-3 hours",
                        "description": "Relax and explore at your own pace"
                    }
        
        elif "more activities" in text or "add more" in text:
            for day in self.itinerary:
                if day.lower() in text:
                    # Suggest the day is packed (user wants more)
                    destination = self.memory["destination"]
                    purpose = self.memory.get("purpose", "leisure")
                    day_num = int(day.split()[1])
                    
                    # Get new suggestions
                    new_places = suggest_places(destination, day_num, purpose, "packed")
                    if new_places:
                        self.itinerary[day]["afternoon"] = {
                            "activity": new_places[1].get("activity", "Additional activity"),
                            "cost": new_places[1].get("cost", 20),
                            "duration": new_places[1].get("duration", "2-3 hours"),
                            "description": new_places[1].get("description", "")
                        }
        
        elif "cheaper" in text or "reduce cost" in text or "budget" in text:
            for day in self.itinerary:
                if day.lower() in text:
                    # Replace with free/cheap activities
                    self.itinerary[day]["morning"]["activity"] = "Free walking tour"
                    self.itinerary[day]["morning"]["cost"] = 0
                    self.itinerary[day]["afternoon"]["cost"] = max(0, self.itinerary[day]["afternoon"]["cost"] - 10)
        
        elif "expensive" in text or "upgrade" in text or "luxury" in text:
            for day in self.itinerary:
                if day.lower() in text:
                    # Suggest more premium options
                    self.itinerary[day]["evening"]["cost"] = self.itinerary[day]["evening"]["cost"] * 1.5
                    self.itinerary[day]["evening"]["description"] = "Premium experience - " + self.itinerary[day]["evening"]["description"]
        
        return self.itinerary

    def get_complete_plan(self):
        """Get the complete travel plan with all details"""
        return {
            "itinerary": self.itinerary,
            "hotels": self.hotels,
            "transport": self.transport,
            "restaurants": self.restaurants,
            "tips": self.tips,
            "budget_breakdown": self.budget_breakdown
        }
