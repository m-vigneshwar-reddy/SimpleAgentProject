import streamlit as st
from travalPlanProject.agent_advanced import TravelPlannerAgent
from travalPlanProject.memory import init_db, load_memory, save_memory, get_all_trips
from travalPlanProject.export_utils import export_to_pdf, export_to_excel, export_to_json, export_to_ical, generate_qr_code
from travalPlanProject.tool_advanced import convert_currency
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import os

# Initialize database
init_db()

# Page configuration
st.set_page_config(
    page_title="🧳 Advanced AI Travel Planner", 
    page_icon="🧳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'generated' not in st.session_state:
    st.session_state.generated = False
if 'agent' not in st.session_state:
    st.session_state.agent = None
if 'plan' not in st.session_state:
    st.session_state.plan = None
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []
if 'show_comparison' not in st.session_state:
    st.session_state.show_comparison = False
if 'preferred_currency' not in st.session_state:
    st.session_state.preferred_currency = 'EUR'

# Load previous memory
memory = load_memory()

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(120deg, #1E88E5, #43A047);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .stat-value {
        font-size: 2rem;
        font-weight: bold;
    }
    .stat-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    .weather-card {
        background: linear-gradient(135deg, #FFB75E 0%, #ED8F03 100%);
        padding: 1rem;
        border-radius: 8px;
        color: white;
        text-align: center;
    }
    .activity-badge {
        background-color: #E3F2FD;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-size: 0.85rem;
        color: #1565C0;
        display: inline-block;
        margin: 0.2rem;
    }
    .rating-stars {
        color: #FFA000;
        font-size: 1.2rem;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    
    # Theme toggle
    if st.button("🌓 Toggle Dark Mode"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()
    
    st.markdown("---")
    
    # Currency selector
    st.markdown("### 💱 Preferred Currency")
    currencies = ["EUR", "USD", "GBP", "JPY", "CNY", "INR", "AUD", "CAD"]
    st.session_state.preferred_currency = st.selectbox(
        "Display prices in:",
        currencies,
        index=currencies.index(st.session_state.preferred_currency)
    )
    
    st.markdown("---")
    
    # Trip history
    st.markdown("### 📚 Trip History")
    all_trips = get_all_trips()
    
    if all_trips:
        for trip in all_trips[:5]:
            with st.expander(f"🌍 {trip['destination']} ({trip['days']} days)"):
                st.write(f"**Budget:** €{trip['budget']}")
                st.write(f"**Purpose:** {trip['purpose']}")
                st.write(f"**Date:** {trip['created_at']}")
    else:
        st.info("No previous trips yet")
    
    st.markdown("---")
    
    # Quick actions
    st.markdown("### 🚀 Quick Actions")
    
    if st.button("🗑️ Clear Current Plan"):
        st.session_state.generated = False
        st.session_state.agent = None
        st.session_state.plan = None
        st.session_state.chat_messages = []
        st.rerun()
    
    if st.session_state.generated and st.session_state.plan:
        st.markdown("#### 📥 Export Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📄 PDF"):
                with st.spinner("Generating PDF..."):
                    try:
                        pdf_file = export_to_pdf(st.session_state.plan)
                        with open(pdf_file, 'rb') as f:
                            st.download_button(
                                "⬇️ Download PDF",
                                f,
                                file_name=pdf_file,
                                mime="application/pdf"
                            )
                    except Exception as e:
                        st.error(f"PDF export failed: {e}")
        
        with col2:
            if st.button("📊 Excel"):
                with st.spinner("Generating Excel..."):
                    try:
                        xlsx_file = export_to_excel(st.session_state.plan)
                        if xlsx_file:
                            with open(xlsx_file, 'rb') as f:
                                st.download_button(
                                    "⬇️ Download Excel",
                                    f,
                                    file_name=xlsx_file,
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                        else:
                            st.error("Install openpyxl: pip install openpyxl")
                    except Exception as e:
                        st.error(f"Excel export failed: {e}")
        
        if st.button("📅 iCalendar"):
            start_date = st.date_input("Trip start date:", datetime.now())
            with st.spinner("Generating calendar..."):
                try:
                    ical_file = export_to_ical(st.session_state.plan, start_date=start_date)
                    with open(ical_file, 'r') as f:
                        st.download_button(
                            "⬇️ Download Calendar",
                            f,
                            file_name=ical_file,
                            mime="text/calendar"
                        )
                except Exception as e:
                    st.error(f"Calendar export failed: {e}")
        
        if st.button("🔗 JSON"):
            with st.spinner("Generating JSON..."):
                try:
                    json_file = export_to_json(st.session_state.plan)
                    with open(json_file, 'r') as f:
                        st.download_button(
                            "⬇️ Download JSON",
                            f,
                            file_name=json_file,
                            mime="application/json"
                        )
                except Exception as e:
                    st.error(f"JSON export failed: {e}")

# Main content
st.markdown('<p class="main-header">🧳 Advanced AI Travel Planner</p>', unsafe_allow_html=True)

# Create tabs for different sections
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🗺️ Plan Your Trip", 
    "📊 Analytics & Stats", 
    "💬 Chat Assistant",
    "🔍 Compare Destinations",
    "📋 Checklist & Packing"
])

# TAB 1: Plan Your Trip
with tab1:
    st.markdown("""
        <div style='background: linear-gradient(135deg, #E3F2FD 0%, #E8F5E9 100%); padding: 1.5rem; border-radius: 12px; margin-bottom: 2rem;'>
            <h3 style='margin: 0; color: #1565C0;'>✨ Your AI-powered travel companion!</h3>
            <p style='margin: 0.5rem 0 0 0; color: #2E7D32;'>
                Get personalized itineraries, hotel recommendations, weather forecasts, transport options, 
                dining suggestions, and essential travel tips - all tailored to your preferences and budget.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Input form
    with st.form("travel_form"):
        st.subheader("📋 Trip Details")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            destination = st.text_input(
                "🌍 Destination",
                value=memory.get("destination", "Paris"),
                placeholder="e.g., Paris, Tokyo, New York"
            )
            
            days = st.number_input(
                "📅 Number of days",
                min_value=1,
                max_value=30,
                value=int(memory.get("days", 5))
            )
        
        with col2:
            budget = st.number_input(
                "💰 Total budget (€)",
                min_value=100,
                max_value=100000,
                value=int(memory.get("budget", 1500)),
                step=100
            )
            
            purpose = st.selectbox(
                "🎯 Travel purpose",
                ["Leisure", "Business", "Adventure", "Cultural", "Romantic", "Family", "Solo"],
                index=0
            )
        
        with col3:
            style = st.selectbox(
                "⚡ Travel style",
                ["Relaxed", "Balanced", "Packed"],
                index=1
            )
            
            include_flights = st.checkbox("✈️ Include flight estimates", value=False)
        
        if include_flights:
            origin_city = st.text_input(
                "📍 Departure city",
                placeholder="e.g., London, New York"
            )
        else:
            origin_city = None
        
        submit = st.form_submit_button("🚀 Generate Complete Travel Plan", use_container_width=True)
    
    # Generate itinerary
    if submit:
        if not destination.strip():
            st.error("⚠️ Please enter a destination!")
        elif include_flights and not origin_city:
            st.error("⚠️ Please enter your departure city for flight estimates!")
        else:
            with st.spinner("🔮 Creating your personalized travel plan... This may take a moment..."):
                memory = {
                    "destination": destination,
                    "days": int(days),
                    "budget": int(budget),
                    "style": style.lower(),
                    "purpose": purpose.lower()
                }
                
                agent = TravelPlannerAgent(memory)
                itinerary = agent.create_itinerary(
                    include_flights=include_flights, 
                    origin_city=origin_city if include_flights else None
                )
                
                st.session_state.agent = agent
                st.session_state.plan = agent.get_complete_plan()
                st.session_state.generated = True
                
                save_memory(agent.memory)
            
            st.success("✅ Your complete travel plan is ready!")
            st.balloons()
    
    # Display the plan
    if st.session_state.generated and st.session_state.plan:
        plan = st.session_state.plan
        
        st.markdown("---")
        
        # Quick stats
        stats = plan.get('stats', {})
        budget_data = plan.get('budget_breakdown', {})
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-value">{stats.get('total_activities', 0)}</div>
                    <div class="stat-label">Total Activities</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-value">€{budget_data.get('per_day_budget', 0):.0f}</div>
                    <div class="stat-label">Per Day Budget</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-value">{stats.get('free_activities', 0)}</div>
                    <div class="stat-label">Free Activities</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-value">{stats.get('budget_utilized', 0):.0f}%</div>
                    <div class="stat-label">Budget Utilized</div>
                </div>
            """, unsafe_allow_html=True)
        
        # Weather Forecast
        if plan.get('weather'):
            st.markdown("### 🌤️ Weather Forecast")
            weather_cols = st.columns(min(len(plan['weather']), 7))
            
            for idx, weather in enumerate(plan['weather'][:7]):
                with weather_cols[idx]:
                    st.markdown(f"""
                        <div class="weather-card">
                            <div style="font-size: 2rem;">{weather['icon']}</div>
                            <div><b>{weather['day']}</b></div>
                            <div>{weather['high']}°/{weather['low']}°C</div>
                            <div style="font-size: 0.85rem;">{weather['condition']}</div>
                        </div>
                    """, unsafe_allow_html=True)
        
        # Flight Options (if included)
        if plan.get('flights'):
            st.markdown("### ✈️ Flight Options")
            flight_cols = st.columns(3)
            
            for idx, flight in enumerate(plan['flights']):
                with flight_cols[idx]:
                    converted = convert_currency(flight['price'], 'EUR', st.session_state.preferred_currency)
                    st.markdown(f"""
                        <div style='background-color: #E8F5E9; padding: 1rem; border-radius: 8px;'>
                            <h4 style='margin: 0; color: #2E7D32;'>{flight['type']}</h4>
                            <p style='font-size: 1.5rem; margin: 0.5rem 0;'>
                                <b>{converted['converted_currency']} {converted['converted_amount']:.2f}</b>
                            </p>
                            <p style='margin: 0; font-size: 0.9rem;'>{flight['description']}</p>
                        </div>
                    """, unsafe_allow_html=True)
        
        # Budget Breakdown
        st.markdown("### 💰 Budget Breakdown")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            converted = convert_currency(budget_data['accommodation'], 'EUR', st.session_state.preferred_currency)
            st.metric("🏨 Accommodation", f"{converted['converted_currency']} {converted['converted_amount']:.2f}")
            st.caption(f"Per night: {converted['converted_currency']} {convert_currency(budget_data['hotel_per_night'], 'EUR', st.session_state.preferred_currency)['converted_amount']:.2f}")
        
        with col2:
            converted = convert_currency(budget_data['food'], 'EUR', st.session_state.preferred_currency)
            st.metric("🍽️ Food & Dining", f"{converted['converted_currency']} {converted['converted_amount']:.2f}")
            st.caption(f"Per day: {converted['converted_currency']} {convert_currency(budget_data['food_per_day'], 'EUR', st.session_state.preferred_currency)['converted_amount']:.2f}")
        
        with col3:
            converted = convert_currency(budget_data['activities'], 'EUR', st.session_state.preferred_currency)
            st.metric("🎭 Activities", f"{converted['converted_currency']} {converted['converted_amount']:.2f}")
            st.caption(f"Per day: {converted['converted_currency']} {convert_currency(budget_data['activities_per_day'], 'EUR', st.session_state.preferred_currency)['converted_amount']:.2f}")
        
        with col4:
            converted = convert_currency(budget_data['transport'] + budget_data['miscellaneous'], 'EUR', st.session_state.preferred_currency)
            st.metric("🚌 Transport & Misc", f"{converted['converted_currency']} {converted['converted_amount']:.2f}")
        
        # Hotels
        st.markdown("### 🏨 Recommended Hotels")
        hotel_cols = st.columns(3)
        
        for idx, hotel in enumerate(plan['hotels']):
            with hotel_cols[idx]:
                rating_stars = "⭐" * int(hotel.get('rating', 0))
                converted = convert_currency(hotel['price'], 'EUR', st.session_state.preferred_currency)
                
                st.markdown(f"""
                    <div style='background-color: #F5F5F5; padding: 1.5rem; border-radius: 12px; height: 100%;'>
                        <h4 style='margin: 0 0 0.5rem 0; color: #2E7D32;'>{hotel['name']}</h4>
                        <div class="rating-stars">{rating_stars}</div>
                        <p style='margin: 0.5rem 0;'><b>{converted['converted_currency']} {converted['converted_amount']:.2f}</b> per night</p>
                        <p style='margin: 0.3rem 0;'>📍 {hotel['area']}</p>
                        <p style='margin: 0.5rem 0; font-size: 0.9rem;'>{hotel['description']}</p>
                        <div style='margin-top: 0.5rem;'>
                """, unsafe_allow_html=True)
                
                for amenity in hotel.get('amenities', []):
                    st.markdown(f'<span class="activity-badge">{amenity}</span>', unsafe_allow_html=True)
                
                st.markdown("</div></div>", unsafe_allow_html=True)
        
        # Transport Options
        st.markdown("### 🚌 Transportation Options")
        transport_cols = st.columns(3)
        
        for idx, transport in enumerate(plan['transport']):
            with transport_cols[idx]:
                eco_badge = "🌿 Eco-Friendly" if transport.get('eco_friendly') else "🚗 Standard"
                converted = convert_currency(transport['cost'], 'EUR', st.session_state.preferred_currency)
                
                st.markdown(f"""
                    <div style='background-color: #E8F5E9; padding: 1.5rem; border-radius: 12px;'>
                        <h4 style='margin: 0 0 0.5rem 0;'>{transport['type']}</h4>
                        <p style='margin: 0.3rem 0;'><b>{converted['converted_currency']} {converted['converted_amount']:.2f}</b></p>
                        <p style='margin: 0.3rem 0; font-size: 0.85rem;'>{eco_badge}</p>
                        <p style='margin: 0.5rem 0;'>{transport['description']}</p>
                    </div>
                """, unsafe_allow_html=True)
        
        # Restaurants
        st.markdown("### 🍽️ Dining Recommendations")
        restaurant_cols = st.columns(3)
        
        for idx, restaurant in enumerate(plan['restaurants']):
            with restaurant_cols[idx]:
                meal_emoji = {"Breakfast": "🌅", "Lunch": "☀️", "Dinner": "🌙"}
                emoji = meal_emoji.get(restaurant['type'], "🍽️")
                rating_stars = "⭐" * int(restaurant.get('rating', 0))
                converted = convert_currency(restaurant['price'], 'EUR', st.session_state.preferred_currency)
                
                st.markdown(f"""
                    <div style='background-color: #FFF3E0; padding: 1.5rem; border-radius: 12px;'>
                        <h4 style='margin: 0 0 0.5rem 0;'>{emoji} {restaurant['type']}</h4>
                        <div class="rating-stars">{rating_stars}</div>
                        <p style='margin: 0.5rem 0;'><b>{restaurant['name']}</b></p>
                        <p style='margin: 0.3rem 0;'>{converted['converted_currency']} {converted['converted_amount']:.2f}</p>
                        <p style='margin: 0.3rem 0; color: #E65100;'>{restaurant['cuisine']}</p>
                        <p style='margin: 0.5rem 0; font-size: 0.85rem;'>Popular: {', '.join(restaurant.get('popular_dishes', []))}</p>
                    </div>
                """, unsafe_allow_html=True)
        
        # Daily Itinerary
        st.markdown("### 📅 Day-by-Day Itinerary")
        
        for day, activities in plan['itinerary'].items():
            weather_info = activities.get('weather', {})
            weather_display = f"{weather_info.get('icon', '🌤️')} {weather_info.get('high', '--')}°/{weather_info.get('low', '--')}°C" if weather_info else ""
            
            converted_cost = convert_currency(activities['estimated_daily_cost'], 'EUR', st.session_state.preferred_currency)
            
            with st.expander(
                f"🗓️ {day} - {weather_display} - Estimated Cost: {converted_cost['converted_currency']} {converted_cost['converted_amount']:.2f}",
                expanded=True
            ):
                col1, col2, col3 = st.columns(3)
                
                for col, period in zip([col1, col2, col3], ['morning', 'afternoon', 'evening']):
                    with col:
                        activity = activities[period]
                        period_emoji = {"morning": "🌅", "afternoon": "☀️", "evening": "🌙"}
                        
                        st.markdown(f"### {period_emoji[period]} {period.capitalize()}")
                        
                        # Place name and activity
                        st.markdown(f"**📍 {activity.get('place_name', 'Activity')}**")
                        st.caption(f"_{activity.get('activity', 'N/A')}_")
                        
                        # Rating
                        rating_stars = "⭐" * int(activity.get('rating', 0))
                        st.markdown(f'<div class="rating-stars">{rating_stars} {activity.get("rating", 0)}</div>', unsafe_allow_html=True)
                        
                        # Address
                        st.markdown(f"📮 **Address:** {activity.get('address', 'N/A')}")
                        
                        # Opening hours
                        st.markdown(f"🕒 **Hours:** {activity.get('opening_hours', 'Check locally')}")
                        
                        # Duration
                        st.caption(f"⏱️ Duration: {activity['duration']}")
                        
                        # Best time to visit
                        if activity.get('best_time'):
                            st.caption(f"🎯 Best time: {activity['best_time']}")
                        
                        # Cost with currency conversion
                        converted_activity = convert_currency(activity['cost'], 'EUR', st.session_state.preferred_currency)
                        st.markdown(f"💰 **Cost:** {converted_activity['converted_currency']} {converted_activity['converted_amount']:.2f}")
                        
                        # Booking required badge
                        if activity.get('booking_required'):
                            st.markdown('<span class="activity-badge" style="background-color: #FFEBEE; color: #C62828;">📅 Booking Recommended</span>', unsafe_allow_html=True)
                        
                        # Category badge
                        st.markdown(f'<span class="activity-badge">{activity.get("category", "General")}</span>', unsafe_allow_html=True)
                        
                        # Description
                        st.write(f"ℹ️ {activity['description']}")
                        
                        # Tips section
                        if activity.get('tips'):
                            with st.expander("💡 Tips & Recommendations"):
                                for tip in activity['tips']:
                                    st.markdown(f"• {tip}")
                        
                        st.markdown("---")
        
        # Travel Tips
        st.markdown("### 💡 Important Travel Tips")
        
        for idx, tip in enumerate(plan['tips'], 1):
            st.markdown(f"""
                <div style='background-color: #FFF9C4; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; border-left: 4px solid #FBC02D;'>
                    <b>{idx}.</b> {tip}
                </div>
            """, unsafe_allow_html=True)
        
        # Feedback Section
        st.markdown("---")
        st.markdown("### 💬 Refine Your Itinerary")
        
        feedback = st.text_area(
            "Have suggestions or changes?",
            placeholder="e.g., 'Day 2 is too busy' or 'Add more cultural activities to Day 3'",
            height=100
        )
        
        if st.button("🔄 Update Itinerary", use_container_width=True):
            if feedback:
                with st.spinner("Updating your itinerary..."):
                    updated_itinerary = st.session_state.agent.refine_itinerary(feedback)
                    st.session_state.plan["itinerary"] = updated_itinerary
                    st.session_state.plan["stats"] = st.session_state.agent.stats
                    save_memory(st.session_state.agent.memory)
                
                st.success("✅ Itinerary updated!")
                st.rerun()
            else:
                st.warning("⚠️ Please enter your feedback first.")

# TAB 2: Analytics & Stats
with tab2:
    if st.session_state.generated and st.session_state.plan:
        st.markdown("## 📊 Trip Analytics & Statistics")
        
        plan = st.session_state.plan
        stats = plan.get('stats', {})
        budget_data = plan.get('budget_breakdown', {})
        
        # Budget Distribution Pie Chart
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 💰 Budget Distribution")
            
            budget_labels = ['Accommodation', 'Food', 'Activities', 'Transport', 'Misc']
            budget_values = [
                budget_data.get('accommodation', 0),
                budget_data.get('food', 0),
                budget_data.get('activities', 0),
                budget_data.get('transport', 0),
                budget_data.get('miscellaneous', 0)
            ]
            
            fig_budget = go.Figure(data=[go.Pie(
                labels=budget_labels,
                values=budget_values,
                hole=0.4,
                marker=dict(colors=['#1E88E5', '#43A047', '#FFA726', '#AB47BC', '#26C6DA'])
            )])
            
            fig_budget.update_layout(
                title="Budget Allocation",
                height=400
            )
            
            st.plotly_chart(fig_budget, use_container_width=True)
        
        with col2:
            st.markdown("### 🎭 Activity Categories")
            
            activity_breakdown = stats.get('activity_breakdown', {})
            
            if activity_breakdown:
                fig_activities = go.Figure(data=[go.Bar(
                    x=list(activity_breakdown.keys()),
                    y=list(activity_breakdown.values()),
                    marker=dict(color='#1E88E5')
                )])
                
                fig_activities.update_layout(
                    title="Activities by Category",
                    xaxis_title="Category",
                    yaxis_title="Count",
                    height=400
                )
                
                st.plotly_chart(fig_activities, use_container_width=True)
            else:
                st.info("No activity data available")
        
        # Daily cost breakdown
        st.markdown("### 📈 Daily Cost Breakdown")
        
        itinerary = plan.get('itinerary', {})
        days = list(itinerary.keys())
        daily_costs = [itinerary[day].get('estimated_daily_cost', 0) for day in days]
        
        fig_daily = go.Figure(data=[go.Scatter(
            x=days,
            y=daily_costs,
            mode='lines+markers',
            marker=dict(size=10, color='#43A047'),
            line=dict(width=3, color='#43A047')
        )])
        
        fig_daily.update_layout(
            title="Daily Activity Costs",
            xaxis_title="Day",
            yaxis_title="Cost (€)",
            height=400
        )
        
        st.plotly_chart(fig_daily, use_container_width=True)
        
        # Statistics summary
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Average Daily Cost", f"€{stats.get('avg_activity_cost_per_day', 0):.2f}")
        
        with col2:
            st.metric("Total Activity Cost", f"€{stats.get('total_activity_cost', 0):.2f}")
        
        with col3:
            st.metric("Budget Efficiency", f"{stats.get('budget_utilized', 0):.1f}%")
    
    else:
        st.info("📊 Generate a trip plan first to see analytics!")

# TAB 3: Chat Assistant
with tab3:
    st.markdown("## 💬 Chat with Your Travel Assistant")
    
    if st.session_state.generated and st.session_state.agent:
        st.markdown("""
            <div style='background-color: #E3F2FD; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;'>
                <p style='margin: 0;'>
                    💡 Ask me anything about your trip! I can help with recommendations, 
                    clarifications, or alternative suggestions.
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        # Display chat history
        for msg in st.session_state.chat_messages:
            role = msg['role']
            message = msg['message']
            
            if role == 'user':
                st.markdown(f"""
                    <div style='background-color: #E8F5E9; padding: 1rem; border-radius: 8px; margin: 0.5rem 0;'>
                        <b>You:</b> {message}
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div style='background-color: #FFF3E0; padding: 1rem; border-radius: 8px; margin: 0.5rem 0;'>
                        <b>🤖 Assistant:</b> {message}
                    </div>
                """, unsafe_allow_html=True)
        
        # Chat input
        user_input = st.text_input(
            "Your message:",
            placeholder="e.g., 'What's the best time to visit the museum?' or 'Can you suggest a romantic restaurant?'",
            key="chat_input"
        )
        
        if st.button("Send 📤") and user_input:
            with st.spinner("Thinking..."):
                response = st.session_state.agent.chat_with_agent(user_input)
                st.session_state.chat_messages.append({"role": "user", "message": user_input})
                st.session_state.chat_messages.append({"role": "assistant", "message": response})
            st.rerun()
        
        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_messages = []
            st.rerun()
    
    else:
        st.info("💬 Generate a trip plan first to chat with the assistant!")

# TAB 4: Compare Destinations
with tab4:
    st.markdown("## 🔍 Compare Destinations")
    
    if st.session_state.generated and st.session_state.agent:
        st.markdown("Compare your current trip with an alternative destination or budget.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            alt_destination = st.text_input("Alternative Destination", placeholder="e.g., Rome")
        
        with col2:
            alt_budget = st.number_input("Alternative Budget (€)", min_value=100, value=1000, step=100)
        
        if st.button("🔄 Compare", use_container_width=True):
            if alt_destination:
                with st.spinner("Generating comparison..."):
                    comparison = st.session_state.agent.compare_with_alternative(alt_destination, alt_budget)
                    
                    st.markdown("### Comparison Results")
                    
                    comp_col1, comp_col2 = st.columns(2)
                    
                    with comp_col1:
                        st.markdown(f"""
                            <div style='background-color: #E3F2FD; padding: 1.5rem; border-radius: 12px;'>
                                <h3 style='color: #1565C0;'>Current Trip</h3>
                                <p><b>Destination:</b> {comparison['current']['destination']}</p>
                                <p><b>Budget:</b> €{comparison['current']['budget']}</p>
                                <p><b>Estimated Cost:</b> €{comparison['current']['total_cost']:.2f}</p>
                                <p><b>Avg Hotel:</b> €{comparison['current']['avg_hotel']:.2f}/night</p>
                                <p><b>Activities:</b> {comparison['current']['activities']}</p>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    with comp_col2:
                        st.markdown(f"""
                            <div style='background-color: #E8F5E9; padding: 1.5rem; border-radius: 12px;'>
                                <h3 style='color: #2E7D32;'>Alternative Trip</h3>
                                <p><b>Destination:</b> {comparison['alternative']['destination']}</p>
                                <p><b>Budget:</b> €{comparison['alternative']['budget']}</p>
                                <p><b>Estimated Cost:</b> €{comparison['alternative']['total_cost']:.2f}</p>
                                <p><b>Avg Hotel:</b> €{comparison['alternative']['avg_hotel']:.2f}/night</p>
                                <p><b>Activities:</b> {comparison['alternative']['activities']}</p>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    # Comparison insights
                    price_diff = comparison['alternative']['total_cost'] - comparison['current']['total_cost']
                    
                    if price_diff < 0:
                        st.success(f"✅ The alternative destination is €{abs(price_diff):.2f} cheaper!")
                    else:
                        st.info(f"ℹ️ The alternative destination is €{price_diff:.2f} more expensive.")
            else:
                st.warning("Please enter an alternative destination.")
    else:
        st.info("🔍 Generate a trip plan first to compare destinations!")

# TAB 5: Checklist & Packing
with tab5:
    if st.session_state.generated and st.session_state.plan:
        st.markdown("## 📋 Packing List & Pre-Trip Checklist")
        
        plan = st.session_state.plan
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🎒 Packing List")
            
            packing_list = plan.get('packing_list', {})
            
            for category, items in packing_list.items():
                st.markdown(f"#### {category}")
                for item in items:
                    st.checkbox(item, key=f"pack_{category}_{item}")
        
        with col2:
            st.markdown("### ✅ Pre-Trip Checklist")
            
            checklist_items = [
                "Book flights and accommodation",
                "Check passport validity (6 months)",
                "Get travel insurance",
                "Notify bank of travel dates",
                "Download offline maps",
                "Make restaurant reservations",
                "Check visa requirements",
                "Pack medications",
                "Charge all devices",
                "Print important documents",
                "Set up international phone plan",
                "Exchange currency",
                "Arrange airport transportation",
                "Check weather forecast",
                "Create emergency contact list"
            ]
            
            for item in checklist_items:
                st.checkbox(item, key=f"check_{item}")
    else:
        st.info("📋 Generate a trip plan first to see your packing list!")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #666; padding: 2rem 0;'>
        <p><b>🧳 Advanced AI Travel Planner</b></p>
        <p>Powered by AI • Made with ❤️ for travelers</p>
    </div>
""", unsafe_allow_html=True)
