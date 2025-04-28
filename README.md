# Financial Risk Evolution Knowledge Graph (FEEKG)

## Overview

The Financial Risk Evolution Knowledge Graph (FEEKG) is an advanced analytical system that transforms financial news, economic data, and market information into a dynamic knowledge graph for risk analysis. The system implements a three-layer architecture (entity-event-risk) to help enterprises and financial institutions identify key risk sources and clarify risk event transmission paths through event association.

![Knowledge Graph Architecture](static/img/kg_architecture.png)

## Features

- **Multi-source Data Collection**: Gather financial news and economic data from various sources
- **Intelligent Entity Extraction**: Identify financial institutions, instruments, people, and markets using NLP
- **Event Modeling**: Detect and categorize financial events from news content
- **Risk Identification & Analysis**: Recognize potential financial risks and their impact
- **Knowledge Graph Construction**: Build a comprehensive graph linking entities, events, and risks
- **Interactive Visualization**: Explore the financial ecosystem through an intuitive graph interface
- **Risk Transmission Paths**: Analyze how risks propagate through the financial system

## Technology Stack

- **Backend**: Python, Flask
- **NLP**: spaCy, en_core_web_sm
- **Graph Processing**: NetworkX, python-louvain
- **Data Collection**: Feedparser, Requests, Trafilatura
- **Visualization**: D3.js, Bootstrap
- **Data Storage**: Lightweight JSON-based persistence

## Installation

### Prerequisites

- Python 3.8+
- pip (Python package manager)

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/financial-risk-kg.git
   cd financial-risk-kg
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Install spaCy language model:
   ```
   python -m spacy download en_core_web_sm
   ```

4. Create necessary directories:
   ```
   mkdir -p data
   mkdir -p logs
   ```

## Configuration

Edit `config.py` to configure:

- Data sources and API keys
- File paths for data storage
- Analysis parameters

### API Keys (Optional)

For enhanced functionality, obtain and configure API keys for:
- FRED (Federal Reserve Economic Data)
- Alpha Vantage (Market data)
- NewsAPI (Financial news)

## Usage

### Running the Application

Start the Flask application:
```
python main.py
```

Or using Flask:
```
export FLASK_APP=main.py
flask run --host=0.0.0.0 --port=5000
```

The application will be available at `http://localhost:5000`

### Data Pipeline

The system processes data through several stages:

1. **Collect News**: Gather financial news and economic data
   - Endpoint: `/api/collect-news`

2. **Extract Entities**: Identify financial entities
   - Endpoint: `/api/process-entities`

3. **Model Events**: Detect financial events from entity relationships
   - Endpoint: `/api/model-events`

4. **Analyze Risks**: Identify potential risks based on events
   - Endpoint: `/api/analyze-risks`

5. **Build Graph**: Construct the knowledge graph
   - Endpoint: `/api/build-graph`

6. **Query the Graph**: Explore and analyze the financial ecosystem
   - Various query endpoints available

### Web Interface

- **Dashboard**: `/` - Overview statistics and system status
- **Knowledge Graph**: `/graph` - Interactive visualization of the financial network
- **Risk Analysis**: `/risk-analysis` - Risk assessment and transmission paths
- **News Collection**: `/news` - Data sources and collection interface
- **Ontology View**: `/ontology` - Financial and risk ontologies

## System Architecture

The FEEKG implements a three-layer knowledge graph architecture:

1. **Entity Layer**: Financial actors, instruments, and markets
2. **Event Layer**: Economic events, transactions, and policy changes
3. **Risk Layer**: Financial risks identified from events

### Component Overview

- `news_collector.py`: Gathers financial news and economic data
- `entity_extractor.py`: Identifies financial entities through NLP
- `event_modeler.py`: Recognizes financial events from entity relationships
- `risk_analyzer.py`: Identifies and categorizes potential risks
- `graph_builder.py`: Constructs the three-layer knowledge graph
- `data_store.py`: Handles data persistence and retrieval

## Analysis Methodology

The system employs a hybrid approach based on the FIBO+SEM+ABC methodology for risk ontology and analysis:

- **Financial Industry Business Ontology (FIBO)**: Standard financial entity classification
- **Semantic Event Modeling (SEM)**: Event representation and linking
- **Activity-Based Costing (ABC)**: Risk impact assessment

## Limitations and Future Work

Current limitations:
- Limited to news from March 9-April 4, 2025 in the initial prototype
- Relies on publicly available financial information
- Simplified risk transmission modeling

Future enhancements:
- Enhanced NLP for specialized financial entity extraction
- More sophisticated event reasoning capabilities
- Dynamic risk propagation simulation
- PDF document processing for regulatory filings and reports
- Integration with additional financial data sources

## License

[Specify your license here]

## Contributors

[List of contributors]

## Acknowledgments

This project implements concepts from academic research on financial risk knowledge graphs and event-driven risk analysis.