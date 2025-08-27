"""
Web interface for KnowledgeHub.
Provides a web-based frontend for URL submission and file browsing.
"""
import os
import glob
import markdown
import sys
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from datetime import datetime

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
        import re
        sanitized_title = re.sub(r'[\\/*?:"<>|]', "", title)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        filepath = os.path.join(vault_path, f"{sanitized_title}.md")
        
        # Create markdown content
        markdown_content = f"""# {title}

**Source:** [{url}]({url})
**Date Processed:** {timestamp}

---

{content}
"""
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        print(f"✅ Demo note saved to: {filepath}")

    # Mock config for demo mode
    class MockConfig:
        def get_vault_path(self):
            return os.path.expanduser("~/KnowledgeHub")
        def get_openai_model(self):
            return "gpt-4 (Demo Mode)"
        def get_whisper_model(self):
            return "medium (Demo Mode)"
        def get_date_format(self):
            return "%Y-%m-%d %H:%M"
        def get_filename_template(self):
            return "{title}.md"
    
    config = MockConfig()
else:
    # Real mode - import actual functions
    from hub import get_article_text, get_youtube_transcription, summarize_text, save_as_markdown
    from config_manager import config

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')

@app.route('/')
def index():
    """Main page with URL submission form."""
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit_url():
    """Process URL submission."""
    url = request.form.get('url', '').strip()
    
    if not url:
        flash('Please enter a valid URL', 'error')
        return redirect(url_for('index'))
    
    try:
        # Determine URL type and process
        if "youtube.com" in url or "youtu.be" in url:
            text, title = get_youtube_transcription(url)
        else:
            text, title = get_article_text(url)
        
        if text and title:
            ai_summary = summarize_text(text, title)
            if ai_summary:
                save_as_markdown(ai_summary, title, url)
                flash(f'Successfully processed: {title}', 'success')
            else:
                flash('Failed to generate AI summary', 'error')
        else:
            flash('Failed to extract content from URL', 'error')
            
    except Exception as e:
        flash(f'Error processing URL: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/api/submit', methods=['POST'])
def api_submit_url():
    """API endpoint for URL submission."""
    data = request.get_json()
    url = data.get('url', '').strip()
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    try:
        # Determine URL type and process
        if "youtube.com" in url or "youtu.be" in url:
            text, title = get_youtube_transcription(url)
        else:
            text, title = get_article_text(url)
        
        if text and title:
            ai_summary = summarize_text(text, title)
            if ai_summary:
                save_as_markdown(ai_summary, title, url)
                return jsonify({'success': True, 'title': title})
            else:
                return jsonify({'error': 'Failed to generate AI summary'}), 500
        else:
            return jsonify({'error': 'Failed to extract content from URL'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/browse')
def browse_files():
    """Browse saved knowledge files."""
    vault_path = config.get_vault_path()
    
    # Get all markdown files from the vault
    files = []
    if os.path.exists(vault_path):
        md_files = glob.glob(os.path.join(vault_path, "*.md"))
        for file_path in sorted(md_files, key=os.path.getmtime, reverse=True):
            file_stat = os.stat(file_path)
            files.append({
                'name': os.path.basename(file_path),
                'path': file_path,
                'size': file_stat.st_size,
                'modified': datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M')
            })
    
    return render_template('browse.html', files=files, vault_path=vault_path)

@app.route('/view/<filename>')
def view_file(filename):
    """View a specific knowledge file."""
    vault_path = config.get_vault_path()
    file_path = os.path.join(vault_path, filename)
    
    # Security check - ensure file is within vault path
    if not os.path.abspath(file_path).startswith(os.path.abspath(vault_path)):
        flash('Invalid file path', 'error')
        return redirect(url_for('browse_files'))
    
    if not os.path.exists(file_path):
        flash('File not found', 'error')
        return redirect(url_for('browse_files'))
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Convert markdown to HTML for display
        html_content = markdown.markdown(content, extensions=['tables', 'fenced_code'])
        
        return render_template('view.html', 
                             filename=filename, 
                             content=content, 
                             html_content=html_content)
    except Exception as e:
        flash(f'Error reading file: {str(e)}', 'error')
        return redirect(url_for('browse_files'))

@app.route('/api/files')
def api_list_files():
    """API endpoint to list files."""
    vault_path = config.get_vault_path()
    
    files = []
    if os.path.exists(vault_path):
        md_files = glob.glob(os.path.join(vault_path, "*.md"))
        for file_path in sorted(md_files, key=os.path.getmtime, reverse=True):
            file_stat = os.stat(file_path)
            files.append({
                'name': os.path.basename(file_path),
                'size': file_stat.st_size,
                'modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat()
            })
    
    return jsonify({'files': files})

@app.route('/config')
def show_config():
    """Show current configuration."""
    config_info = {
        'vault_path': config.get_vault_path(),
        'openai_model': config.get_openai_model(),
        'whisper_model': config.get_whisper_model(),
        'date_format': config.get_date_format(),
        'filename_template': config.get_filename_template()
    }
    return render_template('config.html', config=config_info)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)