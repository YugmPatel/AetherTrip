# 🌌 AetherTrip

**Travel, Redesigned by Intelligence.**

AetherTrip is an AI-powered trip planning application that leverages multi-agent systems to create personalized travel itineraries. Using LangGraph and advanced AI agents, it intelligently researches destinations, finds optimal flights and accommodations, checks weather conditions, and crafts detailed day-by-day travel plans.

## ✨ Features

- **🤖 Multi-Agent Architecture**: Specialized AI agents for different aspects of trip planning
- **🌍 Smart City Selection**: Intelligent destination matching based on your preferences
- **✈️ Flight Integration**: Real-time flight search and optimization
- **🏨 Hotel Recommendations**: Curated accommodation suggestions
- **🌤️ Weather Intelligence**: Live weather data integration for better planning
- **📅 Dynamic Itineraries**: Day-by-day personalized travel plans
- **💰 Cost Estimation**: Transparent budget breakdown and optimization
- **🎨 Beautiful UI**: Modern Streamlit interface with glassmorphism design

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Google API Key (for various services)

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/YugmPatel/AetherTrip.git
   cd AetherTrip
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**

   ```bash
   # Create a .env file in the root directory
   echo 'GOOGLE_API_KEY="your_google_api_key_here"' > .env
   ```

4. **Run the application**

   **Option A: Streamlit Web Interface (Recommended)**

   ```bash
   streamlit run frontend/app.py
   ```

   **Option B: Command Line Interface**

   ```bash
   python backend/main.py
   ```

## 🏗️ Architecture

AetherTrip uses a sophisticated multi-agent architecture built with LangGraph:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   City Agent    │    │  Weather Agent  │    │  Flight Agent   │
│                 │    │                 │    │                 │
│ • Destination   │    │ • Live Weather  │    │ • Flight Search │
│   Research      │    │ • Forecasting   │    │ • Price Comp.   │
│ • Matching      │    │ • Conditions    │    │ • Optimization  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │ Orchestrator    │
                    │                 │
                    │ • State Mgmt    │
                    │ • Flow Control  │
                    │ • Integration   │
                    └─────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Hotel Agent   │    │Itinerary Agent  │    │   Cost Agent    │
│                 │    │                 │    │                 │
│ • Accommodation │    │ • Day Planning  │    │ • Budget Calc   │
│ • Reviews       │    │ • Activities    │    │ • Optimization  │
│ • Booking       │    │ • Scheduling    │    │ • Breakdown     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Key Components

- **`backend/graph.py`**: LangGraph workflow orchestration
- **`backend/agents.py`**: Individual AI agent implementations
- **`backend/state.py`**: Shared state management
- **`backend/apis.py`**: External API integrations
- **`frontend/app.py`**: Streamlit web interface
- **`backend/cache.py`**: Intelligent caching system

## 📁 Project Structure

```
AetherTrip/
├── backend/
│   ├── __init__.py
│   ├── main.py          # CLI entry point
│   ├── graph.py         # LangGraph workflow
│   ├── agents.py        # AI agent implementations
│   ├── state.py         # State management
│   ├── apis.py          # API wrappers
│   ├── cache.py         # Caching system
│   └── utils.py         # Utility functions
├── frontend/
│   └── app.py           # Streamlit web app
├── database/
│   ├── cities.json      # City database
│   ├── cache.json       # API cache
│   └── schema.md        # Data schemas
├── docs/
│   ├── setup_guide.md   # Detailed setup
│   ├── architecture.md  # Technical docs
│   ├── api_usage.md     # API documentation
│   └── roadmap.md       # Future plans
├── tests/
│   ├── test_agents.py
│   ├── test_graph.py
│   ├── test_api_wrappers.py
│   └── test_end_to_end.py
├── requirements.txt
├── .env                 # Environment variables (create this)
├── .gitignore
└── README.md
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Required
GOOGLE_API_KEY="your_google_api_key_here"

# Optional (for enhanced features)
OPENAI_API_KEY="your_openai_key"
ANTHROPIC_API_KEY="your_anthropic_key"
```

### API Keys Setup

1. **Google API Key**: Required for Maps, Places, and other Google services
   - Visit [Google Cloud Console](https://console.cloud.google.com/)
   - Enable required APIs (Maps, Places, etc.)
   - Create credentials and copy the API key

2. **Additional APIs**: Check `docs/api_usage.md` for detailed API setup instructions

## 🎯 Usage Examples

### Web Interface

1. Start the Streamlit app: `streamlit run frontend/app.py`
2. Enter your trip request: "Plan a 5-day trip to Japan in spring"
3. Watch the AI agents work their magic
4. Review your personalized itinerary and cost breakdown

### Command Line

```bash
python backend/main.py
# Enter: "Plan a romantic weekend in Paris"
```

### Programmatic Usage

```python
from backend.state import TripState
from backend.graph import AetherTripGraph

# Initialize
state = TripState(user_input="Plan a 3-day adventure in Iceland")
graph = AetherTripGraph().compile()

# Execute
result = graph.invoke(state)
print(result['itinerary']['plan'])
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
python -m pytest tests/

# Run specific test categories
python -m pytest tests/test_agents.py -v
python -m pytest tests/test_graph.py -v
```

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📚 Documentation

- **[Setup Guide](docs/setup_guide.md)**: Detailed installation and configuration
- **[Architecture](docs/architecture.md)**: Technical deep-dive
- **[API Usage](docs/api_usage.md)**: API integration details
- **[Roadmap](docs/roadmap.md)**: Future development plans

## 🛣️ Roadmap

- [ ] **Multi-language Support**: Expand to support multiple languages
- [ ] **Real-time Booking**: Direct integration with booking platforms
- [ ] **Social Features**: Trip sharing and collaboration
- [ ] **Mobile App**: Native mobile applications
- [ ] **Advanced AI**: Enhanced personalization and learning
- [ ] **Offline Mode**: Cached operation capabilities

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **LangGraph**: For the powerful agent orchestration framework
- **Streamlit**: For the beautiful and intuitive web interface
- **Google APIs**: For comprehensive travel data services
- **OpenAI/Anthropic**: For advanced language model capabilities

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/YugmPatel/AetherTrip/issues)
- **Discussions**: [GitHub Discussions](https://github.com/YugmPatel/AetherTrip/discussions)
- **Email**: [Contact](mailto:your-email@example.com)

---

**Made with ❤️ by [Yugm Patel](https://github.com/YugmPatel)**

_AetherTrip - Where AI meets wanderlust_ ✈️🌍
