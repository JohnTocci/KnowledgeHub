"""
Utility functions and enhancements for KnowledgeHub.
"""
import os
import re
import json
import hashlib
import mimetypes
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse
import streamlit as st


def validate_and_sanitize_url(url: str) -> Tuple[str, bool]:
    """
    Validate and sanitize URL input.
    
    Returns:
        Tuple of (sanitized_url, is_valid)
    """
    if not url or not url.strip():
        return "", False
    
    url = url.strip()
    
    # Remove common formatting artifacts
    url = url.replace('​', '')  # Remove zero-width space
    url = url.replace(' ', '')   # Remove spaces
    
    # Add protocol if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        parsed = urlparse(url)
        if not parsed.netloc:
            return "", False
        
        # Reconstruct clean URL
        clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if parsed.query:
            clean_url += f"?{parsed.query}"
        
        return clean_url, True
    except Exception:
        return "", False


def detect_content_type(url: str) -> str:
    """Detect content type from URL."""
    url_lower = url.lower()
    
    if any(domain in url_lower for domain in ['youtube.com', 'youtu.be']):
        return 'youtube'
    elif any(domain in url_lower for domain in ['vimeo.com', 'dailymotion.com']):
        return 'video'
    elif any(ext in url_lower for ext in ['.pdf', '.doc', '.docx']):
        return 'document'
    elif any(domain in url_lower for domain in ['arxiv.org', 'scholar.google']):
        return 'academic'
    elif any(domain in url_lower for domain in ['github.com', 'gitlab.com']):
        return 'code'
    else:
        return 'article'


def estimate_processing_time(url: str, content_length: Optional[int] = None) -> Dict[str, int]:
    """
    Estimate processing time based on content type and size.
    
    Returns:
        Dictionary with min and max time estimates in seconds
    """
    content_type = detect_content_type(url)
    
    estimates = {
        'youtube': {'min': 30, 'max': 300},    # Depends on video length
        'video': {'min': 30, 'max': 180},
        'article': {'min': 5, 'max': 30},
        'document': {'min': 10, 'max': 60},
        'academic': {'min': 10, 'max': 45},
        'code': {'min': 3, 'max': 15}
    }
    
    base_estimate = estimates.get(content_type, estimates['article'])
    
    # Adjust based on content length if available
    if content_length:
        if content_length > 100000:  # Large content
            base_estimate['min'] *= 1.5
            base_estimate['max'] *= 2
        elif content_length < 10000:  # Small content
            base_estimate['min'] *= 0.7
            base_estimate['max'] *= 0.8
    
    return {
        'min': int(base_estimate['min']),
        'max': int(base_estimate['max']),
        'type': content_type
    }


def get_file_icon(file_path: str) -> str:
    """Get appropriate icon for file type."""
    ext = os.path.splitext(file_path)[1].lower()
    
    icon_map = {
        '.md': '📄',
        '.pdf': '📕',
        '.doc': '📘',
        '.docx': '📘',
        '.txt': '📝',
        '.html': '🌐',
        '.json': '⚙️',
        '.csv': '📊',
        '.xlsx': '📈',
        '.png': '🖼️',
        '.jpg': '🖼️',
        '.jpeg': '🖼️',
        '.gif': '🖼️',
        '.webp': '🖼️'
    }
    
    return icon_map.get(ext, '📄')


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def format_time_ago(timestamp: datetime) -> str:
    """Format timestamp as 'time ago' string."""
    now = datetime.now()
    
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=now.tzinfo)
    
    diff = now - timestamp
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "Just now"


def create_content_preview(content: str, max_length: int = 200) -> str:
    """Create a preview of content with smart truncation."""
    if len(content) <= max_length:
        return content
    
    # Try to cut at sentence boundary
    truncated = content[:max_length]
    last_period = truncated.rfind('.')
    last_exclamation = truncated.rfind('!')
    last_question = truncated.rfind('?')
    
    best_cut = max(last_period, last_exclamation, last_question)
    
    if best_cut > max_length * 0.7:  # If we found a good sentence boundary
        return truncated[:best_cut + 1]
    else:
        # Cut at word boundary
        last_space = truncated.rfind(' ')
        if last_space > max_length * 0.8:
            return truncated[:last_space] + "..."
        else:
            return truncated + "..."


