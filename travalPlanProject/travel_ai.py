import json
import random

from travalPlanProject.ai_adapter import call_ollama


def estimate_flight_cost(origin, destination, days):
    """Estimate flight costs using AI"""
    prompt = f"""
    You are a travel pricing expert. Estimate round-trip flight costs from {origin} to {destination} for a {days}-day trip.
    
    Provide 3 options: Budget, Standard, Premium
    
    Format EXACTLY as:
    Budget | €price | Description
    Standard | €price | Description  
    Premium | €price | Description
    
    Only provide 3 lines, nothing else.
    """
    
    response = call_ollama(prompt)
    
    if not response:
        # Fallback estimates based on distance simulation
        base_price = 200 + (days * 20)
        return [
            {"type": "Budget", "price": base_price, "description": "Economy with layover"},
            {"type": "Standard", "price": base_price * 1.5, "description": "Direct flight, economy"},
            {"type": "Premium", "price": base_price * 3, "description": "Business class, lounge access"}
        ]
    
    flights = []
    for line in response.split('\n'):
        if '|' in line:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 3:
                price_str = parts[1].replace('€', '').replace(',', '').strip()
                try:
                    price = float(''.join(filter(lambda x: x.isdigit() or x == '.', price_str)))
                except:
                    price = 300
                
                flights.append({
                    "type": parts[0],
                    "price": price,
                    "description": parts[2]
                })
    
    if len(flights) < 3:
        base_price = 200 + (days * 20)
        return [
            {"type": "Budget", "price": base_price, "description": "Economy with layover"},
            {"type": "Standard", "price": base_price * 1.5, "description": "Direct flight, economy"},
            {"type": "Premium", "price": base_price * 3, "description": "Business class, lounge access"}
        ]
    
    return flights[:3]


def generate_packing_list(destination, days, purpose, weather_conditions):
    """Generate smart packing list based on trip details"""
    prompt = f"""
    Create a packing list for a {days}-day {purpose} trip to {destination}.
    Weather: {weather_conditions}
    
    Organize into 5 categories: Clothing, Documents, Electronics, Toiletries, Miscellaneous
    
    Provide 3-5 essential items per category.
    Format as: Category | Item1, Item2, Item3
    
    Provide exactly 5 lines, one per category.
    """
    
    response = call_ollama(prompt)
    
    default_list = {
        "Clothing": ["Comfortable shoes", "Weather-appropriate outfits", "Light jacket", "Underwear & socks"],
        "Documents": ["Passport/ID", "Travel insurance", "Hotel confirmations", "Emergency contacts"],
        "Electronics": ["Phone charger", "Power adapter", "Camera", "Headphones"],
        "Toiletries": ["Toothbrush/paste", "Medications", "Sunscreen", "Basic first aid"],
        "Miscellaneous": ["Reusable water bottle", "Day backpack", "Snacks", "Guidebook/map"]
    }
    
    if not response:
        return default_list
    
    packing_list = {}
    for line in response.split('\n'):
        if '|' in line:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 2:
                category = parts[0].strip()
                items = [item.strip() for item in parts[1].split(',')]
                packing_list[category] = items
    
    return packing_list if len(packing_list) >= 3 else default_list


