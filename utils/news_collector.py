"""
News collection module for gathering financial news from various sources.
"""
import logging
import requests
import feedparser
from datetime import datetime
import time
import random
from typing import Dict, List, Any, Optional

# Setup logging
logger = logging.getLogger(__name__)

class NewsCollector:
    """
    Collects financial news articles from RSS feeds and APIs
    within a specified date range.
    """
    
    def __init__(self, data_store):
        """
        Initialize the news collector with a data store.
        
        Args:
            data_store: Data storage interface
        """
        self.data_store = data_store
        
    def collect_from_source(self, source_config: Dict[str, Any], 
                            start_date: datetime, end_date: datetime) -> List[str]:
        """
        Collect news from a specific source within the date range.
        
        Args:
            source_config: Source configuration dictionary
            start_date: Start date for news collection
            end_date: End date for news collection
            
        Returns:
            List of collected news IDs
        """
        logger.info(f"Collecting news from {source_config['name']} between {start_date} and {end_date}")
        
        collected_ids = []
        
        try:
            if source_config['type'] == 'rss':
                collected_ids = self._collect_from_rss(source_config, start_date, end_date)
            elif source_config['type'] == 'api':
                collected_ids = self._collect_from_api(source_config, start_date, end_date)
            else:
                logger.warning(f"Unsupported source type: {source_config['type']}")
                
            logger.info(f"Collected {len(collected_ids)} news items from {source_config['name']}")
            return collected_ids
            
        except Exception as e:
            logger.error(f"Error collecting news from {source_config['name']}: {e}")
            return []
    
    def _collect_from_rss(self, source_config: Dict[str, Any], 
                         start_date: datetime, end_date: datetime) -> List[str]:
        """
        Collect news from an RSS feed source.
        
        Args:
            source_config: RSS source configuration
            start_date: Start date for filtering
            end_date: End date for filtering
            
        Returns:
            List of collected news IDs
        """
        collected_ids = []
        
        # Parse the RSS feed
        feed = feedparser.parse(source_config['rss_url'])
        
        if feed.bozo:
            logger.warning(f"RSS feed error: {feed.bozo_exception}")
        
        # Process each entry
        for entry in feed.entries:
            try:
                # Parse published date
                if hasattr(entry, 'published_parsed'):
                    pub_date = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                elif hasattr(entry, 'updated_parsed'):
                    pub_date = datetime.fromtimestamp(time.mktime(entry.updated_parsed))
                else:
                    # If no date is available, use current time but mark as uncertain
                    pub_date = datetime.now()
                    logger.warning(f"No date found for entry {entry.title}, using current time")
                
                # Filter by date range
                if start_date <= pub_date <= end_date:
                    # Create news item
                    content = entry.summary if hasattr(entry, 'summary') else ''
                    
                    # If there's a longer content available, use it
                    if hasattr(entry, 'content'):
                        for content_item in entry.content:
                            if content_item.value and len(content_item.value) > len(content):
                                content = content_item.value
                    
                    # Extract URL
                    url = entry.link if hasattr(entry, 'link') else ''
                    
                    # Create and save news item
                    news_id = self._save_news_item(
                        title=entry.title,
                        content=content,
                        source=source_config['name'],
                        url=url,
                        published_at=pub_date
                    )
                    
                    if news_id:
                        collected_ids.append(news_id)
            
            except Exception as e:
                logger.error(f"Error processing RSS entry: {e}")
        
        return collected_ids
    
    def _collect_from_api(self, source_config: Dict[str, Any], 
                         start_date: datetime, end_date: datetime) -> List[str]:
        """
        Collect news from an API source.
        
        Args:
            source_config: API source configuration
            start_date: Start date for filtering
            end_date: End date for filtering
            
        Returns:
            List of collected news IDs
        """
        collected_ids = []
        
        # Handle specific API types
        if source_config['name'] == 'Alpha Vantage':
            collected_ids = self._collect_from_alpha_vantage(source_config, start_date, end_date)
        elif source_config['name'] == 'FRED Economic Data':
            collected_ids = self._collect_from_fred(source_config, start_date, end_date)
        elif source_config['name'] == 'SEC Edgar':
            collected_ids = self._collect_from_sec_edgar(source_config, start_date, end_date)
        else:
            logger.warning(f"Unsupported API source: {source_config['name']}")
        
        return collected_ids
    
    def _collect_from_alpha_vantage(self, source_config: Dict[str, Any], 
                                  start_date: datetime, end_date: datetime) -> List[str]:
        """
        Collect news from Alpha Vantage API.
        
        Args:
            source_config: Alpha Vantage API configuration
            start_date: Start date for filtering
            end_date: End date for filtering
            
        Returns:
            List of collected news IDs
        """
        collected_ids = []
        api_key = source_config.get('api_key', '')
        
        if not api_key:
            logger.warning("Alpha Vantage API key not provided")
            return []
        
        # Define major market indices to track news for
        tickers = ['SPY', 'QQQ', 'DIA', 'IWM', 'VGK', 'EEM', 'GLD', 'TLT']
        
        for ticker in tickers:
            try:
                # Make API request for news sentiment
                url = f"{source_config['api_url']}?function=NEWS_SENTIMENT&tickers={ticker}&apikey={api_key}"
                response = requests.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Process each news item
                    feed = data.get('feed', [])
                    for item in feed:
                        try:
                            # Parse the time
                            time_published = item.get('time_published', '')
                            if time_published:
                                # Format is typically YYYYMMDDTHHMMSS
                                pub_date = datetime.strptime(time_published, '%Y%m%dT%H%M%S')
                            else:
                                pub_date = datetime.now()
                            
                            # Filter by date range
                            if start_date <= pub_date <= end_date:
                                # Save the news item
                                news_id = self._save_news_item(
                                    title=item.get('title', 'Untitled'),
                                    content=item.get('summary', ''),
                                    source=f"Alpha Vantage ({item.get('source', 'unknown')})",
                                    url=item.get('url', ''),
                                    published_at=pub_date
                                )
                                
                                if news_id:
                                    collected_ids.append(news_id)
                        
                        except Exception as e:
                            logger.error(f"Error processing Alpha Vantage news item: {e}")
                
                else:
                    logger.warning(f"Alpha Vantage API request failed: {response.status_code}")
                
                # Respect API rate limits
                time.sleep(12)  # Alpha Vantage free tier limits: 5 requests per minute
            
            except Exception as e:
                logger.error(f"Error collecting news from Alpha Vantage for {ticker}: {e}")
        
        return collected_ids
    
    def _collect_from_fred(self, source_config: Dict[str, Any], 
                          start_date: datetime, end_date: datetime) -> List[str]:
        """
        Collect economic data releases from FRED API.
        
        Args:
            source_config: FRED API configuration
            start_date: Start date for filtering
            end_date: End date for filtering
            
        Returns:
            List of collected news IDs
        """
        collected_ids = []
        api_key = source_config.get('api_key', '')
        
        if not api_key:
            logger.warning("FRED API key not provided")
            return []
        
        try:
            # Convert dates to FRED format (YYYY-MM-DD)
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            
            # Get economic data releases in the specified date range
            url = f"{source_config['api_url']}releases?api_key={api_key}&file_type=json&realtime_start={start_str}&realtime_end={end_str}"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                releases = data.get('releases', [])
                
                for release in releases:
                    try:
                        release_id = release.get('id')
                        
                        # Get details for each release
                        detail_url = f"{source_config['api_url']}release?release_id={release_id}&api_key={api_key}&file_type=json"
                        detail_response = requests.get(detail_url)
                        
                        if detail_response.status_code == 200:
                            release_data = detail_response.json().get('releases', [{}])[0]
                            
                            # Get the release date
                            release_date_str = release.get('date', '')
                            if release_date_str:
                                release_date = datetime.strptime(release_date_str, '%Y-%m-%d')
                            else:
                                release_date = datetime.now()
                            
                            # Create content from release details
                            name = release_data.get('name', 'Economic Data Release')
                            notes = release_data.get('notes', '')
                            press_release = release_data.get('press_release', '')
                            
                            content = f"{notes}\n\n{press_release}"
                            
                            # Save as news item
                            news_id = self._save_news_item(
                                title=f"FRED: {name}",
                                content=content,
                                source="FRED Economic Data",
                                url=f"https://fred.stlouisfed.org/releases/show/{release_id}",
                                published_at=release_date
                            )
                            
                            if news_id:
                                collected_ids.append(news_id)
                        
                        # Respect API rate limits
                        time.sleep(0.5)
                    
                    except Exception as e:
                        logger.error(f"Error processing FRED release: {e}")
            
            else:
                logger.warning(f"FRED API request failed: {response.status_code}")
        
        except Exception as e:
            logger.error(f"Error collecting data from FRED: {e}")
        
        return collected_ids
    
    def _collect_from_sec_edgar(self, source_config: Dict[str, Any], 
                               start_date: datetime, end_date: datetime) -> List[str]:
        """
        Collect SEC filing information from EDGAR.
        
        Args:
            source_config: SEC EDGAR configuration
            start_date: Start date for filtering
            end_date: End date for filtering
            
        Returns:
            List of collected news IDs
        """
        collected_ids = []
        
        try:
            # Convert dates to YYYYMMDD format
            start_str = start_date.strftime('%Y%m%d')
            end_str = end_date.strftime('%Y%m%d')
            
            # List of important form types to monitor
            form_types = ['8-K', '10-K', '10-Q', '6-K', 'S-1', 'S-4', 'SC 13D']
            
            for form_type in form_types:
                # Build parameters for EDGAR search
                params = {
                    'action': 'getcompany',
                    'owner': 'exclude',
                    'type': form_type,
                    'dateb': end_str,
                    'datea': start_str,
                    'output': 'atom',
                    'count': 100
                }
                
                # Add a user agent to comply with SEC's policies
                headers = {
                    'User-Agent': 'FinancialRiskKG Research Agent (github.com/financial-risk-kg)'
                }
                
                # Make request to EDGAR
                response = requests.get(source_config['api_url'], params=params, headers=headers)
                
                if response.status_code == 200:
                    # Parse response as feed
                    feed = feedparser.parse(response.content)
                    
                    for entry in feed.entries:
                        try:
                            # Get filing details
                            title = entry.title if hasattr(entry, 'title') else f"SEC Filing: {form_type}"
                            
                            # Parse the filing date
                            if hasattr(entry, 'filing-date'):
                                filing_date = datetime.strptime(entry['filing-date'], '%Y-%m-%d')
                            elif hasattr(entry, 'updated_parsed'):
                                filing_date = datetime.fromtimestamp(time.mktime(entry.updated_parsed))
                            else:
                                filing_date = datetime.now()
                            
                            # Get company details
                            company = entry.get('company-name', '')
                            if company:
                                title = f"{company} - {title}"
                            
                            # Build content from filing details
                            content_parts = []
                            
                            if hasattr(entry, 'summary'):
                                content_parts.append(entry.summary)
                            
                            if hasattr(entry, 'filing-type'):
                                content_parts.append(f"Filing Type: {entry['filing-type']}")
                            
                            if hasattr(entry, 'company-name'):
                                content_parts.append(f"Company: {entry['company-name']}")
                            
                            if hasattr(entry, 'cik'):
                                content_parts.append(f"CIK: {entry['cik']}")
                            
                            # Get the filing URL
                            url = entry.link if hasattr(entry, 'link') else ''
                            
                            # Save as news item
                            news_id = self._save_news_item(
                                title=title,
                                content="\n\n".join(content_parts),
                                source="SEC EDGAR",
                                url=url,
                                published_at=filing_date
                            )
                            
                            if news_id:
                                collected_ids.append(news_id)
                        
                        except Exception as e:
                            logger.error(f"Error processing SEC EDGAR entry: {e}")
                
                else:
                    logger.warning(f"SEC EDGAR request failed: {response.status_code}")
                
                # Respect SEC EDGAR rate limits
                time.sleep(0.1)
        
        except Exception as e:
            logger.error(f"Error collecting from SEC EDGAR: {e}")
        
        return collected_ids
    
    def _save_news_item(self, title: str, content: str, source: str, 
                       url: str, published_at: datetime) -> Optional[str]:
        """
        Create and save a news item to the data store.
        
        Args:
            title: News title
            content: News content
            source: News source name
            url: Source URL
            published_at: Publication date
            
        Returns:
            News ID if saved successfully, None otherwise
        """
        try:
            # Check for duplicate news based on URL or title
            existing_news = self.data_store.find_news_by_url(url)
            
            if existing_news:
                logger.info(f"Skipping duplicate news: {title}")
                return existing_news.id
            
            # Create new news item
            from models import NewsItem
            news_item = NewsItem.create(
                title=title,
                content=content,
                source=source,
                url=url,
                published_at=published_at
            )
            
            # Save to data store
            self.data_store.save_news(news_item)
            
            return news_item.id
        
        except Exception as e:
            logger.error(f"Error saving news item: {e}")
            return None
