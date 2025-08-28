"""
Database manager for KnowledgeHub using SQLite.
Handles metadata storage and retrieval for improved efficiency.
"""
import sqlite3
import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import logging

class DatabaseManager:
    """Manages SQLite database for KnowledgeHub metadata."""
    
    def __init__(self, db_path: str = None):
        """Initialize database manager with optional custom path."""
        if db_path is None:
            # Default to knowledge vault directory
            from config_manager import Config
            config = Config()
            vault_path = config.get_vault_path()
            db_path = os.path.join(vault_path, "knowledgehub.db")
        
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Content metadata table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS content_metadata (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_path TEXT UNIQUE NOT NULL,
                        title TEXT NOT NULL,
                        content_type TEXT NOT NULL,
                        source_url TEXT,
                        file_size INTEGER,
                        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        modified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        tags TEXT,  -- JSON array of tags
                        summary TEXT,
                        key_takeaways TEXT,
                        author TEXT,
                        word_count INTEGER,
                        processing_status TEXT DEFAULT 'completed'
                    )
                ''')
                
                # Tags table for efficient tag management
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tags (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tag_name TEXT UNIQUE NOT NULL,
                        usage_count INTEGER DEFAULT 1,
                        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Content-tag relationships
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS content_tags (
                        content_id INTEGER,
                        tag_id INTEGER,
                        PRIMARY KEY (content_id, tag_id),
                        FOREIGN KEY (content_id) REFERENCES content_metadata (id),
                        FOREIGN KEY (tag_id) REFERENCES tags (id)
                    )
                ''')
                
                # User preferences
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_preferences (
                        key TEXT PRIMARY KEY,
                        value TEXT,
                        updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                logging.info(f"Database initialized at {self.db_path}")
                
        except Exception as e:
            logging.error(f"Error initializing database: {e}")
            raise
    
    def add_content(self, file_path: str, title: str, content_type: str, 
                   source_url: str = None, tags: List[str] = None, 
                   summary: str = None, key_takeaways: str = None,
                   author: str = None, word_count: int = None) -> int:
        """Add new content metadata to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get file size
                file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                
                # Insert content metadata
                cursor.execute('''
                    INSERT OR REPLACE INTO content_metadata 
                    (file_path, title, content_type, source_url, file_size, tags, 
                     summary, key_takeaways, author, word_count, modified_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (file_path, title, content_type, source_url, file_size,
                      json.dumps(tags) if tags else None, summary, key_takeaways,
                      author, word_count))
                
                content_id = cursor.lastrowid
                
                # Handle tags
                if tags:
                    self._update_tags(cursor, content_id, tags)
                
                conn.commit()
                logging.info(f"Added content metadata for {title}")
                return content_id
                
        except Exception as e:
            logging.error(f"Error adding content metadata: {e}")
            raise
    
    def _update_tags(self, cursor, content_id: int, tags: List[str]):
        """Update tags for content."""
        # Remove existing tag relationships
        cursor.execute('DELETE FROM content_tags WHERE content_id = ?', (content_id,))
        
        for tag in tags:
            tag = tag.strip().lower()
            if not tag:
                continue
                
            # Insert or update tag
            cursor.execute('''
                INSERT OR IGNORE INTO tags (tag_name) VALUES (?)
            ''', (tag,))
            
            cursor.execute('''
                UPDATE tags SET usage_count = usage_count + 1 
                WHERE tag_name = ?
            ''', (tag,))
            
            # Get tag ID
            cursor.execute('SELECT id FROM tags WHERE tag_name = ?', (tag,))
            tag_id = cursor.fetchone()[0]
            
            # Create relationship
            cursor.execute('''
                INSERT OR IGNORE INTO content_tags (content_id, tag_id) 
                VALUES (?, ?)
            ''', (content_id, tag_id))
    
    def get_content_metadata(self, file_path: str = None, content_id: int = None) -> Optional[Dict]:
        """Get content metadata by file path or ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if content_id:
                    cursor.execute('SELECT * FROM content_metadata WHERE id = ?', (content_id,))
                elif file_path:
                    cursor.execute('SELECT * FROM content_metadata WHERE file_path = ?', (file_path,))
                else:
                    return None
                
                row = cursor.fetchone()
                if row:
                    return self._row_to_dict(cursor, row)
                return None
                
        except Exception as e:
            logging.error(f"Error getting content metadata: {e}")
            return None
    
    def get_all_content(self, limit: int = None, content_type: str = None) -> List[Dict]:
        """Get all content metadata with optional filtering."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = 'SELECT * FROM content_metadata'
                params = []
                
                if content_type:
                    query += ' WHERE content_type = ?'
                    params.append(content_type)
                
                query += ' ORDER BY created_date DESC'
                
                if limit:
                    query += ' LIMIT ?'
                    params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                return [self._row_to_dict(cursor, row) for row in rows]
                
        except Exception as e:
            logging.error(f"Error getting all content: {e}")
            return []
    
    def get_content_by_tags(self, tags: List[str]) -> List[Dict]:
        """Get content filtered by tags."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Build query with tag filtering
                placeholders = ','.join(['?' for _ in tags])
                query = f'''
                    SELECT DISTINCT cm.* FROM content_metadata cm
                    JOIN content_tags ct ON cm.id = ct.content_id
                    JOIN tags t ON ct.tag_id = t.id
                    WHERE t.tag_name IN ({placeholders})
                    ORDER BY cm.created_date DESC
                '''
                
                cursor.execute(query, [tag.lower() for tag in tags])
                rows = cursor.fetchall()
                
                return [self._row_to_dict(cursor, row) for row in rows]
                
        except Exception as e:
            logging.error(f"Error getting content by tags: {e}")
            return []
    
    def update_content_tags(self, content_id: int, tags: List[str]):
        """Update tags for existing content."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Update the tags JSON in content_metadata
                cursor.execute('''
                    UPDATE content_metadata 
                    SET tags = ?, modified_date = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (json.dumps(tags), content_id))
                
                # Update tag relationships
                self._update_tags(cursor, content_id, tags)
                
                conn.commit()
                logging.info(f"Updated tags for content ID {content_id}")
                
        except Exception as e:
            logging.error(f"Error updating content tags: {e}")
            raise
    
    def get_all_tags(self) -> List[Dict]:
        """Get all tags with usage counts."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT tag_name, usage_count FROM tags 
                    ORDER BY usage_count DESC, tag_name
                ''')
                
                return [{'name': row[0], 'count': row[1]} for row in cursor.fetchall()]
                
        except Exception as e:
            logging.error(f"Error getting tags: {e}")
            return []
    
    def get_content_stats(self) -> Dict:
        """Get content statistics for analytics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total content count
                cursor.execute('SELECT COUNT(*) FROM content_metadata')
                total_count = cursor.fetchone()[0]
                
                # Content by type
                cursor.execute('''
                    SELECT content_type, COUNT(*) 
                    FROM content_metadata 
                    GROUP BY content_type
                ''')
                content_by_type = dict(cursor.fetchall())
                
                # Content by date (last 30 days)
                cursor.execute('''
                    SELECT DATE(created_date) as date, COUNT(*) 
                    FROM content_metadata 
                    WHERE created_date >= date('now', '-30 days')
                    GROUP BY DATE(created_date)
                    ORDER BY date
                ''')
                content_by_date = dict(cursor.fetchall())
                
                # Top tags
                cursor.execute('''
                    SELECT tag_name, usage_count 
                    FROM tags 
                    ORDER BY usage_count DESC 
                    LIMIT 20
                ''')
                top_tags = [{'name': row[0], 'count': row[1]} for row in cursor.fetchall()]
                
                return {
                    'total_count': total_count,
                    'content_by_type': content_by_type,
                    'content_by_date': content_by_date,
                    'top_tags': top_tags
                }
                
        except Exception as e:
            logging.error(f"Error getting content stats: {e}")
            return {}
    
    def search_content(self, query: str, search_type: str = 'all') -> List[Dict]:
        """Search content by title, tags, or summary."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query_lower = f'%{query.lower()}%'
                
                if search_type == 'title':
                    sql = 'SELECT * FROM content_metadata WHERE LOWER(title) LIKE ? ORDER BY created_date DESC'
                    params = [query_lower]
                elif search_type == 'tags':
                    sql = '''
                        SELECT DISTINCT cm.* FROM content_metadata cm
                        JOIN content_tags ct ON cm.id = ct.content_id
                        JOIN tags t ON ct.tag_id = t.id
                        WHERE LOWER(t.tag_name) LIKE ?
                        ORDER BY cm.created_date DESC
                    '''
                    params = [query_lower]
                else:  # all
                    sql = '''
                        SELECT * FROM content_metadata 
                        WHERE LOWER(title) LIKE ? OR LOWER(summary) LIKE ? OR LOWER(tags) LIKE ?
                        ORDER BY created_date DESC
                    '''
                    params = [query_lower, query_lower, query_lower]
                
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                
                return [self._row_to_dict(cursor, row) for row in rows]
                
        except Exception as e:
            logging.error(f"Error searching content: {e}")
            return []
    
    def delete_content(self, content_id: int):
        """Delete content and associated relationships."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Delete tag relationships
                cursor.execute('DELETE FROM content_tags WHERE content_id = ?', (content_id,))
                
                # Delete content metadata
                cursor.execute('DELETE FROM content_metadata WHERE id = ?', (content_id,))
                
                # Clean up unused tags
                cursor.execute('''
                    DELETE FROM tags WHERE id NOT IN (
                        SELECT DISTINCT tag_id FROM content_tags
                    )
                ''')
                
                conn.commit()
                logging.info(f"Deleted content ID {content_id}")
                
        except Exception as e:
            logging.error(f"Error deleting content: {e}")
            raise
    
    def _row_to_dict(self, cursor, row) -> Dict:
        """Convert database row to dictionary."""
        columns = [description[0] for description in cursor.description]
        result = dict(zip(columns, row))
        
        # Parse JSON fields
        if result.get('tags'):
            try:
                result['tags'] = json.loads(result['tags'])
            except:
                result['tags'] = []
        else:
            result['tags'] = []
        
        return result
    
    def set_preference(self, key: str, value: str):
        """Set user preference."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO user_preferences (key, value, updated_date)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (key, value))
                conn.commit()
        except Exception as e:
            logging.error(f"Error setting preference: {e}")
    
    def get_preference(self, key: str, default: str = None) -> str:
        """Get user preference."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT value FROM user_preferences WHERE key = ?', (key,))
                row = cursor.fetchone()
                return row[0] if row else default
        except Exception as e:
            logging.error(f"Error getting preference: {e}")
            return default