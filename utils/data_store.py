"""
Data storage module for the Financial Risk Knowledge Graph system.
"""
import logging
import json
import os
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import copy

# Setup logging
logger = logging.getLogger(__name__)

class DataStore:
    """
    Handles data persistence using JSON files.
    """
    
    def __init__(self, entity_file: str, event_file: str, risk_file: str, 
                news_file: str, graph_file: str):
        """
        Initialize the data store with file paths.
        
        Args:
            entity_file: Path to entities JSON file
            event_file: Path to events JSON file
            risk_file: Path to risks JSON file
            news_file: Path to news JSON file
            graph_file: Path to graph JSON file
        """
        self.entity_file = entity_file
        self.event_file = event_file
        self.risk_file = risk_file
        self.news_file = news_file
        self.graph_file = graph_file
        
        # In-memory data cache
        self.entities = {}
        self.events = {}
        self.risks = {}
        self.news = {}
        self.relationships = {}
        
        # Create data directory if it doesn't exist
        for file_path in [entity_file, event_file, risk_file, news_file, graph_file]:
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
        
        # Load data if files exist
        self._load_data()
    
    def _load_data(self) -> None:
        """
        Load data from JSON files into memory.
        """
        # Load entities
        self._load_entities()
        
        # Load relationships
        # (stored alongside entities)
        
        # Load events
        self._load_events()
        
        # Load risks
        self._load_risks()
        
        # Load news
        self._load_news()
        
        logger.info(f"Loaded data: {len(self.entities)} entities, {len(self.relationships)} relationships, "
                  f"{len(self.events)} events, {len(self.risks)} risks, {len(self.news)} news items")
    
    def _load_entities(self) -> None:
        """
        Load entities from JSON file.
        """
        self.entities = {}
        self.relationships = {}
        
        if os.path.exists(self.entity_file):
            try:
                with open(self.entity_file, 'r') as f:
                    data = json.load(f)
                
                # Handle different data formats for entities
                entities_to_process = []
                relationships_to_process = []
                
                if isinstance(data, dict):
                    # Format: {"entities": [...], "relationships": [...]}
                    if "entities" in data:
                        entities_to_process = data["entities"]
                    if "relationships" in data:
                        relationships_to_process = data["relationships"]
                elif isinstance(data, list):
                    # Format: [...]
                    entities_to_process = data
                    
                # Process each entity
                for entity_data in entities_to_process:
                    if not isinstance(entity_data, dict):
                        continue
                        
                    entity_id = entity_data.get("id")
                    if entity_id:
                        # Convert JSON data to Entity object
                        from models import Entity
                        try:
                            entity = Entity(
                                id=entity_data["id"],
                                name=entity_data["name"],
                                type=entity_data["type"],
                                subtype=entity_data.get("subtype"),
                                attributes=entity_data.get("attributes", {}),
                                mentions=entity_data.get("mentions", []),
                                created_at=datetime.fromisoformat(entity_data.get("created_at", datetime.now().isoformat())),
                                updated_at=datetime.fromisoformat(entity_data.get("updated_at", datetime.now().isoformat()))
                            )
                            self.entities[entity_id] = entity
                        except KeyError as ke:
                            logger.warning(f"Missing required field in entity data: {ke}")
                        except ValueError as ve:
                            logger.warning(f"Invalid value in entity data: {ve}")
                
                # Process each relationship
                for rel_data in relationships_to_process:
                    if not isinstance(rel_data, dict):
                        continue
                        
                    rel_id = rel_data.get("id")
                    if rel_id:
                        # Convert JSON data to Relationship object
                        from models import Relationship
                        try:
                            relationship = Relationship(
                                id=rel_data["id"],
                                source_id=rel_data["source_id"],
                                target_id=rel_data["target_id"],
                                type=rel_data["type"],
                                attributes=rel_data.get("attributes", {}),
                                confidence=rel_data.get("confidence", 1.0),
                                mentions=rel_data.get("mentions", []),
                                created_at=datetime.fromisoformat(rel_data.get("created_at", datetime.now().isoformat()))
                            )
                            self.relationships[rel_id] = relationship
                        except KeyError as ke:
                            logger.warning(f"Missing required field in relationship data: {ke}")
                        except ValueError as ve:
                            logger.warning(f"Invalid value in relationship data: {ve}")
            
            except Exception as e:
                logger.error(f"Error loading entities: {e}")
    
    def _load_events(self) -> None:
        """
        Load events from JSON file.
        """
        self.events = {}
        
        if os.path.exists(self.event_file):
            try:
                with open(self.event_file, 'r') as f:
                    data = json.load(f)
                
                # Handle different data formats
                events_to_process = []
                if isinstance(data, dict) and "events" in data:
                    # Format: {"events": [...]}
                    events_to_process = data["events"]
                elif isinstance(data, list):
                    # Format: [...]
                    events_to_process = data
                
                # Process each event
                for event_data in events_to_process:
                    if not isinstance(event_data, dict):
                        continue
                        
                    event_id = event_data.get("id")
                    if event_id:
                        # Convert JSON data to Event object
                        from models import Event
                        try:
                            event = Event(
                                id=event_data["id"],
                                title=event_data["title"],
                                description=event_data["description"],
                                event_type=event_data["event_type"],
                                event_date=datetime.fromisoformat(event_data["event_date"]),
                                entities=event_data.get("entities", []),
                                relationships=event_data.get("relationships", []),
                                news_sources=event_data.get("news_sources", []),
                                attributes=event_data.get("attributes", {}),
                                created_at=datetime.fromisoformat(event_data.get("created_at", datetime.now().isoformat()))
                            )
                            self.events[event_id] = event
                        except KeyError as ke:
                            logger.warning(f"Missing required field in event data: {ke}")
                        except ValueError as ve:
                            logger.warning(f"Invalid value in event data: {ve}")
            
            except Exception as e:
                logger.error(f"Error loading events: {e}")
    
    def _load_risks(self) -> None:
        """
        Load risks from JSON file.
        """
        self.risks = {}
        
        if os.path.exists(self.risk_file):
            try:
                with open(self.risk_file, 'r') as f:
                    data = json.load(f)
                
                # Handle different data formats
                risks_to_process = []
                if isinstance(data, dict) and "risks" in data:
                    # Format: {"risks": [...]}
                    risks_to_process = data["risks"]
                elif isinstance(data, list):
                    # Format: [...]
                    risks_to_process = data
                
                # Process each risk
                for risk_data in risks_to_process:
                    if not isinstance(risk_data, dict):
                        continue
                        
                    risk_id = risk_data.get("id")
                    if risk_id:
                        # Convert JSON data to Risk object
                        from models import Risk
                        try:
                            risk = Risk(
                                id=risk_data["id"],
                                title=risk_data["title"],
                                description=risk_data["description"],
                                risk_type=risk_data["risk_type"],
                                severity=risk_data["severity"],
                                likelihood=risk_data["likelihood"],
                                entities=risk_data.get("entities", []),
                                events=risk_data.get("events", []),
                                related_risks=risk_data.get("related_risks", []),
                                impact_areas=risk_data.get("impact_areas", []),
                                attributes=risk_data.get("attributes", {}),
                                created_at=datetime.fromisoformat(risk_data.get("created_at", datetime.now().isoformat()))
                            )
                            self.risks[risk_id] = risk
                        except KeyError as ke:
                            logger.warning(f"Missing required field in risk data: {ke}")
                        except ValueError as ve:
                            logger.warning(f"Invalid value in risk data: {ve}")
            
            except Exception as e:
                logger.error(f"Error loading risks: {e}")
    
    def _load_news(self) -> None:
        """
        Load news items from JSON file.
        """
        self.news = {}
        
        if os.path.exists(self.news_file):
            try:
                with open(self.news_file, 'r') as f:
                    data = json.load(f)
                
                # Handle different data formats
                news_to_process = []
                if isinstance(data, dict) and "news" in data:
                    # Format: {"news": [...]}
                    news_to_process = data["news"]
                elif isinstance(data, list):
                    # Format: [...]
                    news_to_process = data
                
                # Process each news item
                for news_data in news_to_process:
                    if not isinstance(news_data, dict):
                        continue
                        
                    news_id = news_data.get("id")
                    if news_id:
                        # Convert JSON data to NewsItem object
                        from models import NewsItem
                        try:
                            news_item = NewsItem(
                                id=news_data["id"],
                                title=news_data["title"],
                                content=news_data["content"],
                                source=news_data["source"],
                                url=news_data["url"],
                                published_at=datetime.fromisoformat(news_data["published_at"]),
                                entities=news_data.get("entities", []),
                                events=news_data.get("events", []),
                                processed=news_data.get("processed", False),
                                collected_at=datetime.fromisoformat(news_data.get("collected_at", datetime.now().isoformat()))
                            )
                            self.news[news_id] = news_item
                        except KeyError as ke:
                            logger.warning(f"Missing required field in news data: {ke}")
                        except ValueError as ve:
                            logger.warning(f"Invalid value in news data: {ve}")
            
            except Exception as e:
                logger.error(f"Error loading news: {e}")
    
    def _save_entities(self) -> None:
        """
        Save entities and relationships to JSON file.
        """
        try:
            # Convert entities and relationships to dictionaries
            entity_dicts = [entity.to_dict() for entity in self.entities.values()]
            relationship_dicts = [rel.to_dict() for rel in self.relationships.values()]
            
            # Create data structure
            data = {
                "entities": entity_dicts,
                "relationships": relationship_dicts
            }
            
            # Save to file
            with open(self.entity_file, 'w') as f:
                json.dump(data, f, indent=2)
        
        except Exception as e:
            logger.error(f"Error saving entities: {e}")
    
    def _save_events(self) -> None:
        """
        Save events to JSON file.
        """
        try:
            # Convert events to dictionaries
            event_dicts = [event.to_dict() for event in self.events.values()]
            
            # Create data structure
            data = {
                "events": event_dicts
            }
            
            # Save to file
            with open(self.event_file, 'w') as f:
                json.dump(data, f, indent=2)
        
        except Exception as e:
            logger.error(f"Error saving events: {e}")
    
    def _save_risks(self) -> None:
        """
        Save risks to JSON file.
        """
        try:
            # Convert risks to dictionaries
            risk_dicts = [risk.to_dict() for risk in self.risks.values()]
            
            # Create data structure
            data = {
                "risks": risk_dicts
            }
            
            # Save to file
            with open(self.risk_file, 'w') as f:
                json.dump(data, f, indent=2)
        
        except Exception as e:
            logger.error(f"Error saving risks: {e}")
    
    def _save_news(self) -> None:
        """
        Save news items to JSON file.
        """
        try:
            # Convert news items to dictionaries
            news_dicts = [news.to_dict() for news in self.news.values()]
            
            # Create data structure
            data = {
                "news": news_dicts
            }
            
            # Save to file
            with open(self.news_file, 'w') as f:
                json.dump(data, f, indent=2)
        
        except Exception as e:
            logger.error(f"Error saving news: {e}")
    
    # Entity methods
    
    def save_entity(self, entity) -> None:
        """
        Save an entity to the data store.
        
        Args:
            entity: Entity object to save
        """
        # Update entity in memory
        self.entities[entity.id] = entity
        
        # Save to file
        self._save_entities()
    
    def get_entity(self, entity_id: str) -> Optional[Any]:
        """
        Get an entity by ID.
        
        Args:
            entity_id: Entity ID
            
        Returns:
            Entity object or None if not found
        """
        return self.entities.get(entity_id)
    
    def get_all_entities(self) -> List[Any]:
        """
        Get all entities.
        
        Returns:
            List of all entity objects
        """
        return list(self.entities.values())
    
    def find_entity_by_name(self, name: str) -> Optional[Any]:
        """
        Find an entity by name (case-insensitive).
        
        Args:
            name: Entity name to search for
            
        Returns:
            Entity object or None if not found
        """
        name_lower = name.lower()
        for entity in self.entities.values():
            if entity.name.lower() == name_lower:
                return entity
        return None
    
    def get_top_entities(self, limit: int = 10) -> List[Any]:
        """
        Get top entities by mention count.
        
        Args:
            limit: Maximum number of entities to return
            
        Returns:
            List of top entity objects
        """
        sorted_entities = sorted(self.entities.values(), key=lambda e: len(e.mentions), reverse=True)
        return sorted_entities[:limit]
    
    # Relationship methods
    
    def save_relationship(self, relationship) -> None:
        """
        Save a relationship to the data store.
        
        Args:
            relationship: Relationship object to save
        """
        # Update relationship in memory
        self.relationships[relationship.id] = relationship
        
        # Save to file
        self._save_entities()
    
    def get_relationship(self, relationship_id: str) -> Optional[Any]:
        """
        Get a relationship by ID.
        
        Args:
            relationship_id: Relationship ID
            
        Returns:
            Relationship object or None if not found
        """
        return self.relationships.get(relationship_id)
    
    def get_all_relationships(self) -> List[Any]:
        """
        Get all relationships.
        
        Returns:
            List of all relationship objects
        """
        return list(self.relationships.values())
    
    def get_relationships_between_entities(self, entity_ids: List[str]) -> List[Any]:
        """
        Get relationships between a set of entities.
        
        Args:
            entity_ids: List of entity IDs
            
        Returns:
            List of relationship objects
        """
        entity_ids_set = set(entity_ids)
        return [r for r in self.relationships.values() 
                if r.source_id in entity_ids_set and r.target_id in entity_ids_set]
    
    # Event methods
    
    def save_event(self, event) -> None:
        """
        Save an event to the data store.
        
        Args:
            event: Event object to save
        """
        # Update event in memory
        self.events[event.id] = event
        
        # Save to file
        self._save_events()
    
    def get_event(self, event_id: str) -> Optional[Any]:
        """
        Get an event by ID.
        
        Args:
            event_id: Event ID
            
        Returns:
            Event object or None if not found
        """
        return self.events.get(event_id)
    
    def get_all_events(self) -> List[Any]:
        """
        Get all events.
        
        Returns:
            List of all event objects
        """
        return list(self.events.values())
    
    def get_recent_events(self, limit: int = 5) -> List[Any]:
        """
        Get most recent events by date.
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List of recent event objects
        """
        sorted_events = sorted(self.events.values(), key=lambda e: e.event_date, reverse=True)
        return sorted_events[:limit]
    
    # Risk methods
    
    def save_risk(self, risk) -> None:
        """
        Save a risk to the data store.
        
        Args:
            risk: Risk object to save
        """
        # Update risk in memory
        self.risks[risk.id] = risk
        
        # Save to file
        self._save_risks()
    
    def get_risk(self, risk_id: str) -> Optional[Any]:
        """
        Get a risk by ID.
        
        Args:
            risk_id: Risk ID
            
        Returns:
            Risk object or None if not found
        """
        return self.risks.get(risk_id)
    
    def get_all_risks(self) -> List[Any]:
        """
        Get all risks.
        
        Returns:
            List of all risk objects
        """
        return list(self.risks.values())
    
    def get_top_risks(self, limit: int = 5) -> List[Any]:
        """
        Get top risks by severity and likelihood.
        
        Args:
            limit: Maximum number of risks to return
            
        Returns:
            List of top risk objects
        """
        sorted_risks = sorted(self.risks.values(), 
                             key=lambda r: (r.severity, r.likelihood), reverse=True)
        return sorted_risks[:limit]
    
    # News methods
    
    def save_news(self, news) -> None:
        """
        Save a news item to the data store.
        
        Args:
            news: NewsItem object to save
        """
        # Update news in memory
        self.news[news.id] = news
        
        # Save to file
        self._save_news()
    
    def get_news(self, news_id: str) -> Optional[Any]:
        """
        Get a news item by ID.
        
        Args:
            news_id: News ID
            
        Returns:
            NewsItem object or None if not found
        """
        return self.news.get(news_id)
    
    def get_all_news(self) -> List[Any]:
        """
        Get all news items.
        
        Returns:
            List of all news item objects
        """
        return list(self.news.values())
    
    def get_unprocessed_news(self) -> List[Any]:
        """
        Get unprocessed news items.
        
        Returns:
            List of unprocessed news item objects
        """
        return [n for n in self.news.values() if not n.processed]
    
    def get_processed_news(self) -> List[Any]:
        """
        Get processed news items.
        
        Returns:
            List of processed news item objects
        """
        return [n for n in self.news.values() if n.processed]
    
    def find_news_by_url(self, url: str) -> Optional[Any]:
        """
        Find a news item by URL.
        
        Args:
            url: News URL to search for
            
        Returns:
            NewsItem object or None if not found
        """
        for news in self.news.values():
            if news.url == url:
                return news
        return None
