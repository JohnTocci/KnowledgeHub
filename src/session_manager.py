"""
Session state management and utilities for KnowledgeHub.
"""
import streamlit as st
from typing import Any, Dict, Optional
import json
import os
from datetime import datetime


class SessionManager:
    """Manages session state for KnowledgeHub application."""
    
    def __init__(self):
        self.initialize_session_state()
    
    def initialize_session_state(self):
        """Initialize session state variables."""
        default_state = {
            'processing_history': [],
            'last_processed_url': '',
            'user_preferences': {
                'auto_scroll_to_results': True,
                'show_processing_details': True,
                'default_expand_results': False,
                'max_recent_files': 10
            },
            'error_count': 0,
            'success_count': 0,
            'current_task_id': None,
            'last_error': None,
            'app_initialized': False
        }
        
        for key, value in default_state.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    def add_to_processing_history(self, url: str, title: str, status: str, 
                                 timestamp: datetime = None):
        """Add entry to processing history."""
        if timestamp is None:
            timestamp = datetime.now()
        
        entry = {
            'url': url,
            'title': title,
            'status': status,
            'timestamp': timestamp.isoformat(),
            'id': len(st.session_state.processing_history)
        }
        
        st.session_state.processing_history.append(entry)
        
        # Keep only last N entries
        max_entries = st.session_state.user_preferences['max_recent_files']
        if len(st.session_state.processing_history) > max_entries:
            st.session_state.processing_history = st.session_state.processing_history[-max_entries:]
    
    def get_processing_history(self, limit: int = None) -> list:
        """Get processing history."""
        history = st.session_state.processing_history
        if limit:
            return history[-limit:]
        return history
    
    def update_counters(self, success: bool = False, error: bool = False):
        """Update success/error counters."""
        if success:
            st.session_state.success_count += 1
        if error:
            st.session_state.error_count += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get session statistics."""
        return {
            'total_processed': len(st.session_state.processing_history),
            'success_count': st.session_state.success_count,
            'error_count': st.session_state.error_count,
            'success_rate': (st.session_state.success_count / 
                           max(1, st.session_state.success_count + st.session_state.error_count) * 100)
        }
    
    def set_preference(self, key: str, value: Any):
        """Set user preference."""
        if key in st.session_state.user_preferences:
            st.session_state.user_preferences[key] = value
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get user preference."""
        return st.session_state.user_preferences.get(key, default)
    
    def clear_history(self):
        """Clear processing history."""
        st.session_state.processing_history = []
        st.session_state.success_count = 0
        st.session_state.error_count = 0
    
    def export_session_data(self) -> str:
        """Export session data as JSON."""
        data = {
            'processing_history': st.session_state.processing_history,
            'user_preferences': st.session_state.user_preferences,
            'statistics': self.get_statistics(),
            'export_timestamp': datetime.now().isoformat()
        }
        return json.dumps(data, indent=2)
    
    def import_session_data(self, json_data: str) -> bool:
        """Import session data from JSON."""
        try:
            data = json.loads(json_data)
            
            if 'processing_history' in data:
                st.session_state.processing_history = data['processing_history']
            
            if 'user_preferences' in data:
                # Merge preferences, keeping existing ones for any missing keys
                for key, value in data['user_preferences'].items():
                    if key in st.session_state.user_preferences:
                        st.session_state.user_preferences[key] = value
            
            return True
        except (json.JSONDecodeError, KeyError):
            return False


class URLHistory:
    """Manages URL processing history with smart suggestions."""
    
    def __init__(self):
        self.session_manager = SessionManager()
    
    def add_url(self, url: str, success: bool = True):
        """Add URL to history."""
        # Normalize URL
        url = url.strip().lower()
        
        # Check if already exists
        history = self.get_recent_urls()
        if url not in [item['url'] for item in history]:
            entry = {
                'url': url,
                'timestamp': datetime.now().isoformat(),
                'success': success,
                'count': 1
            }
            
            # Add to session state
            if 'url_history' not in st.session_state:
                st.session_state.url_history = []
            
            st.session_state.url_history.append(entry)
            
            # Keep only last 50 URLs
            if len(st.session_state.url_history) > 50:
                st.session_state.url_history = st.session_state.url_history[-50:]
        else:
            # Update existing entry
            for item in st.session_state.url_history:
                if item['url'] == url:
                    item['count'] += 1
                    item['timestamp'] = datetime.now().isoformat()
                    item['success'] = success
                    break
    
    def get_recent_urls(self, limit: int = 10) -> list:
        """Get recent URLs."""
        if 'url_history' not in st.session_state:
            return []
        
        # Sort by timestamp (most recent first)
        history = sorted(
            st.session_state.url_history,
            key=lambda x: x['timestamp'],
            reverse=True
        )
        
        return history[:limit]
    
    def get_url_suggestions(self, partial_url: str, limit: int = 5) -> list:
        """Get URL suggestions based on partial input."""
        if not partial_url or len(partial_url) < 3:
            return []
        
        partial_url = partial_url.lower()
        history = self.get_recent_urls()
        
        suggestions = []
        for item in history:
            if partial_url in item['url'] and item['success']:
                suggestions.append(item['url'])
        
        return suggestions[:limit]
    
    def get_domain_statistics(self) -> Dict[str, int]:
        """Get statistics by domain."""
        if 'url_history' not in st.session_state:
            return {}
        
        domains = {}
        for item in st.session_state.url_history:
            try:
                # Extract domain from URL
                url = item['url']
                if '://' in url:
                    domain = url.split('://')[1].split('/')[0]
                else:
                    domain = url.split('/')[0]
                
                domains[domain] = domains.get(domain, 0) + 1
            except:
                continue
        
        return domains


# Global instances
session_manager = SessionManager()
url_history = URLHistory()


def show_session_statistics():
    """Display session statistics in sidebar or info panel."""
    stats = session_manager.get_statistics()
    
    if stats['total_processed'] > 0:
        st.markdown("**Session Statistics**")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Processed", stats['total_processed'])
            st.metric("Success Rate", f"{stats['success_rate']:.1f}%")
        
        with col2:
            st.metric("Successful", stats['success_count'])
            st.metric("Errors", stats['error_count'])


def show_recent_activity():
    """Show recent processing activity."""
    history = session_manager.get_processing_history(limit=5)
    
    if history:
        st.markdown("**Recent Activity**")
        for entry in reversed(history):  # Show most recent first
            status_icon = "✅" if entry['status'] == 'success' else "❌"
            timestamp = datetime.fromisoformat(entry['timestamp']).strftime("%H:%M")
            
            st.markdown(f"{status_icon} {timestamp} - {entry['title'][:40]}...")


def show_url_suggestions(current_url: str = ""):
    """Show URL suggestions based on history."""
    if current_url and len(current_url) > 3:
        suggestions = url_history.get_url_suggestions(current_url)
        
        if suggestions:
            st.markdown("**Recent URLs:**")
            for suggestion in suggestions:
                if st.button(f"🔗 {suggestion}", key=f"url_suggestion_{suggestion}", help="Click to use this URL"):
                    return suggestion
    
    return None