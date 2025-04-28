"""
Main Flask application for the Financial Risk Knowledge Graph system.
"""
import os
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime
import json

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "financial-risk-kg-secret")

# Import utility modules
from utils.news_collector import NewsCollector
from utils.entity_extractor import EntityExtractor
from utils.event_modeler import EventModeler
from utils.risk_analyzer import RiskAnalyzer
from utils.graph_builder import GraphBuilder
from utils.data_store import DataStore
from config import START_DATE, END_DATE, NEWS_SOURCES, DB_CONFIG

# Initialize components
data_store = DataStore(
    entity_file=DB_CONFIG["entity_file"],
    event_file=DB_CONFIG["event_file"],
    risk_file=DB_CONFIG["risk_file"],
    news_file=DB_CONFIG["news_file"],
    graph_file=DB_CONFIG["graph_file"]
)

news_collector = NewsCollector(data_store)
entity_extractor = EntityExtractor(data_store)
event_modeler = EventModeler(data_store)
risk_analyzer = RiskAnalyzer(data_store)
graph_builder = GraphBuilder(data_store)

# Ensure data directories exist
os.makedirs(os.path.dirname(DB_CONFIG["entity_file"]), exist_ok=True)


# Routes
@app.route('/')
def index():
    """Render the dashboard homepage."""
    try:
        # Get summary statistics for the dashboard
        stats = {
            'news_count': len(data_store.get_all_news()),
            'entity_count': len(data_store.get_all_entities()),
            'event_count': len(data_store.get_all_events()),
            'risk_count': len(data_store.get_all_risks()),
            'date_range': f"{START_DATE.strftime('%b %d, %Y')} - {END_DATE.strftime('%b %d, %Y')}"
        }
        
        # Get top entities and events for display
        top_entities = data_store.get_top_entities(10)
        recent_events = data_store.get_recent_events(5)
        top_risks = data_store.get_top_risks(5)
        
        return render_template('index.html', 
                            stats=stats, 
                            top_entities=top_entities,
                            recent_events=recent_events,
                            top_risks=top_risks)
    except Exception as e:
        logger.error(f"Error in index page: {e}")
        import traceback
        traceback.print_exc()
        
        # Return with empty data
        empty_stats = {
            'news_count': 0,
            'entity_count': 0,
            'event_count': 0,
            'risk_count': 0,
            'date_range': f"{START_DATE.strftime('%b %d, %Y')} - {END_DATE.strftime('%b %d, %Y')}"
        }
        return render_template('index.html', 
                            stats=empty_stats, 
                            top_entities=[],
                            recent_events=[],
                            top_risks=[])


@app.route('/graph')
def graph():
    """Render the knowledge graph visualization page."""
    try:
        # The graph data is fetched via an API call directly from the client
        # to allow visualization controls to work in the frontend
        return render_template('graph.html')
    except Exception as e:
        logger.error(f"Error rendering graph page: {e}")
        import traceback
        traceback.print_exc()
        return render_template('error.html', error=str(e)), 500


@app.route('/news')
def news():
    """Render the news collection and analysis page."""
    try:
        news_items = data_store.get_all_news()
        return render_template('news.html', news_items=news_items)
    except Exception as e:
        logger.error(f"Error in news page: {e}")
        import traceback
        traceback.print_exc()
        # Return with empty data
        return render_template('news.html', news_items=[])


@app.route('/risk-analysis')
def risk_analysis():
    """Render the risk analysis page."""
    try:
        risks = data_store.get_all_risks()
        risk_paths = risk_analyzer.find_risk_transmission_paths()
        risk_metrics = risk_analyzer.calculate_risk_metrics()
        
        return render_template('risk_analysis.html', 
                              risks=risks,
                              risk_paths=risk_paths,
                              risk_metrics=risk_metrics)
    except Exception as e:
        logger.error(f"Error in risk analysis page: {e}")
        import traceback
        traceback.print_exc()
        # Return with empty data
        return render_template('risk_analysis.html', 
                              risks=[],
                              risk_paths=[],
                              risk_metrics={"total_risks": 0, "risk_categories": [], "severity_distribution": [], "entity_risk_exposure": []})


@app.route('/ontology')
def ontology():
    """Render the ontology viewing page."""
    try:
        # Load ontology data from files
        with open('ontology/financial_ontology.json', 'r') as f:
            financial_ontology_data = json.load(f)
        
        with open('ontology/risk_ontology.json', 'r') as f:
            risk_ontology_data = json.load(f)
            
        # Prepare the entity types for the template
        entity_types = []
        for cls in financial_ontology_data.get('classes', []):
            if cls.get('id') == 'FinancialEntity':
                for subclass in cls.get('subclasses', []):
                    entity_types.append({
                        'name': subclass.get('label', ''),
                        'definition': subclass.get('description', ''),
                        'examples': [sc.get('label', '') for sc in subclass.get('subclasses', [])[:3]]
                    })
        
        # Prepare relationships for the template
        relationships = []
        for rel in financial_ontology_data.get('relationships', []):
            relationships.append({
                'name': rel.get('label', ''),
                'definition': rel.get('description', ''),
                'domain': rel.get('domain', ''),
                'range': rel.get('range', '')
            })
            
        # Prepare risk types for the template
        risk_types = []
        if 'categories' in risk_ontology_data:
            for risk_cat in risk_ontology_data.get('categories', []):
                risk_types.append({
                    'name': risk_cat.get('label', ''),
                    'definition': risk_cat.get('description', ''),
                    'impact_areas': risk_cat.get('impacts', ['Financial', 'Operational', 'Reputational'])
                })
        
        # Prepare propagation rules for the template
        propagation_rules = []
        if 'propagation_rules' in risk_ontology_data:
            for rule in risk_ontology_data.get('propagation_rules', []):
                propagation_rules.append({
                    'source': rule.get('source', ''),
                    'target': rule.get('target', ''),
                    'mechanism': rule.get('mechanism', ''),
                    'conditions': rule.get('conditions', ['High correlation', 'Direct exposure'])
                })
        
        # Create the structured data expected by the template
        financial_ontology = {
            'entity_types': entity_types,
            'relationships': relationships
        }
        
        risk_ontology = {
            'risk_types': risk_types or [
                {'name': 'Market Risk', 'definition': 'Risk of losses due to market movements', 'impact_areas': ['Asset Values', 'Trading Positions', 'Investment Returns']},
                {'name': 'Credit Risk', 'definition': 'Risk of default by borrowers or counterparties', 'impact_areas': ['Loan Portfolios', 'Counterparty Exposure', 'Bond Holdings']},
                {'name': 'Liquidity Risk', 'definition': 'Risk of insufficient liquid assets to meet obligations', 'impact_areas': ['Cash Flow', 'Funding Sources', 'Asset Liquidity']},
                {'name': 'Operational Risk', 'definition': 'Risk from inadequate processes, systems, or external events', 'impact_areas': ['Process Failures', 'System Outages', 'External Disruptions']}
            ],
            'propagation_rules': propagation_rules or [
                {'source': 'Market Risk', 'target': 'Liquidity Risk', 'mechanism': 'Asset devaluation leading to liquidity strain', 'conditions': ['Severe market decline', 'High leverage']},
                {'source': 'Credit Risk', 'target': 'Market Risk', 'mechanism': 'Default concerns triggering market selloff', 'conditions': ['Systemic importance', 'Contagion effects']},
                {'source': 'Operational Risk', 'target': 'Reputational Risk', 'mechanism': 'Operational failures damaging brand image', 'conditions': ['Public visibility', 'Customer impact']}
            ]
        }
            
        return render_template('ontology.html', 
                              financial_ontology=financial_ontology,
                              risk_ontology=risk_ontology)
    except Exception as e:
        logger.error(f"Error rendering ontology page: {e}")
        import traceback
        traceback.print_exc()
        return render_template('error.html', error=str(e)), 500


