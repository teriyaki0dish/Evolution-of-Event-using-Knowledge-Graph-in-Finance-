"""
Data models for the Financial Risk Knowledge Graph system.
These are the core structures that represent our domain model.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid


@dataclass
class Entity:
    """Entity model representing a financial entity in the knowledge graph."""
    id: str  # Unique identifier
    name: str  # Entity name
    type: str  # Entity type (Organization, Person, etc.)
    subtype: Optional[str] = None  # Financial subtype (Company, Bank, etc.)
    attributes: Dict[str, Any] = field(default_factory=dict)  # Additional attributes
    mentions: List[Dict[str, Any]] = field(default_factory=list)  # News mentions
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    @classmethod
    def create(cls, name: str, entity_type: str, subtype: Optional[str] = None, **attributes):
        """Factory method to create a new entity"""
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            type=entity_type,
            subtype=subtype,
            attributes=attributes,
            mentions=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def add_mention(self, news_id: str, context: str, confidence: float):
        """Add a news mention to this entity"""
        self.mentions.append({
            "news_id": news_id,
            "context": context,
            "confidence": confidence,
            "timestamp": datetime.now()
        })
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "subtype": self.subtype,
            "attributes": self.attributes,
            "mentions": self.mentions,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class Relationship:
    """Relationship model representing a connection between entities"""
    id: str  # Unique identifier
    source_id: str  # Source entity ID
    target_id: str  # Target entity ID
    type: str  # Relationship type
    attributes: Dict[str, Any] = field(default_factory=dict)  # Additional attributes
    confidence: float = 1.0  # Confidence score
    mentions: List[Dict[str, Any]] = field(default_factory=list)  # Evidence mentions
    created_at: datetime = field(default_factory=datetime.now)
    
    @classmethod
    def create(cls, source_id: str, target_id: str, rel_type: str, confidence: float = 1.0, **attributes):
        """Factory method to create a new relationship"""
        return cls(
            id=str(uuid.uuid4()),
            source_id=source_id,
            target_id=target_id,
            type=rel_type,
            attributes=attributes,
            confidence=confidence,
            mentions=[],
            created_at=datetime.now()
        )
    
    def add_mention(self, news_id: str, context: str):
        """Add evidence for this relationship from news"""
        self.mentions.append({
            "news_id": news_id,
            "context": context,
            "timestamp": datetime.now()
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "type": self.type,
            "attributes": self.attributes,
            "confidence": self.confidence,
            "mentions": self.mentions,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class NewsItem:
    """Model representing a news article"""
    id: str  # Unique identifier
    title: str  # News title
    content: str  # Full text content
    source: str  # News source
    url: str  # Original URL
    published_at: datetime  # Publication date
    entities: List[str] = field(default_factory=list)  # Referenced entity IDs
    events: List[str] = field(default_factory=list)  # Referenced event IDs
    processed: bool = False  # Processing status flag
    collected_at: datetime = field(default_factory=datetime.now)
    
    @classmethod
    def create(cls, title: str, content: str, source: str, url: str, published_at: datetime):
        """Factory method to create a new news item"""
        return cls(
            id=str(uuid.uuid4()),
            title=title,
            content=content,
            source=source,
            url=url,
            published_at=published_at,
            entities=[],
            events=[],
            processed=False,
            collected_at=datetime.now()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "source": self.source,
            "url": self.url,
            "published_at": self.published_at.isoformat(),
            "entities": self.entities,
            "events": self.events,
            "processed": self.processed,
            "collected_at": self.collected_at.isoformat()
        }


@dataclass
class Event:
    """Model representing a financial event in the knowledge graph"""
    id: str  # Unique identifier
    title: str  # Event title
    description: str  # Event description
    event_type: str  # Event type
    event_date: datetime  # When the event occurred
    entities: List[str] = field(default_factory=list)  # Involved entity IDs
    relationships: List[Dict[str, Any]] = field(default_factory=list)  # Entity relationships in this event
    news_sources: List[str] = field(default_factory=list)  # News source IDs
    attributes: Dict[str, Any] = field(default_factory=dict)  # Additional event attributes
    created_at: datetime = field(default_factory=datetime.now)
    
    @classmethod
    def create(cls, title: str, description: str, event_type: str, event_date: datetime):
        """Factory method to create a new event"""
        return cls(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            event_type=event_type,
            event_date=event_date,
            entities=[],
            relationships=[],
            news_sources=[],
            attributes={},
            created_at=datetime.now()
        )
    
    def add_entity(self, entity_id: str, role: str = "participant"):
        """Add an entity to this event with a specific role"""
        if entity_id not in self.entities:
            self.entities.append(entity_id)
            self.attributes.setdefault("entity_roles", {})[entity_id] = role
    
    def add_relationship(self, source_id: str, target_id: str, rel_type: str):
        """Add a relationship between entities in this event context"""
        self.relationships.append({
            "source_id": source_id,
            "target_id": target_id,
            "type": rel_type
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "event_type": self.event_type,
            "event_date": self.event_date.isoformat(),
            "entities": self.entities,
            "relationships": self.relationships,
            "news_sources": self.news_sources,
            "attributes": self.attributes,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class Risk:
    """Model representing a financial risk in the knowledge graph"""
    id: str  # Unique identifier
    title: str  # Risk title
    description: str  # Risk description
    risk_type: str  # Risk category/type
    severity: int  # Severity level (1-5)
    likelihood: float  # Probability (0.0-1.0)
    entities: List[str] = field(default_factory=list)  # Affected entity IDs
    events: List[str] = field(default_factory=list)  # Triggering event IDs
    related_risks: List[str] = field(default_factory=list)  # Related risk IDs
    impact_areas: List[str] = field(default_factory=list)  # Areas of impact
    attributes: Dict[str, Any] = field(default_factory=dict)  # Additional risk attributes
    created_at: datetime = field(default_factory=datetime.now)
    
    @classmethod
    def create(cls, title: str, description: str, risk_type: str, severity: int, likelihood: float):
        """Factory method to create a new risk"""
        return cls(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            risk_type=risk_type,
            severity=severity,
            likelihood=likelihood,
            entities=[],
            events=[],
            related_risks=[],
            impact_areas=[],
            attributes={},
            created_at=datetime.now()
        )
    
    def add_entity(self, entity_id: str, impact_level: float = 1.0):
        """Add an entity affected by this risk"""
        if entity_id not in self.entities:
            self.entities.append(entity_id)
            self.attributes.setdefault("entity_impacts", {})[entity_id] = impact_level
    
    def add_event(self, event_id: str, correlation: float = 1.0):
        """Add a triggering or related event"""
        if event_id not in self.events:
            self.events.append(event_id)
            self.attributes.setdefault("event_correlations", {})[event_id] = correlation
    
    def add_related_risk(self, risk_id: str, relationship_type: str = "contributes_to"):
        """Add a related risk with relationship type"""
        if risk_id not in self.related_risks:
            self.related_risks.append(risk_id)
            self.attributes.setdefault("risk_relationships", {})[risk_id] = relationship_type
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "risk_type": self.risk_type,
            "severity": self.severity,
            "likelihood": self.likelihood,
            "entities": self.entities,
            "events": self.events,
            "related_risks": self.related_risks,
            "impact_areas": self.impact_areas,
            "attributes": self.attributes,
            "created_at": self.created_at.isoformat()
        }
