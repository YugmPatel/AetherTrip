import sys
import os

# Ensure the project root is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.state import TripState
from backend.graph import AetherTripGraph
from backend.utils import setup_logger

logger = setup_logger("Main")

def main():
    print("Welcome to AetherTrip - Agentic Trip Planner")
    user_request = input("Enter your trip details (e.g., 'Plan a trip to Tokyo for 5 days'): ")
    
    if not user_request:
        print("No input provided. Exiting.")
        return

    # Initialize State
    initial_state = TripState(user_input=user_request)
    
    # Build Graph
    graph = AetherTripGraph().compile()
    
    print("\nProcessing your request... Please wait.")
    try:
        # Execute Graph
        final_state = graph.invoke(initial_state)
        
        print("\n--- Trip Plan ---")
        if final_state.get('itinerary'):
            print(final_state['itinerary'].get('plan', 'No plan generated.'))
        
        print("\n--- Cost Estimate ---")
        if final_state.get('cost_estimate'):
            print(final_state['cost_estimate'])
            
        if final_state.get('errors'):
            print("\nWarnings/Errors encountered:")
            for err in final_state['errors']:
                print(f"- {err}")
                
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
