"""
Modern Streamlit Web Interface for KnowledgeHub.
A visually appealing, responsive web application for knowledge management.
"""
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

from dotenv import load_dotenv
load_dotenv()

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Check if we're in demo mode (no API key)
DEMO_MODE = not os.environ.get('OPENAI_API_KEY')

if DEMO_MODE:
    # Demo mode - create mock functions
    def get_article_text(url):
        return "This is demo content extracted from the article.", "Demo Article Title"
    
    def get_youtube_transcription(url):
        return "This is demo transcription content from the YouTube video.", "Demo YouTube Video Title"
    
    def summarize_text(text, title):
        return f"""# Summary for {title}

## Summary
This is a demo summary of the content. In the real application, this would be generated using OpenAI's API to provide intelligent summarization of the article or video content.

## Key Takeaways
- Demo takeaway point 1
- Demo takeaway point 2  
- Demo takeaway point 3

## Suggested Tags
demo, test, knowledge-hub, ai, summarization"""

    def save_as_markdown(content, title, url):
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
    except ImportError:
        st.error("Could not import hub functions. Please check your installation.")
        st.stop()

# Configure Streamlit page
st.set_page_config(
    page_title="KnowledgeHub",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    
    .feature-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem;
    }
    
    .success-message {
        background: linear-gradient(90deg, #56ab2f 0%, #a8e6cf 100%);
        color: white;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .demo-banner {
        background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 1rem;
        border-radius: 5px;
        text-align: center;
        margin: 1rem 0;
    }
    
    .file-item {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 3px solid #667eea;
    }
    
    .sidebar .stSelectbox > div > div {
        background-color: #f0f0f0;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Sidebar navigation
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/brain.png", width=64)
        st.title("🧠 KnowledgeHub")
        
        selected = option_menu(
            menu_title=None,
            options=["Add Content", "Browse Files", "Analytics", "Configuration"],
            icons=["plus-circle", "folder", "bar-chart", "gear"],
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "#fafafa"},
                "icon": {"color": "orange", "font-size": "18px"}, 
                "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
                "nav-link-selected": {"background-color": "#667eea"},
            }
        )
        
        # Demo mode indicator
        if DEMO_MODE:
            st.markdown('<div class="demo-banner">🎮 Demo Mode Active</div>', unsafe_allow_html=True)
            st.info("Add your OpenAI API key to enable full functionality.")
        
        # Quick stats
        vault_path = get_vault_path()
        if os.path.exists(vault_path):
            files = glob.glob(os.path.join(vault_path, "*.md"))
            total_size = sum(os.path.getsize(f) for f in files if os.path.isfile(f))
            
            st.markdown("### 📊 Quick Stats")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Files", len(files))
            with col2:
                st.metric("Vault Size", f"{total_size / (1024*1024):.1f} MB")

    # Main content area
    if selected == "Add Content":
        show_add_content_page()
    elif selected == "Browse Files":
        show_browse_files_page()
    elif selected == "Analytics":
        show_analytics_page()
    elif selected == "Configuration":
        show_configuration_page()

def show_add_content_page():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🚀 Transform Knowledge with AI</h1>
        <p>Convert any article or YouTube video into structured, searchable knowledge</p>
    </div>
    """, unsafe_allow_html=True)
    
    # URL input form
    with st.container():
        st.markdown("### 📝 Add New Content")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            url = st.text_input(
                "Enter URL",
                placeholder="https://example.com/article or https://youtube.com/watch?v=...",
                help="Supports web articles and YouTube videos"
            )
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)  # Spacing
            process_btn = st.button("🔄 Process Content", type="primary", use_container_width=True)
    
    # Process content when button is clicked
    if process_btn and url:
        process_content(url)
    elif process_btn and not url:
        st.error("Please enter a URL to process.")
    
    # Feature showcase
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>🌐 Web Articles</h3>
            <p>Extract clean content from any web article, ignoring ads and clutter.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>🎥 YouTube Videos</h3>
            <p>Transcribe and summarize YouTube videos using AI-powered speech recognition.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h3>🤖 AI Summaries</h3>
            <p>Generate concise summaries, key takeaways, and relevant tags automatically.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Recent files preview
    show_recent_files_preview()

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
        search_term = st.text_input("🔍 Search files", placeholder="Search by filename...")
    with col2:
        sort_by = st.selectbox("Sort by", ["Date (Newest)", "Date (Oldest)", "Name (A-Z)", "Name (Z-A)", "Size"])
    with col3:
        view_mode = st.selectbox("View", ["List", "Grid"])
    with col4:
        st.markdown("<br>", unsafe_allow_html=True)  # Spacing
        bulk_delete_mode = st.checkbox("🗑️ Bulk Delete Mode")
    
    # Process files
    file_data = []
    for file_path in files:
        stat = os.stat(file_path)
        filename = os.path.basename(file_path)
        
        # Apply search filter
        if search_term and search_term.lower() not in filename.lower():
            continue
        
        file_data.append({
            'name': filename,
            'path': file_path,
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime),
            'size_mb': stat.st_size / (1024 * 1024)
        })
    
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
    view_mode = st.radio("View Mode", ["📖 Rendered", "📝 Raw Markdown"], horizontal=True)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if view_mode == "📖 Rendered":
            st.markdown(content, unsafe_allow_html=True)
        else:
            st.code(content, language="markdown")
        
        # Copy button
        if st.button("📋 Copy to Clipboard"):
            st.code(content)
            st.success("Content ready to copy!")
            
    except Exception as e:
        st.error(f"Error reading file: {e}")

def show_analytics_page():
    st.markdown("# 📊 Knowledge Analytics")
    
    vault_path = get_vault_path()
    
    if not os.path.exists(vault_path):
        st.info("No knowledge vault found. Create content to see analytics!")
        return
    
    files = glob.glob(os.path.join(vault_path, "*.md"))
    
    if not files:
        st.info("No files to analyze yet!")
        return
    
    # File statistics
    col1, col2, col3, col4 = st.columns(4)
    
    total_files = len(files)
    total_size = sum(os.path.getsize(f) for f in files)
    avg_size = total_size / total_files if total_files > 0 else 0
    
    # Recent activity
    recent_files = [f for f in files if (datetime.now() - datetime.fromtimestamp(os.path.getmtime(f))).days <= 7]
    
    with col1:
        st.markdown("""
        <div class="stat-card">
            <h2>📚</h2>
            <h3>{}</h3>
            <p>Total Files</p>
        </div>
        """.format(total_files), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="stat-card">
            <h2>💾</h2>
            <h3>{:.1f} MB</h3>
            <p>Total Size</p>
        </div>
        """.format(total_size / (1024*1024)), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="stat-card">
            <h2>📄</h2>
            <h3>{:.1f} KB</h3>
            <p>Avg File Size</p>
        </div>
        """.format(avg_size / 1024), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="stat-card">
            <h2>🆕</h2>
            <h3>{}</h3>
            <p>This Week</p>
        </div>
        """.format(len(recent_files)), unsafe_allow_html=True)
    
    # Charts
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 File Creation Timeline")
        
        # Prepare data for timeline chart
        dates = [datetime.fromtimestamp(os.path.getmtime(f)).date() for f in files]
        date_counts = pd.Series(dates).value_counts().sort_index()
        
        fig = px.line(
            x=date_counts.index, 
            y=date_counts.values,
            title="Files Created Over Time",
            labels={'x': 'Date', 'y': 'Files Created'}
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 📊 File Size Distribution")
        
        # File size histogram
        sizes = [os.path.getsize(f) / 1024 for f in files]  # Convert to KB
        
        fig = px.histogram(
            x=sizes,
            nbins=10,
            title="File Size Distribution (KB)",
            labels={'x': 'File Size (KB)', 'y': 'Count'}
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )
        st.plotly_chart(fig, use_container_width=True)

def show_configuration_page():
    st.markdown("# ⚙️ Configuration")
    
    # Environment status
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
        
        interface = "🌐 Streamlit Web Interface"
        st.info(f"**Interface:** {interface}")
    
    # Configuration details
    st.markdown("### 📋 Current Configuration")
    
    config_data = {
        "Knowledge Vault Path": get_vault_path(),
        "OpenAI Model": "GPT-5 (Demo Mode)" if DEMO_MODE else "GPT-5 Mini",
        "Whisper Model": "medium (Demo Mode)" if DEMO_MODE else "medium",
        "Date Format": "%Y-%m-%d %H:%M",
        "Filename Template": "{title}.md"
    }
    
    for key, value in config_data.items():
        st.text(f"{key}: {value}")
    
    st.markdown("---")
    
    # Help section
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
        
        All processed content is saved here as markdown files.
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

def process_content(url):
    """Process URL content and save to knowledge vault."""
    
    with st.spinner("🔄 Processing content..."):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Step 1: Extract content
            status_text.text("📥 Extracting content...")
            progress_bar.progress(25)
            
            if "youtube.com" in url or "youtu.be" in url:
                content, title = get_youtube_transcription(url)
                content_type = "YouTube Video"
            else:
                content, title = get_article_text(url)
                content_type = "Web Article"
            
            if not content or not title:
                st.error("❌ Failed to extract content from URL")
                return
            
            # Step 2: Generate AI summary
            status_text.text("🤖 Generating AI summary...")
            progress_bar.progress(50)
            
            summary = summarize_text(content, title)
            
            # Step 3: Save to knowledge vault
            status_text.text("💾 Saving to knowledge vault...")
            progress_bar.progress(75)
            
            filepath = save_as_markdown(summary, title, url)
            
            # Complete
            progress_bar.progress(100)
            status_text.text("✅ Processing complete!")
            
            # Success message
            st.markdown(f"""
            <div class="success-message">
                <h3>🎉 Content Processed Successfully!</h3>
                <p><strong>Type:</strong> {content_type}</p>
                <p><strong>Title:</strong> {title}</p>
                <p><strong>Saved to:</strong> {os.path.basename(filepath)}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Show preview
            with st.expander("👁️ Preview Generated Content"):
                st.markdown(summary)
                
        except Exception as e:
            st.error(f"❌ Error processing content: {str(e)}")
        finally:
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()

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