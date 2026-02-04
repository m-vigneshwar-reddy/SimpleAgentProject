import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3"


def call_ollama(prompt):
    """Helper function to call Ollama API"""
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=30
        )
        data = response.json()
        
        if "response" in data:
            return data["response"].strip()
        elif "message" in data and "content" in data["message"]:
            return data["message"]["content"].strip()
        else:
            return None
    except Exception as e:
        print(f"Ollama API Error: {e}")
        return None


def suggest_hotels(destination, budget_per_night, travel_purpose):
    """Suggest hotels based on destination, budget, and purpose"""
    prompt = f"""
    You are a travel expert. Suggest 3 hotels in {destination} for a {travel_purpose} trip.
    Budget per night: €{budget_per_night}
    
    For each hotel, provide:
    - Hotel name
    - Approximate price per night
    - Location area
    - Brief description (one line)
    
    Format your response EXACTLY as:
    Hotel Name 1 | €price | Area | Description
    Hotel Name 2 | €price | Area | Description
    Hotel Name 3 | €price | Area | Description
    
    Only provide the 3 lines, nothing else.
    """
    
    response = call_ollama(prompt)
    
    if not response:
        return [
            {"name": "Budget Hotel", "price": budget_per_night * 0.7, "area": "City Center", "description": "Comfortable stay"},
            {"name": "Mid-range Hotel", "price": budget_per_night, "area": "Downtown", "description": "Good amenities"},
            {"name": "Premium Option", "price": budget_per_night * 1.3, "area": "Tourist District", "description": "Excellent service"}
        ]
    
    hotels = []
    for line in response.split('\n'):
        if '|' in line:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 4:
                price_str = parts[1].replace('€', '').replace(',', '').strip()
                try:
                    price = float(''.join(filter(lambda x: x.isdigit() or x == '.', price_str)))
                except:
                    price = budget_per_night
                
                hotels.append({
                    "name": parts[0],
                    "price": price,
                    "area": parts[2],
                    "description": parts[3] if len(parts) > 3 else "Great choice"
                })
    
    if len(hotels) < 3:
        return [
            {"name": "Budget Hotel", "price": budget_per_night * 0.7, "area": "City Center", "description": "Comfortable stay"},
            {"name": "Mid-range Hotel", "price": budget_per_night, "area": "Downtown", "description": "Good amenities"},
            {"name": "Premium Option", "price": budget_per_night * 1.3, "area": "Tourist District", "description": "Excellent service"}
        ]
    
    return hotels[:3]


def suggest_transport(destination, days, travel_purpose):
    """Suggest transportation options"""
    prompt = f"""
    You are a travel expert. Suggest the best transportation methods for a {days}-day {travel_purpose} trip in {destination}.
    
    Provide 3 transportation options:
    1. Within city transportation
    2. Airport/arrival transportation
    3. Day trips transportation (if applicable)
    
    Format EXACTLY as:
    Transport Type 1 | €estimated_cost | Description
    Transport Type 2 | €estimated_cost | Description
    Transport Type 3 | €estimated_cost | Description
    
    Only provide 3 lines, nothing else.
    """
    
    response = call_ollama(prompt)
    
    if not response:
        return [
            {"type": "Public Transport Pass", "cost": 20 * days, "description": "Metro, bus, tram access"},
            {"type": "Airport Transfer", "cost": 30, "description": "Shared shuttle or taxi"},
            {"type": "Bike Rental", "cost": 15 * days, "description": "Explore at your own pace"}
        ]
    
    transport = []
    for line in response.split('\n'):
        if '|' in line:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 3:
                cost_str = parts[1].replace('€', '').replace(',', '').strip()
                try:
                    cost = float(''.join(filter(lambda x: x.isdigit() or x == '.', cost_str)))
                except:
                    cost = 50
                
                transport.append({
                    "type": parts[0],
                    "cost": cost,
                    "description": parts[2] if len(parts) > 2 else "Convenient option"
                })
    
    if len(transport) < 3:
        return [
            {"type": "Public Transport Pass", "cost": 20 * days, "description": "Metro, bus, tram access"},
            {"type": "Airport Transfer", "cost": 30, "description": "Shared shuttle or taxi"},
            {"type": "Bike Rental", "cost": 15 * days, "description": "Explore at your own pace"}
        ]
    
    return transport[:3]


def suggest_places(destination, day_number, travel_purpose, style):
    """Suggest places to visit for a specific day"""
    prompt = f"""
    You are a travel expert. Suggest 3 activities/places for Day {day_number} of a {travel_purpose} trip in {destination}.
    Travel style: {style}
    
    Provide one activity for: Morning, Afternoon, Evening
    
    Format EXACTLY as:
    Activity 1 | €cost | Duration | Description
    Activity 2 | €cost | Duration | Description
    Activity 3 | €cost | Duration | Description
    
    Only provide 3 lines, nothing else.
    """
    
    response = call_ollama(prompt)
    
    if not response:
        return [
            {"activity": "Morning City Walk", "cost": 0, "duration": "2-3 hours", "description": "Explore main attractions"},
            {"activity": "Afternoon Museum Visit", "cost": 15, "duration": "2-3 hours", "description": "Local culture and history"},
            {"activity": "Evening Dining", "cost": 30, "duration": "2 hours", "description": "Try local cuisine"}
        ]
    
    places = []
    for line in response.split('\n'):
        if '|' in line:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 4:
                cost_str = parts[1].replace('€', '').replace(',', '').strip()
                try:
                    cost = float(''.join(filter(lambda x: x.isdigit() or x == '.', cost_str)))
                except:
                    cost = 20
                
                places.append({
                    "activity": parts[0],
                    "cost": cost,
                    "duration": parts[2],
                    "description": parts[3] if len(parts) > 3 else "Great experience"
                })
    
    if len(places) < 3:
        return [
            {"activity": "Morning City Walk", "cost": 0, "duration": "2-3 hours", "description": "Explore main attractions"},
            {"activity": "Afternoon Museum Visit", "cost": 15, "duration": "2-3 hours", "description": "Local culture and history"},
            {"activity": "Evening Dining", "cost": 30, "duration": "2 hours", "description": "Try local cuisine"}
        ]
    
    return places[:3]