def suggest_hotels(destination, budget_per_night, travel_purpose):
    """Enhanced hotel suggestions with ratings"""
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
            {
                "name": "Budget Hotel",
                "price": budget_per_night * 0.7,
                "area": "City Center",
                "description": "Comfortable stay",
                "rating": 3.8,
                "amenities": ["WiFi", "Breakfast"]
            },
            {
                "name": "Mid-range Hotel",
                "price": budget_per_night,
                "area": "Downtown",
                "description": "Good amenities",
                "rating": 4.2,
                "amenities": ["WiFi", "Gym", "Pool"]
            },
            {
                "name": "Premium Option",
                "price": budget_per_night * 1.3,
                "area": "Tourist District",
                "description": "Excellent service",
                "rating": 4.6,
                "amenities": ["WiFi", "Spa", "Restaurant", "Concierge"]
            }
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
                
                rating = 3.5 + (price / budget_per_night) * 0.8
                rating = min(5.0, max(3.0, rating))
                
                if price < budget_per_night * 0.8:
                    amenities = ["WiFi", "Breakfast"]
                elif price < budget_per_night * 1.2:
                    amenities = ["WiFi", "Gym", "Breakfast", "Pool"]
                else:
                    amenities = ["WiFi", "Spa", "Restaurant", "Gym", "Pool", "Concierge"]
                
                hotels.append({
                    "name": parts[0],
                    "price": price,
                    "area": parts[2],
                    "description": parts[3],
                    "rating": round(rating, 1),
                    "amenities": amenities
                })
    
    if len(hotels) < 3:
        return [
            {
                "name": "Budget Hotel",
                "price": budget_per_night * 0.7,
                "area": "City Center",
                "description": "Comfortable stay",
                "rating": 3.8,
                "amenities": ["WiFi", "Breakfast"]
            },
            {
                "name": "Mid-range Hotel",
                "price": budget_per_night,
                "area": "Downtown",
                "description": "Good amenities",
                "rating": 4.2,
                "amenities": ["WiFi", "Gym", "Pool"]
            },
            {
                "name": "Premium Option",
                "price": budget_per_night * 1.3,
                "area": "Tourist District",
                "description": "Excellent service",
                "rating": 4.6,
                "amenities": ["WiFi", "Spa", "Restaurant", "Concierge"]
            }
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
            {
                "type": "Public Transport Pass",
                "cost": 20 * days,
                "description": "Metro, bus, tram access",
                "eco_friendly": True
            },
            {
                "type": "Airport Transfer",
                "cost": 30,
                "description": "Shared shuttle or taxi",
                "eco_friendly": False
            },
            {
                "type": "Bike Rental",
                "cost": 15 * days,
                "description": "Explore at your own pace",
                "eco_friendly": True
            }
        ]
    
    transport = []
    eco_keywords = ["bike", "public", "metro", "bus", "tram", "walk", "train"]
    
    for line in response.split('\n'):
        if '|' in line:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 3:
                cost_str = parts[1].replace('€', '').replace(',', '').strip()
                try:
                    cost = float(''.join(filter(lambda x: x.isdigit() or x == '.', cost_str)))
                except:
                    cost = 50
                
                is_eco = any(keyword in parts[0].lower() for keyword in eco_keywords)
                
                transport.append({
                    "type": parts[0],
                    "cost": cost,
                    "description": parts[2],
                    "eco_friendly": is_eco
                })
    
    if len(transport) < 3:
        return [
            {
                "type": "Public Transport Pass",
                "cost": 20 * days,
                "description": "Metro, bus, tram access",
                "eco_friendly": True
            },
            {
                "type": "Airport Transfer",
                "cost": 30,
                "description": "Shared shuttle or taxi",
                "eco_friendly": False
            },
            {
                "type": "Bike Rental",
                "cost": 15 * days,
                "description": "Explore at your own pace",
                "eco_friendly": True
            }
        ]
    
    return transport[:3]


