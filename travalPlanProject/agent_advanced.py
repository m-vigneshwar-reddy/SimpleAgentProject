from travalPlanProject.tool_advanced import (
    suggest_hotels, 
    suggest_transport, 
    suggest_places, 
    suggest_restaurants,
    suggest_important_tips,
    calculate_budget_breakdown,
    get_weather_forecast,
    convert_currency,
    estimate_flight_cost,
    generate_packing_list,
    generate_trip_stats,
)
from travalPlanProject.ai_adapter import call_ollama
import json


class TravelPlannerAgent:
    def __init__(self, memory):
        self.memory = memory
        self.itinerary = {}
        self.hotels = []
        self.transport = []
        self.restaurants = []
        self.tips = []
        self.budget_breakdown = {}
        self.weather = []
        self.packing_list = {}
        self.flights = []
        self.stats = {}
        self.chat_history = []

    def create_itinerary(self, include_flights=False, origin_city=None):
        """Create a comprehensive travel itinerary"""
        destination = self.memory["destination"]
        days = self.memory["days"]
        budget = self.memory["budget"]
        purpose = self.memory.get("purpose", "leisure")
        style = self.memory.get("style", "relaxed")
        
        # Get flight estimates if requested
        flight_cost = 0
        if include_flights and origin_city:
            self.flights = estimate_flight_cost(origin_city, destination, days)
            # Use standard option as default
            flight_cost = self.flights[1]["price"] if len(self.flights) > 1 else 0
        
        # Calculate budget breakdown
        self.budget_breakdown = calculate_budget_breakdown(budget, days, include_flights, flight_cost)
        
        # Get weather forecast
        self.weather = get_weather_forecast(destination, days)
        
        # Get hotel suggestions
        hotel_budget_per_night = self.budget_breakdown["hotel_per_night"]
        self.hotels = suggest_hotels(destination, hotel_budget_per_night, purpose)
        
        # Get transport suggestions
        self.transport = suggest_transport(destination, days, purpose)
        
        # Get restaurant suggestions
        meal_budget = self.budget_breakdown["food_per_day"] / 3
        self.restaurants = suggest_restaurants(destination, purpose, meal_budget)
        
        # Get important tips
        self.tips = suggest_important_tips(destination, days, purpose)
        
        # Create daily itinerary
        activity_budget_per_day = self.budget_breakdown["activities_per_day"]
        
        for day in range(1, days + 1):
            daily_places = suggest_places(destination, day, purpose, style)
            
            while len(daily_places) < 3:
                daily_places.append({
                    "place_name": "Free Time",
                    "activity": "Leisure / Exploration",
                    "address": "Your choice",
                    "opening_hours": "Flexible",
                    "cost": 0,
                    "duration": "Flexible",
                    "description": "Explore at your own pace",
                    "rating": 4.5,
                    "category": "Leisure",
                    "best_time": "Anytime",
                    "tips": ["Discover hidden gems", "Visit local shops", "Relax at a café"],
                    "booking_required": False
                })
            
            daily_activity_cost = sum(place.get("cost", 0) for place in daily_places[:3])
            
            self.itinerary[f"Day {day}"] = {
                "morning": {
                    "place_name": daily_places[0].get("place_name", "Morning Activity"),
                    "activity": daily_places[0].get("activity", "Sightseeing"),
                    "address": daily_places[0].get("address", "City Center"),
                    "opening_hours": daily_places[0].get("opening_hours", "Check locally"),
                    "cost": daily_places[0].get("cost", 0),
                    "duration": daily_places[0].get("duration", "2-3 hours"),
                    "description": daily_places[0].get("description", ""),
                    "rating": daily_places[0].get("rating", 4.5),
                    "category": daily_places[0].get("category", "General"),
                    "best_time": daily_places[0].get("best_time", "Morning"),
                    "tips": daily_places[0].get("tips", []),
                    "booking_required": daily_places[0].get("booking_required", False)
                },
                "afternoon": {
                    "place_name": daily_places[1].get("place_name", "Afternoon Activity"),
                    "activity": daily_places[1].get("activity", "Sightseeing"),
                    "address": daily_places[1].get("address", "City Center"),
                    "opening_hours": daily_places[1].get("opening_hours", "Check locally"),
                    "cost": daily_places[1].get("cost", 0),
                    "duration": daily_places[1].get("duration", "2-3 hours"),
                    "description": daily_places[1].get("description", ""),
                    "rating": daily_places[1].get("rating", 4.5),
                    "category": daily_places[1].get("category", "General"),
                    "best_time": daily_places[1].get("best_time", "Afternoon"),
                    "tips": daily_places[1].get("tips", []),
                    "booking_required": daily_places[1].get("booking_required", False)
                },
                "evening": {
                    "place_name": daily_places[2].get("place_name", "Evening Activity"),
                    "activity": daily_places[2].get("activity", "Dining"),
                    "address": daily_places[2].get("address", "City Center"),
                    "opening_hours": daily_places[2].get("opening_hours", "Check locally"),
                    "cost": daily_places[2].get("cost", 0),
                    "duration": daily_places[2].get("duration", "2 hours"),
                    "description": daily_places[2].get("description", ""),
                    "rating": daily_places[2].get("rating", 4.5),
                    "category": daily_places[2].get("category", "General"),
                    "best_time": daily_places[2].get("best_time", "Evening"),
                    "tips": daily_places[2].get("tips", []),
                    "booking_required": daily_places[2].get("booking_required", False)
                },
                "estimated_daily_cost": round(daily_activity_cost, 2),
                "weather": self.weather[day-1] if day-1 < len(self.weather) else None
            }
        
        # Generate packing list based on weather
        weather_summary = ", ".join([w["condition"] for w in self.weather[:3]]) if self.weather else "Variable"
        self.packing_list = generate_packing_list(destination, days, purpose, weather_summary)
        
        # Generate trip statistics
        self.stats = generate_trip_stats(self.itinerary, self.budget_breakdown)
        
        return self.itinerary

    def refine_itinerary(self, feedback):
        """Refine itinerary based on user feedback"""
        self.memory["feedback"] = feedback
        text = feedback.lower()
        
        if "busy" in text or "too much" in text:
            for day in self.itinerary:
                if day.lower() in text:
                    self.itinerary[day]["afternoon"] = {
                        "place_name": "Free Time",
                        "activity": "Free time / Cafe visit",
                        "address": "Your choice",
                        "opening_hours": "Flexible",
                        "cost": 10,
                        "duration": "2-3 hours",
                        "description": "Relax and explore at your own pace",
                        "rating": 4.5,
                        "category": "Leisure",
                        "best_time": "Afternoon",
                        "tips": ["Find a local café", "People watching", "Light shopping"],
                        "booking_required": False
                    }
        
        elif "more activities" in text or "add more" in text:
            for day in self.itinerary:
                if day.lower() in text:
                    destination = self.memory["destination"]
                    purpose = self.memory.get("purpose", "leisure")
                    day_num = int(day.split()[1])
                    
                    new_places = suggest_places(destination, day_num, purpose, "packed")
                    if new_places and len(new_places) > 1:
                        self.itinerary[day]["afternoon"] = {
                            "place_name": new_places[1].get("place_name", "Additional Activity"),
                            "activity": new_places[1].get("activity", "Activity"),
                            "address": new_places[1].get("address", "City Center"),
                            "opening_hours": new_places[1].get("opening_hours", "Check locally"),
                            "cost": new_places[1].get("cost", 20),
                            "duration": new_places[1].get("duration", "2-3 hours"),
                            "description": new_places[1].get("description", ""),
                            "rating": new_places[1].get("rating", 4.5),
                            "category": new_places[1].get("category", "General"),
                            "best_time": new_places[1].get("best_time", "Afternoon"),
                            "tips": new_places[1].get("tips", []),
                            "booking_required": new_places[1].get("booking_required", False)
                        }
        
        elif "cheaper" in text or "reduce cost" in text or "budget" in text:
            for day in self.itinerary:
                if day.lower() in text:
                    self.itinerary[day]["morning"]["place_name"] = "Free Walking Tour"
                    self.itinerary[day]["morning"]["activity"] = "Free walking tour"
                    self.itinerary[day]["morning"]["cost"] = 0
                    self.itinerary[day]["afternoon"]["cost"] = max(0, self.itinerary[day]["afternoon"]["cost"] - 10)
        
        elif "expensive" in text or "upgrade" in text or "luxury" in text:
            for day in self.itinerary:
                if day.lower() in text:
                    self.itinerary[day]["evening"]["cost"] = self.itinerary[day]["evening"]["cost"] * 1.5
                    self.itinerary[day]["evening"]["description"] = "Premium experience - " + self.itinerary[day]["evening"]["description"]
        
        # Recalculate stats after changes
        self.stats = generate_trip_stats(self.itinerary, self.budget_breakdown)
        
        return self.itinerary

    def chat_with_agent(self, user_message):
        """Chat interface for asking questions about the trip"""
        self.chat_history.append({"role": "user", "message": user_message})
        
        # Create context from the trip plan
        context = f"""
        You are a helpful travel assistant for a trip to {self.memory.get('destination', 'the destination')}.
        Trip details:
        - Duration: {self.memory.get('days', 0)} days
        - Budget: €{self.memory.get('budget', 0)}
        - Purpose: {self.memory.get('purpose', 'leisure')}
        - Style: {self.memory.get('style', 'balanced')}
        
        Answer the user's question about their trip in a friendly, helpful manner.
        Keep responses concise (2-3 sentences max).
        
        User question: {user_message}
        """
        
        response = call_ollama(context)
        
        if not response:
            response = "I'm here to help with your travel plans! Could you please rephrase your question?"
        
        self.chat_history.append({"role": "assistant", "message": response})
        
        return response

    def compare_with_alternative(self, alt_destination, alt_budget):
        """Compare current trip with an alternative destination/budget"""
        # Create a comparison agent
        alt_memory = self.memory.copy()
        alt_memory["destination"] = alt_destination
        alt_memory["budget"] = alt_budget
        
        alt_agent = TravelPlannerAgent(alt_memory)
        alt_agent.create_itinerary()
        
        comparison = {
            "current": {
                "destination": self.memory["destination"],
                "budget": self.memory["budget"],
                "total_cost": sum(day.get("estimated_daily_cost", 0) for day in self.itinerary.values()),
                "avg_hotel": sum(h["price"] for h in self.hotels) / len(self.hotels) if self.hotels else 0,
                "activities": self.stats.get("total_activities", 0)
            },
            "alternative": {
                "destination": alt_destination,
                "budget": alt_budget,
                "total_cost": sum(day.get("estimated_daily_cost", 0) for day in alt_agent.itinerary.values()),
                "avg_hotel": sum(h["price"] for h in alt_agent.hotels) / len(alt_agent.hotels) if alt_agent.hotels else 0,
                "activities": alt_agent.stats.get("total_activities", 0)
            }
        }
        
        return comparison

    def get_complete_plan(self):
        """Get the complete travel plan with all details"""
        return {
            "itinerary": self.itinerary,
            "hotels": self.hotels,
            "transport": self.transport,
            "restaurants": self.restaurants,
            "tips": self.tips,
            "budget_breakdown": self.budget_breakdown,
            "weather": self.weather,
            "packing_list": self.packing_list,
            "flights": self.flights,
            "stats": self.stats
        }
    
    def export_to_dict(self):
        """Export complete plan as dictionary for export functions"""
        plan = self.get_complete_plan()
        plan["memory"] = self.memory
        return plan
