from langgraph.graph import StateGraph, END
from backend.state import TripState
from backend.agents import (
    InputAnalyzerAgent, CitySelectorAgent, DataFetcherAgent, 
    ItineraryAgent, CostAgent
)

class AetherTripGraph:
    def __init__(self):
        self.workflow = StateGraph(TripState)
        self._setup_graph()

    def _setup_graph(self):
        # Initialize Agents
        input_agent = InputAnalyzerAgent()
        city_agent = CitySelectorAgent()
        data_agent = DataFetcherAgent()
        itinerary_agent = ItineraryAgent()
        cost_agent = CostAgent()

        # Add Nodes
        self.workflow.add_node("input_analyzer", lambda state: input_agent.run(state))
        self.workflow.add_node("city_selector", lambda state: city_agent.run(state))
        self.workflow.add_node("data_fetcher", lambda state: data_agent.run(state))
        self.workflow.add_node("itinerary_builder", lambda state: itinerary_agent.run(state))
        self.workflow.add_node("cost_estimator", lambda state: cost_agent.run(state))

        # Define Edges (Sequential)
        self.workflow.set_entry_point("input_analyzer")
        self.workflow.add_edge("input_analyzer", "city_selector")
        self.workflow.add_edge("city_selector", "data_fetcher")
        self.workflow.add_edge("data_fetcher", "itinerary_builder")
        self.workflow.add_edge("itinerary_builder", "cost_estimator")
        self.workflow.add_edge("cost_estimator", END)

    def compile(self):
        return self.workflow.compile()