def suggest_places(destination, day_number, travel_purpose, style):
    """Suggest places to visit for a specific day with detailed information"""
    prompt = f"""
    You are a travel expert. Suggest 3 specific places/attractions for Day {day_number} of a {travel_purpose} trip in {destination}.
    Travel style: {style}
    
    Provide one place for: Morning, Afternoon, Evening
    For each place, include: Name | Address/Area | Opening Hours | Entrance Fee | Best Time | Why Visit
    
    Format EXACTLY as:
    Place Name 1 | Address/Area | Hours | €fee | Best time | Why visit (one sentence)
    Place Name 2 | Address/Area | Hours | €fee | Best time | Why visit (one sentence)
    Place Name 3 | Address/Area | Hours | €fee | Best time | Why visit (one sentence)
    
    Only provide 3 lines, nothing else. Be specific with actual place names in {destination}.
    """
    
    response = call_ollama(prompt)
    
    if not response:
        return [
            {
                "place_name": f"Historic Center of {destination}",
                "activity": "Guided Walking Tour",
                "address": "City Center",
                "opening_hours": "24/7 (Tours: 9 AM - 5 PM)",
                "cost": 0,
                "duration": "2-3 hours",
                "description": "Explore the main historic attractions and landmarks",
                "rating": 4.5,
                "category": "Sightseeing",
                "best_time": "Early morning (9-11 AM)",
                "tips": ["Wear comfortable shoes", "Bring water", "Free walking tours available"],
                "booking_required": False
            },
            {
                "place_name": f"National Museum of {destination}",
                "activity": "Museum Visit",
                "address": "Museum District",
                "opening_hours": "10 AM - 6 PM (Closed Mondays)",
                "cost": 15,
                "duration": "2-3 hours",
                "description": "Discover local culture, art, and history",
                "rating": 4.3,
                "category": "Culture",
                "best_time": "Afternoon (2-4 PM)",
                "tips": ["Buy tickets online", "Audio guides available", "Photography allowed"],
                "booking_required": False
            },
            {
                "place_name": f"Traditional Restaurant Area",
                "activity": "Local Cuisine Experience",
                "address": "Old Town",
                "opening_hours": "6 PM - 11 PM",
                "cost": 30,
                "duration": "2 hours",
                "description": "Enjoy authentic local dishes in traditional setting",
                "rating": 4.6,
                "category": "Food",
                "best_time": "Evening (7-9 PM)",
                "tips": ["Reservations recommended", "Try local specialties", "Ask for daily specials"],
                "booking_required": True
            }
        ]
    
    places = []
    categories = ["Sightseeing", "Culture", "Food", "Adventure", "Shopping", "Nature", "Entertainment"]
    periods = ["Morning", "Afternoon", "Evening"]
    
    for idx, line in enumerate(response.split('\n')):
        if '|' in line:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 6:
                place_name = parts[0]
                address = parts[1] if len(parts) > 1 else "City Center"
                opening_hours = parts[2] if len(parts) > 2 else "Check locally"
                
                cost_str = parts[3].replace('€', '').replace(',', '').strip() if len(parts) > 3 else "0"
                try:
                    cost = float(''.join(filter(lambda x: x.isdigit() or x == '.', cost_str)))
                except:
                    cost = 10 if idx == 1 else (0 if idx == 0 else 25)
                
                best_time = parts[4] if len(parts) > 4 else periods[idx]
                why_visit = parts[5] if len(parts) > 5 else "Popular local attraction"
                
                rating = 4.0 + (random.random() * 0.9)
                
                place_lower = place_name.lower()
                if "museum" in place_lower or "gallery" in place_lower or "exhibition" in place_lower:
                    category = "Culture"
                    activity = "Museum/Gallery Visit"
                elif "park" in place_lower or "garden" in place_lower or "nature" in place_lower or "beach" in place_lower:
                    category = "Nature"
                    activity = "Outdoor Experience"
                elif "restaurant" in place_lower or "café" in place_lower or "food" in place_lower or "market" in place_lower:
                    category = "Food"
                    activity = "Dining/Food Experience"
                elif "temple" in place_lower or "church" in place_lower or "cathedral" in place_lower or "mosque" in place_lower:
                    category = "Culture"
                    activity = "Religious/Historic Site Visit"
                elif "tower" in place_lower or "palace" in place_lower or "castle" in place_lower:
                    category = "Sightseeing"
                    activity = "Historic Landmark Tour"
                elif "shop" in place_lower or "mall" in place_lower or "bazaar" in place_lower:
                    category = "Shopping"
                    activity = "Shopping Experience"
                else:
                    category = categories[idx % len(categories)]
                    activity = "Local Experience"
                
                tips = []
                if category == "Culture":
                    tips = ["Buy tickets online to skip queues", "Audio guides often available", "Photography rules vary"]
                elif category == "Food":
                    tips = ["Reservations recommended for dinner", "Try the daily specials", "Ask locals for recommendations"]
                elif category == "Nature":
                    tips = ["Wear comfortable walking shoes", "Bring sun protection", "Best light for photos at sunset"]
                elif category == "Shopping":
                    tips = ["Bargaining may be acceptable", "Keep receipts for tax refunds", "Cash often preferred"]
                else:
                    tips = ["Arrive early to avoid crowds", "Check weather conditions", "Bring water and snacks"]
                
                booking_required = cost > 20 or "restaurant" in place_lower or "tour" in place_lower
                
                if category in ["Food"]:
                    duration = "1.5-2 hours"
                elif category in ["Nature", "Sightseeing"]:
                    duration = "2-4 hours"
                else:
                    duration = "1-3 hours"
                
                places.append({
                    "place_name": place_name,
                    "activity": activity,
                    "address": address,
                    "opening_hours": opening_hours,
                    "cost": cost,
                    "duration": duration,
                    "description": why_visit,
                    "rating": round(rating, 1),
                    "category": category,
                    "best_time": best_time,
                    "tips": tips,
                    "booking_required": booking_required
                })
    
    if len(places) < 3:
        return [
            {
                "place_name": f"Historic Center of {destination}",
                "activity": "Guided Walking Tour",
                "address": "City Center",
                "opening_hours": "24/7 (Tours: 9 AM - 5 PM)",
                "cost": 0,
                "duration": "2-3 hours",
                "description": "Explore the main historic attractions and landmarks",
                "rating": 4.5,
                "category": "Sightseeing",
                "best_time": "Early morning (9-11 AM)",
                "tips": ["Wear comfortable shoes", "Bring water", "Free walking tours available"],
                "booking_required": False
            },
            {
                "place_name": f"National Museum of {destination}",
                "activity": "Museum Visit",
                "address": "Museum District",
                "opening_hours": "10 AM - 6 PM (Closed Mondays)",
                "cost": 15,
                "duration": "2-3 hours",
                "description": "Discover local culture, art, and history",
                "rating": 4.3,
                "category": "Culture",
                "best_time": "Afternoon (2-4 PM)",
                "tips": ["Buy tickets online", "Audio guides available", "Photography allowed"],
                "booking_required": False
            },
            {
                "place_name": f"Traditional Restaurant Area",
                "activity": "Local Cuisine Experience",
                "address": "Old Town",
                "opening_hours": "6 PM - 11 PM",
                "cost": 30,
                "duration": "2 hours",
                "description": "Enjoy authentic local dishes in traditional setting",
                "rating": 4.6,
                "category": "Food",
                "best_time": "Evening (7-9 PM)",
                "tips": ["Reservations recommended", "Try local specialties", "Ask for daily specials"],
                "booking_required": True
            }
        ]
    
    return places[:3]


