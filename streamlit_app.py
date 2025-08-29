import os
import sys
import glob
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import re
from streamlit_option_menu import option_menu
import pandas as pd
import logging

from dotenv import load_dotenv
load_dotenv()

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Check if we're in demo mode (no API key)
DEMO_MODE = not os.environ.get('OPENAI_API_KEY')

if DEMO_MODE:
    # Demo mode - create mock functions
    def get_article_text(url):
        return {
            'text': "This is demo content extracted from the article. It contains sample data and statistics for demonstration purposes.",
            'title': "Demo Article Title",
            'authors': ["Demo Author"],
            'publish_date': datetime.now(),
            'top_image': "https://example.com/demo-image.jpg",
            'images': ["https://example.com/demo-image1.jpg", "https://example.com/demo-image2.jpg"],
            'meta_description': "This is a demo article for testing the enhanced KnowledgeHub functionality.",
            'meta_keywords': ["demo", "test", "knowledgehub"]
        }
    
    def get_youtube_transcription(url):
        return "This is demo transcription content from the YouTube video.", "Demo YouTube Video Title"
    
    def summarize_text(text, title, additional_context=""):
        return f"""# Summary for {title}

## Summary
This is a demo summary of the content. In the real application, this would be generated using OpenAI's API to provide intelligent summarization of the article or video content with enhanced data extraction.

## Key Takeaways
- Demo takeaway point 1
- Demo takeaway point 2  
- Demo takeaway point 3

## Data Insights
| Metric | Value | Source |
|--------|-------|--------|
| Demo Stat 1 | 42% | Article analysis |
| Demo Stat 2 | 1,234 | User survey |
| Demo Stat 3 | 2025 | Publication year |

## Visual Elements
- Found 2 demo images related to the content
- Suggested visualization: Bar chart showing key metrics
- Recommended: Timeline of events mentioned in article

## Suggested Tags
demo, test, knowledge-hub, ai, summarization, data-extraction"""

    def download_and_save_images(images, title, vault_path):
        # Mock function for demo mode
        return [
            {'filename': 'demo_image1.jpg', 'path': '/demo/path/image1.jpg', 'url': 'https://example.com/image1.jpg'},
            {'filename': 'demo_image2.jpg', 'path': '/demo/path/image2.jpg', 'url': 'https://example.com/image2.jpg'}
        ]

    def save_as_markdown(content, title, url, saved_images=None, metadata=None):
        # Mock function for demo mode
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        markdown_content = f"""# {title}

**Source:** [{url}]({url})
**Date Processed:** {timestamp}

---

{content}
"""
        
        # In demo mode, just return a fake filepath
        filepath = f"/demo/vault/{title.replace(' ', '_')}.md"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return filepath
    
    # Import utility functions for demo mode too
    from session_manager import SessionManager, URLHistory
    from utils import (
        validate_and_sanitize_url, detect_content_type, estimate_processing_time,
        format_file_size, format_time_ago, ContentAnalyzer
    )
    
    # Mock the new modules for demo mode
    class MockDatabaseManager:
        def __init__(self, *args, **kwargs): pass
        def add_content(self, *args, **kwargs): return 1
        def get_content_stats(self): 
            return {'total_count': 5, 'content_by_type': {'article': 3, 'video': 2}, 'content_by_date': {}, 'top_tags': []}
        def get_all_tags(self): return [{'name': 'demo', 'count': 3}, {'name': 'test', 'count': 2}]
        def search_content(self, *args, **kwargs): return []
        def get_all_content(self, *args, **kwargs): return []
        def set_preference(self, *args, **kwargs): pass
        def get_preference(self, key, default=None): return 'dark' if key == 'theme' else default
    
    class MockFileProcessor:
        def __init__(self): pass
        def is_supported_file(self, file_path): return True
        def get_supported_extensions(self): return ['.pdf', '.docx', '.xlsx', '.csv', '.jpg', '.png']
        def process_file(self, file_path, title=None):
            return {
                'title': title or 'Demo File',
                'content': 'This is demo content extracted from the uploaded file.',
                'file_type': 'document',
                'word_count': 50,
                'metadata': {},
                'error': None
            }
    
    DatabaseManager = MockDatabaseManager
    FileProcessor = MockFileProcessor
    
    class MockInternalLinker:
        def __init__(self, db_manager): pass
        def find_related_content(self, *args, **kwargs): return []
        def add_internal_links(self, *args, **kwargs): return False
        def update_all_internal_links(self): return {"updated": 0, "skipped": 0, "errors": 0}
        def find_broken_links(self): return []
    
    class MockFeedManager:
        def __init__(self, db_manager): pass
        def get_feeds(self): return [{'name': 'Demo Feed', 'url': 'https://example.com/rss', 'auto_process': True}]
        def add_feed(self, *args, **kwargs): return {'success': True, 'feed_name': 'Demo Feed'}
        def validate_feed_url(self, url): return {'valid': True, 'title': 'Demo Feed'}
        def get_feed_stats(self): return {'total_feed_items': 5, 'feeds_configured': 1}
    
    InternalLinker = MockInternalLinker
    FeedManager = MockFeedManager
    
    # Create instances for demo mode
    session_manager = SessionManager()
    url_history = URLHistory()
    
    def display_error(error, show_retry=False):
        st.error(f"Demo Mode Error: {str(error)}")
        return False if not show_retry else st.button("Retry")
    
    def get_error_recovery_suggestions(error):
        return ["This is demo mode - errors are simulated", "Add your OpenAI API key for full functionality"]
        # Create a demo knowledge vault
        vault_path = os.path.expanduser("~/KnowledgeHub")
        os.makedirs(vault_path, exist_ok=True)
        
        # Sanitize filename
        sanitized_title = re.sub(r'[\\/*?:"<>|]', "", title)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        filepath = os.path.join(vault_path, f"{sanitized_title}.md")
        
        # Create markdown content
        markdown_content = f"""# {title}

**Source:** [{url}]({url})
**Date Processed:** {timestamp}

{content}
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return filepath

else:
    # Import real functions from hub.py
    try:
        from hub import get_article_text, get_youtube_transcription, summarize_text, save_as_markdown
        from error_handler import (
            display_error, validate_url, KnowledgeHubError, APIError, ValidationError,
            get_error_recovery_suggestions
        )
        from background_tasks import task_manager, run_with_progress
        from session_manager import session_manager, url_history, show_session_statistics
        from utils import (
            validate_and_sanitize_url, detect_content_type, estimate_processing_time,
            format_file_size, format_time_ago, ContentAnalyzer
        )
        from database_manager import DatabaseManager
        from file_processor import FileProcessor
        from internal_linking import InternalLinker
        from rss_feeds import FeedManager
        # Initialize session manager
        session_manager.initialize_session_state()
    except ImportError as e:
        st.error(f"Could not import required modules: {e}")
        st.error("Please check your installation and ensure all dependencies are installed.")
        st.stop()

# Configure Streamlit page
st.set_page_config(
    page_title="KnowledgeHub - Professional Knowledge Management",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    
    .chat-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    
    .chat-container {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
        border: 1px solid #e9ecef;
    }
    
    .chat-message {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border-left: 4px solid #667eea;
    }
    
    .feature-card {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 2px 15px rgba(0,0,0,0.08);
        margin: 1rem 0;
        border-left: 4px solid #2a5298;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 25px rgba(0,0,0,0.12);
    }
    
    .stat-card {
        background: linear-gradient(135deg, #2a5298 0%, #1e3c72 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        margin: 0.5rem;
        box-shadow: 0 3px 15px rgba(0,0,0,0.1);
    }
    
    .success-message {
        background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    .error-message {
        background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    .warning-message {
        background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    .demo-banner {
        background: linear-gradient(135deg, #9b59b6 0%, #8e44ad 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        margin: 1rem 0;
        font-weight: 500;
    }
    
    .file-item {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 3px solid #667eea;
    }
    
    .tips-box {
        background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    
    .content-stats {
        background: linear-gradient(135deg, #00b894 0%, #00a085 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    
    .sidebar .stSelectbox > div > div {
        background-color: #f0f0f0;
    }
    
    /* Enhanced chat styling */
    div[data-testid="stChatMessage"] {
        background: white !important;
        border-radius: 12px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05) !important;
        margin: 0.5rem 0 !important;
        border: 1px solid #e9ecef !important;
    }
    
    div[data-testid="stChatMessage"][data-testid*="user"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
    }
    
    div[data-testid="stChatMessage"][data-testid*="assistant"] {
        background: #f8f9fa !important;
        border-left: 4px solid #667eea !important;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Sidebar navigation
    with st.sidebar:
        # Professional header
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <h2 style="color: #2a5298; margin: 0;">KnowledgeHub</h2>
            <p style="color: #666; margin: 0; font-size: 0.9rem;">Professional Knowledge Management</p>
        </div>
        """, unsafe_allow_html=True)
        
        selected = option_menu(
            menu_title=None,
            options=["Add Content", "Upload Files", "Browse Files", "Analytics", "Chat", "Settings"],
            icons=["plus-square", "cloud-upload", "folder2-open", "graph-up", "chat-dots", "gear"],
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "#fafafa"},
                "icon": {"color": "#2a5298", "font-size": "18px"}, 
                "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#e8f2ff"},
                "nav-link-selected": {"background-color": "#2a5298", "color": "white"},
            }
        )
        
        # Demo mode indicator with enhanced styling
        if DEMO_MODE:
            st.markdown("""
            <div class="demo-banner">
                <strong>🚧 Demo Mode Active</strong><br>
                Add your OpenAI API key to enable full functionality
                <br><small>Limited to basic features and sample data</small>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%); 
                        color: white; padding: 0.8rem; border-radius: 8px; 
                        text-align: center; margin: 1rem 0; font-size: 0.85rem;">
                ✅ <strong>Full Mode Active</strong><br>
                All features enabled
            </div>
            """, unsafe_allow_html=True)
        
        # Enhanced quick stats with database integration
        st.markdown("---")
        st.markdown("**📊 Knowledge Vault Overview**")
        
        try:
            if not DEMO_MODE:
                from database_manager import DatabaseManager
                db_manager = DatabaseManager()
                stats = db_manager.get_content_stats()
                total_content = stats.get('total_count', 0)
                content_types = stats.get('content_by_type', {})
                top_tags = stats.get('top_tags', [])
                
                # Display content stats
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("📄 Items", total_content)
                with col2:
                    st.metric("🏷️ Tags", len(top_tags))
                
                if content_types:
                    st.markdown("**Content Types:**")
                    for content_type, count in content_types.items():
                        st.markdown(f"• {content_type.title()}: {count}")
                
                if total_content > 0 and top_tags:
                    st.markdown("**Top Tags:**")
                    for tag in top_tags[:3]:
                        st.markdown(f"• {tag['name']} ({tag['count']})")
                        
            else:
                # Demo mode stats
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("📄 Items", "42")
                with col2:
                    st.metric("🏷️ Tags", "18")
                st.markdown("**Content Types:**")
                st.markdown("• Articles: 28")
                st.markdown("• Videos: 14")
                
        except Exception as e:
            # Fallback to file-based stats
            vault_path = get_vault_path()
            if os.path.exists(vault_path):
                files = glob.glob(os.path.join(vault_path, "*.md"))
                total_size = sum(os.path.getsize(f) for f in files if os.path.isfile(f))
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("📄 Files", len(files))
                with col2:
                    st.metric("💾 Size", f"{total_size / (1024*1024):.1f} MB")
        
        # Quick action buttons
        st.markdown("---")
        st.markdown("**⚡ Quick Actions**")
        
        if st.button("🔍 Search Content", use_container_width=True):
            st.session_state.nav_override = "Chat"
            st.rerun()
            
        if st.button("📝 Add New Content", use_container_width=True):
            st.session_state.nav_override = "Add Content"
            st.rerun()
            
        if st.button("📊 View Analytics", use_container_width=True):
            st.session_state.nav_override = "Analytics"
            st.rerun()

    # Handle navigation overrides from quick action buttons
    if hasattr(st.session_state, 'nav_override'):
        selected = st.session_state.nav_override
        del st.session_state.nav_override

    # Main content area
    if selected == "Add Content":
        show_add_content_page()
    elif selected == "Upload Files":
        show_upload_files_page()
    elif selected == "Browse Files":
        show_browse_files_page()
    elif selected == "Analytics":
        show_analytics_page()
    elif selected == "Chat":
        show_chat_page()
    elif selected == "Settings":
        show_configuration_page()

