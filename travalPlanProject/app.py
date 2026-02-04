import streamlit as st
from agent import TravelPlannerAgent
from memory import init_db, load_memory, save_memory

# Initialize database
init_db()

# Initialize session state
if 'generated' not in st.session_state:
    st.session_state.generated = False
if 'agent' not in st.session_state:
    st.session_state.agent = None
if 'plan' not in st.session_state:
    st.session_state.plan = None

# Load previous memory
memory = load_memory()

# Page configuration
st.set_page_config(
    page_title="AI Travel Planner", 
    page_icon="🧳",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1E88E5;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #424242;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #1E88E5;
        padding-bottom: 0.5rem;
    }
    .budget-box {
        background-color: #E3F2FD;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .tip-box {
        background-color: #FFF9C4;
        padding: 0.8rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #FBC02D;
    }
    .hotel-card {
        background-color: #F5F5F5;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #43A047;
    }
    .transport-card {
        background-color: #E8F5E9;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Main title
st.markdown('<p class="main-header">🧳 AI Travel Planning Agent</p>', unsafe_allow_html=True)

st.markdown("""
    <div style='background-color: #E3F2FD; padding: 1rem; border-radius: 8px; margin-bottom: 2rem;'>
        <p style='margin: 0; color: #1565C0;'>
            ✨ <b>Your AI-powered travel companion!</b> Get personalized itineraries, hotel recommendations, 
            transport options, dining suggestions, and essential travel tips - all tailored to your preferences and budget.
        </p>
    </div>
""", unsafe_allow_html=True)

# Input form
with st.form("travel_form"):
    st.subheader("📋 Trip Details")
    
    col1, col2 = st.columns(2)
    
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
            value=memory.get("days", 5)
        )
        
        budget = st.number_input(
            "💰 Total budget (€)",
            min_value=100,
            max_value=50000,
            value=memory.get("budget", 1000),
            step=100
        )
    
    with col2:
        purpose = st.selectbox(
            "🎯 Travel purpose",
            ["Leisure", "Business", "Adventure", "Cultural", "Romantic", "Family", "Solo"],
            index=["Leisure", "Business", "Adventure", "Cultural", "Romantic", "Family", "Solo"].index(
                memory.get("purpose", "Leisure").capitalize() if memory.get("purpose") else "Leisure"
            )
        )
        
        style = st.selectbox(
            "⚡ Travel style",
            ["Relaxed", "Balanced", "Packed"],
            index=["Relaxed", "Balanced", "Packed"].index(
                memory.get("style", "Relaxed").capitalize() if memory.get("style") else "Relaxed"
            )
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
    
    submit = st.form_submit_button("🚀 Generate Complete Travel Plan", use_container_width=True)

# Generate itinerary
if submit:
    if not destination.strip():
        st.error("⚠️ Please enter a destination!")
    else:
        with st.spinner("🔮 Creating your personalized travel plan... This may take a moment..."):
            # Update memory
            memory = {
                "destination": destination,
                "days": int(days),
                "budget": int(budget),
                "style": style.lower(),
                "purpose": purpose.lower()
            }
            
            # Create agent and generate plan
            agent = TravelPlannerAgent(memory)
            itinerary = agent.create_itinerary()
            
            # Save to session state
            st.session_state.agent = agent
            st.session_state.plan = agent.get_complete_plan()
            st.session_state.generated = True
            
            # Save to database
            save_memory(agent.memory)
        
        st.success("✅ Your complete travel plan is ready!")
        st.balloons()

# Display the complete plan
if st.session_state.generated and st.session_state.plan:
    plan = st.session_state.plan
    agent = st.session_state.agent
    
    st.markdown("---")
    
    # Budget Breakdown Section
    st.markdown('<p class="section-header">💰 Budget Breakdown</p>', unsafe_allow_html=True)
    
    budget_data = plan["budget_breakdown"]
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🏨 Accommodation", f"€{budget_data['accommodation']:.2f}")
        st.caption(f"€{budget_data['hotel_per_night']:.2f} per night")
    
    with col2:
        st.metric("🍽️ Food & Dining", f"€{budget_data['food']:.2f}")
        st.caption(f"€{budget_data['food_per_day']:.2f} per day")
    
    with col3:
        st.metric("🎭 Activities", f"€{budget_data['activities']:.2f}")
        st.caption(f"€{budget_data['activities_per_day']:.2f} per day")
    
    with col4:
        st.metric("🚌 Transport", f"€{budget_data['transport']:.2f}")
        st.caption(f"+ €{budget_data['miscellaneous']:.2f} misc.")
    
    # Hotels Section
    st.markdown('<p class="section-header">🏨 Recommended Hotels</p>', unsafe_allow_html=True)
    
    hotel_cols = st.columns(3)
    for idx, hotel in enumerate(plan["hotels"]):
        with hotel_cols[idx]:
            st.markdown(f"""
                <div class="hotel-card">
                    <h4 style='margin: 0 0 0.5rem 0; color: #2E7D32;'>{hotel['name']}</h4>
                    <p style='margin: 0.2rem 0;'><b>💵 €{hotel['price']:.2f}</b> per night</p>
                    <p style='margin: 0.2rem 0;'>📍 {hotel['area']}</p>
                    <p style='margin: 0.5rem 0 0 0; font-size: 0.9rem; color: #555;'>{hotel['description']}</p>
                </div>
            """, unsafe_allow_html=True)
    
    # Transport Section
    st.markdown('<p class="section-header">🚌 Transportation Options</p>', unsafe_allow_html=True)
    
    transport_cols = st.columns(3)
    for idx, transport in enumerate(plan["transport"]):
        with transport_cols[idx]:
            st.markdown(f"""
                <div class="transport-card">
                    <h4 style='margin: 0 0 0.5rem 0; color: #1B5E20;'>{transport['type']}</h4>
                    <p style='margin: 0.2rem 0;'><b>💵 €{transport['cost']:.2f}</b></p>
                    <p style='margin: 0.5rem 0 0 0; font-size: 0.9rem;'>{transport['description']}</p>
                </div>
            """, unsafe_allow_html=True)
    
    # Restaurants Section
    st.markdown('<p class="section-header">🍽️ Dining Recommendations</p>', unsafe_allow_html=True)
    
    restaurant_cols = st.columns(3)
    for idx, restaurant in enumerate(plan["restaurants"]):
        with restaurant_cols[idx]:
            meal_emoji = {"Breakfast": "🌅", "Lunch": "☀️", "Dinner": "🌙"}
            emoji = meal_emoji.get(restaurant['type'], "🍽️")
            st.markdown(f"""
                <div style='background-color: #FFF3E0; padding: 1rem; border-radius: 8px; margin: 0.5rem 0;'>
                    <h4 style='margin: 0 0 0.5rem 0;'>{emoji} {restaurant['type']}</h4>
                    <p style='margin: 0.2rem 0;'><b>{restaurant['name']}</b></p>
                    <p style='margin: 0.2rem 0;'>💵 ~€{restaurant['price']:.2f}</p>
                    <p style='margin: 0.2rem 0; font-size: 0.9rem; color: #E65100;'>{restaurant['cuisine']}</p>
                </div>
            """, unsafe_allow_html=True)
    
    # Daily Itinerary
    st.markdown('<p class="section-header">📅 Day-by-Day Itinerary</p>', unsafe_allow_html=True)
    
    for day, activities in plan["itinerary"].items():
        with st.expander(f"🗓️ {day} - Estimated Cost: €{activities['estimated_daily_cost']:.2f}", expanded=True):
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("### 🌅 Morning")
                st.markdown(f"**{activities['morning']['activity']}**")
                st.caption(f"⏱️ {activities['morning']['duration']}")
                st.caption(f"💰 €{activities['morning']['cost']:.2f}")
                st.write(activities['morning']['description'])
            
            with col2:
                st.markdown("### ☀️ Afternoon")
                st.markdown(f"**{activities['afternoon']['activity']}**")
                st.caption(f"⏱️ {activities['afternoon']['duration']}")
                st.caption(f"💰 €{activities['afternoon']['cost']:.2f}")
                st.write(activities['afternoon']['description'])
            
            with col3:
                st.markdown("### 🌙 Evening")
                st.markdown(f"**{activities['evening']['activity']}**")
                st.caption(f"⏱️ {activities['evening']['duration']}")
                st.caption(f"💰 €{activities['evening']['cost']:.2f}")
                st.write(activities['evening']['description'])
    
    # Important Tips Section
    st.markdown('<p class="section-header">💡 Important Travel Tips</p>', unsafe_allow_html=True)
    
    for idx, tip in enumerate(plan["tips"], 1):
        st.markdown(f"""
            <div class="tip-box">
                <b>{idx}.</b> {tip}
            </div>
        """, unsafe_allow_html=True)
    
    # Feedback Section
    st.markdown("---")
    st.markdown('<p class="section-header">💬 Refine Your Itinerary</p>', unsafe_allow_html=True)
    
    feedback = st.text_area(
        "Have suggestions or changes?",
        placeholder="e.g., 'Day 2 is too busy' or 'Add more cultural activities to Day 3' or 'Make Day 1 cheaper'",
        height=100
    )
    
    if st.button("🔄 Update Itinerary", use_container_width=True):
        if feedback:
            with st.spinner("Updating your itinerary..."):
                updated_itinerary = agent.refine_itinerary(feedback)
                st.session_state.plan["itinerary"] = updated_itinerary
                save_memory(agent.memory)
            
            st.success("✅ Itinerary updated based on your feedback!")
            st.rerun()
        else:
            st.warning("⚠️ Please enter your feedback first.")

# Sidebar with additional info
with st.sidebar:
    st.markdown("### ℹ️ About")
    st.info("""
        This AI Travel Planner uses advanced language models to create 
        personalized travel itineraries based on your preferences.
        
        **Features:**
        - 🏨 Hotel recommendations
        - 🚌 Transport options
        - 🍽️ Restaurant suggestions
        - 📅 Day-by-day itinerary
        - 💰 Budget breakdown
        - 💡 Travel tips
    """)
    
    st.markdown("### 🎨 Customize")
    st.markdown("""
        **Travel Purposes:**
        - 🏖️ Leisure - Relaxation and fun
        - 💼 Business - Professional travel
        - 🏔️ Adventure - Thrilling experiences
        - 🎭 Cultural - Museums and history
        - 💑 Romantic - Couples getaway
        - 👨‍👩‍👧 Family - Family-friendly
        - 🎒 Solo - Independent travel
        
        **Travel Styles:**
        - 😌 Relaxed - Slow-paced
        - ⚖️ Balanced - Mix of both
        - ⚡ Packed - Action-packed
    """)
    
    if st.button("🗑️ Clear History"):
        st.session_state.generated = False
        st.session_state.agent = None
        st.session_state.plan = None
        st.rerun()
