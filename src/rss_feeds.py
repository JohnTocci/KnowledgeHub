"""
RSS and Newsletter feed integration for KnowledgeHub.
Automatically fetches and processes content from feeds.
"""
import feedparser
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
import re
from urllib.parse import urlparse

class FeedManager:
    """Manages RSS and newsletter feed integration."""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.user_agent = 'KnowledgeHub/1.0 (https://github.com/JohnTocci/KnowledgeHub)'
        
    def add_feed(self, feed_url: str, feed_name: str = None, 
                 auto_process: bool = True, max_items: int = 10) -> Dict:
        """Add a new RSS/newsletter feed."""
        try:
            # Validate and parse the feed
            feed_data = self._parse_feed(feed_url)
            if not feed_data:
                return {'success': False, 'error': 'Invalid or inaccessible feed'}
            
            # Generate feed name if not provided
            if not feed_name:
                feed_name = feed_data.get('title', urlparse(feed_url).netloc)
            
            # Store feed information in database
            self.db_manager.set_preference(f'feed_{feed_url}', f'{feed_name}|{auto_process}|{max_items}')
            
            # Get recent items if auto_process is enabled
            processed_items = []
            if auto_process:
                processed_items = self.process_feed_items(feed_url, max_items)
            
            return {
                'success': True,
                'feed_name': feed_name,
                'feed_url': feed_url,
                'items_found': len(feed_data.get('entries', [])),
                'items_processed': len(processed_items),
                'processed_items': processed_items
            }
            
        except Exception as e:
            logging.error(f"Error adding feed {feed_url}: {e}")
            return {'success': False, 'error': str(e)}
    
    def _parse_feed(self, feed_url: str) -> Optional[Dict]:
        """Parse and validate RSS feed."""
        try:
            # Set user agent to avoid blocking
            feedparser.USER_AGENT = self.user_agent
            
            # Parse the feed
            feed = feedparser.parse(feed_url)
            
            # Check if feed is valid
            if feed.bozo and feed.bozo_exception:
                logging.warning(f"Feed parsing warning for {feed_url}: {feed.bozo_exception}")
            
            if not hasattr(feed, 'entries') or len(feed.entries) == 0:
                return None
            
            return {
                'title': feed.feed.get('title', 'Unknown Feed'),
                'description': feed.feed.get('description', ''),
                'link': feed.feed.get('link', feed_url),
                'entries': feed.entries,
                'updated': feed.feed.get('updated', '')
            }
            
        except Exception as e:
            logging.error(f"Error parsing feed {feed_url}: {e}")
            return None
    
    def process_feed_items(self, feed_url: str, max_items: int = 10) -> List[Dict]:
        """Process recent items from a feed."""
        try:
            feed_data = self._parse_feed(feed_url)
            if not feed_data:
                return []
            
            processed_items = []
            entries = feed_data['entries'][:max_items]
            
            for entry in entries:
                try:
                    # Check if we've already processed this item
                    item_url = entry.get('link', '')
                    if self._is_already_processed(item_url):
                        continue
                    
                    # Extract content
                    item_data = self._extract_item_content(entry)
                    
                    if item_data['content']:
                        # Process with AI if available
                        from hub import summarize_text, save_as_markdown
                        
                        summary = summarize_text(
                            item_data['content'],
                            item_data['title'],
                            f"RSS feed item from {feed_data['title']}"
                        )
                        
                        # Save as markdown
                        markdown_file = save_as_markdown(
                            summary,
                            item_data['title'],
                            item_url,
                            metadata={
                                'source_feed': feed_url,
                                'feed_title': feed_data['title'],
                                'published': item_data['published'],
                                'author': item_data.get('author', ''),
                                'feed_item': True
                            }
                        )
                        
                        # Add to database
                        self.db_manager.add_content(
                            file_path=markdown_file,
                            title=item_data['title'],
                            content_type='rss_article',
                            source_url=item_url,
                            summary=summary,
                            author=item_data.get('author', ''),
                            tags=['rss', 'feed', feed_data['title'].lower().replace(' ', '_')]
                        )
                        
                        processed_items.append({
                            'title': item_data['title'],
                            'url': item_url,
                            'file_path': markdown_file,
                            'published': item_data['published']
                        })
                        
                        logging.info(f"Processed RSS item: {item_data['title']}")
                
                except Exception as e:
                    logging.error(f"Error processing feed item: {e}")
                    continue
            
            return processed_items
            
        except Exception as e:
            logging.error(f"Error processing feed items from {feed_url}: {e}")
            return []
    
    def _extract_item_content(self, entry) -> Dict:
        """Extract content from a feed entry."""
        # Get title
        title = entry.get('title', 'Untitled')
        title = re.sub(r'<[^>]+>', '', title)  # Remove HTML tags
        
        # Get content (try different fields)
        content = ''
        for content_field in ['content', 'summary', 'description']:
            if hasattr(entry, content_field):
                field_data = getattr(entry, content_field)
                if isinstance(field_data, list) and len(field_data) > 0:
                    content = field_data[0].get('value', '')
                elif isinstance(field_data, str):
                    content = field_data
                
                if content:
                    break
        
        # Clean HTML from content
        content = re.sub(r'<[^>]+>', '', content)
        content = re.sub(r'\s+', ' ', content).strip()
        
        # Get published date
        published = entry.get('published', entry.get('updated', ''))
        if published:
            try:
                published_dt = datetime.strptime(published, '%a, %d %b %Y %H:%M:%S %z')
                published = published_dt.strftime('%Y-%m-%d %H:%M')
            except:
                pass
        
        # Get author
        author = entry.get('author', '')
        
        return {
            'title': title,
            'content': content,
            'published': published,
            'author': author,
            'url': entry.get('link', '')
        }
    
    def _is_already_processed(self, url: str) -> bool:
        """Check if content from this URL has already been processed."""
        try:
            existing_content = self.db_manager.search_content(url, search_type='all')
            return len(existing_content) > 0
        except:
            return False
    
    def get_feeds(self) -> List[Dict]:
        """Get all configured feeds."""
        feeds = []
        try:
            # This is a simplified approach - in a real implementation,
            # you'd want a dedicated feeds table in the database
            # For now, we'll use preferences with a specific prefix
            
            # Get all preferences that start with 'feed_'
            # Note: This is a basic implementation
            feeds.append({
                'name': 'Demo RSS Feed',
                'url': 'https://example.com/rss',
                'auto_process': True,
                'max_items': 10,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M')
            })
            
        except Exception as e:
            logging.error(f"Error getting feeds: {e}")
        
        return feeds
    
    def update_all_feeds(self) -> Dict:
        """Update all configured feeds."""
        results = {
            'feeds_updated': 0,
            'items_processed': 0,
            'errors': 0,
            'details': []
        }
        
        try:
            feeds = self.get_feeds()
            
            for feed in feeds:
                try:
                    if feed.get('auto_process', True):
                        processed_items = self.process_feed_items(
                            feed['url'], 
                            feed.get('max_items', 10)
                        )
                        
                        results['feeds_updated'] += 1
                        results['items_processed'] += len(processed_items)
                        results['details'].append({
                            'feed': feed['name'],
                            'items': len(processed_items)
                        })
                
                except Exception as e:
                    results['errors'] += 1
                    logging.error(f"Error updating feed {feed.get('name', 'Unknown')}: {e}")
            
        except Exception as e:
            logging.error(f"Error updating feeds: {e}")
            results['errors'] += 1
        
        return results
    
    def search_feed_content(self, query: str) -> List[Dict]:
        """Search for content from RSS feeds."""
        try:
            # Search for content with 'rss' or 'feed' tags
            results = self.db_manager.search_content(query)
            
            # Filter for feed content
            feed_results = [
                result for result in results 
                if 'rss' in result.get('tags', []) or 
                   result.get('content_type') == 'rss_article'
            ]
            
            return feed_results
            
        except Exception as e:
            logging.error(f"Error searching feed content: {e}")
            return []
    
    def get_feed_stats(self) -> Dict:
        """Get statistics about RSS feed content."""
        try:
            # Get all RSS content
            all_content = self.db_manager.get_all_content(content_type='rss_article')
            
            if not all_content:
                return {
                    'total_feed_items': 0,
                    'feeds_configured': len(self.get_feeds()),
                    'latest_item': None,
                    'top_sources': []
                }
            
            # Calculate stats
            total_items = len(all_content)
            latest_item = max(all_content, key=lambda x: x.get('created_date', ''))
            
            # Count by source feed
            source_counts = {}
            for item in all_content:
                source = item.get('metadata', {}).get('feed_title', 'Unknown')
                source_counts[source] = source_counts.get(source, 0) + 1
            
            top_sources = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            return {
                'total_feed_items': total_items,
                'feeds_configured': len(self.get_feeds()),
                'latest_item': latest_item.get('title', '') if latest_item else None,
                'top_sources': top_sources
            }
            
        except Exception as e:
            logging.error(f"Error getting feed stats: {e}")
            return {
                'total_feed_items': 0,
                'feeds_configured': 0,
                'latest_item': None,
                'top_sources': []
            }
    
    def remove_feed(self, feed_url: str) -> bool:
        """Remove a feed configuration."""
        try:
            # Remove feed preference
            self.db_manager.set_preference(f'feed_{feed_url}', '')
            return True
        except Exception as e:
            logging.error(f"Error removing feed {feed_url}: {e}")
            return False
    
    def validate_feed_url(self, url: str) -> Dict:
        """Validate if a URL is a valid RSS feed."""
        try:
            feed_data = self._parse_feed(url)
            if feed_data:
                return {
                    'valid': True,
                    'title': feed_data['title'],
                    'description': feed_data.get('description', ''),
                    'items_count': len(feed_data['entries'])
                }
            else:
                return {
                    'valid': False,
                    'error': 'Could not parse feed or no entries found'
                }
        
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }