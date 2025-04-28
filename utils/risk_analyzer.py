"""
Risk analysis module for identifying financial risks from events.
"""
import logging
import networkx as nx
from typing import List, Dict, Any, Set, Tuple, Optional
from datetime import datetime
import re
import itertools

# Setup logging
logger = logging.getLogger(__name__)

class RiskAnalyzer:
    """
    Analyzes financial risks from events and builds risk models.
    """
    
    def __init__(self, data_store):
        """
        Initialize the risk analyzer with data store.
        
        Args:
            data_store: Data storage interface
        """
        self.data_store = data_store
        
        # Risk patterns for different risk categories
        self.risk_patterns = {
            "Market Risk Event": [
                r"(market|stock|index|bond)\s+(crash|collapse|volatility|correction)",
                r"(interest rate|yield|spread)\s+(rise|increase|jump|spike|volatility)",
                r"(bull|bear)\s+market",
                r"market\s+uncertainty",
                r"(valuation|bubble|overvaluation|undervaluation)"
            ],
            "Credit Risk Event": [
                r"(default|bankruptcy|insolvency|restructuring)",
                r"(debt|loan)\s+(problem|issue|concern)",
                r"(credit|debt)\s+rating\s+(downgrade|cut|lower)",
                r"(non-performing|bad)\s+(loan|debt)",
                r"debt\s+burden"
            ],
            "Liquidity Risk Event": [
                r"(liquidity|cash|funding)\s+(problem|issue|concern|crisis|squeeze)",
                r"(unable|difficulty)\s+to\s+(raise|secure)\s+(funding|capital|money)",
                r"(frozen|dry up|seized)\s+(credit|market|funding)",
                r"(bank|financial)\s+run",
                r"(withdraw|redemption)\s+surge"
            ],
            "Operational Risk Event": [
                r"(operational|system|technical)\s+(failure|breakdown|outage|disruption)",
                r"(cyber|security)\s+(attack|breach|incident|threat)",
                r"(fraud|misconduct|corruption|scandal)",
                r"(human|employee)\s+error",
                r"(natural disaster|fire|flood|earthquake|pandemic|supply chain)\s+(disruption|issue)"
            ],
            "Legal Risk Event": [
                r"(lawsuit|litigation|legal action|sue|sued)",
                r"(fine|penalty|sanction)",
                r"(regulatory|compliance|legal)\s+(violation|breach|issue|problem)",
                r"(investigation|probe|inquiry)",
                r"(settlement|judgment)\s+against"
            ],
            "Strategic Risk Event": [
                r"(strategic|strategy)\s+(failure|mistake|error)",
                r"(competition|competitor)\s+(pressure|threat)",
                r"(merger|acquisition|partnership)\s+(failure|problem|issue)",
                r"(business model|strategy)\s+(change|shift)",
                r"(enter|exit)\s+(market|business|industry)"
            ],
            "Reputation Risk Event": [
                r"(reputation|reputational)\s+(damage|harm|crisis|issue)",
                r"(public|customer|consumer)\s+(backlash|criticism|protest)",
                r"(scandal|controversy)",
                r"(social media|PR)\s+(crisis|disaster|backlash)",
                r"(boycott|public relations)\s+issue"
            ],
            "Regulatory Risk Event": [
                r"(regulation|regulatory)\s+(change|reform|tightening|new)",
                r"(compliance|regulatory)\s+(cost|burden|requirement)",
                r"(legislation|law|rule)\s+(change|new|proposed)",
                r"(regulatory|government)\s+(crackdown|enforcement)",
                r"(license|permit|approval)\s+(revoke|suspend|deny|delay)"
            ]
        }
        
        # Risk propagation rules from FEEKG framework
        self.risk_propagation_rules = {
            # Entity type -> Risk type -> Propagation factors
            "Company": {
                "Market Risk Event": 0.7,
                "Credit Risk Event": 0.8,
                "Liquidity Risk Event": 0.8,
                "Operational Risk Event": 0.9,
                "Legal Risk Event": 0.7,
                "Strategic Risk Event": 0.9,
                "Reputation Risk Event": 0.8,
                "Regulatory Risk Event": 0.7
            },
            "Bank": {
                "Market Risk Event": 0.8,
                "Credit Risk Event": 0.9,
                "Liquidity Risk Event": 0.9,
                "Operational Risk Event": 0.8,
                "Legal Risk Event": 0.7,
                "Strategic Risk Event": 0.7,
                "Reputation Risk Event": 0.9,
                "Regulatory Risk Event": 0.9
            },
            "Insurance": {
                "Market Risk Event": 0.7,
                "Credit Risk Event": 0.6,
                "Liquidity Risk Event": 0.7,
                "Operational Risk Event": 0.8,
                "Legal Risk Event": 0.8,
                "Strategic Risk Event": 0.7,
                "Reputation Risk Event": 0.8,
                "Regulatory Risk Event": 0.8
            },
            "Asset Manager": {
                "Market Risk Event": 0.9,
                "Credit Risk Event": 0.6,
                "Liquidity Risk Event": 0.8,
                "Operational Risk Event": 0.7,
                "Legal Risk Event": 0.6,
                "Strategic Risk Event": 0.8,
                "Reputation Risk Event": 0.9,
                "Regulatory Risk Event": 0.7
            },
            "Regulator": {
                "Market Risk Event": 0.3,
                "Credit Risk Event": 0.3,
                "Liquidity Risk Event": 0.3,
                "Operational Risk Event": 0.6,
                "Legal Risk Event": 0.4,
                "Strategic Risk Event": 0.5,
                "Reputation Risk Event": 0.7,
                "Regulatory Risk Event": 0.2  # Creating regulation not as affected by it
            },
            "Central Bank": {
                "Market Risk Event": 0.5,
                "Credit Risk Event": 0.4,
                "Liquidity Risk Event": 0.5,
                "Operational Risk Event": 0.6,
                "Legal Risk Event": 0.5,
                "Strategic Risk Event": 0.6,
                "Reputation Risk Event": 0.8,
                "Regulatory Risk Event": 0.4
            },
            "Government": {
                "Market Risk Event": 0.6,
                "Credit Risk Event": 0.7,
                "Liquidity Risk Event": 0.5,
                "Operational Risk Event": 0.6,
                "Legal Risk Event": 0.5,
                "Strategic Risk Event": 0.7,
                "Reputation Risk Event": 0.8,
                "Regulatory Risk Event": 0.4
            },
            "Exchange": {
                "Market Risk Event": 0.9,
                "Credit Risk Event": 0.5,
                "Liquidity Risk Event": 0.8,
                "Operational Risk Event": 0.9,
                "Legal Risk Event": 0.6,
                "Strategic Risk Event": 0.7,
                "Reputation Risk Event": 0.8,
                "Regulatory Risk Event": 0.8
            },
            # For generic types of entities
            "DEFAULT_ORG": {
                "Market Risk Event": 0.7,
                "Credit Risk Event": 0.7,
                "Liquidity Risk Event": 0.6,
                "Operational Risk Event": 0.8,
                "Legal Risk Event": 0.7,
                "Strategic Risk Event": 0.8,
                "Reputation Risk Event": 0.8,
                "Regulatory Risk Event": 0.7
            },
            "DEFAULT_PERSON": {
                "Market Risk Event": 0.3,
                "Credit Risk Event": 0.3,
                "Liquidity Risk Event": 0.2,
                "Operational Risk Event": 0.4,
                "Legal Risk Event": 0.7,
                "Strategic Risk Event": 0.5,
                "Reputation Risk Event": 0.8,
                "Regulatory Risk Event": 0.3
            },
            "DEFAULT_PRODUCT": {
                "Market Risk Event": 0.8,
                "Credit Risk Event": 0.5,
                "Liquidity Risk Event": 0.7,
                "Operational Risk Event": 0.6,
                "Legal Risk Event": 0.5,
                "Strategic Risk Event": 0.7,
                "Reputation Risk Event": 0.6,
                "Regulatory Risk Event": 0.5
            }
        }
    
    def identify_all_risks(self) -> List[str]:
        """
        Process all events to identify risks.
        
        Returns:
            List of risk IDs created
        """
        created_risk_ids = []
        
        # Get all events
        events = self.data_store.get_all_events()
        
        # Process each event to identify potential risks
        for event in events:
            try:
                # Identify risks for this event
                risk_ids = self._identify_risks_from_event(event)
                created_risk_ids.extend(risk_ids)
                
                logger.info(f"Identified {len(risk_ids)} risks from event {event.id}")
            
            except Exception as e:
                logger.error(f"Error identifying risks from event {event.id}: {e}")
        
        # After all risks are identified, model risk transmission
        try:
            self._model_risk_transmission()
            logger.info("Modeled risk transmission relationships")
        except Exception as e:
            logger.error(f"Error modeling risk transmission: {e}")
        
        return created_risk_ids
    
    def _identify_risks_from_event(self, event) -> List[str]:
        """
        Identify potential risks from an event.
        
        Args:
            event: Event object
            
        Returns:
            List of risk IDs created
        """
        risk_ids = []
        
        # Get all news items related to this event
        news_items = [self.data_store.get_news(news_id) for news_id in event.news_sources]
        news_items = [n for n in news_items if n is not None]
        
        if not news_items:
            return risk_ids
        
        # Combine news content for risk assessment
        combined_text = f"{event.title} {event.description} "
        for news in news_items:
            combined_text += f"{news.title} {news.content} "
        
        combined_text = combined_text.lower()
        
        # Check for risk patterns in each category
        for risk_type, patterns in self.risk_patterns.items():
            risk_score = 0
            pattern_matches = []
            
            for pattern in patterns:
                matches = re.findall(pattern, combined_text)
                risk_score += len(matches)
                if matches:
                    pattern_matches.extend(matches)
            
            # If risk score reaches threshold, create a risk
            if risk_score >= 2:
                # Calculate risk severity and likelihood based on pattern matches
                severity = min(5, max(1, int(risk_score / 2)))
                likelihood = min(0.9, max(0.1, risk_score / 10.0))
                
                # Create risk title and description
                risk_title = self._generate_risk_title(event, risk_type)
                risk_description = self._generate_risk_description(event, risk_type, pattern_matches)
                
                # Create risk object
                from models import Risk
                risk = Risk.create(
                    title=risk_title,
                    description=risk_description,
                    risk_type=risk_type,
                    severity=severity,
                    likelihood=likelihood
                )
                
                # Add event as trigger
                risk.add_event(event.id, 1.0)
                
                # Add affected entities
                for entity_id in event.entities:
                    entity = self.data_store.get_entity(entity_id)
                    if entity:
                        # Determine impact level based on entity type and risk type
                        impact_level = self._calculate_entity_impact_level(entity, risk_type)
                        risk.add_entity(entity_id, impact_level)
                
                # Add impact areas
                risk.impact_areas = self._determine_impact_areas(risk_type)
                
                # Save risk
                self.data_store.save_risk(risk)
                risk_ids.append(risk.id)
        
        return risk_ids
    
    def _generate_risk_title(self, event, risk_type: str) -> str:
        """
        Generate a descriptive title for a risk.
        
        Args:
            event: Triggering event
            risk_type: Risk category
            
        Returns:
            Risk title
        """
        # Get primary entities from event
        primary_entities = []
        for entity_id in event.entities[:2]:  # Consider up to 2 main entities
            entity = self.data_store.get_entity(entity_id)
            if entity:
                primary_entities.append(entity.name)
        
        # Format entity text
        if primary_entities:
            entity_text = " and ".join(primary_entities)
        else:
            entity_text = "Financial system"
        
        # Format risk type for title
        risk_category = risk_type.replace(" Event", "")
        
        return f"{risk_category} for {entity_text} from {event.event_type.replace('_', ' ').title()} Event"
    
    def _generate_risk_description(self, event, risk_type: str, pattern_matches: List) -> str:
        """
        Generate a descriptive text for a risk.
        
        Args:
            event: Triggering event
            risk_type: Risk category
            pattern_matches: Risk pattern matches from text
            
        Returns:
            Risk description
        """
        # Base description referencing the event
        base_desc = f"Risk identified from event: {event.title}. "
        
        # Add event description
        event_desc = f"Event details: {event.description}. "
        
        # Add specific risk indicators found
        if pattern_matches:
            indicators = ", ".join(set(str(match) for match in pattern_matches if match))
            indicators_desc = f"Risk indicators found: {indicators}. "
        else:
            indicators_desc = ""
        
        # Add general risk description based on type
        risk_explanations = {
            "Market Risk Event": "Market risk involves potential losses due to market movements and volatility.",
            "Credit Risk Event": "Credit risk involves potential losses due to counterparty default or credit deterioration.",
            "Liquidity Risk Event": "Liquidity risk involves potential losses or operational issues due to inability to meet cash flow needs.",
            "Operational Risk Event": "Operational risk involves potential losses due to failed internal processes, people, systems, or external events.",
            "Legal Risk Event": "Legal risk involves potential losses due to legal actions, regulatory violations, or contractual issues.",
            "Strategic Risk Event": "Strategic risk involves potential losses due to failed business decisions or implementation.",
            "Reputation Risk Event": "Reputation risk involves potential losses due to damage to company image or brand.",
            "Regulatory Risk Event": "Regulatory risk involves potential losses due to regulatory changes or compliance failures."
        }
        
        type_desc = risk_explanations.get(risk_type, "")
        
        # Combine parts
        return f"{base_desc}{event_desc}{indicators_desc}{type_desc}"
    
    def _calculate_entity_impact_level(self, entity, risk_type: str) -> float:
        """
        Calculate the impact level of a risk on an entity.
        
        Args:
            entity: Entity object
            risk_type: Risk category
            
        Returns:
            Impact level (0.0-1.0)
        """
        # Get entity type or subtype for lookup
        entity_type = entity.subtype if entity.subtype else entity.type
        
        # Check if we have specific rules for this entity type
        if entity_type in self.risk_propagation_rules:
            type_rules = self.risk_propagation_rules[entity_type]
            if risk_type in type_rules:
                return type_rules[risk_type]
        
        # Try to find a default rule for the entity's general type
        default_key = f"DEFAULT_{entity.type}"
        if default_key in self.risk_propagation_rules:
            default_rules = self.risk_propagation_rules[default_key]
            if risk_type in default_rules:
                return default_rules[risk_type]
        
        # Default impact level
        return 0.5
    
    def _determine_impact_areas(self, risk_type: str) -> List[str]:
        """
        Determine the impact areas for a risk based on its type.
        
        Args:
            risk_type: Risk category
            
        Returns:
            List of impact areas
        """
        # Map risk types to impact areas
        impact_areas_map = {
            "Market Risk Event": ["Financial Markets", "Investment Performance", "Asset Valuations"],
            "Credit Risk Event": ["Debt Servicing", "Counterparty Exposure", "Credit Ratings"],
            "Liquidity Risk Event": ["Cash Flow", "Funding Access", "Asset Liquidity"],
            "Operational Risk Event": ["Business Operations", "Systems & Technology", "People & Process"],
            "Legal Risk Event": ["Legal Liability", "Compliance", "Corporate Governance"],
            "Strategic Risk Event": ["Business Strategy", "Competitive Position", "Business Model"],
            "Reputation Risk Event": ["Brand Value", "Customer Trust", "Public Perception"],
            "Regulatory Risk Event": ["Regulatory Compliance", "Policy Environment", "Licensing"]
        }
        
        return impact_areas_map.get(risk_type, ["Financial", "Operational"])
    
    def _model_risk_transmission(self) -> None:
        """
        Model transmission relationships between identified risks.
        """
        # Get all risks
        risks = self.data_store.get_all_risks()
        
        # Skip if very few risks
        if len(risks) < 2:
            return
        
        # Build a graph of entity relationships
        entity_graph = nx.Graph()
        
        # Add all entity relationships to graph
        relationships = self.data_store.get_all_relationships()
        for rel in relationships:
            entity_graph.add_edge(rel.source_id, rel.target_id, weight=rel.confidence)
        
        # For each pair of risks, check if they are connected through entities
        for risk1, risk2 in itertools.combinations(risks, 2):
            # Skip if risks are the same
            if risk1.id == risk2.id:
                continue
            
            # Check if risks share entities
            common_entities = set(risk1.entities).intersection(set(risk2.entities))
            if common_entities:
                # Risks share entities directly
                correlation = len(common_entities) / min(len(risk1.entities), len(risk2.entities))
                
                # Create bi-directional risk relationships
                relationship_type = "correlated_with"
                
                risk1.add_related_risk(risk2.id, relationship_type)
                risk2.add_related_risk(risk1.id, relationship_type)
                
                # Store correlation in relationship attributes
                risk1.attributes.setdefault("risk_correlations", {})[risk2.id] = correlation
                risk2.attributes.setdefault("risk_correlations", {})[risk1.id] = correlation
                
                # Save risks
                self.data_store.save_risk(risk1)
                self.data_store.save_risk(risk2)
            
            else:
                # Check if risks are connected through entity relationships
                all_paths = []
                
                for entity1 in risk1.entities:
                    for entity2 in risk2.entities:
                        if entity_graph.has_node(entity1) and entity_graph.has_node(entity2):
                            try:
                                # Find the shortest path between entities
                                if nx.has_path(entity_graph, entity1, entity2):
                                    path = nx.shortest_path(entity_graph, entity1, entity2)
                                    all_paths.append(path)
                            except:
                                continue
                
                if all_paths:
                    # Risks are connected through entity relationships
                    shortest_path = min(all_paths, key=len)
                    path_length = len(shortest_path) - 1  # Count edges, not nodes
                    
                    # Calculate transmission strength based on path length
                    transmission_strength = 1.0 / path_length if path_length > 0 else 0.5
                    
                    # Determine direction based on risk types
                    risk_hierarchy = {
                        "Market Risk Event": 1,
                        "Credit Risk Event": 2,
                        "Liquidity Risk Event": 3,
                        "Operational Risk Event": 4,
                        "Legal Risk Event": 5,
                        "Strategic Risk Event": 6,
                        "Reputation Risk Event": 7,
                        "Regulatory Risk Event": 8
                    }
                    
                    # Lower numbers typically affect higher numbers in the hierarchy
                    risk1_level = risk_hierarchy.get(risk1.risk_type, 0)
                    risk2_level = risk_hierarchy.get(risk2.risk_type, 0)
                    
                    if risk1_level < risk2_level:
                        # Risk1 likely affects Risk2
                        risk1.add_related_risk(risk2.id, "may_cause")
                        risk2.add_related_risk(risk1.id, "may_be_caused_by")
                    elif risk1_level > risk2_level:
                        # Risk2 likely affects Risk1
                        risk1.add_related_risk(risk2.id, "may_be_caused_by")
                        risk2.add_related_risk(risk1.id, "may_cause")
                    else:
                        # Same level, bidirectional influence
                        risk1.add_related_risk(risk2.id, "may_influence")
                        risk2.add_related_risk(risk1.id, "may_influence")
                    
                    # Store transmission strength
                    risk1.attributes.setdefault("risk_transmissions", {})[risk2.id] = transmission_strength
                    risk2.attributes.setdefault("risk_transmissions", {})[risk1.id] = transmission_strength
                    
                    # Store path for visualization
                    risk1.attributes.setdefault("transmission_paths", {})[risk2.id] = shortest_path
                    risk2.attributes.setdefault("transmission_paths", {})[risk1.id] = shortest_path
                    
                    # Save risks
                    self.data_store.save_risk(risk1)
                    self.data_store.save_risk(risk2)
    
    def find_risk_transmission_paths(self) -> List[Dict[str, Any]]:
        """
        Find and return all risk transmission paths.
        
        Returns:
            List of risk transmission paths
        """
        transmission_paths = []
        
        try:
            # Get all risks
            risks = self.data_store.get_all_risks()
            
            if not risks:
                logger.info("No risks found for transmission path analysis")
                return []
            
            # Extract transmission paths
            for risk in risks:
                if not hasattr(risk, 'attributes') or not isinstance(risk.attributes, dict):
                    continue
                    
                if "transmission_paths" in risk.attributes:
                    for target_id, path in risk.attributes["transmission_paths"].items():
                        target_risk = self.data_store.get_risk(target_id)
                        if target_risk:
                            # Get path information
                            try:
                                source_type = risk.risk_type
                                target_type = target_risk.risk_type
                                
                                # Get entity names along the path
                                entity_names = []
                                for entity_id in path:
                                    entity = self.data_store.get_entity(entity_id)
                                    if entity:
                                        entity_names.append(entity.name)
                                
                                # Get transmission strength if available
                                strength = risk.attributes.get("risk_transmissions", {}).get(target_id, 0.5)
                                
                                # Get relationship type
                                relationship = risk.attributes.get("risk_relationships", {}).get(target_id, "connected_to")
                                
                                # Add path information
                                transmission_paths.append({
                                    "source_id": risk.id,
                                    "source_title": risk.title,
                                    "source_type": source_type,
                                    "target_id": target_id,
                                    "target_title": target_risk.title,
                                    "target_type": target_type,
                                    "path": entity_names,
                                    "strength": strength,
                                    "relationship": relationship
                                })
                            except Exception as inner_e:
                                logger.warning(f"Error processing risk path {risk.id} -> {target_id}: {inner_e}")
                                continue
            
        except Exception as e:
            logger.error(f"Error finding risk transmission paths: {e}")
            import traceback
            traceback.print_exc()
        
        return transmission_paths
    
    def find_risk_path(self, source_id: str, target_id: str) -> List[Dict[str, Any]]:
        """
        Find the transmission path between two specific risks.
        
        Args:
            source_id: Source risk ID
            target_id: Target risk ID
            
        Returns:
            List with the specific risk path
        """
        try:
            # Get the risks
            source_risk = self.data_store.get_risk(source_id)
            target_risk = self.data_store.get_risk(target_id)
            
            if not source_risk or not target_risk:
                logger.warning(f"Source risk {source_id} or target risk {target_id} not found")
                return []
            
            # Check if there is a direct transmission path
            if hasattr(source_risk, 'attributes') and isinstance(source_risk.attributes, dict) and \
               "transmission_paths" in source_risk.attributes and \
               target_id in source_risk.attributes["transmission_paths"]:
                try:
                    path = source_risk.attributes["transmission_paths"][target_id]
                    
                    # Get entity names along the path
                    entity_names = []
                    for entity_id in path:
                        entity = self.data_store.get_entity(entity_id)
                        if entity and hasattr(entity, 'name'):
                            entity_names.append(entity.name)
                    
                    # Get transmission strength if available
                    strength = source_risk.attributes.get("risk_transmissions", {}).get(target_id, 0.5)
                    
                    # Get relationship type
                    relationship = source_risk.attributes.get("risk_relationships", {}).get(target_id, "connected_to")
                    
                    return [{
                        "source_id": source_risk.id,
                        "source_title": source_risk.title,
                        "source_type": source_risk.risk_type,
                        "target_id": target_id,
                        "target_title": target_risk.title,
                        "target_type": target_risk.risk_type,
                        "path": entity_names,
                        "strength": strength,
                        "relationship": relationship
                    }]
                except Exception as direct_path_error:
                    logger.warning(f"Error processing direct risk path: {direct_path_error}")
            
            # If no direct path, try to find an indirect path through other risks
            risk_graph = nx.DiGraph()
            
            # Build a graph of risk relationships
            try:
                risks = self.data_store.get_all_risks()
                if not risks:
                    return []
                    
                for risk in risks:
                    if not hasattr(risk, 'related_risks') or not isinstance(risk.related_risks, list) or not hasattr(risk, 'id'):
                        continue
                        
                    for related_id in risk.related_risks:
                        # Use transmission strength as weight if available
                        weight = 1.0
                        if hasattr(risk, 'attributes') and isinstance(risk.attributes, dict) and \
                           "risk_transmissions" in risk.attributes and \
                           related_id in risk.attributes["risk_transmissions"]:
                            weight = 1.0 - risk.attributes["risk_transmissions"][related_id]  # Convert to distance
                        
                        risk_graph.add_edge(risk.id, related_id, weight=weight)
                
                # Try to find a path in the risk graph
                if risk_graph.has_node(source_id) and risk_graph.has_node(target_id):
                    try:
                        if nx.has_path(risk_graph, source_id, target_id):
                            # Find the shortest path
                            path = nx.shortest_path(risk_graph, source_id, target_id, weight='weight')
                            
                            # Build a more detailed path description
                            detailed_path = []
                            for i in range(len(path) - 1):
                                current_id = path[i]
                                next_id = path[i+1]
                                
                                current_risk = self.data_store.get_risk(current_id)
                                next_risk = self.data_store.get_risk(next_id)
                                
                                if current_risk and next_risk and hasattr(current_risk, 'attributes') and \
                                   isinstance(current_risk.attributes, dict) and hasattr(current_risk, 'title') and \
                                   hasattr(current_risk, 'risk_type') and hasattr(next_risk, 'title') and \
                                   hasattr(next_risk, 'risk_type'):
                                    # Get relationship information
                                    relationship = current_risk.attributes.get("risk_relationships", {}).get(next_id, "connected_to")
                                    
                                    # Get strength information
                                    strength = current_risk.attributes.get("risk_transmissions", {}).get(next_id, 0.5)
                                    
                                    detailed_path.append({
                                        "source_id": current_id,
                                        "source_title": current_risk.title,
                                        "source_type": current_risk.risk_type,
                                        "target_id": next_id,
                                        "target_title": next_risk.title,
                                        "target_type": next_risk.risk_type,
                                        "relationship": relationship,
                                        "strength": strength
                                    })
                            
                            return detailed_path
                    except Exception as path_error:
                        logger.warning(f"Error finding path in risk graph: {path_error}")
            except Exception as graph_error:
                logger.warning(f"Error building risk graph: {graph_error}")
                
        except Exception as e:
            logger.error(f"Error finding risk path: {e}")
            import traceback
            traceback.print_exc()
        
        return []
    
    def calculate_risk_metrics(self) -> Dict[str, Any]:
        """
        Calculate summary risk metrics from all identified risks.
        
        Returns:
            Dictionary of risk metrics
        """
        default_metrics = {
            "total_risks": 0,
            "risk_categories": [],
            "severity_distribution": [],
            "entity_risk_exposure": []
        }
        
        try:
            # Get all risks and events
            risks = self.data_store.get_all_risks()
            events = self.data_store.get_all_events()
            
            if not risks:
                logger.info("No risks found for risk metrics calculation")
                return default_metrics
            
            metrics = {
                "total_risks": 0,
                "risk_type_distribution": {},
                "risk_severity_distribution": {},
                "most_affected_entities": [],
                "highest_severity_risks": [],
                "risk_event_correlation": {},
                "risk_over_time": {}
            }
            
            # Total risks
            metrics["total_risks"] = len(risks)
            
            # Risk type distribution
            type_counts = {}
            for risk in risks:
                if not hasattr(risk, 'risk_type'):
                    continue
                    
                if risk.risk_type not in type_counts:
                    type_counts[risk.risk_type] = 0
                type_counts[risk.risk_type] += 1
            metrics["risk_type_distribution"] = type_counts
            
            # Risk severity distribution
            severity_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            for risk in risks:
                if not hasattr(risk, 'severity'):
                    continue
                    
                severity_counts[risk.severity] = severity_counts.get(risk.severity, 0) + 1
            metrics["risk_severity_distribution"] = severity_counts
            
            # Most affected entities
            entity_risk_counts = {}
            for risk in risks:
                if not hasattr(risk, 'entities') or not isinstance(risk.entities, list):
                    continue
                    
                for entity_id in risk.entities:
                    if entity_id not in entity_risk_counts:
                        entity_risk_counts[entity_id] = 0
                    entity_risk_counts[entity_id] += 1
            
            # Get top 10 affected entities
            top_entities = sorted(entity_risk_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            metrics["most_affected_entities"] = []
            
            for entity_id, count in top_entities:
                entity = self.data_store.get_entity(entity_id)
                if entity and hasattr(entity, 'name') and hasattr(entity, 'type'):
                    metrics["most_affected_entities"].append({
                        "id": entity_id,
                        "name": entity.name,
                        "type": entity.type,
                        "subtype": getattr(entity, 'subtype', ''),
                        "risk_count": count
                    })
            
            # Highest severity risks
            try:
                high_severity_risks = sorted(risks, key=lambda r: (getattr(r, 'severity', 0), getattr(r, 'likelihood', 0)), reverse=True)[:10]
                metrics["highest_severity_risks"] = []
                
                for risk in high_severity_risks:
                    if not hasattr(risk, 'id') or not hasattr(risk, 'title') or not hasattr(risk, 'risk_type'):
                        continue
                        
                    metrics["highest_severity_risks"].append({
                        "id": risk.id,
                        "title": risk.title,
                        "type": risk.risk_type,
                        "severity": getattr(risk, 'severity', 0),
                        "likelihood": getattr(risk, 'likelihood', 0.0)
                    })
            except Exception as sort_error:
                logger.warning(f"Error sorting risks by severity: {sort_error}")
                metrics["highest_severity_risks"] = []
            
            # Risk-event correlation
            event_types = set()
            for event in events:
                if hasattr(event, 'event_type'):
                    event_types.add(event.event_type)
            
            risk_event_matrix = {}
            for risk_type in type_counts.keys():
                risk_event_matrix[risk_type] = {}
                for event_type in event_types:
                    risk_event_matrix[risk_type][event_type] = 0
            
            # Count correlations
            for risk in risks:
                if not hasattr(risk, 'events') or not isinstance(risk.events, list) or not hasattr(risk, 'risk_type'):
                    continue
                    
                for event_id in risk.events:
                    event = self.data_store.get_event(event_id)
                    if event and hasattr(event, 'event_type'):
                        risk_event_matrix[risk.risk_type][event.event_type] = \
                            risk_event_matrix[risk.risk_type].get(event.event_type, 0) + 1
            
            metrics["risk_event_correlation"] = risk_event_matrix
            
            # Risk over time
            time_distribution = {}
            
            for risk in risks:
                if not hasattr(risk, 'created_at') or not hasattr(risk, 'risk_type'):
                    continue
                    
                try:
                    # Use creation date
                    date_str = datetime.fromisoformat(risk.created_at).strftime('%Y-%m-%d')
                    
                    if date_str not in time_distribution:
                        time_distribution[date_str] = {
                            "total": 0,
                            "by_type": {}
                        }
                    
                    time_distribution[date_str]["total"] += 1
                    
                    # Also track by type
                    if risk.risk_type not in time_distribution[date_str]["by_type"]:
                        time_distribution[date_str]["by_type"][risk.risk_type] = 0
                    time_distribution[date_str]["by_type"][risk.risk_type] += 1
                except Exception as date_error:
                    logger.warning(f"Error processing date for risk {getattr(risk, 'id', 'unknown')}: {date_error}")
            
            metrics["risk_over_time"] = time_distribution
            
            # Format data for template
            risk_categories = []
            for risk_type, count in type_counts.items():
                risk_categories.append({
                    "name": risk_type,
                    "count": count,
                    "percentage": round(count * 100 / metrics["total_risks"], 1) if metrics["total_risks"] > 0 else 0
                })
            
            severity_distribution = []
            for severity, count in severity_counts.items():
                if severity > 0:  # Skip zero severity
                    severity_distribution.append({
                        "level": severity,
                        "count": count,
                        "percentage": round(count * 100 / metrics["total_risks"], 1) if metrics["total_risks"] > 0 else 0
                    })
            
            # Create simplified metrics for template
            simplified_metrics = {
                "total_risks": metrics["total_risks"],
                "risk_categories": sorted(risk_categories, key=lambda x: x["count"], reverse=True),
                "severity_distribution": sorted(severity_distribution, key=lambda x: x["level"]),
                "entity_risk_exposure": metrics["most_affected_entities"]
            }
            
            return simplified_metrics
            
        except Exception as e:
            logger.error(f"Error calculating risk metrics: {e}")
            import traceback
            traceback.print_exc()
            return default_metrics
