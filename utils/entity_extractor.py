"""
Entity extraction module for identifying financial entities in news articles.
"""
import logging
import spacy
from typing import List, Dict, Any, Tuple, Set
import re

# Setup logging
logger = logging.getLogger(__name__)

class EntityExtractor:
    """
    Extracts entities from financial news using NLP techniques.
    """
    
    def __init__(self, data_store):
        """
        Initialize the entity extractor with data store.
        
        Args:
            data_store: Data storage interface
        """
        self.data_store = data_store
        
        # Load spaCy NLP model
        try:
            self.nlp = spacy.load("en_core_web_lg")
        except OSError:
            logger.warning("Could not load en_core_web_lg. Downloading...")
            spacy.cli.download("en_core_web_lg")
            self.nlp = spacy.load("en_core_web_lg")
        
        # Financial entity patterns to enhance spaCy's NER
        financial_patterns = [
            {"label": "ORG", "pattern": [{"LOWER": {"IN": ["fed", "federal", "reserve"]}}, {"LOWER": "bank"}]},
            {"label": "ORG", "pattern": [{"LOWER": "treasury"}]},
            {"label": "ORG", "pattern": [{"LOWER": "sec"}]},
            {"label": "ORG", "pattern": [{"LOWER": "cftc"}]},
            {"label": "ORG", "pattern": [{"LOWER": "imf"}]},
            {"label": "ORG", "pattern": [{"LOWER": "world"}, {"LOWER": "bank"}]},
            {"label": "ORG", "pattern": [{"LOWER": "ecb"}]},
            {"label": "ORG", "pattern": [{"LOWER": "european"}, {"LOWER": "central"}, {"LOWER": "bank"}]},
            {"label": "ORG", "pattern": [{"LOWER": "bank"}, {"LOWER": "of"}, {"LOWER": "england"}]},
            {"label": "ORG", "pattern": [{"LOWER": "bank"}, {"LOWER": "of"}, {"LOWER": "japan"}]},
            {"label": "ORG", "pattern": [{"LOWER": "people's"}, {"LOWER": "bank"}, {"LOWER": "of"}, {"LOWER": "china"}]},
            {"label": "ORG", "pattern": [{"LOWER": "basel"}, {"LOWER": "committee"}]},
            {"label": "PRODUCT", "pattern": [{"LOWER": "s&p"}, {"LOWER": "500"}]},
            {"label": "PRODUCT", "pattern": [{"LOWER": "dow"}, {"LOWER": "jones"}]},
            {"label": "PRODUCT", "pattern": [{"LOWER": "nasdaq"}, {"LOWER": "composite"}]},
            {"label": "PRODUCT", "pattern": [{"LOWER": "russell"}, {"LOWER": "2000"}]},
            {"label": "PRODUCT", "pattern": [{"LOWER": "ftse"}, {"LOWER": "100"}]},
            {"label": "PRODUCT", "pattern": [{"LOWER": "nikkei"}, {"LOWER": "225"}]},
            {"label": "PRODUCT", "pattern": [{"LOWER": "dax"}]},
            {"label": "PRODUCT", "pattern": [{"LOWER": "cac"}, {"LOWER": "40"}]},
            {"label": "PRODUCT", "pattern": [{"LOWER": "hang"}, {"LOWER": "seng"}]},
            {"label": "PRODUCT", "pattern": [{"LOWER": "vix"}]},
            {"label": "PRODUCT", "pattern": [{"LOWER": "libor"}]},
            {"label": "PRODUCT", "pattern": [{"LOWER": "euribor"}]},
            {"label": "PRODUCT", "pattern": [{"LOWER": "treasury"}, {"LOWER": "bond"}]},
            {"label": "PRODUCT", "pattern": [{"LOWER": "brent"}, {"LOWER": "crude"}]},
            {"label": "PRODUCT", "pattern": [{"LOWER": "wti"}, {"LOWER": "crude"}]},
            {"label": "PRODUCT", "pattern": [{"LOWER": "natural"}, {"LOWER": "gas"}]},
            {"label": "PRODUCT", "pattern": [{"LOWER": "gold"}]},
            {"label": "PRODUCT", "pattern": [{"LOWER": "silver"}]},
            {"label": "PRODUCT", "pattern": [{"LOWER": "bitcoin"}]},
            {"label": "PRODUCT", "pattern": [{"LOWER": "ethereum"}]},
            {"label": "EVENT", "pattern": [{"LOWER": "market"}, {"LOWER": "crash"}]},
            {"label": "EVENT", "pattern": [{"LOWER": "financial"}, {"LOWER": "crisis"}]},
            {"label": "EVENT", "pattern": [{"LOWER": "bankruptcy"}]},
            {"label": "EVENT", "pattern": [{"LOWER": "default"}]},
            {"label": "EVENT", "pattern": [{"LOWER": "merger"}]},
            {"label": "EVENT", "pattern": [{"LOWER": "acquisition"}]},
            {"label": "EVENT", "pattern": [{"LOWER": "ipo"}]},
            {"label": "EVENT", "pattern": [{"LOWER": "earnings"}, {"LOWER": "report"}]},
            {"label": "EVENT", "pattern": [{"LOWER": "rate"}, {"LOWER": "hike"}]},
            {"label": "EVENT", "pattern": [{"LOWER": "rate"}, {"LOWER": "cut"}]},
            {"label": "EVENT", "pattern": [{"LOWER": "inflation"}, {"LOWER": "report"}]},
            {"label": "EVENT", "pattern": [{"LOWER": "gdp"}, {"LOWER": "release"}]},
            {"label": "EVENT", "pattern": [{"LOWER": "unemployment"}, {"LOWER": "data"}]},
            {"label": "EVENT", "pattern": [{"LOWER": "stock"}, {"LOWER": "split"}]},
            {"label": "LAW", "pattern": [{"LOWER": "dodd"}, {"LOWER": "frank"}, {"LOWER": "act"}]},
            {"label": "LAW", "pattern": [{"LOWER": "basel"}, {"LOWER": "iii"}]},
            {"label": "LAW", "pattern": [{"LOWER": "sarbanes"}, {"LOWER": "oxley"}]},
            {"label": "LAW", "pattern": [{"LOWER": "mifid"}, {"LOWER": "ii"}]},
            {"label": "LAW", "pattern": [{"LOWER": "regulation"}, {"IS_ALPHA": True}]},
        ]
        
        # Add patterns to NLP pipeline
        from spacy.pipeline import EntityRuler
        self.ruler = EntityRuler(self.nlp, patterns=financial_patterns, overwrite_ents=True)
        self.nlp.add_pipe("entity_ruler", before="ner")
        
        # Financial ticker pattern
        self.ticker_pattern = re.compile(r'\b[A-Z]{1,5}\b(?!\d)')
        
        # Financial entity subtypes mapping
        self.entity_subtypes = {
            # Regulators and Government Institutions
            "SEC": "Regulator",
            "Federal Reserve": "Central Bank",
            "Treasury": "Government",
            "CFTC": "Regulator",
            "FCA": "Regulator",
            "ECB": "Central Bank",
            "IMF": "International Organization",
            "World Bank": "International Organization",
            
            # Financial Market Infrastructure
            "NYSE": "Exchange",
            "NASDAQ": "Exchange",
            "LSE": "Exchange",
            "CME": "Exchange",
            "ICE": "Exchange",
            "CBOE": "Exchange",
            "Euronext": "Exchange",
            
            # Financial Indices
            "S&P 500": "Index",
            "Dow Jones": "Index",
            "NASDAQ Composite": "Index",
            "Russell 2000": "Index",
            "FTSE 100": "Index",
            "DAX": "Index",
            "Nikkei 225": "Index",
            "Hang Seng": "Index",
            "VIX": "Volatility Index",
            
            # Financial Products
            "Treasury Bond": "Government Bond",
            "Treasury Bill": "Government Bond",
            "Corporate Bond": "Corporate Bond", 
            "Municipal Bond": "Municipal Bond",
            "LIBOR": "Interest Rate Benchmark",
            "SOFR": "Interest Rate Benchmark",
            "EURIBOR": "Interest Rate Benchmark",
            "Gold": "Commodity",
            "Silver": "Commodity",
            "Crude Oil": "Commodity",
            "Natural Gas": "Commodity",
            "Bitcoin": "Cryptocurrency",
            "Ethereum": "Cryptocurrency",
            
            # Credit Rating Agencies
            "Moody's": "Rating Agency",
            "S&P Global": "Rating Agency",
            "Fitch Ratings": "Rating Agency",
            
            # Banking Types
            "JPMorgan": "Investment Bank",
            "Bank of America": "Commercial Bank",
            "Goldman Sachs": "Investment Bank",
            "Morgan Stanley": "Investment Bank",
            "Citigroup": "Commercial Bank",
            "Wells Fargo": "Commercial Bank",
            "HSBC": "Commercial Bank",
            "Deutsche Bank": "Investment Bank",
            "Barclays": "Investment Bank",
            "UBS": "Investment Bank",
            "Credit Suisse": "Investment Bank",
            
            # Insurance
            "AIG": "Insurance",
            "MetLife": "Insurance",
            "Prudential": "Insurance",
            "Allianz": "Insurance",
            
            # Asset Management
            "BlackRock": "Asset Manager",
            "Vanguard": "Asset Manager",
            "State Street": "Asset Manager",
            "Fidelity": "Asset Manager",
            
            # Technology and Fintech
            "PayPal": "Fintech",
            "Square": "Fintech",
            "Stripe": "Fintech",
            "Robinhood": "Fintech",
            "Coinbase": "Cryptocurrency Exchange",
            
            # Default subtypes by entity type
            "DEFAULT_ORG": "Company",
            "DEFAULT_PERSON": "Person",
            "DEFAULT_GPE": "Country",
            "DEFAULT_MONEY": "Currency",
            "DEFAULT_PERCENT": "Rate",
            "DEFAULT_PRODUCT": "Financial Product",
            "DEFAULT_EVENT": "Financial Event",
            "DEFAULT_LAW": "Regulation",
        }
        
    def extract_all_entities(self) -> List[str]:
        """
        Process all unprocessed news items to extract entities.
        
        Returns:
            List of entity IDs extracted
        """
        extracted_entity_ids = []
        
        # Get all unprocessed news items
        news_items = self.data_store.get_unprocessed_news()
        
        for news_item in news_items:
            try:
                # Extract entities from this news item
                entity_ids = self.extract_entities_from_news(news_item)
                extracted_entity_ids.extend(entity_ids)
                
                # Mark news as processed
                news_item.processed = True
                self.data_store.save_news(news_item)
                
                logger.info(f"Processed news item: {news_item.id}, extracted {len(entity_ids)} entities")
            
            except Exception as e:
                logger.error(f"Error extracting entities from news {news_item.id}: {e}")
        
        return extracted_entity_ids
    
    def extract_entities_from_news(self, news_item) -> List[str]:
        """
        Extract entities from a single news item.
        
        Args:
            news_item: News item object
            
        Returns:
            List of entity IDs extracted
        """
        entity_ids = []
        
        try:
            # Combine title and content for processing
            text = f"{news_item.title}\n\n{news_item.content}"
            
            # Process with spaCy
            doc = self.nlp(text)
            
            # Extract named entities
            entities = self._extract_named_entities(doc, news_item)
            
            # Extract financial tickers if not already captured
            ticker_entities = self._extract_financial_tickers(text, news_item)
            
            # Save all unique entities
            all_entities = entities + ticker_entities
            
            # Extract relationships between entities
            self._extract_entity_relationships(all_entities, doc, news_item)
            
            # Update news item with entity references
            news_item.entities = [entity.id for entity in all_entities]
            self.data_store.save_news(news_item)
            
            entity_ids = [entity.id for entity in all_entities]
        
        except Exception as e:
            logger.error(f"Error in entity extraction: {e}")
        
        return entity_ids
    
    def _extract_named_entities(self, doc, news_item) -> List[Any]:
        """
        Extract named entities from spaCy document.
        
        Args:
            doc: spaCy processed document
            news_item: News item being processed
            
        Returns:
            List of entity objects
        """
        entities = []
        entity_texts = set()  # Track to avoid duplicates
        
        # Process each named entity found by spaCy
        for ent in doc.ents:
            try:
                # Skip very short entities or punctuation-only entities
                if len(ent.text.strip()) < 2 or ent.text.strip().isdigit():
                    continue
                
                # Normalize entity text
                entity_text = ent.text.strip()
                
                # Skip if already processed this entity in this document
                if entity_text.lower() in entity_texts:
                    continue
                
                entity_texts.add(entity_text.lower())
                
                # Determine entity type and subtype
                entity_type = ent.label_
                entity_subtype = self._determine_entity_subtype(entity_text, entity_type)
                
                # Find or create entity
                entity = self.data_store.find_entity_by_name(entity_text)
                
                if not entity:
                    # Create new entity
                    from models import Entity
                    entity = Entity.create(
                        name=entity_text,
                        entity_type=entity_type,
                        subtype=entity_subtype
                    )
                
                # Add mention from this news item
                entity.add_mention(
                    news_id=news_item.id,
                    context=ent.sent.text if ent.sent else ent.text,
                    confidence=0.9  # Default confidence for spaCy entities
                )
                
                # Save entity
                self.data_store.save_entity(entity)
                entities.append(entity)
            
            except Exception as e:
                logger.error(f"Error processing entity {ent.text}: {e}")
        
        return entities
    
    def _extract_financial_tickers(self, text, news_item) -> List[Any]:
        """
        Extract potential stock tickers from text.
        
        Args:
            text: Text to process
            news_item: News item being processed
            
        Returns:
            List of entity objects for tickers
        """
        entities = []
        
        # Find all potential tickers (1-5 uppercase letters)
        potential_tickers = set(self.ticker_pattern.findall(text))
        
        # Filter out common acronyms not likely to be tickers
        common_acronyms = {"I", "A", "AN", "THE", "US", "UK", "EU", "UN", "CEO", "CFO", "CTO", "COO", "GDP", "CPI"}
        tickers = potential_tickers - common_acronyms
        
        for ticker in tickers:
            try:
                # Find or create entity for this ticker
                entity = self.data_store.find_entity_by_name(ticker)
                
                if not entity:
                    # Create new entity
                    from models import Entity
                    entity = Entity.create(
                        name=ticker,
                        entity_type="TICKER",
                        subtype="Stock Ticker"
                    )
                
                # Add mention from this news item
                entity.add_mention(
                    news_id=news_item.id,
                    context=f"Ticker symbol: {ticker}",
                    confidence=0.7  # Lower confidence for pattern-extracted tickers
                )
                
                # Save entity
                self.data_store.save_entity(entity)
                entities.append(entity)
            
            except Exception as e:
                logger.error(f"Error processing ticker {ticker}: {e}")
        
        return entities
    
    def _extract_entity_relationships(self, entities, doc, news_item) -> None:
        """
        Extract relationships between entities in the same document.
        
        Args:
            entities: List of entities found in the document
            doc: spaCy processed document
            news_item: News item being processed
        """
        # Skip if fewer than 2 entities
        if len(entities) < 2:
            return
        
        # Create a mapping of entity spans to entity objects
        entity_spans = {}
        for ent in doc.ents:
            entity_name = ent.text.strip()
            for entity in entities:
                if entity.name.lower() == entity_name.lower():
                    entity_spans[ent] = entity
                    break
        
        # Track processed entity pairs to avoid duplicates
        processed_pairs = set()
        
        # Extract relationships based on syntactic dependencies
        for sent in doc.sents:
            for token in sent:
                if token.dep_ in ('nsubj', 'nsubjpass') and token.head.pos_ == 'VERB':
                    # Find subject entity
                    subj_entity = None
                    for ent_span, entity in entity_spans.items():
                        if token.i >= ent_span.start and token.i < ent_span.end:
                            subj_entity = entity
                            break
                    
                    if not subj_entity:
                        continue
                    
                    # Find object entity connected to the same verb
                    for obj_token in token.head.children:
                        if obj_token.dep_ in ('dobj', 'pobj'):
                            obj_entity = None
                            for ent_span, entity in entity_spans.items():
                                if obj_token.i >= ent_span.start and obj_token.i < ent_span.end:
                                    obj_entity = entity
                                    break
                            
                            if not obj_entity or obj_entity.id == subj_entity.id:
                                continue
                            
                            # Define relationship based on the verb
                            relation_type = token.head.lemma_
                            
                            # Create a pair key to track processed pairs
                            pair_key = (subj_entity.id, obj_entity.id, relation_type)
                            if pair_key in processed_pairs:
                                continue
                            processed_pairs.add(pair_key)
                            
                            # Create relationship
                            from models import Relationship
                            relationship = Relationship.create(
                                source_id=subj_entity.id,
                                target_id=obj_entity.id,
                                rel_type=relation_type,
                                confidence=0.8
                            )
                            
                            # Add context from sentence
                            relationship.add_mention(
                                news_id=news_item.id,
                                context=sent.text
                            )
                            
                            # Save relationship
                            self.data_store.save_relationship(relationship)
        
        # Also create co-occurrence relationships for entities in the same sentence
        for sent in doc.sents:
            sent_entities = set()
            
            # Find entities in this sentence
            for ent_span, entity in entity_spans.items():
                if any(token.i >= ent_span.start and token.i < ent_span.end for token in sent):
                    sent_entities.add(entity)
            
            # Create co-occurrence relationships
            sent_entities = list(sent_entities)
            for i in range(len(sent_entities)):
                for j in range(i+1, len(sent_entities)):
                    # Create a pair key to track processed pairs
                    pair_key = (sent_entities[i].id, sent_entities[j].id, "co_occurs_with")
                    reverse_key = (sent_entities[j].id, sent_entities[i].id, "co_occurs_with")
                    
                    if pair_key in processed_pairs or reverse_key in processed_pairs:
                        continue
                    processed_pairs.add(pair_key)
                    
                    # Create relationship
                    from models import Relationship
                    relationship = Relationship.create(
                        source_id=sent_entities[i].id,
                        target_id=sent_entities[j].id,
                        rel_type="co_occurs_with",
                        confidence=0.6
                    )
                    
                    # Add context from sentence
                    relationship.add_mention(
                        news_id=news_item.id,
                        context=sent.text
                    )
                    
                    # Save relationship
                    self.data_store.save_relationship(relationship)
    
    def _determine_entity_subtype(self, entity_text, entity_type) -> str:
        """
        Determine the financial subtype of an entity.
        
        Args:
            entity_text: Entity text
            entity_type: Entity type from spaCy
            
        Returns:
            Entity subtype
        """
        # Check if we have a specific mapping for this entity
        if entity_text in self.entity_subtypes:
            return self.entity_subtypes[entity_text]
        
        # Check for partial matches in known entities
        for known_entity, subtype in self.entity_subtypes.items():
            if known_entity in entity_text:
                return subtype
        
        # Use default subtype based on entity type
        default_key = f"DEFAULT_{entity_type}"
        return self.entity_subtypes.get(default_key, "Other")