def show_add_content_page():
    # Professional header
    st.markdown("""
    <div class="main-header">
        <h1>Transform Knowledge with AI</h1>
        <p>Convert articles and videos into structured, searchable knowledge</p>
    </div>
    """, unsafe_allow_html=True)
    
    # URL input form with improved validation and suggestions
    with st.container():
        st.markdown("### Add New Content")
        
        col1, col2 = st.columns([4, 1])
        with col1:
            # URL input with smart suggestions
            url = st.text_input(
                "Content URL",
                value=st.session_state.get('last_url_input', ''),
                placeholder="https://example.com/article or https://youtube.com/watch?v=...",
                help="Enter a web article URL or YouTube video link"
            )
            
            # Store the current input
            st.session_state.last_url_input = url
            
            # Show URL suggestions if user has history
            if url and len(url) > 5:
                suggestions = url_history.get_url_suggestions(url)
                if suggestions:
                    st.markdown("**Similar URLs from history:**")
                    for suggestion in suggestions[:3]:
                        if st.button(f"🔗 {suggestion[:50]}...", key=f"suggestion_{hash(suggestion)}"):
                            st.session_state.last_url_input = suggestion
                            st.rerun()
            
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)  # Spacing
            process_btn = st.button("Process Content", type="primary", use_container_width=True)
    
    # Show content type detection and time estimate
    if url:
        clean_url, is_valid = validate_and_sanitize_url(url)
        if is_valid:
            content_type = detect_content_type(clean_url)
            time_estimate = estimate_processing_time(clean_url)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"**Type:** {content_type.title()}")
            with col2:
                st.info(f"**Est. Time:** {time_estimate['min']}-{time_estimate['max']}s")
            with col3:
                if content_type == 'youtube':
                    st.info("**Audio:** Will be transcribed")
                else:
                    st.info("**Text:** Will be extracted")
        elif url.strip():
            st.warning("⚠️ URL format appears invalid")
    
    # Process content when button is clicked with improved error handling
    if process_btn:
        if not url:
            st.error("**Error:** Please enter a URL to process.")
        else:
            # Validate and clean URL
            clean_url, is_valid = validate_and_sanitize_url(url)
            if not is_valid:
                st.error("**Error:** Invalid URL format. Please check and try again.")
                st.info("**Examples:**\n- https://www.example.com/article\n- https://youtube.com/watch?v=abc123")
            else:
                # Add to URL history
                url_history.add_url(clean_url)
                
                # Process with enhanced error handling
                try:
                    process_content_with_error_handling(clean_url)
                    session_manager.add_to_processing_history(clean_url, "Processing...", "success")
                    session_manager.update_counters(success=True)
                except Exception as e:
                    session_manager.add_to_processing_history(clean_url, "Failed", "error")
                    session_manager.update_counters(error=True)
                    display_error(e)
                    
                    # Show suggestions
                    suggestions = get_error_recovery_suggestions(e)
                    if suggestions:
                        with st.expander("💡 Suggestions"):
                            for suggestion in suggestions:
                                st.write(f"• {suggestion}")
    
    # Show recent activity in sidebar
    with st.sidebar:
        if st.session_state.get('processing_history'):
            st.markdown("---")
            st.markdown("**Recent Activity**")
            
            # Show last 3 processed items
            recent = session_manager.get_processing_history(limit=3)
            for entry in reversed(recent):
                status_icon = "✅" if entry['status'] == 'success' else "❌"
                timestamp = datetime.fromisoformat(entry['timestamp'])
                time_ago = format_time_ago(timestamp)
                
                with st.container():
                    st.write(f"{status_icon} {entry['title'][:30]}...")
                    st.caption(f"{time_ago}")
            
            # Show session stats
            stats = session_manager.get_statistics()
            if stats['total_processed'] > 0:
                st.markdown("**Session Stats**")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Processed", stats['total_processed'])
                with col2:
                    st.metric("Success", f"{stats['success_rate']:.0f}%")
    
    # Professional feature showcase
    st.markdown("---")
    st.markdown("### Supported Content Types")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h4>Web Articles</h4>
            <p>Extract clean content from web articles, automatically filtering out ads and navigation elements.</p>
            <ul>
                <li>Automatic content extraction</li>
                <li>Metadata preservation</li>
                <li>Image downloading</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h4>YouTube Videos</h4>
            <p>Transcribe and summarize YouTube videos using advanced speech recognition technology.</p>
            <ul>
                <li>Audio transcription</li>
                <li>Multiple quality options</li>
                <li>Automatic cleanup</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h4>AI Processing</h4>
            <p>Generate intelligent summaries with key insights and automatic categorization.</p>
            <ul>
                <li>Structured summaries</li>
                <li>Key takeaways</li>
                <li>Automatic tagging</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Recent files preview
    show_recent_files_preview()

def search_file_content(file_path, search_term, search_mode):
    """Search through file content and metadata."""
    if not search_term:
        return True
    
    search_term_lower = search_term.lower()
    filename = os.path.basename(file_path)
    
    # Search in filename
    if search_mode in ["All", "Filename only"]:
        if search_term_lower in filename.lower():
            return True
    
    # Search in content and tags
    if search_mode in ["All", "Content only", "Tags only"]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract tags from the content (look for "## Suggested Tags" or "## Tags" section)
            tags = ""
            lines = content.split('\n')
            in_tags_section = False
            for line in lines:
                if line.strip().startswith('## Suggested Tags') or line.strip().startswith('## Tags'):
                    in_tags_section = True
                    continue
                elif line.strip().startswith('##') and in_tags_section:
                    break
                elif in_tags_section:
                    tags += line.strip() + " "
            
            # Search in tags only
            if search_mode == "Tags only":
                return search_term_lower in tags.lower()
            
            # Search in content only or all
            if search_mode in ["All", "Content only"]:
                return search_term_lower in content.lower()
                
        except Exception as e:
            # If file can't be read, fall back to filename search
            pass
    
    return False