def suggest_restaurants(destination, travel_purpose, meal_budget):
    """Suggest restaurants with enhanced details"""
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
            {
                "name": "Local Cafe",
                "price": meal_budget * 0.5,
                "cuisine": "Breakfast & Coffee",
                "type": "Breakfast",
                "rating": 4.3,
                "popular_dishes": ["Croissants", "Coffee"]
            },
            {
                "name": "Casual Bistro",
                "price": meal_budget,
                "cuisine": "Local Cuisine",
                "type": "Lunch",
                "rating": 4.4,
                "popular_dishes": ["Daily specials", "Salads"]
            },
            {
                "name": "Fine Dining",
                "price": meal_budget * 1.5,
                "cuisine": "Traditional",
                "type": "Dinner",
                "rating": 4.7,
                "popular_dishes": ["Signature dish", "Local wine"]
            }
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
                
                rating = 4.0 + (random.random() * 0.9)
                
                dishes_by_type = {
                    "Breakfast": ["Pastries", "Coffee", "Eggs"],
                    "Lunch": ["Sandwiches", "Salads", "Soup"],
                    "Dinner": ["Main course", "Dessert", "Wine"]
                }
                
                restaurants.append({
                    "name": parts[0],
                    "price": price,
                    "cuisine": parts[2],
                    "type": meal_types[idx],
                    "rating": round(rating, 1),
                    "popular_dishes": dishes_by_type.get(meal_types[idx], ["Local favorites"])
                })
                idx += 1
    
    if len(restaurants) < 3:
        return [
            {
                "name": "Local Cafe",
                "price": meal_budget * 0.5,
                "cuisine": "Breakfast & Coffee",
                "type": "Breakfast",
                "rating": 4.3,
                "popular_dishes": ["Croissants", "Coffee"]
            },
            {
                "name": "Casual Bistro",
                "price": meal_budget,
                "cuisine": "Local Cuisine",
                "type": "Lunch",
                "rating": 4.4,
                "popular_dishes": ["Daily specials", "Salads"]
            },
            {
                "name": "Fine Dining",
                "price": meal_budget * 1.5,
                "cuisine": "Traditional",
                "type": "Dinner",
                "rating": 4.7,
                "popular_dishes": ["Signature dish", "Local wine"]
            }
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
    
    Format as simple bullet points, one tip per line, maximum 15 words per tip.
    Provide ONLY 5 tips, nothing else.
    """
    
    response = call_ollama(prompt)
    
    if not response:
        return [
            "Carry local currency for small purchases and markets",
            "Download offline maps and translation apps before arriving",
            "Learn basic local phrases to show respect",
            "Keep copies of important documents in cloud storage",
            "Check weather forecast and pack appropriate clothing"
        ]
    
    tips = []
    for line in response.split('\n'):
        line = line.strip()
        if line and len(line) > 5:
            clean_line = line.lstrip('•-*123456789. ')
            if clean_line:
                tips.append(clean_line)
    
    if len(tips) < 5:
        return [
            "Carry local currency for small purchases and markets",
            "Download offline maps and translation apps before arriving",
            "Learn basic local phrases to show respect",
            "Keep copies of important documents in cloud storage",
            "Check weather forecast and pack appropriate clothing"
        ]
    
    return tips[:5]
