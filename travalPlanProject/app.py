import streamlit as st
from agent import TravelPlannerAgent
from memory import init_db, load_memory, save_memory
init_db()
memory = load_memory()
st.set_page_config(page_title="AI Travel Planner", page_icon="🧳")
st.title("🧳 AI Travel Planning Agent")
with st.form("travel_form"):
    destination = st.text_input("Destination",
        memory.get("destination", "Amsterdam")
    )
    days = st.number_input("Number of days",
        min_value=1, value=memory.get("days", 3)
    )
    budget = st.number_input("Total budget (€)",
        min_value=100,value=memory.get("budget", 500)
    )
    style = st.selectbox("Travel style",["relaxed", "packed"],
        index=0 if memory.get("style", "relaxed") == "relaxed" else 1
    )
    submit = st.form_submit_button("Generate Itinerary")
if submit:
    memory = {
        "destination": destination,
        "days": days,
        "budget": budget,
        "style": style
    }
    agent = TravelPlannerAgent(memory)
    itinerary = agent.create_itinerary()
    save_memory(agent.memory)
    st.success("Itinerary generated")
    for day, plan in itinerary.items():
        with st.expander(day):
            for k, v in plan.items():
                st.write(f"**{k}:** {v}")
    feedback = st.text_input("Feedback (e.g., 'Day 2 is too busy')")
    if feedback:
        updated = agent.refine_itinerary(feedback)
        save_memory(agent.memory)
        st.info("Itinerary updated")
        for day, plan in updated.items():
            with st.expander(day):
                for k, v in plan.items():
                    st.write(f"**{k}:** {v}")