def apply_filters(file_info, date_from, date_to, size_filter):
    """Apply date and size filters to files."""
    # Date filter
    if date_from and file_info['modified'].date() < date_from:
        return False
    if date_to and file_info['modified'].date() > date_to:
        return False
    
    # Size filter
    size_kb = file_info['size'] / 1024
    if size_filter == "< 1KB" and size_kb >= 1:
        return False
    elif size_filter == "1KB - 10KB" and (size_kb < 1 or size_kb > 10):
        return False
    elif size_filter == "10KB - 100KB" and (size_kb < 10 or size_kb > 100):
        return False
    elif size_filter == "> 100KB" and size_kb <= 100:
        return False
    
    return True

def show_browse_files_page():
    st.markdown("# 📁 Knowledge Vault")
    
    vault_path = get_vault_path()
    
    if not os.path.exists(vault_path):
        st.info("No knowledge vault found. Create your first content to get started!")
        return
    
    # Get all markdown files
    files = glob.glob(os.path.join(vault_path, "*.md"))
    
    if not files:
        st.info("No files in your knowledge vault yet. Start by adding some content!")
        return
    
    # Search and filter options
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        search_term = st.text_input("🔍 Search files", placeholder="Search by filename, content, or tags...")
    with col2:
        search_mode = st.selectbox("Search in", ["All", "Filename only", "Content only", "Tags only"])
    with col3:
        sort_by = st.selectbox("Sort by", ["Date (Newest)", "Date (Oldest)", "Name (A-Z)", "Name (Z-A)", "Size"])
    with col4:
        view_mode = st.selectbox("View", ["List", "Grid"])
    
    # Advanced search options
    with st.expander("🔧 Advanced Search"):
        col1, col2, col3 = st.columns(3)
        with col1:
            date_from = st.date_input("From date", value=None)
        with col2:
            date_to = st.date_input("To date", value=None)
        with col3:
            size_filter = st.selectbox("File size", ["Any", "< 1KB", "1KB - 10KB", "10KB - 100KB", "> 100KB"])
        
        bulk_delete_mode = st.checkbox("🗑️ Bulk Delete Mode")
    
    # Process files with enhanced search
    file_data = []
    for file_path in files:
        stat = os.stat(file_path)
        filename = os.path.basename(file_path)
        
        # Apply search filter
        if not search_file_content(file_path, search_term, search_mode):
            continue
        
        file_info = {
            'name': filename,
            'path': file_path,
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime),
            'size_mb': stat.st_size / (1024 * 1024)
        }
        
        # Apply advanced filters
        if not apply_filters(file_info, date_from, date_to, size_filter):
            continue
        
        file_data.append(file_info)
    
    # Sort files
    if sort_by == "Date (Newest)":
        file_data.sort(key=lambda x: x['modified'], reverse=True)
    elif sort_by == "Date (Oldest)":
        file_data.sort(key=lambda x: x['modified'])
    elif sort_by == "Name (A-Z)":
        file_data.sort(key=lambda x: x['name'])
    elif sort_by == "Name (Z-A)":
        file_data.sort(key=lambda x: x['name'], reverse=True)
    elif sort_by == "Size":
        file_data.sort(key=lambda x: x['size'], reverse=True)
    
    st.markdown(f"**Found {len(file_data)} files**")
    
    # Bulk delete functionality
    if bulk_delete_mode:
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("🗑️ Delete Selected", type="secondary", help="Delete all selected files"):
                selected_files = [k for k, v in st.session_state.items() if k.startswith('delete_') and v]
                if selected_files:
                    delete_files = []
                    for key in selected_files:
                        file_name = key.replace('delete_', '')
                        for file_info in file_data:
                            if file_info['name'] == file_name:
                                delete_files.append(file_info)
                                break
                    
                    if delete_files:
                        with st.spinner(f"Deleting {len(delete_files)} files..."):
                            deleted_count = 0
                            for file_info in delete_files:
                                try:
                                    os.remove(file_info['path'])
                                    if f"delete_{file_info['name']}" in st.session_state:
                                        del st.session_state[f"delete_{file_info['name']}"]
                                    deleted_count += 1
                                except Exception as e:
                                    st.error(f"Error deleting {file_info['name']}: {e}")
                        
                        if deleted_count > 0:
                            st.success(f"Successfully deleted {deleted_count} files!")
                            st.rerun()
                else:
                    st.warning("No files selected for deletion")
        
        with col2:
            if st.button("☑️ Select All"):
                for file_info in file_data:
                    st.session_state[f"delete_{file_info['name']}"] = True
                st.rerun()
        
        with col3:
            if st.button("🔄 Clear Selection"):
                for file_info in file_data:
                    if f"delete_{file_info['name']}" in st.session_state:
                        del st.session_state[f"delete_{file_info['name']}"]
                st.rerun()
    
    # Display files
    if view_mode == "List":
        for file_info in file_data:
            with st.container():
                if bulk_delete_mode:
                    col1, col2, col3, col4, col5 = st.columns([0.5, 2.5, 1, 1, 1])
                    with col1:
                        st.checkbox("", key=f"delete_{file_info['name']}", label_visibility="collapsed")
                else:
                    col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
                
                with col1 if not bulk_delete_mode else col2:
                    st.markdown(f"**{file_info['name'].replace('.md', '')}**")
                with col2 if not bulk_delete_mode else col3:
                    st.text(f"{file_info['size_mb']:.2f} MB")
                with col3 if not bulk_delete_mode else col4:
                    st.text(file_info['modified'].strftime("%m/%d/%Y"))
                with col4 if not bulk_delete_mode else col5:
                    if not bulk_delete_mode:
                        subcol1, subcol2 = st.columns(2)
                        with subcol1:
                            if st.button("👁️ View", key=f"view_{file_info['name']}"):
                                st.session_state.selected_file = file_info['path']
                                st.rerun()
                        with subcol2:
                            if st.button("🗑️", key=f"single_delete_{file_info['name']}", help="Delete this file"):
                                if confirm_delete_file(file_info):
                                    st.rerun()
                    else:
                        if st.button("👁️ View", key=f"view_{file_info['name']}"):
                            st.session_state.selected_file = file_info['path']
                            st.rerun()
                st.divider()
    else:
        # Grid view
        cols = st.columns(3)
        for i, file_info in enumerate(file_data):
            with cols[i % 3]:
                if bulk_delete_mode:
                    st.checkbox(f"Select", key=f"delete_{file_info['name']}")
                
                st.markdown(f"""
                <div class="file-item">
                    <h4>{file_info['name'].replace('.md', '')}</h4>
                    <p>📄 {file_info['size_mb']:.2f} MB | 📅 {file_info['modified'].strftime("%m/%d/%Y")}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if not bulk_delete_mode:
                    subcol1, subcol2 = st.columns(2)
                    with subcol1:
                        if st.button("👁️ View", key=f"view_grid_{file_info['name']}"):
                            st.session_state.selected_file = file_info['path']
                            st.rerun()
                    with subcol2:
                        if st.button("🗑️ Delete", key=f"grid_delete_{file_info['name']}"):
                            if confirm_delete_file(file_info):
                                st.rerun()
                else:
                    if st.button("👁️ View", key=f"view_grid_{file_info['name']}"):
                        st.session_state.selected_file = file_info['path']
                        st.rerun()
    
    # File viewer
    if 'selected_file' in st.session_state and st.session_state.selected_file:
        show_file_viewer(st.session_state.selected_file)

def show_file_viewer(file_path):
    st.markdown("---")
    st.markdown("### 📖 File Viewer")
    
    # Breadcrumb and actions
    filename = os.path.basename(file_path)
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"**📁 Knowledge Vault** › **{filename.replace('.md', '')}**")
    with col2:
        if st.button("🗑️ Delete File", type="secondary"):
            file_info = {
                'name': filename,
                'path': file_path,
                'size': os.path.getsize(file_path),
                'modified': datetime.fromtimestamp(os.path.getmtime(file_path)),
                'size_mb': os.path.getsize(file_path) / (1024 * 1024)
            }
            if confirm_delete_file(file_info):
                st.rerun()
    with col3:
        if st.button("← Back to Files"):
            del st.session_state.selected_file
            st.rerun()
    
    # View mode selector
    col1, col2 = st.columns([2, 1])
    with col1:
        view_mode = st.radio("View Mode", ["📖 Rendered", "📝 Raw Markdown"], horizontal=True)
    with col2:
        show_images = st.checkbox("🖼️ Show Images", value=True)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Tag Management Section
        st.markdown("---")
        st.markdown("### 🏷️ Tag Management")
        
        # Initialize database manager
        db_manager = DatabaseManager()
        
        # Get current tags for this file
        file_metadata = db_manager.get_content_metadata(file_path=file_path)
        current_tags = file_metadata.get('tags', []) if file_metadata else []
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Display current tags
            if current_tags:
                st.markdown("**Current Tags:**")
                tag_cols = st.columns(min(len(current_tags), 4))
                for i, tag in enumerate(current_tags):
                    with tag_cols[i % 4]:
                        if st.button(f"❌ {tag}", key=f"remove_tag_{tag}_{filename}", help="Click to remove"):
                            # Remove tag
                            new_tags = [t for t in current_tags if t != tag]
                            if file_metadata:
                                db_manager.update_content_tags(file_metadata['id'], new_tags)
                            st.success(f"Removed tag: {tag}")
                            st.rerun()
            else:
                st.info("No tags assigned yet")
        
        with col2:
            # Add new tag
            new_tag = st.text_input("Add new tag:", placeholder="Enter tag name", key=f"new_tag_{filename}")
            if st.button("➕ Add Tag", key=f"add_tag_btn_{filename}"):
                if new_tag and new_tag.strip():
                    clean_tag = new_tag.strip().lower()
                    if clean_tag not in current_tags:
                        new_tags = current_tags + [clean_tag]
                        
                        # Add to database
                        if file_metadata:
                            db_manager.update_content_tags(file_metadata['id'], new_tags)
                        else:
                            # Create new entry if not in database
                            title = filename.replace('.md', '').replace('_', ' ').title()
                            db_manager.add_content(
                                file_path=file_path,
                                title=title,
                                content_type='article',
                                tags=new_tags
                            )
                        
                        st.success(f"Added tag: {clean_tag}")
                        st.rerun()
                    else:
                        st.warning("Tag already exists!")
                else:
                    st.warning("Please enter a valid tag name")
        
        # Suggested tags from other content
        all_tags = db_manager.get_all_tags()
        if all_tags:
            popular_tags = [tag['name'] for tag in all_tags[:10] if tag['name'] not in current_tags]
            if popular_tags:
                st.markdown("**Suggested tags (click to add):**")
                suggestion_cols = st.columns(min(len(popular_tags), 5))
                for i, tag in enumerate(popular_tags):
                    with suggestion_cols[i % 5]:
                        if st.button(f"+ {tag}", key=f"suggest_tag_{tag}_{filename}"):
                            new_tags = current_tags + [tag]
                            if file_metadata:
                                db_manager.update_content_tags(file_metadata['id'], new_tags)
                            else:
                                title = filename.replace('.md', '').replace('_', ' ').title()
                                db_manager.add_content(
                                    file_path=file_path,
                                    title=title,
                                    content_type='article',
                                    tags=new_tags
                                )
                            st.success(f"Added suggested tag: {tag}")
                            st.rerun()
        
        st.markdown("---")
        
        # File content display
        if view_mode == "📖 Rendered":
            st.markdown(content, unsafe_allow_html=True)
        else:
            st.code(content, language="markdown")
        
        # Show images if they exist and checkbox is checked
        if show_images:
            sanitized_title = re.sub(r'[\\/*?:"<>|]', "", filename.replace('.md', ''))
            images_dir = os.path.join(os.path.dirname(file_path), f"{sanitized_title}_images")
            
            if os.path.exists(images_dir):
                image_files = [f for f in os.listdir(images_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
                
                if image_files:
                    st.markdown("---")
                    st.markdown("### 🖼️ Associated Images")
                    
                    # Display images in a grid
                    cols = st.columns(min(3, len(image_files)))
                    for i, img_file in enumerate(image_files):
                        with cols[i % 3]:
                            img_path = os.path.join(images_dir, img_file)
                            try:
                                st.image(img_path, caption=img_file, use_container_width=True)
                            except Exception as e:
                                st.error(f"Could not display {img_file}: {e}")
        
        # Copy button
        if st.button("📋 Copy to Clipboard"):
            st.code(content)
            st.success("Content ready to copy!")
            
    except Exception as e:
        st.error(f"Error reading file: {e}")

def show_analytics_page():
    """Enhanced analytics page with tag cloud, content breakdown, and heatmap."""
    st.markdown("""
    <div class="main-header">
        <h1>📊 Knowledge Analytics</h1>
        <p>Visualize and analyze your knowledge vault</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize database manager
    db_manager = DatabaseManager()
    vault_path = get_vault_path()
    
    if not os.path.exists(vault_path):
        st.info("No knowledge vault found. Create content to see analytics!")
        return
    
    # Get statistics from database
    stats = db_manager.get_content_stats()
    
    # Legacy file counting for files not in database yet
    files = glob.glob(os.path.join(vault_path, "*.md"))
    total_files = max(len(files), stats.get('total_count', 0))
    
    if total_files == 0:
        st.info("No files to analyze yet!")
        return
    
    # Dashboard stats
    col1, col2, col3, col4 = st.columns(4)
    
    total_size = sum(os.path.getsize(f) for f in files) if files else 0
    avg_size = total_size / total_files if total_files > 0 else 0
    
    # Recent activity
    recent_files = [f for f in files if (datetime.now() - datetime.fromtimestamp(os.path.getmtime(f))).days <= 7] if files else []
    
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <h2>📚</h2>
            <h3>{total_files}</h3>
            <p>Total Files</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <h2>💾</h2>
            <h3>{total_size / (1024*1024):.1f} MB</h3>
            <p>Total Size</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <h2>📄</h2>
            <h3>{avg_size / 1024:.1f} KB</h3>
            <p>Avg File Size</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="stat-card">
            <h2>🆕</h2>
            <h3>{len(recent_files)}</h3>
            <p>This Week</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Three-column layout for enhanced analytics
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        st.markdown("### ☁️ Tag Cloud")
        
        # Get tags from database
        tags_data = db_manager.get_all_tags()
        
        if tags_data and not DEMO_MODE:
            try:
                from wordcloud import WordCloud
                import matplotlib.pyplot as plt
                
                # Prepare tag data for word cloud
                tag_freq = {tag['name']: tag['count'] for tag in tags_data}
                
                if tag_freq:
                    # Generate word cloud
                    wordcloud = WordCloud(
                        width=400, 
                        height=300, 
                        background_color='white',
                        colormap='viridis',
                        max_words=50
                    ).generate_from_frequencies(tag_freq)
                    
                    # Display word cloud
                    fig, ax = plt.subplots(figsize=(8, 6))
                    ax.imshow(wordcloud, interpolation='bilinear')
                    ax.axis('off')
                    st.pyplot(fig)
                else:
                    st.info("No tags found yet!")
                    
            except ImportError:
                # Fallback: Show top tags as text
                st.markdown("**Top Tags:**")
                for tag in tags_data[:10]:
                    st.write(f"• {tag['name']} ({tag['count']})")
        else:
            # Demo mode or no tags
            st.markdown("""
            **Demo Tag Cloud:**
            - AI ⭐⭐⭐⭐
            - Knowledge Management ⭐⭐⭐
            - Productivity ⭐⭐⭐
            - Technology ⭐⭐
            - Learning ⭐⭐
            - Automation ⭐
            """)
    
    with col2:
        st.markdown("### 📊 Content Type Breakdown")
        
        # Get content type distribution
        content_by_type = stats.get('content_by_type', {})
        
        if not content_by_type and files:
            # Fallback: analyze file types from filesystem
            content_by_type = {'article': len(files)}
        
        if content_by_type:
            # Create pie chart
            fig = px.pie(
                values=list(content_by_type.values()),
                names=list(content_by_type.keys()),
                title="Content Distribution"
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                showlegend=True
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No content to analyze yet!")
    
    with col3:
        st.markdown("### 🔥 Activity Heatmap")
        
        # Get activity data by date
        content_by_date = stats.get('content_by_date', {})
        
        if not content_by_date and files:
            # Fallback: create from file modification dates
            dates = [datetime.fromtimestamp(os.path.getmtime(f)).date() for f in files]
            date_counts = pd.Series(dates).value_counts()
            content_by_date = {str(date): count for date, count in date_counts.items()}
        
        if content_by_date:
            # Create heatmap-style calendar view
            dates = list(content_by_date.keys())
            counts = list(content_by_date.values())
            
            df = pd.DataFrame({
                'date': pd.to_datetime(dates),
                'count': counts
            })
            
            # Group by week for better visualization
            df['week'] = df['date'].dt.isocalendar().week
            df['day'] = df['date'].dt.day_name()
            
            if len(df) > 0:
                heatmap_data = df.pivot_table(
                    values='count', 
                    index='day', 
                    columns='week', 
                    fill_value=0
                )
                
                fig = px.imshow(
                    heatmap_data,
                    title="Activity by Day/Week",
                    color_continuous_scale="Greens"
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Not enough data for heatmap")
        else:
            # Demo heatmap
            demo_data = pd.DataFrame({
                'day': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                'activity': [2, 1, 3, 0, 1, 0, 1]
            })
            
            fig = px.bar(
                demo_data,
                x='day',
                y='activity',
                title="Weekly Activity (Demo)"
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Additional analytics
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 Timeline Trend")
        
        if files:
            # Prepare data for timeline chart
            dates = [datetime.fromtimestamp(os.path.getmtime(f)).date() for f in files]
            date_counts = pd.Series(dates).value_counts().sort_index()
            
            fig = px.line(
                x=date_counts.index, 
                y=date_counts.values,
                title="Content Created Over Time"
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No timeline data available")
    
    with col2:
        st.markdown("### 💾 Storage Analysis")
        
        if files:
            # File size distribution
            sizes = [os.path.getsize(f) / 1024 for f in files]  # Convert to KB
            
            fig = px.histogram(
                x=sizes,
                nbins=10,
                title="File Size Distribution (KB)"
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No storage data available")

def show_configuration_page():
    """Enhanced configuration page with theme settings and preferences."""
    st.markdown("""
    <div class="main-header">
        <h1>⚙️ Settings & Configuration</h1>
        <p>Customize your KnowledgeHub experience</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize database manager for preferences
    db_manager = DatabaseManager()
    
    # Theme and UI Settings
    st.markdown("### 🎨 Theme & Appearance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Dark mode toggle
        current_theme = db_manager.get_preference('theme', 'light')
        dark_mode = st.checkbox("🌙 Dark Mode", value=(current_theme == 'dark'))
        
        if dark_mode != (current_theme == 'dark'):
            new_theme = 'dark' if dark_mode else 'light'
            db_manager.set_preference('theme', new_theme)
            
            # Apply dark mode CSS
            if dark_mode:
                st.markdown("""
                <style>
                .stApp {
                    background-color: #1e1e1e;
                    color: #ffffff;
                }
                .main-header {
                    background: linear-gradient(135deg, #2d2d2d 0%, #1a1a1a 100%);
                }
                .stat-card {
                    background: linear-gradient(135deg, #3d3d3d 0%, #2a2a2a 100%);
                }
                </style>
                """, unsafe_allow_html=True)
            
            st.success(f"Theme changed to {'Dark' if dark_mode else 'Light'} mode!")
            st.info("🔄 Refresh the page to see full theme changes.")
    
    with col2:
        # Default view preferences  
        default_view = db_manager.get_preference('default_view', 'list')
        view_pref = st.selectbox(
            "📋 Default File View", 
            options=['list', 'grid'],
            index=0 if default_view == 'list' else 1,
            format_func=lambda x: 'List View' if x == 'list' else 'Grid View'
        )
        
        if view_pref != default_view:
            db_manager.set_preference('default_view', view_pref)
            st.success(f"Default view set to {view_pref.title()} View!")
    
    # Content Processing Settings
    st.markdown("---")
    st.markdown("### 🤖 AI Processing Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Auto-tagging preference
        auto_tag = db_manager.get_preference('auto_tagging', 'true') == 'true'
        auto_tagging = st.checkbox("🏷️ Automatic Tag Generation", value=auto_tag)
        
        if auto_tagging != auto_tag:
            db_manager.set_preference('auto_tagging', str(auto_tagging).lower())
            st.success("Auto-tagging preference updated!")
        
        # Image processing preference
        process_images = db_manager.get_preference('process_images', 'true') == 'true'
        img_processing = st.checkbox("🖼️ Process Images in Articles", value=process_images)
        
        if img_processing != process_images:
            db_manager.set_preference('process_images', str(img_processing).lower())
            st.success("Image processing preference updated!")
    
    with col2:
        # Summary length preference
        summary_length = db_manager.get_preference('summary_length', 'medium')
        length_pref = st.selectbox(
            "📝 Summary Length",
            options=['short', 'medium', 'long'],
            index=['short', 'medium', 'long'].index(summary_length),
            format_func=lambda x: f"{x.title()} (~{150 if x=='short' else 300 if x=='medium' else 500} words)"
        )
        
        if length_pref != summary_length:
            db_manager.set_preference('summary_length', length_pref)
            st.success("Summary length preference updated!")
        
        # Language preference
        language = db_manager.get_preference('language', 'english')
        lang_pref = st.selectbox(
            "🌍 Processing Language",
            options=['english', 'spanish', 'french', 'german', 'chinese'],
            index=['english', 'spanish', 'french', 'german', 'chinese'].index(language),
            format_func=lambda x: x.title()
        )
        
        if lang_pref != language:
            db_manager.set_preference('language', lang_pref)
            st.success("Language preference updated!")
    
    # Environment Status
    st.markdown("---")
    st.markdown("### 🌍 Environment Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        api_key_status = "✅ Configured" if os.environ.get('OPENAI_API_KEY') else "❌ Not Set"
        st.info(f"**OpenAI API Key:** {api_key_status}")
        
        vault_path = get_vault_path()
        vault_status = "✅ Accessible" if os.path.exists(vault_path) else "❌ Not Found"
        st.info(f"**Knowledge Vault:** {vault_status}")
    
    with col2:
        mode = "🎮 Demo Mode" if DEMO_MODE else "🚀 Full Mode"
        st.info(f"**Current Mode:** {mode}")
        
        # Database status
        try:
            stats = db_manager.get_content_stats()
            db_status = f"✅ Connected ({stats.get('total_count', 0)} items)"
        except:
            db_status = "❌ Connection Error"
        st.info(f"**Database:** {db_status}")
    
    # Configuration details
    st.markdown("---")
    st.markdown("### 📋 Current Configuration")
    
    config_data = {
        "Knowledge Vault Path": get_vault_path(),
        "OpenAI Model": "GPT-5 (Demo Mode)" if DEMO_MODE else "GPT-5 Mini",
        "Whisper Model": "medium (Demo Mode)" if DEMO_MODE else "medium",
        "Date Format": "%Y-%m-%d %H:%M",
        "Filename Template": "{title}.md",
        "Theme": db_manager.get_preference('theme', 'light').title(),
        "Auto-tagging": "Enabled" if db_manager.get_preference('auto_tagging', 'true') == 'true' else "Disabled",
        "Default View": db_manager.get_preference('default_view', 'list').title()
    }
    
    for key, value in config_data.items():
        st.text(f"{key}: {value}")
    
    # RSS Feed Management
    st.markdown("---")
    st.markdown("### 📡 RSS Feed Management")
    
    feed_manager = FeedManager(db_manager)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📋 Current Feeds**")
        feeds = feed_manager.get_feeds()
        
        if feeds:
            for i, feed in enumerate(feeds):
                with st.container():
                    st.markdown(f"""
                    **{feed['name']}**  
                    🔗 {feed['url'][:50]}{'...' if len(feed['url']) > 50 else ''}  
                    ⚙️ Auto-process: {'✅' if feed.get('auto_process') else '❌'}
                    """)
                    
                    if not DEMO_MODE and st.button(f"🗑️ Remove", key=f"remove_feed_{i}"):
                        if feed_manager.remove_feed(feed['url']):
                            st.success(f"Removed feed: {feed['name']}")
                            st.rerun()
        else:
            st.info("No RSS feeds configured yet")
        
        # Feed stats
        if not DEMO_MODE:
            feed_stats = feed_manager.get_feed_stats()
            st.markdown(f"""
            **📊 Feed Statistics:**
            - Total items: {feed_stats.get('total_feed_items', 0)}
            - Configured feeds: {feed_stats.get('feeds_configured', 0)}
            """)
    
    with col2:
        st.markdown("**➕ Add New Feed**")
        
        new_feed_url = st.text_input(
            "RSS Feed URL", 
            placeholder="https://example.com/rss.xml",
            key="new_feed_url"
        )
        
        new_feed_name = st.text_input(
            "Feed Name (optional)", 
            placeholder="My Blog Feed",
            key="new_feed_name"
        )
        
        auto_process = st.checkbox("Auto-process new items", value=True, key="auto_process_feed")
        max_items = st.number_input("Max items to process", min_value=1, max_value=50, value=10, key="max_feed_items")
        
        if st.button("🔍 Validate Feed", key="validate_feed"):
            if new_feed_url:
                validation = feed_manager.validate_feed_url(new_feed_url)
                if validation['valid']:
                    st.success(f"✅ Valid feed: {validation['title']}")
                    st.info(f"Found {validation.get('items_count', 0)} items")
                else:
                    st.error(f"❌ Invalid feed: {validation['error']}")
            else:
                st.warning("Please enter a feed URL")
        
        if st.button("➕ Add Feed", key="add_feed"):
            if new_feed_url:
                if not DEMO_MODE:
                    result = feed_manager.add_feed(new_feed_url, new_feed_name, auto_process, max_items)
                    if result['success']:
                        st.success(f"✅ Added feed: {result['feed_name']}")
                        st.info(f"Processed {result.get('items_processed', 0)} items")
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to add feed: {result['error']}")
                else:
                    st.success("✅ Demo: Feed would be added in full mode")
            else:
                st.warning("Please enter a feed URL")
        
        if st.button("🔄 Update All Feeds", key="update_feeds"):
            if not DEMO_MODE:
                with st.spinner("Updating feeds..."):
                    results = feed_manager.update_all_feeds()
                    st.success(f"Updated {results['feeds_updated']} feeds, processed {results['items_processed']} items")
                    if results['errors'] > 0:
                        st.warning(f"Encountered {results['errors']} errors")
            else:
                st.success("✅ Demo: Feeds would be updated in full mode")
    
    # Internal Linking Management
    st.markdown("---")
    st.markdown("### 🔗 Internal Linking")
    
    internal_linker = InternalLinker(db_manager)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🔧 Link Management**")
        
        if st.button("🔄 Update All Internal Links", key="update_internal_links"):
            if not DEMO_MODE:
                with st.spinner("Updating internal links..."):
                    results = internal_linker.update_all_internal_links()
                    st.success(f"Updated: {results['updated']}, Skipped: {results['skipped']}")
                    if results['errors'] > 0:
                        st.warning(f"Errors: {results['errors']}")
            else:
                st.success("✅ Demo: Internal links would be updated in full mode")
        
        if st.button("🔍 Find Broken Links", key="find_broken_links"):
            if not DEMO_MODE:
                broken_links = internal_linker.find_broken_links()
                if broken_links:
                    st.warning(f"Found {len(broken_links)} broken links")
                    for link in broken_links[:5]:  # Show first 5
                        st.text(f"• {link['source_title']}: '{link['broken_link']}'")
                else:
                    st.success("No broken links found!")
            else:
                st.success("✅ Demo: Would check for broken links in full mode")
    
    with col2:
        st.markdown("**📊 Linking Statistics**")
        
        if not DEMO_MODE:
            all_content = db_manager.get_all_content()
            total_content = len(all_content)
            
            # Count content with potential links (basic estimation)
            linked_content = sum(1 for content in all_content if content.get('tags'))
            
            st.metric("Total Content", total_content)
            st.metric("Tagged Content", linked_content)
            st.metric("Link Potential", f"{(linked_content/max(total_content,1)*100):.0f}%")
        else:
            st.metric("Total Content", "42")
            st.metric("Tagged Content", "28") 
            st.metric("Link Potential", "67%")
        
        st.markdown("**⚙️ Linking Settings**")
        
        min_similarity = st.slider(
            "Minimum similarity for auto-linking",
            min_value=0.1,
            max_value=1.0,
            value=0.3,
            step=0.1,
            key="min_similarity"
        )
        
        max_links = st.number_input(
            "Max links per document",
            min_value=1,
            max_value=20,
            value=5,
            key="max_links"
        )
    
    # Data Management
    st.markdown("---")
    st.markdown("### 🗂️ Data Management")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📤 Export Settings", type="secondary"):
            try:
                # Export all preferences
                preferences = {}
                for key in ['theme', 'default_view', 'auto_tagging', 'process_images', 'summary_length', 'language']:
                    preferences[key] = db_manager.get_preference(key, '')
                
                st.download_button(
                    label="⬇️ Download Settings JSON",
                    data=pd.DataFrame([preferences]).to_json(orient='records'),
                    file_name="knowledgehub_settings.json",
                    mime="application/json"
                )
            except Exception as e:
                st.error(f"Export failed: {str(e)}")
    
    with col2:
        if st.button("🔄 Reset to Defaults", type="secondary"):
            try:
                # Reset key preferences
                defaults = {
                    'theme': 'light',
                    'default_view': 'list', 
                    'auto_tagging': 'true',
                    'process_images': 'true',
                    'summary_length': 'medium',
                    'language': 'english'
                }
                
                for key, value in defaults.items():
                    db_manager.set_preference(key, value)
                
                st.success("Settings reset to defaults!")
                st.info("🔄 Refresh the page to see changes.")
            except Exception as e:
                st.error(f"Reset failed: {str(e)}")
    
    with col3:
        if st.button("📊 Database Info", type="secondary"):
            try:
                stats = db_manager.get_content_stats()
                st.json(stats)
            except Exception as e:
                st.error(f"Could not retrieve database info: {str(e)}")
    
    # Help section
    st.markdown("---")
    st.markdown("### 📚 Configuration Help")
    
    with st.expander("🔑 Setting up OpenAI API Key"):
        st.markdown("""
        To enable full functionality:
        1. Get your API key from [OpenAI's website](https://platform.openai.com/api-keys)
        2. Set the environment variable: `export OPENAI_API_KEY="your-key-here"`
        3. Or create a `.env` file in the project root with: `OPENAI_API_KEY=your-key-here`
        4. Restart the application
        """)
    
    with st.expander("📁 Knowledge Vault Location"):
        st.markdown(f"""
        Your knowledge vault is located at:
        ```
        {get_vault_path()}
        ```
        
        All processed content is saved here as markdown files with a SQLite database for metadata.
        """)
    
    with st.expander("🎨 Theme Customization"):
        st.markdown("""
        **Dark Mode Benefits:**
        - Reduced eye strain in low light
        - Better for OLED displays
        - Modern, professional appearance
        
        **Theme applies to:**
        - Background colors
        - Text colors
        - Card and component styling
        - Chart and visualization themes
        """)
    
    with st.expander("🚀 Running the Application"):
        st.markdown("""
        **Streamlit Web Interface:**
        ```bash
        streamlit run streamlit_app.py
        ```
        
        **CLI Interface (still available):**
        ```bash
        python src/hub.py
        ```
        """)
    
    with st.expander("🆕 New Features"):
        st.markdown("""
        **Recent Enhancements:**
        - 📁 File upload for PDFs, documents, images, spreadsheets
        - 🏷️ Tag management system with add/remove functionality
        - 🗄️ SQLite database for improved efficiency
        - 🌙 Dark mode theme
        - 💬 Chat interface for natural language queries
        - 📊 Enhanced analytics with tag cloud and heatmap
        - 🔗 Automatic internal linking (coming soon)
        - 📡 RSS/Newsletter integration (coming soon)
        """)

def process_content_with_error_handling(url):
    """Process URL content with improved error handling and background processing."""
    
    # Create containers for progress tracking
    progress_container = st.container()
    
    def process_task(progress_callback):
        """Background task for processing content."""
        try:
            progress_callback(0.1, "Initializing...")
            
            # Step 1: Extract content
            progress_callback(0.2, "Extracting content...")
            
            if "youtube.com" in url.lower() or "youtu.be" in url.lower():
                content, title = get_youtube_transcription(url)
                content_type = "YouTube Video"
                saved_images = []
                metadata = {}
                additional_context = "Content source: YouTube video transcription"
                progress_callback(0.5, "Transcription completed")
            else:
                article_data = get_article_text(url)
                content = article_data['text']
                title = article_data['title']
                content_type = "Web Article"
                
                progress_callback(0.4, "Downloading images...")
                
                if not DEMO_MODE:
                    from hub import download_and_save_images
                    vault_path = get_vault_path()
                    saved_images = download_and_save_images(article_data['images'], title, vault_path)
                else:
                    saved_images = download_and_save_images(article_data['images'], title, "")
                
                # Prepare metadata
                metadata = {
                    'authors': article_data['authors'],
                    'publish_date': article_data['publish_date'],
                    'meta_description': article_data['meta_description'],
                    'meta_keywords': article_data['meta_keywords']
                }
                
                additional_context = f"""
                Content source: Web article
                Number of images found: {len(article_data['images'])}
                Authors: {', '.join(article_data['authors']) if article_data['authors'] else 'Unknown'}
                Publication date: {article_data['publish_date'] if article_data['publish_date'] else 'Unknown'}
                Meta description: {article_data['meta_description'] if article_data['meta_description'] else 'None'}
                """
            
            progress_callback(0.6, "Generating AI summary...")
            
            # Step 2: Generate AI summary
            summary = summarize_text(content, title, additional_context)
            
            progress_callback(0.8, "Saving to knowledge vault...")
            
            # Step 3: Save to knowledge vault
            filepath = save_as_markdown(summary, title, url, saved_images, metadata)
            
            # Step 4: Add to database if not in demo mode
            if not DEMO_MODE:
                try:
                    from database_manager import DatabaseManager
                    db_manager = DatabaseManager()
                    
                    # Extract tags from metadata and content
                    tags = []
                    if metadata and metadata.get('meta_keywords'):
                        tags.extend(metadata['meta_keywords'])
                    
                    # Calculate word count from summary
                    word_count = len(summary.split()) if summary else 0
                    
                    # Add content to database
                    db_manager.add_content(
                        file_path=filepath,
                        title=title,
                        content_type=content_type.lower().replace(' ', '_'),
                        source_url=url,
                        summary=summary,
                        tags=tags,
                        author=', '.join(metadata.get('authors', [])) if metadata else None,
                        word_count=word_count
                    )
                    logging.info(f"Added content to database: {title}")
                except Exception as db_error:
                    logging.error(f"Failed to add content to database: {db_error}")
                    # Don't fail the entire process if database fails
            
            progress_callback(1.0, "Processing complete!")
            
            return {
                'success': True,
                'title': title,
                'content_type': content_type,
                'filepath': filepath,
                'summary': summary,
                'saved_images': saved_images,
                'metadata': metadata
            }
            
        except Exception as e:
            logging.error(f"Error processing content: {e}", exc_info=True)
            raise e
    
    # Run with progress tracking
    if DEMO_MODE:
        # For demo mode, run synchronously to keep it simple
        try:
            result = process_task(lambda p, m="": None)
            display_success_result(result)
        except Exception as e:
            display_error(e, show_retry=True)
    else:
        # Use background processing for real mode
        with progress_container:
            try:
                result = run_with_progress(process_task, "Processing Content")
                if result and result.get('success'):
                    display_success_result(result)
            except Exception as e:
                display_error(e, show_retry=True)


def display_success_result(result):
    """Display successful processing results with enhanced information."""
    st.markdown(f"""
    <div class="success-message">
        <h3>Content Processed Successfully</h3>
        <p><strong>Type:</strong> {result['content_type']}</p>
        <p><strong>Title:</strong> {result['title']}</p>
        <p><strong>File:</strong> {os.path.basename(result['filepath']) if result['filepath'] else 'Demo Mode'}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Analyze content and show insights
    if result.get('summary'):
        analyzer = ContentAnalyzer()
        content_stats = analyzer.count_elements(result['summary'])
        reading_time = analyzer.estimate_reading_time(result['summary'])
        
        # Show content analysis
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Words", content_stats['words'])
        with col2:
            st.metric("Read Time", f"{reading_time} min")
        with col3:
            st.metric("Paragraphs", content_stats['paragraphs'])
        with col4:
            if result['saved_images']:
                st.metric("Images", len(result['saved_images']))
            else:
                st.metric("Images", 0)
    
    # Show additional details
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if result['saved_images']:
            st.success(f"✅ Downloaded {len(result['saved_images'])} images")
        
        if result['metadata'] and result['metadata'].get('authors'):
            st.info(f"👤 Authors: {', '.join(result['metadata']['authors'])}")
        
        if result['metadata'] and result['metadata'].get('publish_date'):
            st.info(f"📅 Published: {result['metadata']['publish_date']}")
    
    with col2:
        # Action buttons
        if st.button("📖 View Summary", type="secondary", use_container_width=True):
            st.session_state.show_content_preview = True
        
        if result['saved_images'] and st.button("🖼️ View Images", type="secondary", use_container_width=True):
            st.session_state.show_images_preview = True
        
        if result['filepath'] and st.button("📁 Open Folder", type="secondary", use_container_width=True):
            st.info(f"File saved to: {os.path.dirname(result['filepath'])}")
    
    # Expandable content sections
    if st.session_state.get('show_content_preview', False):
        with st.expander("📖 Generated Summary", expanded=True):
            st.markdown(result['summary'])
            
            # Add copy button functionality via text area
            st.text_area("Copy text from here:", result['summary'], height=200, key="summary_copy")
    
    if st.session_state.get('show_images_preview', False) and result['saved_images']:
        with st.expander("🖼️ Downloaded Images", expanded=True):
            for i, img in enumerate(result['saved_images']):
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.markdown(f"**Image {i+1}**")
                    st.caption(f"File: {img['filename']}")
                with col2:
                    st.markdown(f"Source: [{img['url']}]({img['url']})")
                    if os.path.exists(img['path']):
                        try:
                            st.image(img['path'], width=200)
                        except Exception:
                            st.text("Preview not available")
                st.divider()
    
    # Clear preview states
    if st.button("🔄 Process Another URL", type="primary"):
        st.session_state.show_content_preview = False
        st.session_state.show_images_preview = False
        st.session_state.last_url_input = ""
        st.rerun()


def process_content(url):
    """Legacy process content function - redirects to new implementation."""
    return process_content_with_error_handling(url)


def show_recent_files_preview():
    """Show a preview of recent files."""
    
    vault_path = get_vault_path()
    if not os.path.exists(vault_path):
        return
    
    files = glob.glob(os.path.join(vault_path, "*.md"))
    if not files:
        return
    
    # Sort by modification time (newest first)
    files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    recent_files = files[:5]  # Show 5 most recent
    
    st.markdown("### 📋 Recent Files")
    
    for file_path in recent_files:
        filename = os.path.basename(file_path).replace('.md', '')
        modified = datetime.fromtimestamp(os.path.getmtime(file_path))
        
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.text(filename)
        with col2:
            st.text(modified.strftime("%m/%d/%Y"))
        with col3:
            if st.button("View", key=f"recent_{filename}"):
                st.session_state.selected_file = file_path
                st.rerun()

def confirm_delete_file(file_info):
    """Confirm and delete a single file."""
    # Create a confirmation dialog using session state
    confirm_key = f"confirm_delete_{file_info['name']}"
    
    if confirm_key not in st.session_state:
        st.session_state[confirm_key] = False
    
    if not st.session_state[confirm_key]:
        st.warning(f"⚠️ Are you sure you want to delete '{file_info['name'].replace('.md', '')}'?")
        # Use buttons without columns since we're already in a nested column structure
        if st.button("✅ Yes, Delete", key=f"confirm_yes_{file_info['name']}"):
            st.session_state[confirm_key] = True
            return True
        if st.button("❌ Cancel", key=f"confirm_no_{file_info['name']}"):
            return False
        return False
    else:
        # Actually delete the file
        try:
            os.remove(file_info['path'])
            st.success(f"✅ Successfully deleted '{file_info['name'].replace('.md', '')}'!")
            # Clean up session state
            if confirm_key in st.session_state:
                del st.session_state[confirm_key]
            # Clear selected file if it was the deleted one
            if 'selected_file' in st.session_state and st.session_state.selected_file == file_info['path']:
                del st.session_state.selected_file
            return True
        except Exception as e:
            st.error(f"❌ Error deleting file: {e}")
            # Clean up session state on error
            if confirm_key in st.session_state:
                del st.session_state[confirm_key]
            return False

def show_upload_files_page():
    """Display file upload interface for various document types."""
    st.markdown("""
    <div class="main-header">
        <h1>📁 Upload Documents</h1>
        <p>Upload PDFs, documents, images, spreadsheets, and more for AI processing</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize database manager and file processor
    db_manager = DatabaseManager()
    file_processor = FileProcessor()
    
    # File upload section
    st.markdown("### Upload Files")
    
    # Support multiple file types
    supported_extensions = file_processor.get_supported_extensions()
    uploaded_files = st.file_uploader(
        "Choose files to upload",
        type=[ext.lstrip('.') for ext in supported_extensions],
        accept_multiple_files=True,
        help=f"Supported formats: {', '.join(supported_extensions)}"
    )
    
    if uploaded_files:
        st.markdown(f"### Processing {len(uploaded_files)} file(s)")
        
        # Process each uploaded file
        for uploaded_file in uploaded_files:
            with st.container():
                st.markdown(f"#### 📄 {uploaded_file.name}")
                
                # Show file info
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.info(f"**Size:** {format_file_size(uploaded_file.size)}")
                with col2:
                    file_type = file_processor.get_file_type(uploaded_file.name)
                    st.info(f"**Type:** {file_type.title()}")
                with col3:
                    st.info(f"**Format:** {uploaded_file.type}")
                
                # Process button for each file
                if st.button(f"Process {uploaded_file.name}", key=f"process_{uploaded_file.name}"):
                    
                    if not DEMO_MODE:
                        # Save uploaded file temporarily
                        vault_path = get_vault_path()
                        os.makedirs(vault_path, exist_ok=True)
                        
                        temp_path = os.path.join(vault_path, uploaded_file.name)
                        with open(temp_path, "wb") as f:
                            f.write(uploaded_file.getvalue())
                        
                        try:
                            # Process the file
                            with st.spinner(f"Processing {uploaded_file.name}..."):
                                result = file_processor.process_file(temp_path, uploaded_file.name.split('.')[0])
                                
                                if result.get('error'):
                                    st.error(f"❌ Processing failed: {result['error']}")
                                else:
                                    # Summarize content using AI
                                    if result['content']:
                                        summary = summarize_text(
                                            result['content'], 
                                            result['title'],
                                            f"File type: {result['file_type']}. Metadata: {result.get('metadata', {})}"
                                        )
                                        
                                        # Save as markdown
                                        markdown_file = save_as_markdown(
                                            summary, 
                                            result['title'], 
                                            f"file://{temp_path}",
                                            metadata=result.get('metadata', {})
                                        )
                                        
                                        # Add to database
                                        db_manager.add_content(
                                            file_path=markdown_file,
                                            title=result['title'],
                                            content_type=result['file_type'],
                                            source_url=f"file://{temp_path}",
                                            summary=summary,
                                            word_count=result.get('word_count', 0)
                                        )
                                        
                                        st.success(f"✅ Successfully processed {uploaded_file.name}")
                                        
                                        # Show results
                                        with st.expander(f"📖 Summary for {result['title']}", expanded=True):
                                            st.markdown(summary)
                                        
                                        # Show metadata if available
                                        if result.get('metadata'):
                                            with st.expander("📊 File Metadata"):
                                                st.json(result['metadata'])
                                    else:
                                        st.warning("⚠️ No content could be extracted from this file")
                        
                        except Exception as e:
                            st.error(f"❌ Error processing file: {str(e)}")
                        finally:
                            # Clean up temporary file
                            if os.path.exists(temp_path):
                                os.remove(temp_path)
                    
                    else:
                        # Demo mode processing
                        with st.spinner(f"Processing {uploaded_file.name}..."):
                            result = file_processor.process_file("demo_path", uploaded_file.name.split('.')[0])
                            st.success(f"✅ Demo: Successfully processed {uploaded_file.name}")
                            
                            with st.expander(f"📖 Demo Summary for {result['title']}", expanded=True):
                                st.markdown("""
                                ### Demo Summary
                                This is a demonstration of file processing capabilities. In full mode:
                                - Text is extracted from PDFs and documents
                                - Data is analyzed from spreadsheets  
                                - Images are processed for content recognition
                                - AI generates summaries and tags
                                - Content is saved to your knowledge vault
                                """)
                
                st.markdown("---")
    
    # Show supported file types
    st.markdown("### 📋 Supported File Types")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        **📄 Documents**
        - PDF files (.pdf)
        - Word documents (.docx)
        - Text files (.txt, .md)
        """)
    
    with col2:
        st.markdown("""
        **📊 Spreadsheets**
        - Excel files (.xlsx, .xls)
        - CSV files (.csv)
        """)
    
    with col3:
        st.markdown("""
        **🖼️ Images**
        - JPEG (.jpg, .jpeg)
        - PNG (.png)
        - GIF (.gif)
        - WebP (.webp)
        """)
    
    with col4:
        st.markdown("""
        **🎯 Processing**
        - Text extraction
        - AI summarization
        - Tag generation
        - Metadata extraction
        """)

def show_chat_page():
    """Display enhanced chat interface for querying knowledge vault."""
    st.markdown("""
    <div class="chat-header">
        <h1>💬 Knowledge Chat</h1>
        <p>Ask questions about your knowledge vault in natural language</p>
        <p style="font-size: 0.9rem; opacity: 0.8;">Powered by intelligent search and AI reasoning</p>
    </div>
    """, unsafe_allow_html=True)
    
    if DEMO_MODE:
        st.warning("🚧 Chat functionality requires OpenAI API key. Currently in demo mode.")
        
        st.markdown("### Demo Chat Interface")
        user_question = st.text_input("Ask a question about your knowledge:", placeholder="What are the main themes in my saved articles?")
        
        if user_question:
            st.markdown("#### 🤖 AI Response:")
            st.markdown("""
            **Demo Response:** This is a demonstration of the chat feature. In full mode, the AI would:
            
            1. Search through your knowledge vault
            2. Find relevant content based on your question
            3. Generate a comprehensive answer using context from your saved articles and documents
            4. Provide citations and sources
            
            Your question: *"{}"*
            
            **Sample Answer:** Based on your knowledge vault, I found several articles discussing artificial intelligence, productivity tools, and knowledge management. The main themes include automated content processing, AI-powered summarization, and personal knowledge organization systems.
            """.format(user_question))
    else:
        # Initialize database for searching
        db_manager = DatabaseManager()
        
        # Show vault statistics in sidebar or info box
        with st.expander("📊 Knowledge Vault Status", expanded=False):
            stats = db_manager.get_content_stats()
            total_content = stats.get('total_count', 0)
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                <div class="content-stats">
                    <h3>{total_content}</h3>
                    <p>Total Items</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                content_types = stats.get('content_by_type', {})
                type_count = len(content_types)
                st.markdown(f"""
                <div class="content-stats">
                    <h3>{type_count}</h3>
                    <p>Content Types</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                top_tags = stats.get('top_tags', [])
                tag_count = len(top_tags)
                st.markdown(f"""
                <div class="content-stats">
                    <h3>{tag_count}</h3>
                    <p>Unique Tags</p>
                </div>
                """, unsafe_allow_html=True)
            
            if total_content == 0:
                st.markdown("""
                <div class="tips-box">
                    <h4>🚀 Get Started</h4>
                    <p>Your knowledge vault is empty. Add some content to start chatting!</p>
                    <ul>
                        <li>📝 Add articles and YouTube videos</li>
                        <li>📁 Upload PDFs and documents</li>
                        <li>🏷️ Use tags to organize content</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
        
        # Chat interface
        if "chat_messages" not in st.session_state:
            st.session_state.chat_messages = []
        
        # Display chat history
        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if message.get("sources"):
                    with st.expander("📚 Sources"):
                        for source in message["sources"]:
                            st.markdown(f"- [{source['title']}]({source['path']})")
        
        # Chat input
        if prompt := st.chat_input("Ask me anything about your knowledge vault..."):
            # Add user message
            st.session_state.chat_messages.append({"role": "user", "content": prompt})
            
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Generate AI response
            with st.chat_message("assistant"):
                with st.spinner("Searching knowledge vault..."):
                    try:
                        # Search for relevant content
                        search_results = db_manager.search_content(prompt)
                        
                        if search_results:
                            # Prepare enhanced context from search results
                            context_content = []
                            sources = []
                            
                            st.info(f"🔍 Found {len(search_results)} relevant items in your vault")
                            
                            for i, result in enumerate(search_results[:5]):  # Top 5 results
                                # Enhanced context with more fields
                                content_piece = f"""Title: {result['title']}
Summary: {result.get('summary', 'No summary available')}
Key Takeaways: {result.get('key_takeaways', 'Not available')}
Tags: {result.get('tags', 'No tags')}
Type: {result.get('content_type', 'Unknown')}"""
                                
                                context_content.append(content_piece)
                                sources.append({
                                    'title': result['title'], 
                                    'path': result['file_path'],
                                    'type': result.get('content_type', 'Unknown'),
                                    'tags': result.get('tags', '')
                                })
                            
                            context = "\n\n---\n\n".join(context_content)
                            
                            # Generate response using OpenAI
                            response_prompt = f"""
                            Based on the following content from the user's knowledge vault, answer their question: "{prompt}"
                            
                            Context from knowledge vault:
                            {context}
                            
                            Provide a helpful and comprehensive answer based on the available content. If you reference specific information, mention which source it comes from. If the information is insufficient, say so.
                            """
                            
                            ai_response = summarize_text(response_prompt, "Chat Response", "")
                            
                            st.markdown(ai_response)
                            
                            # Add assistant message with sources
                            st.session_state.chat_messages.append({
                                "role": "assistant", 
                                "content": ai_response,
                                "sources": sources
                            })
                            
                            # Enhanced sources display
                            if sources:
                                with st.expander(f"📚 Sources ({len(sources)} items found)"):
                                    for i, source in enumerate(sources, 1):
                                        col1, col2 = st.columns([3, 1])
                                        with col1:
                                            st.markdown(f"**{i}. {source['title']}**")
                                            if source.get('tags'):
                                                st.markdown(f"🏷️ *Tags: {source['tags']}*")
                                        with col2:
                                            st.markdown(f"📄 *{source.get('type', 'Unknown')}*")
                                        
                                        st.markdown(f"📁 `{source['path']}`")
                                        if i < len(sources):
                                            st.markdown("---")
                        
                        else:
                            # Enhanced fallback with helpful suggestions
                            db_stats = db_manager.get_content_stats()
                            total_content = db_stats.get('total_count', 0)
                            top_tags = db_stats.get('top_tags', [])
                            
                            if total_content == 0:
                                response = """I don't see any content in your knowledge vault yet! 🗂️
                                
To get started:
1. 📝 **Add Content**: Use the "Add Content" page to save articles or YouTube videos
2. 📁 **Upload Files**: Upload PDFs, documents, or other files
3. 🏷️ **Tag Content**: Add relevant tags to make content easier to find

Once you have some content saved, I'll be able to help you find information and answer questions!"""
                            else:
                                suggestion_tags = [tag['name'] for tag in top_tags[:5]]
                                suggestions = ""
                                if suggestion_tags:
                                    suggestions = f"\n\n**Try asking about:** {', '.join(suggestion_tags)}"
                                
                                response = f"""I couldn't find specific content matching your question in your knowledge vault. 🔍

**Your vault contains {total_content} items** - try being more specific or use different keywords.{suggestions}

**Tips for better results:**
- Use keywords from your saved content
- Try broader terms if your search was very specific
- Check the Browse page to see what content you have saved"""
                            
                            st.markdown(response)
                            st.session_state.chat_messages.append({"role": "assistant", "content": response})
                    
                    except Exception as e:
                        error_msg = f"Sorry, I encountered an error while searching: {str(e)}"
                        st.error(error_msg)
                        st.session_state.chat_messages.append({"role": "assistant", "content": error_msg})

def get_vault_path():
    """Get the knowledge vault path."""
    try:
        from config_manager import config
        return config.get_vault_path()
    except:
        # Fallback to default path
        return os.path.expanduser("~/KnowledgeHub")

if __name__ == "__main__":
    main()