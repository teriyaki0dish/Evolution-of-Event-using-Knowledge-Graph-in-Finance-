"""
Event modeling module for identifying and modeling financial events.
"""
import logging
from typing import List, Dict, Any, Set, Tuple
from datetime import datetime, timedelta
import re
import itertools
import uuid

# Setup logging
logger = logging.getLogger(__name__)

class EventModeler:
    """
    Models financial events from news and entities.
    """
    
    def __init__(self, data_store):
        """
        Initialize the event modeler with data store.
        
        Args:
            data_store: Data storage interface
        """
        self.data_store = data_store
        
        # Event type patterns for classification
        self.event_patterns = {
            "market_movement": [
                r"(rise|fall|drop|jump|plunge|surge|soar|tumble|spike|crash)",
                r"(gain|lose|increase|decrease)\s+\d+(\.\d+)?\s*(%|percent)",
                r"(bull|bear)\s+market",
                r"market\s+(correction|rally|collapse|rebound)",
                r"(stock|share|bond|market)s?\s+(fall|rise|drop|jump|plunge|surge|soar|tumble)"
            ],
            "company_financial": [
                r"(report|announce|disclose|reveal)\s+\w+\s+earnings",
                r"(quarterly|annual)\s+(results|earnings|report)",
                r"(profit|revenue|sales)\s+(up|down|rise|fall|drop|jump|plunge|surge|soar|tumble)",
                r"(beat|miss|exceed|fall short of)\s+(forecast|expectation|estimate)",
                r"(raise|lower|cut)\s+(guidance|forecast|outlook)"
            ],
            "merger_acquisition": [
                r"(merger|acquisition|takeover|buyout)",
                r"(acquire|buy|purchase)\s+\w+\s+(company|business|unit|division|stake)",
                r"(sell|divest)\s+\w+\s+(company|business|unit|division|stake)",
                r"(offer|bid)\s+to\s+(buy|acquire|take over)",
                r"merger\s+agreement"
            ],
            "corporate_governance": [
                r"(appoint|name|elect|hire)\s+\w+\s+(CEO|CFO|COO|CTO|chairman|director|board member)",
                r"(resign|step down|depart|leave)\s+\w+\s+(CEO|CFO|COO|CTO|chairman|director|position)",
                r"(board|shareholder)\s+meeting",
                r"(vote|approval|rejection)\s+of\s+(proposal|resolution)",
                r"corporate\s+restructuring"
            ],
            "regulatory_legal": [
                r"(lawsuit|litigation|legal action|court|judge|trial|sue|charged|settlement)",
                r"(investigation|probe|inquiry)\s+by\s+(SEC|FTC|DOJ|regulator)",
                r"(fine|penalty|sanction)\s+of\s+\$?\d+",
                r"(regulatory|legal|compliance)\s+(issue|problem|violation|action)",
                r"(approve|reject|clear|block)\s+\w+\s+(merger|acquisition|deal)"
            ],
            "debt_financing": [
                r"(debt|bond|note|loan)\s+(issue|offering|sale)",
                r"(raise|borrow)\s+\$?\d+\s+\w+\s+(capital|fund|financing)",
                r"(refinance|restructure)\s+\w+\s+debt",
                r"(credit|debt)\s+rating\s+(upgrade|downgrade)",
                r"default\s+on\s+(debt|loan|bond|payment)"
            ],
            "equity_financing": [
                r"(IPO|initial public offering)",
                r"(secondary|follow-on)\s+offering",
                r"(stock|share)\s+(issue|offering|sale|buyback|repurchase)",
                r"(raise|seek)\s+\$?\d+\s+\w+\s+(equity|capital)",
                r"private\s+placement"
            ],
            "dividend_capital_return": [
                r"(announce|declare|pay)\s+\w+\s+dividend",
                r"(raise|increase|cut|reduce|suspend|cancel)\s+\w+\s+dividend",
                r"special\s+dividend",
                r"(stock|share)\s+split",
                r"capital\s+return"
            ],
            "economic_indicator": [
                r"(GDP|gross domestic product)",
                r"(inflation|CPI|consumer price index)",
                r"(unemployment|jobs|labor|employment)\s+(report|data|figure)",
                r"(interest rate|fed rate|benchmark rate)",
                r"(housing|retail sales|industrial production|manufacturing)\s+data"
            ],
            "monetary_policy": [
                r"(Fed|ECB|BOJ|central bank)\s+(meeting|decision)",
                r"(raise|cut|increase|decrease|hold|maintain)\s+\w+\s+interest\s+rate",
                r"(hawkish|dovish)\s+\w+\s+(stance|policy|outlook)",
                r"(monetary|policy)\s+(tightening|easing)",
                r"quantitative\s+(easing|tightening)"
            ],
            "fiscal_policy": [
                r"(tax|tariff)\s+(cut|increase|reform|change)",
                r"(government|federal)\s+(spending|budget|deficit)",
                r"fiscal\s+(stimulus|policy|reform)",
                r"infrastructure\s+(plan|bill|package)",
                r"economic\s+stimulus"
            ],
            "international_trade": [
                r"(trade|tariff)\s+(war|dispute|tension|negotiation|agreement|deal)",
                r"(import|export)\s+(restriction|ban|quota|duty)",
                r"(impose|lift)\s+\w+\s+tariff",
                r"trade\s+deficit",
                r"currency\s+(manipulation|devaluation)"
            ],
            "geopolitical": [
                r"(war|conflict|tension|attack|sanction)",
                r"(political|diplomatic)\s+(crisis|tension|relation)",
                r"(election|vote|referendum)",
                r"(terrorism|terrorist)\s+(attack|threat)",
                r"(natural disaster|hurricane|earthquake|flood|wildfire)"
            ],
            "technology_innovation": [
                r"(launch|release|unveil|introduce)\s+\w+\s+(product|service)",
                r"(patent|intellectual property|technology)\s+(filing|approval|litigation)",
                r"research\s+and\s+development",
                r"(AI|artificial intelligence|machine learning|blockchain|crypto)",
                r"(data breach|cybersecurity|hack|attack)"
            ],
            "commodity_price": [
                r"(oil|gold|silver|natural gas|commodity)\s+price\s+(rise|fall|drop|jump|plunge|surge|soar|tumble)",
                r"OPEC\s+(meeting|decision|cut|increase)",
                r"(supply|demand)\s+(issue|concern|disruption)",
                r"(inventory|stockpile)\s+(build|draw)",
                r"(production|output)\s+(increase|decrease|cut)"
            ]
        }
        
    def model_all_events(self) -> List[str]:
        """
        Process all news items to model events.
        
        Returns:
            List of event IDs created
        """
        created_event_ids = []
        
        # Get all processed news items
        news_items = self.data_store.get_processed_news()
        
        # Group news by publication date (same day)
        date_news_groups = self._group_news_by_date(news_items)
        
        # Process each day's news
        for date_str, date_news in date_news_groups.items():
            try:
                # Model events for this day
                event_ids = self._model_events_for_date(date_str, date_news)
                created_event_ids.extend(event_ids)
                
                logger.info(f"Modeled {len(event_ids)} events for date {date_str}")
            
            except Exception as e:
                logger.error(f"Error modeling events for date {date_str}: {e}")
        
        # Model evolution between events
        try:
            self._model_event_evolution()
            logger.info("Modeled event evolution relationships")
        except Exception as e:
            logger.error(f"Error modeling event evolution: {e}")
        
        return created_event_ids
    
    def _group_news_by_date(self, news_items) -> Dict[str, List]:
        """
        Group news items by publication date.
        
        Args:
            news_items: List of news items
            
        Returns:
            Dictionary mapping dates to news items
        """
        date_groups = {}
        
        for news in news_items:
            # Get date string (YYYY-MM-DD)
            date_str = news.published_at.strftime('%Y-%m-%d')
            
            if date_str not in date_groups:
                date_groups[date_str] = []
            
            date_groups[date_str].append(news)
        
        return date_groups
    
    def _model_events_for_date(self, date_str: str, news_items: List) -> List[str]:
        """
        Model events from news items published on the same day.
        
        Args:
            date_str: Date string (YYYY-MM-DD)
            news_items: List of news items for this date
            
        Returns:
            List of event IDs created
        """
        event_ids = []
        
        # Group news by topic/entity clusters
        news_clusters = self._cluster_news_by_entities(news_items)
        
        # Process each cluster to create events
        for cluster_idx, cluster_news in enumerate(news_clusters):
            try:
                # Skip very small clusters
                if len(cluster_news) < 1:
                    continue
                
                # Get all entities mentioned in this cluster
                all_entities = set()
                for news in cluster_news:
                    all_entities.update(news.entities)
                
                # Get entity objects
                entity_objects = [self.data_store.get_entity(entity_id) for entity_id in all_entities]
                entity_objects = [e for e in entity_objects if e is not None]
                
                # Skip if no valid entities
                if not entity_objects:
                    continue
                
                # Determine event type based on news content
                event_type = self._classify_event_type(cluster_news)
                
                # Create event title and description
                title, description = self._generate_event_title_desc(cluster_news, entity_objects, event_type)
                
                # Parse date
                event_date = datetime.strptime(date_str, '%Y-%m-%d')
                
                # Create event
                from models import Event
                event = Event.create(
                    title=title,
                    description=description,
                    event_type=event_type,
                    event_date=event_date
                )
                
                # Add entities to event
                for entity in entity_objects:
                    role = self._determine_entity_role(entity, cluster_news)
                    event.add_entity(entity.id, role)
                
                # Add relationships between entities in this event
                self._add_event_entity_relationships(event, entity_objects, cluster_news)
                
                # Add news sources
                event.news_sources = [news.id for news in cluster_news]
                
                # Save event
                self.data_store.save_event(event)
                event_ids.append(event.id)
                
                # Update news items with event reference
                for news in cluster_news:
                    if event.id not in news.events:
                        news.events.append(event.id)
                        self.data_store.save_news(news)
            
            except Exception as e:
                logger.error(f"Error creating event for cluster {cluster_idx}: {e}")
        
        return event_ids
    
    def _cluster_news_by_entities(self, news_items: List) -> List[List]:
        """
        Cluster news items based on shared entities.
        
        Args:
            news_items: List of news items
            
        Returns:
            List of news item clusters
        """
        # Skip clustering if only one news item
        if len(news_items) <= 1:
            return [news_items]
        
        # Create a matrix of entity overlap between news items
        news_count = len(news_items)
        overlap_matrix = [[0 for _ in range(news_count)] for _ in range(news_count)]
        
        for i in range(news_count):
            for j in range(i, news_count):
                if i == j:
                    overlap_matrix[i][j] = 1.0
                    continue
                
                # Calculate Jaccard similarity of entities
                entities_i = set(news_items[i].entities)
                entities_j = set(news_items[j].entities)
                
                if not entities_i or not entities_j:
                    overlap_matrix[i][j] = 0.0
                    overlap_matrix[j][i] = 0.0
                    continue
                
                intersection = len(entities_i.intersection(entities_j))
                union = len(entities_i.union(entities_j))
                
                similarity = intersection / union if union > 0 else 0.0
                
                overlap_matrix[i][j] = similarity
                overlap_matrix[j][i] = similarity
        
        # Simple clustering algorithm: connect news with similarity above threshold
        clusters = []
        visited = set()
        
        for i in range(news_count):
            if i in visited:
                continue
            
            # Start a new cluster
            cluster = [news_items[i]]
            visited.add(i)
            
            # Find connected news
            for j in range(news_count):
                if j in visited:
                    continue
                
                if overlap_matrix[i][j] >= 0.3:  # Similarity threshold
                    cluster.append(news_items[j])
                    visited.add(j)
            
            clusters.append(cluster)
        
        # If there are too many small clusters, combine them
        if len(clusters) > news_count // 2:
            # Group remaining small clusters by event type
            small_clusters = [c for c in clusters if len(c) < 3]
            large_clusters = [c for c in clusters if len(c) >= 3]
            
            # Classify small clusters
            type_clusters = {}
            for cluster in small_clusters:
                event_type = self._classify_event_type(cluster)
                if event_type not in type_clusters:
                    type_clusters[event_type] = []
                type_clusters[event_type].extend(cluster)
            
            # Add type-based clusters
            for event_type, cluster in type_clusters.items():
                if cluster:
                    large_clusters.append(cluster)
            
            return large_clusters
        
        return clusters
    
    def _classify_event_type(self, news_items: List) -> str:
        """
        Classify the event type based on news content.
        
        Args:
            news_items: List of news items
            
        Returns:
            Event type classification
        """
        # Combine all text from news items
        combined_text = ""
        for news in news_items:
            combined_text += f"{news.title} {news.content} "
        
        combined_text = combined_text.lower()
        
        # Count pattern matches for each event type
        type_scores = {}
        
        for event_type, patterns in self.event_patterns.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, combined_text)
                score += len(matches)
            
            type_scores[event_type] = score
        
        # Get event type with highest score
        best_type = max(type_scores.items(), key=lambda x: x[1])
        
        # Default to market_movement if no clear match
        if best_type[1] == 0:
            return "market_movement"
        
        return best_type[0]
    
    def _generate_event_title_desc(self, news_items: List, entities: List, event_type: str) -> Tuple[str, str]:
        """
        Generate event title and description from news items.
        
        Args:
            news_items: List of news items
            entities: List of entity objects
            event_type: Classified event type
            
        Returns:
            Tuple of (title, description)
        """
        # Extract top entities by mentions
        top_entities = sorted(entities, key=lambda e: len(e.mentions), reverse=True)[:3]
        entity_names = [e.name for e in top_entities]
        
        # Format entity text
        if len(entity_names) == 1:
            entity_text = entity_names[0]
        elif len(entity_names) == 2:
            entity_text = f"{entity_names[0]} and {entity_names[1]}"
        elif len(entity_names) >= 3:
            entity_text = f"{entity_names[0]}, {entity_names[1]}, and {entity_names[2]}"
        else:
            entity_text = "Financial markets"
        
        # Format event type
        type_map = {
            "market_movement": "Market Movement",
            "company_financial": "Financial Results",
            "merger_acquisition": "Merger & Acquisition",
            "corporate_governance": "Corporate Governance",
            "regulatory_legal": "Regulatory/Legal",
            "debt_financing": "Debt Financing",
            "equity_financing": "Equity Financing",
            "dividend_capital_return": "Dividend & Capital Return",
            "economic_indicator": "Economic Indicator",
            "monetary_policy": "Monetary Policy",
            "fiscal_policy": "Fiscal Policy",
            "international_trade": "International Trade",
            "geopolitical": "Geopolitical",
            "technology_innovation": "Technology & Innovation",
            "commodity_price": "Commodity Price"
        }
        
        event_type_text = type_map.get(event_type, event_type.replace('_', ' ').title())
        
        # Create title
        title = f"{event_type_text} Event: {entity_text}"
        
        # Create description from first few news items
        description_parts = []
        used_titles = set()
        
        for news in sorted(news_items, key=lambda n: n.published_at, reverse=True)[:3]:
            if news.title not in used_titles:
                description_parts.append(news.title)
                used_titles.add(news.title)
        
        if description_parts:
            description = " | ".join(description_parts)
        else:
            description = f"Event involving {entity_text} related to {event_type_text.lower()}"
        
        return title, description
    
    def _determine_entity_role(self, entity, news_items: List) -> str:
        """
        Determine the role of an entity in an event.
        
        Args:
            entity: Entity object
            news_items: List of news items
            
        Returns:
            Entity role
        """
        # Default role
        role = "participant"
        
        # Count mention positions (subject vs object)
        subject_count = 0
        object_count = 0
        
        # Check entity mentions in news
        for news_id in [news.id for news in news_items]:
            for mention in entity.mentions:
                if mention.get('news_id') == news_id:
                    context = mention.get('context', '').lower()
                    
                    # Very simple heuristic - entity at beginning of sentence likely subject
                    sentences = re.split(r'[.!?]', context)
                    for sentence in sentences:
                        if entity.name.lower() in sentence.lower():
                            words = sentence.strip().split()
                            if words and entity.name.lower() in words[0].lower():
                                subject_count += 1
                            else:
                                object_count += 1
        
        # Determine role based on counts
        if subject_count > object_count:
            role = "main_actor"
        elif subject_count < object_count:
            role = "affected_entity"
        
        # Additional role determination based on entity type
        if entity.type == "PERSON" and entity.subtype == "Person":
            if "CEO" in entity.name or "Chief" in entity.name:
                role = "decision_maker"
        elif entity.type == "ORG":
            if entity.subtype in ["Regulator", "Central Bank", "Government"]:
                role = "regulator"
        
        return role
    
    def _add_event_entity_relationships(self, event, entities: List, news_items: List) -> None:
        """
        Add relationships between entities in this event.
        
        Args:
            event: Event object
            entities: List of entity objects
            news_items: List of news items
        """
        # Get all existing relationships between these entities
        entity_ids = [entity.id for entity in entities]
        relationships = self.data_store.get_relationships_between_entities(entity_ids)
        
        # Add relationships to event
        for rel in relationships:
            if rel.source_id in entity_ids and rel.target_id in entity_ids:
                event.add_relationship(rel.source_id, rel.target_id, rel.type)
        
        # Also add relationships from temporal ordering if applicable
        if len(entities) > 1:
            # Check for temporal mentions in news
            for i, entity1 in enumerate(entities):
                for j in range(i+1, len(entities)):
                    entity2 = entities[j]
                    
                    # Look for temporal patterns in news mentioning both entities
                    has_temporal = False
                    relation_type = None
                    
                    for news in news_items:
                        if entity1.id in news.entities and entity2.id in news.entities:
                            # Check for patterns like "before", "after", "following", etc.
                            text = f"{news.title} {news.content}".lower()
                            
                            e1_name = entity1.name.lower()
                            e2_name = entity2.name.lower()
                            
                            # Very simple pattern matching
                            if f"{e1_name}.*before.*{e2_name}" in text:
                                has_temporal = True
                                relation_type = "preceded"
                                break
                            elif f"{e1_name}.*after.*{e2_name}" in text:
                                has_temporal = True
                                relation_type = "followed"
                                break
                            elif f"{e1_name}.*following.*{e2_name}" in text:
                                has_temporal = True
                                relation_type = "followed"
                                break
                            elif f"{e1_name}.*led to.*{e2_name}" in text:
                                has_temporal = True
                                relation_type = "caused"
                                break
                            elif f"{e1_name}.*caused.*{e2_name}" in text:
                                has_temporal = True
                                relation_type = "caused"
                                break
                    
                    if has_temporal and relation_type:
                        event.add_relationship(entity1.id, entity2.id, relation_type)
    
    def _model_event_evolution(self) -> None:
        """
        Model evolution relationships between events across time.
        """
        # Get all events sorted by date
        all_events = self.data_store.get_all_events()
        sorted_events = sorted(all_events, key=lambda e: e.event_date)
        
        # Skip if very few events
        if len(sorted_events) < 2:
            return
        
        # Process each event and find related earlier events
        for i, event in enumerate(sorted_events):
            if i == 0:
                continue  # Skip first event (no prior events)
            
            # Look back at events up to 7 days before
            event_date = event.event_date
            week_before = event_date - timedelta(days=7)
            
            # Get potential predecessor events
            predecessors = [e for e in sorted_events[:i] if e.event_date >= week_before]
            
            for pred_event in predecessors:
                # Calculate event similarity based on shared entities
                similarity = self._calculate_event_similarity(event, pred_event)
                
                if similarity >= 0.3:  # Similarity threshold
                    # Determine relationship type
                    rel_type = self._determine_event_relationship_type(event, pred_event)
                    
                    # Create event evolution relationship in both events
                    event.attributes.setdefault("predecessors", []).append({
                        "event_id": pred_event.id,
                        "type": rel_type,
                        "similarity": similarity
                    })
                    
                    pred_event.attributes.setdefault("successors", []).append({
                        "event_id": event.id,
                        "type": rel_type,
                        "similarity": similarity
                    })
                    
                    # Save events
                    self.data_store.save_event(event)
                    self.data_store.save_event(pred_event)
    
    def _calculate_event_similarity(self, event1, event2) -> float:
        """
        Calculate similarity between two events.
        
        Args:
            event1: First event
            event2: Second event
            
        Returns:
            Similarity score (0-1)
        """
        # Calculate entity overlap
        entities1 = set(event1.entities)
        entities2 = set(event2.entities)
        
        entity_similarity = 0.0
        if entities1 and entities2:
            intersection = len(entities1.intersection(entities2))
            union = len(entities1.union(entities2))
            entity_similarity = intersection / union
        
        # Check event type similarity
        type_similarity = 1.0 if event1.event_type == event2.event_type else 0.0
        
        # Combine similarities with weights
        similarity = (0.7 * entity_similarity) + (0.3 * type_similarity)
        
        return similarity
    
    def _determine_event_relationship_type(self, later_event, earlier_event) -> str:
        """
        Determine the relationship type between two events.
        
        Args:
            later_event: The later occurring event
            earlier_event: The earlier occurring event
            
        Returns:
            Relationship type
        """
        # Default relationship
        rel_type = "follows"
        
        # Check if events have a causal relationship based on type
        cause_effect_pairs = {
            ("monetary_policy", "market_movement"): "causes",
            ("fiscal_policy", "market_movement"): "causes",
            ("economic_indicator", "market_movement"): "influences",
            ("geopolitical", "market_movement"): "triggers",
            ("commodity_price", "company_financial"): "impacts",
            ("regulatory_legal", "company_financial"): "affects",
            ("merger_acquisition", "market_movement"): "leads_to",
            ("company_financial", "market_movement"): "drives",
            ("international_trade", "commodity_price"): "affects",
            ("technology_innovation", "company_financial"): "enables"
        }
        
        # Check if the event types form a known cause-effect pair
        type_pair = (earlier_event.event_type, later_event.event_type)
        if type_pair in cause_effect_pairs:
            rel_type = cause_effect_pairs[type_pair]
        
        # Check if the events share many entities, suggesting continuous development
        entities1 = set(earlier_event.entities)
        entities2 = set(later_event.entities)
        
        if len(entities1.intersection(entities2)) > 0.7 * len(entities1):
            if earlier_event.event_type == later_event.event_type:
                rel_type = "continues"
            else:
                rel_type = "evolves_into"
        
        return rel_type
