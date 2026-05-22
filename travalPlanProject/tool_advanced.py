import json
from datetime import datetime, timedelta
import random

from travalPlanProject.travel_ai import (
    estimate_flight_cost,
    generate_packing_list,
    suggest_hotels,
    suggest_transport,
    suggest_places,
    suggest_restaurants,
    suggest_important_tips
)


def get_weather_forecast(destination, days):
    """Simulate weather forecast (in production, use a real API like OpenWeather)"""
    # Simulated weather data - in production, use real API
    conditions = ["Sunny", "Partly Cloudy", "Cloudy", "Light Rain", "Clear"]
    
    forecast = []
    for day in range(1, min(days + 1, 8)):  # Max 7 day forecast
        temp_high = random.randint(15, 28)
        temp_low = random.randint(8, 18)
        condition = random.choice(conditions)
        
        forecast.append({
            "day": f"Day {day}",
            "high": temp_high,
            "low": temp_low,
            "condition": condition,
            "icon": {
                "Sunny": "☀️",
                "Partly Cloudy": "⛅",
                "Cloudy": "☁️",
                "Light Rain": "🌧️",
                "Clear": "🌤️"
            }.get(condition, "🌤️")
        })
    
    return forecast


def convert_currency(amount, from_currency="EUR", to_currency="USD"):
    """Simulate currency conversion (in production, use real API like exchangerate-api.com)"""
    # Simulated exchange rates - in production, use real API
    rates = {
        "EUR": 1.0,
        "USD": 1.10,
        "GBP": 0.86,
        "JPY": 163.0,
        "CNY": 7.85,
        "INR": 91.5,
        "AUD": 1.65,
        "CAD": 1.48
    }
    
    eur_amount = amount / rates.get(from_currency, 1.0)
    converted = eur_amount * rates.get(to_currency, 1.0)
    
    return {
        "original_amount": amount,
        "original_currency": from_currency,
        "converted_amount": round(converted, 2),
        "converted_currency": to_currency,
        "rate": round(rates.get(to_currency, 1.0), 2)
    }








def calculate_budget_breakdown(total_budget, days, include_flights=False, flight_cost=0):
    """Calculate detailed budget breakdown with optional flight costs"""
    
    # If including flights, subtract from total budget
    remaining_budget = total_budget - flight_cost if include_flights else total_budget
    
    # Allocation percentages
    accommodation_pct = 0.35  # 35% for hotels
    food_pct = 0.25           # 25% for food
    activities_pct = 0.25     # 25% for activities/attractions
    transport_pct = 0.10      # 10% for local transport
    misc_pct = 0.05           # 5% for miscellaneous
    
    breakdown = {
        "total_budget": total_budget,
        "flight_cost": flight_cost if include_flights else 0,
        "remaining_budget": remaining_budget,
        "accommodation": round(remaining_budget * accommodation_pct, 2),
        "food": round(remaining_budget * food_pct, 2),
        "activities": round(remaining_budget * activities_pct, 2),
        "transport": round(remaining_budget * transport_pct, 2),
        "miscellaneous": round(remaining_budget * misc_pct, 2),
        "per_day_budget": round(remaining_budget / days, 2),
        "hotel_per_night": round((remaining_budget * accommodation_pct) / days, 2),
        "food_per_day": round((remaining_budget * food_pct) / days, 2),
        "activities_per_day": round((remaining_budget * activities_pct) / days, 2)
    }
    
    return breakdown


def generate_trip_stats(itinerary, budget_breakdown):
    """Generate trip statistics and analytics"""
    total_activities = sum(1 for day in itinerary.values() 
                          for period in ['morning', 'afternoon', 'evening'] 
                          if day.get(period, {}).get('activity'))
    
    total_activity_cost = sum(day.get('estimated_daily_cost', 0) for day in itinerary.values())
    
    # Count activities by category
    categories = {}
    for day in itinerary.values():
        for period in ['morning', 'afternoon', 'evening']:
            activity = day.get(period, {})
            category = activity.get('category', 'Other')
            categories[category] = categories.get(category, 0) + 1
    
    # Calculate average costs
    avg_activity_cost = total_activity_cost / len(itinerary) if itinerary else 0
    
    stats = {
        "total_activities": total_activities,
        "total_activity_cost": round(total_activity_cost, 2),
        "avg_activity_cost_per_day": round(avg_activity_cost, 2),
        "activity_breakdown": categories,
        "budget_utilized": round((total_activity_cost / budget_breakdown.get('activities', 1)) * 100, 1),
        "free_activities": sum(1 for day in itinerary.values() 
                              for period in ['morning', 'afternoon', 'evening']
                              if day.get(period, {}).get('cost', 0) == 0)
    }
    
    return stats
