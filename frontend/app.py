import streamlit as st
import sys
import os
import time
import json
from typing import Dict, List, Any, Optional

# Add project root to path to allow backend imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import Backend Components
# We are importing the graph directly to implement the 'run_aethertrip' logic 
# as a bridge, ensuring the frontend works even if backend/main.py isn't updated yet.
try:
    from backend.state import TripState
    from backend.graph import AetherTripGraph
except ImportError:
    # Fallback for development if backend is not accessible
    TripState = None
    AetherTripGraph = None

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AetherTrip — Travel, Redesigned by Intelligence.",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -----------------------------------------------------------------------------
# CUSTOM CSS (Aether Design System)
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    /* IMPORT FONTS */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* GLOBAL RESET & BACKGROUND */
    .stApp {
        background-color: #000000;
        background-image: 
            radial-gradient(circle at 50% 0%, rgba(10, 20, 40, 1) 0%, rgba(0, 0, 0, 1) 90%),
            radial-gradient(circle at 50% 40%, rgba(0, 114, 255, 0.1) 0%, rgba(0, 0, 0, 0) 60%);
        background-attachment: fixed;
        color: #e0e0e0;
        font-family: 'Inter', sans-serif;
    }
    
    /* HIDE STREAMLIT ELEMENTS */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {
        padding-top: 3rem;
        padding-bottom: 5rem;
    }

    /* TYPOGRAPHY */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff;
        font-weight: 400;
        letter-spacing: -0.5px;
    }

    /* HEADER */
    .header-container {
        text-align: center;
        margin-bottom: 3rem;
    }
    .app-title {
        font-size: 3.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #ffffff 0%, #4facfe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
        letter-spacing: -1px;
    }
    .app-subtitle {
        font-size: 1.1rem;
        color: #8899a6;
        font-weight: 300;
        letter-spacing: 0.5px;
    }

    /* INPUT SECTION */
    .stTextInput > div > div > input {
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 50px !important;
        padding: 15px 30px !important;
        font-size: 1.1rem !important;
        text-align: center !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4) !important;
    }
    .stTextInput > div > div > input:focus {
        background-color: rgba(255, 255, 255, 0.08) !important;
        border-color: #4facfe !important;
        box-shadow: 0 0 25px rgba(79, 172, 254, 0.3) !important;
    }
    .stTextInput > label { display: none; }

    /* BUTTON */
    .stButton {
        text-align: center;
        margin-top: 1rem;
    }
    .stButton > button {
        background: linear-gradient(90deg, #00c6ff 0%, #0072ff 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 50px !important;
        padding: 14px 40px !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
        box-shadow: 0 0 20px rgba(0, 114, 255, 0.4) !important;
        transition: all 0.3s ease !important;
        min-width: 220px !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 0 35px rgba(0, 114, 255, 0.6) !important;
    }

    /* GLASS CARDS */
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 25px;
        height: 100%;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    .glass-card:hover {
        border-color: rgba(79, 172, 254, 0.4);
        box-shadow: 0 0 30px rgba(79, 172, 254, 0.15);
        transform: translateY(-4px);
    }
    .card-label {
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        color: #8899a6;
        margin-bottom: 0.8rem;
        font-weight: 600;
    }
    .card-value {
        font-size: 1.1rem;
        color: #ffffff;
        font-weight: 500;
        line-height: 1.5;
    }
    .highlight-blue {
        color: #4facfe;
    }

    /* TIMELINE */
    .timeline-wrapper {
        position: relative;
        padding-left: 30px;
        margin-top: 40px;
        margin-bottom: 40px;
    }
    .timeline-line {
        position: absolute;
        left: 7px;
        top: 10px;
        bottom: 10px;
        width: 2px;
        background: linear-gradient(to bottom, #4facfe 0%, rgba(79, 172, 254, 0.1) 100%);
    }
    .timeline-item {
        position: relative;
        margin-bottom: 30px;
        padding-left: 25px;
    }
    .timeline-dot {
        position: absolute;
        left: -29px;
        top: 5px;
        width: 14px;
        height: 14px;
        background: #000;
        border: 2px solid #4facfe;
        border-radius: 50%;
        box-shadow: 0 0 10px rgba(79, 172, 254, 0.8);
        z-index: 2;
    }
    .timeline-day {
        font-size: 0.9rem;
        color: #4facfe;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 4px;
    }
    .timeline-title {
        font-size: 1.1rem;
        color: #ffffff;
        font-weight: 600;
        margin-bottom: 4px;
    }
    .timeline-desc {
        font-size: 0.95rem;
        color: #aab8c2;
        line-height: 1.4;
    }

    /* COST GRID */
    .cost-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 15px;
        text-align: center;
    }
    .cost-box {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 10px;
        padding: 15px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .cost-title {
        font-size: 0.75rem;
        color: #8899a6;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 5px;
    }
    .cost-number {
        font-size: 1.3rem;
        color: #ffffff;
        font-weight: 700;
    }
    .cost-total {
        color: #4facfe;
        text-shadow: 0 0 15px rgba(79, 172, 254, 0.4);
    }

    /* LOADING */
    .loading-wrapper {
        text-align: center;
        margin-top: 2rem;
        color: #4facfe;
        font-size: 1.1rem;
        letter-spacing: 1px;
    }
    @keyframes blink {
        0% { opacity: 0.2; }
        20% { opacity: 1; }
        100% { opacity: 0.2; }
    }
    .loading-dots span {
        animation: blink 1.4s infinite both;
        font-size: 2rem;
        margin: 0 2px;
    }
    .loading-dots span:nth-child(2) { animation-delay: 0.2s; }
    .loading-dots span:nth-child(3) { animation-delay: 0.4s; }

</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# BACKEND INTERFACE
# -----------------------------------------------------------------------------
def run_aethertrip(user_input: str) -> dict:
    """
    Executes the backend LangGraph workflow and formats the result.
    """
    if not AetherTripGraph or not TripState:
        # Mock response if backend is missing (for dev safety)
        time.sleep(2)
        return {
            "selected_cities": ["Tokyo", "Kyoto"],
            "weather_data": {"summary": "Sunny with mild breeze", "temp": "18°C"},
            "flight_data": {"summary": "JL123 (Direct)", "price": 1200},
            "hotel_data": {"summary": "Aman Tokyo, Ritz-Carlton", "price": 2500},
            "itinerary": [
                {"day": 1, "title": "Arrival in Tokyo", "description": "Check-in at Aman Tokyo. Evening stroll in Ginza."},
                {"day": 2, "title": "Tokyo Culture", "description": "Visit Senso-ji Temple and Shibuya Crossing."},
                {"day": 3, "title": "Bullet Train to Kyoto", "description": "Experience the Shinkansen. Check-in at Ritz-Carlton Kyoto."}
            ],
            "cost_estimate": {"flights": 1200, "hotels": 2500, "total": 3700},
            "errors": []
        }

    # Real Execution
    initial_state = TripState(user_input=user_input)
    graph = AetherTripGraph().compile()
    final_state = graph.invoke(initial_state)

    # Map State to Frontend Dict
    # Note: We use safe gets and defaults to ensure UI doesn't break
    
    # Helper to extract summary string from complex dicts if needed
    def extract_summary(data):
        if not data: return "No data available"
        if isinstance(data, str): return data
        # If it's a dict, try to find a summary-like key or join values
        return str(list(data.values())[0]) if data else "No data"

    return {
        "selected_cities": final_state.get("selected_cities") or [],
        "weather_data": final_state.get("weather_data") or {},
        "flight_data": final_state.get("flight_data") or {},
        "hotel_data": final_state.get("hotel_data") or {},
        "itinerary": _parse_itinerary(final_state.get("itinerary", {})),
        "cost_estimate": final_state.get("cost_estimate") or {"total": 0, "flights": 0, "hotels": 0},
        "errors": final_state.get("errors", [])
    }

def _parse_itinerary(itinerary_data: Any) -> List[Dict]:
    """Helper to ensure itinerary is a list of dicts."""
    if isinstance(itinerary_data, list):
        return itinerary_data
    
    if isinstance(itinerary_data, dict) and "plan" in itinerary_data:
        plan_content = itinerary_data["plan"]
        
        # If the plan is ALREADY a list (structured JSON from LLM/Mock), return it directly
        if isinstance(plan_content, list):
            return plan_content
            
        # If it's a string (raw text fallback), parse it manually
        if isinstance(plan_content, str):
            return [
                {"day": i+1, "title": f"Day {i+1}", "description": line.strip()} 
                for i, line in enumerate(plan_content.split('\n')) if line.strip()
            ]
            
    return []

# -----------------------------------------------------------------------------
# UI COMPONENTS
# -----------------------------------------------------------------------------

def render_header():
    st.markdown("""
        <div class="header-container">
            <div class="app-title">AetherTrip</div>
            <div class="app-subtitle">Travel, Redesigned by Intelligence.</div>
        </div>
    """, unsafe_allow_html=True)

def render_input_section():
    # Centered layout for input
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        user_input = st.text_input("", placeholder="Where to next, traveler?", key="user_input_field")
        
        # Button centered below
        b_col1, b_col2, b_col3 = st.columns([1, 1, 1])
        with b_col2:
            generate_clicked = st.button("Generate Trip Plan")
            
    return user_input, generate_clicked

def render_loading_state(status_text="Thinking..."):
    st.markdown(f"""
        <div class="loading-wrapper">
            <div class="loading-dots"><span>•</span><span>•</span><span>•</span></div>
            <div style="margin-top: 10px; color: #8899a6; font-size: 0.9rem;">{status_text}</div>
        </div>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# MAIN APP LOGIC
# -----------------------------------------------------------------------------

def render_result_cards(result: dict):
    # Prepare Data
    cities = ", ".join(result.get("selected_cities", [])) or "Unknown Destination"
    
    w_data = result.get("weather_data", {})
    # Handle both mock dict and real dict structures safely
    weather_text = "Sunny, 22°C" # Default fallback
    if isinstance(w_data, dict) and w_data:
        # Try to grab first value if it's a dict of cities
        first_val = list(w_data.values())[0]
        if isinstance(first_val, dict):
            weather_text = f"{first_val.get('condition', 'Clear')}, {first_val.get('temp', '--')}°C"
        else:
            weather_text = str(first_val)

    f_data = result.get("flight_data", {})
    flight_text = "Standard Route"
    if isinstance(f_data, dict) and f_data:
        first_val = list(f_data.values())[0]
        if isinstance(first_val, list) and first_val:
            flight_text = f"{first_val[0].get('airline', 'Airline')} (Direct)"
        elif isinstance(first_val, str):
            flight_text = first_val

    h_data = result.get("hotel_data", {})
    hotel_text = "Best Available"
    if isinstance(h_data, dict) and h_data:
        first_val = list(h_data.values())[0]
        if isinstance(first_val, list) and first_val:
            hotel_text = ", ".join([h.get('name', 'Hotel') for h in first_val[:2]])
        elif isinstance(first_val, str):
            hotel_text = first_val

    # Render 2x2 Grid
    st.markdown("<br>", unsafe_allow_html=True)
    col_spacer_l, col_grid, col_spacer_r = st.columns([1, 4, 1])
    
    with col_grid:
        r1_c1, r1_c2 = st.columns(2)
        with r1_c1:
            st.markdown(f"""
            <div class="glass-card">
                <div class="card-label">Selected Cities</div>
                <div class="card-value">{cities}</div>
            </div>
            """, unsafe_allow_html=True)
        with r1_c2:
            st.markdown(f"""
            <div class="glass-card">
                <div class="card-label">Weather Summary</div>
                <div class="card-value">{weather_text}</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
        
        r2_c1, r2_c2 = st.columns(2)
        with r2_c1:
            st.markdown(f"""
            <div class="glass-card">
                <div class="card-label">Flight Details</div>
                <div class="card-value">{flight_text}</div>
            </div>
            """, unsafe_allow_html=True)
        with r2_c2:
            st.markdown(f"""
            <div class="glass-card">
                <div class="card-label">Hotel & Stay</div>
                <div class="card-value">{hotel_text}</div>
            </div>
            """, unsafe_allow_html=True)

def render_itinerary_timeline(itinerary: List[Dict]):
    if not itinerary:
        return

    # Start wrapper
    timeline_html = '<div class="timeline-wrapper"><div class="timeline-line"></div>'
    
    for item in itinerary:
        day = item.get("day", "?")
        title = item.get("title", "Activity")
        desc = item.get("description", "")
        
        # IMPORTANT: No indentation in the HTML string to avoid Markdown code block detection
        timeline_html += f"""
<div class="timeline-item">
<div class="timeline-dot"></div>
<div class="timeline-day">Day {day}</div>
<div class="timeline-title">{title}</div>
<div class="timeline-desc">{desc}</div>
</div>"""
    
    timeline_html += '</div>'
    
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        st.markdown(timeline_html, unsafe_allow_html=True)

def render_cost_summary(cost: dict):
    flights = cost.get("flights", 0)
    hotels = cost.get("hotels", 0)
    total = cost.get("total", 0)
    
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        st.markdown(f"""
        <div class="glass-card" style="margin-top: 20px;">
            <div class="cost-grid">
                <div class="cost-box">
                    <div class="cost-title">Flights</div>
                    <div class="cost-number">${flights}</div>
                </div>
                <div class="cost-box">
                    <div class="cost-title">Hotels</div>
                    <div class="cost-number">${hotels}</div>
                </div>
                <div class="cost-box" style="border-color: rgba(79, 172, 254, 0.3);">
                    <div class="cost-title">Total</div>
                    <div class="cost-number cost-total">${total}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def main():
    # Session State Initialization
    if "result" not in st.session_state:
        st.session_state.result = None
    if "is_loading" not in st.session_state:
        st.session_state.is_loading = False
    if "error" not in st.session_state:
        st.session_state.error = None

    # Render Top Section
    render_header()
    user_input, generate_clicked = render_input_section()

    # Interaction Logic
    if generate_clicked:
        if not user_input.strip():
            st.error("Please enter a destination to proceed.")
        else:
            st.session_state.is_loading = True
            st.session_state.error = None
            st.session_state.result = None
            
            # Create a placeholder for the loading state
            loading_placeholder = st.empty()
            
            # Agent Status Messages
            agent_msgs = [
                "Understanding your journey...",
                "Scanning 200+ cities for the best matches...",
                "Probing live weather systems...",
                "Mapping optimal flight paths...",
                "Sifting through stays and hotels...",
                "Hunting for must-see attractions...",
                "Weaving a day-by-day itinerary...",
                "Balancing costs and optimizing your budget..."
            ]
            
            # Simulate Agent Steps
            # In a real async setup, we'd hook into callbacks. 
            # Here we simulate the "work" time for the visual effect.
            try:
                # Cycle through messages
                for i, msg in enumerate(agent_msgs):
                    with loading_placeholder.container():
                        render_loading_state(f"[Agent {i+1}] {msg}")
                    time.sleep(0.8) # Simulate work time per agent
                
                # Execute Backend
                result = run_aethertrip(user_input)
                st.session_state.result = result
                
            except Exception as e:
                st.session_state.error = str(e)
            finally:
                st.session_state.is_loading = False
                loading_placeholder.empty() # Clear loading
                st.rerun()

    # Display Error
    if st.session_state.error:
        st.markdown("<br>", unsafe_allow_html=True)
        st.error(f"An error occurred: {st.session_state.error}")

    # Display Result
    if st.session_state.result:
        render_result_cards(st.session_state.result)
        render_itinerary_timeline(st.session_state.result.get("itinerary", []))
        render_cost_summary(st.session_state.result.get("cost_estimate", {}))

if __name__ == "__main__":
    main()
