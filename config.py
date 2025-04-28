"""
Configuration settings for the Financial Risk Knowledge Graph system.
"""
import os
from datetime import datetime

# Date range for financial news collection
START_DATE = datetime(2025, 3, 9)
END_DATE = datetime(2025, 4, 4)

# News sources configuration
NEWS_SOURCES = [
    {
        "name": "Yahoo Finance",
        "rss_url": "https://finance.yahoo.com/rss/",
        "type": "rss"
    },
    {
        "name": "MarketWatch",
        "rss_url": "http://feeds.marketwatch.com/marketwatch/topstories/",
        "type": "rss"
    },
    {
        "name": "SEC Edgar",
        "api_url": "https://www.sec.gov/cgi-bin/browse-edgar",
        "type": "api"
    },
    {
        "name": "FRED Economic Data",
        "api_url": "https://api.stlouisfed.org/fred/",
        # "api_key": os.environ.get("FRED_API_KEY", ""),
        "api_key": "6fc4628d4e90fc37a8107e076671f2ce",
        "type": "api"
    },
    {
        "name": "Alpha Vantage",
        "api_url": "https://www.alphavantage.co/query",
        # "api_key": os.environ.get("ALPHA_VANTAGE_API_KEY", ""),
        "api_key": "BK4R2YPMA1FRDLVS",
        "type": "api"
    }
]

# Entity types to extract
ENTITY_TYPES = [
    "ORGANIZATION", "PERSON", "GPE", "DATE", "MONEY", 
    "PERCENT", "PRODUCT", "EVENT", "LAW", "FACILITY"
]

# Financial-specific entity types
FINANCIAL_ENTITY_TYPES = [
    "COMPANY", "STOCK", "BOND", "CURRENCY", "COMMODITY", 
    "INDEX", "REGULATOR", "SECTOR", "PRODUCT", "SERVICE"
]

# Risk event categories based on the FEEKG model
RISK_EVENT_CATEGORIES = [
    "Market Risk Event",
    "Credit Risk Event",
    "Liquidity Risk Event",
    "Operational Risk Event",
    "Legal Risk Event",
    "Strategic Risk Event",
    "Reputation Risk Event",
    "Regulatory Risk Event"
]

# Database storage configuration
DB_CONFIG = {
    "type": "json",  # Using JSON file storage as specified
    "entity_file": "data/entities.json",
    "event_file": "data/events.json",
    "risk_file": "data/risks.json",
    "news_file": "data/news.json",
    "graph_file": "data/knowledge_graph.json"
}

# NLP processing settings
NLP_CONFIG = {
    "spacy_model": "en_core_web_sm",  # Using smaller model for faster loading
    "min_entity_freq": 2,
    "min_relation_conf": 0.6
}

# Graph analysis parameters
GRAPH_CONFIG = {
    "centrality_methods": ["degree", "betweenness", "closeness", "eigenvector"],
    "community_detection": ["louvain", "label_propagation"],
    "risk_propagation_threshold": 0.3,
    "max_path_length": 4
}

# Flask application settings
FLASK_CONFIG = {
    "debug": True,
    "host": "0.0.0.0",
    "port": 5000
}