def suggest_restaurants(destination, travel_purpose, meal_budget):
    """Suggest restaurants for different meal types"""
    prompt = f"""
    You are a travel expert. Suggest 3 restaurants/dining options in {destination} for a {travel_purpose} trip.
    Budget per meal: €{meal_budget}
    
    Provide options for: Breakfast, Lunch, Dinner
    
    Format EXACTLY as:
    Restaurant Name 1 | €price_range | Cuisine Type | Description
    Restaurant Name 2 | €price_range | Cuisine Type | Description
    Restaurant Name 3 | €price_range | Cuisine Type | Description
    
    Only provide 3 lines, nothing else.
    """
    
    response = call_ollama(prompt)
    
    if not response:
        return [
            {"name": "Local Cafe", "price": meal_budget * 0.5, "cuisine": "Breakfast & Coffee", "type": "Breakfast"},
            {"name": "Casual Bistro", "price": meal_budget, "cuisine": "Local Cuisine", "type": "Lunch"},
            {"name": "Restaurant", "price": meal_budget * 1.5, "cuisine": "Traditional", "type": "Dinner"}
        ]
    
    restaurants = []
    meal_types = ["Breakfast", "Lunch", "Dinner"]
    idx = 0
    
    for line in response.split('\n'):
        if '|' in line and idx < 3:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 4:
                price_str = parts[1].replace('€', '').replace(',', '').strip()
                try:
                    price = float(''.join(filter(lambda x: x.isdigit() or x == '.', price_str)))
                except:
                    price = meal_budget
                
                restaurants.append({
                    "name": parts[0],
                    "price": price,
                    "cuisine": parts[2],
                    "type": meal_types[idx]
                })
                idx += 1
    
    if len(restaurants) < 3:
        return [
            {"name": "Local Cafe", "price": meal_budget * 0.5, "cuisine": "Breakfast & Coffee", "type": "Breakfast"},
            {"name": "Casual Bistro", "price": meal_budget, "cuisine": "Local Cuisine", "type": "Lunch"},
            {"name": "Restaurant", "price": meal_budget * 1.5, "cuisine": "Traditional", "type": "Dinner"}
        ]
    
    return restaurants[:3]


def suggest_important_tips(destination, days, travel_purpose):
    """Suggest important travel tips and essentials"""
    prompt = f"""
    You are a travel expert. Provide 5 important tips for a {days}-day {travel_purpose} trip to {destination}.
    
    Include tips about:
    - Local customs/etiquette
    - Safety considerations
    - Must-have items
    - Money/payment methods
    - Best time to visit attractions
    
    Format as simple bullet points, one tip per line, maximum 10 words per tip.
    Provide ONLY 5 tips, nothing else.
    """
    
    response = call_ollama(prompt)
    
    if not response:
        return [
            "Carry local currency for small purchases",
            "Download offline maps before arriving",
            "Learn basic local phrases",
            "Keep copies of important documents",
            "Check weather forecast and pack accordingly"
        ]
    
    tips = []
    for line in response.split('\n'):
        line = line.strip()
        if line and len(line) > 5:
            # Remove bullet points, numbers, etc.
            clean_line = line.lstrip('•-*123456789. ')
            if clean_line:
                tips.append(clean_line)
    
    if len(tips) < 5:
        return [
            "Carry local currency for small purchases",
            "Download offline maps before arriving",
            "Learn basic local phrases",
            "Keep copies of important documents",
            "Check weather forecast and pack accordingly"
        ]
    
    return tips[:5]


def calculate_budget_breakdown(total_budget, days):
    """Calculate detailed budget breakdown"""
    # Allocation percentages
    accommodation_pct = 0.35  # 35% for hotels
    food_pct = 0.25           # 25% for food
    activities_pct = 0.25     # 25% for activities/attractions
    transport_pct = 0.10      # 10% for local transport
    misc_pct = 0.05           # 5% for miscellaneous
    
    breakdown = {
        "accommodation": round(total_budget * accommodation_pct, 2),
        "food": round(total_budget * food_pct, 2),
        "activities": round(total_budget * activities_pct, 2),
        "transport": round(total_budget * transport_pct, 2),
        "miscellaneous": round(total_budget * misc_pct, 2),
        "per_day_budget": round(total_budget / days, 2),
        "hotel_per_night": round((total_budget * accommodation_pct) / days, 2),
        "food_per_day": round((total_budget * food_pct) / days, 2),
        "activities_per_day": round((total_budget * activities_pct) / days, 2)
    }
    
    return breakdown