# API endpoints for data retrieval and processing
@app.route('/api/collect-news', methods=['POST'])
def api_collect_news():
    """API endpoint to trigger news collection."""
    try:
        source = request.json.get('source', 'all')
        start_date_str = request.json.get('start_date')
        end_date_str = request.json.get('end_date')
        
        # Parse dates if provided, otherwise use configured defaults
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else START_DATE
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else END_DATE
        
        # Collect news
        if source == 'all':
            for news_source in NEWS_SOURCES:
                news_collector.collect_from_source(news_source, start_date, end_date)
        else:
            # Find the specific source
            source_config = next((s for s in NEWS_SOURCES if s['name'] == source), None)
            if source_config:
                news_collector.collect_from_source(source_config, start_date, end_date)
        
        return jsonify({"status": "success", "message": f"Collected news from {source}"})
    except Exception as e:
        logger.error(f"Error collecting news: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/process-entities', methods=['POST'])
def api_process_entities():
    """API endpoint to extract entities from collected news."""
    try:
        entity_extractor.extract_all_entities()
        return jsonify({"status": "success", "message": "Extracted entities from news"})
    except Exception as e:
        logger.error(f"Error extracting entities: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/model-events', methods=['POST'])
def api_model_events():
    """API endpoint to model events from entities and news."""
    try:
        event_modeler.model_all_events()
        return jsonify({"status": "success", "message": "Modeled events from news and entities"})
    except Exception as e:
        logger.error(f"Error modeling events: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/analyze-risks', methods=['POST'])
def api_analyze_risks():
    """API endpoint to analyze risks based on events."""
    try:
        risk_analyzer.identify_all_risks()
        return jsonify({"status": "success", "message": "Analyzed risks from events"})
    except Exception as e:
        logger.error(f"Error analyzing risks: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/build-graph', methods=['POST'])
def api_build_graph():
    """API endpoint to build the knowledge graph."""
    try:
        graph_builder.build_complete_graph()
        return jsonify({"status": "success", "message": "Built knowledge graph"})
    except Exception as e:
        logger.error(f"Error building graph: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/get-graph-data', methods=['GET'])
def api_get_graph_data():
    """API endpoint to get knowledge graph data for visualization."""
    try:
        layer = request.args.get('layer', 'all')  # entity, event, risk, or all
        graph_data = graph_builder.get_visualization_data(layer)
        return jsonify(graph_data)
    except Exception as e:
        logger.error(f"Error getting graph data: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/get-risk-paths', methods=['GET'])
def api_get_risk_paths():
    """API endpoint to get risk transmission paths."""
    try:
        source_id = request.args.get('source_id')
        target_id = request.args.get('target_id')
        
        if source_id and target_id:
            paths = risk_analyzer.find_risk_path(source_id, target_id)
        else:
            paths = risk_analyzer.find_risk_transmission_paths()
            
        return jsonify({"status": "success", "paths": paths})
    except Exception as e:
        logger.error(f"Error getting risk paths: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/process-all', methods=['POST'])
def process_all():
    """Process the entire pipeline from news collection to graph building."""
    try:
        # Collect news from all sources
        for news_source in NEWS_SOURCES:
            news_collector.collect_from_source(news_source, START_DATE, END_DATE)
        
        # Extract entities
        entity_extractor.extract_all_entities()
        
        # Model events
        event_modeler.model_all_events()
        
        # Analyze risks
        risk_analyzer.identify_all_risks()
        
        # Build knowledge graph
        graph_builder.build_complete_graph()
        
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error in process_all: {e}")
        return render_template('error.html', error=str(e))


@app.route('/api/query-graph', methods=['POST'])
def api_query_graph():
    """API endpoint to query the knowledge graph."""
    try:
        query_type = request.json.get('type')
        params = request.json.get('params', {})
        
        results = {}
        
        if query_type == 'entity_search':
            results = graph_builder.search_entities(params.get('term', ''))
        elif query_type == 'event_search':
            results = graph_builder.search_events(params.get('term', ''))
        elif query_type == 'risk_search':
            results = graph_builder.search_risks(params.get('term', ''))
        elif query_type == 'centrality':
            results = graph_builder.analyze_centrality(params.get('measure', 'degree'))
        elif query_type == 'community':
            results = graph_builder.detect_communities(params.get('method', 'louvain'))
        elif query_type == 'path':
            results = graph_builder.find_paths(
                params.get('source_id'), 
                params.get('target_id'),
                params.get('max_length', 3)
            )
        
        return jsonify({"status": "success", "results": results})
    except Exception as e:
        logger.error(f"Error querying graph: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