def extract_keywords_from_content(content: str, max_keywords: int = 10) -> List[str]:
    """Extract keywords from content using simple frequency analysis."""
    # Remove common words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 
        'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 
        'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
        'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
    }
    
    # Clean and split content
    words = re.findall(r'\b[a-zA-Z]{3,}\b', content.lower())
    
    # Count word frequency
    word_freq = {}
    for word in words:
        if word not in stop_words:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # Sort by frequency and return top keywords
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, freq in sorted_words[:max_keywords]]


def generate_content_hash(content: str) -> str:
    """Generate a hash for content to detect duplicates."""
    return hashlib.md5(content.encode()).hexdigest()[:16]


def create_backup_filename(original_path: str) -> str:
    """Create a backup filename with timestamp."""
    dir_path = os.path.dirname(original_path)
    filename = os.path.basename(original_path)
    name, ext = os.path.splitext(filename)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"{name}_backup_{timestamp}{ext}"
    
    return os.path.join(dir_path, backup_filename)


def safe_filename(text: str, max_length: int = 100) -> str:
    """Create a safe filename from text."""
    # Remove or replace problematic characters
    safe_text = re.sub(r'[<>:"/\\|?*]', '', text)
    safe_text = re.sub(r'\s+', '_', safe_text.strip())
    
    # Truncate if too long
    if len(safe_text) > max_length:
        safe_text = safe_text[:max_length]
    
    # Ensure it's not empty
    if not safe_text:
        safe_text = f"untitled_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    return safe_text


def check_disk_space(path: str, required_mb: int = 100) -> Tuple[bool, int]:
    """
    Check if there's enough disk space for operations.
    
    Returns:
        Tuple of (has_space, available_mb)
    """
    try:
        statvfs = os.statvfs(path)
        available_bytes = statvfs.f_frsize * statvfs.f_available
        available_mb = available_bytes / (1024 * 1024)
        
        return available_mb >= required_mb, int(available_mb)
    except Exception:
        return True, 0  # Assume OK if we can't check


def create_progress_message(step: str, progress: float, details: str = "") -> str:
    """Create a formatted progress message."""
    percentage = int(progress * 100)
    
    if details:
        return f"{step} ({percentage}%) - {details}"
    else:
        return f"{step} ({percentage}%)"


def suggest_related_topics(content: str, existing_files: List[str]) -> List[str]:
    """Suggest related topics based on content and existing files."""
    keywords = extract_keywords_from_content(content, 15)
    
    suggestions = []
    
    # Look for similar keywords in existing file names
    for file_path in existing_files:
        filename = os.path.basename(file_path).lower()
        for keyword in keywords:
            if keyword in filename and file_path not in suggestions:
                suggestions.append(os.path.basename(file_path))
                break
    
    return suggestions[:5]  # Return top 5 suggestions


class ContentAnalyzer:
    """Analyze content and provide insights."""
    
    @staticmethod
    def estimate_reading_time(content: str) -> int:
        """Estimate reading time in minutes (average 200 words per minute)."""
        word_count = len(content.split())
        return max(1, word_count // 200)
    
    @staticmethod
    def count_elements(content: str) -> Dict[str, int]:
        """Count various elements in content."""
        return {
            'words': len(content.split()),
            'characters': len(content),
            'paragraphs': len([p for p in content.split('\n\n') if p.strip()]),
            'sentences': len(re.findall(r'[.!?]+', content)),
            'urls': len(re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content)),
            'emails': len(re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content))
        }
    
    @staticmethod
    def detect_language(content: str) -> str:
        """Simple language detection based on common words."""
        # This is a very basic implementation
        english_words = {'the', 'and', 'is', 'in', 'to', 'of', 'a', 'that', 'it', 'with', 'for', 'as', 'was', 'on', 'are'}
        
        words = set(re.findall(r'\b[a-zA-Z]{2,}\b', content.lower()))
        english_count = len(words.intersection(english_words))
        
        if english_count >= 3:
            return 'English'
        else:
            return 'Unknown'
    
    @staticmethod
    def extract_dates(content: str) -> List[str]:
        """Extract dates from content."""
        date_patterns = [
            r'\b\d{1,2}/\d{1,2}/\d{4}\b',  # MM/DD/YYYY
            r'\b\d{4}-\d{2}-\d{2}\b',      # YYYY-MM-DD
            r'\b\d{1,2}-\d{1,2}-\d{4}\b',  # MM-DD-YYYY
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b'  # Month DD, YYYY
        ]
        
        dates = []
        for pattern in date_patterns:
            dates.extend(re.findall(pattern, content, re.IGNORECASE))
        
        return list(set(dates))  # Remove duplicates