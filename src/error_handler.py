"""
Enhanced error handling and retry mechanisms for KnowledgeHub.
"""
import time
import logging
import streamlit as st
from typing import Callable, Any, Dict, List, Optional
from functools import wraps
import openai
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError


class KnowledgeHubError(Exception):
    """Base exception for KnowledgeHub errors."""
    
    def __init__(self, message: str, error_type: str = "general", 
                 user_action: str = None, retry_possible: bool = False):
        self.message = message
        self.error_type = error_type
        self.user_action = user_action
        self.retry_possible = retry_possible
        super().__init__(message)


class APIError(KnowledgeHubError):
    """API-related errors."""
    
    def __init__(self, message: str, api_name: str = "API", 
                 status_code: int = None, retry_possible: bool = True):
        self.api_name = api_name
        self.status_code = status_code
        user_action = self._get_user_action(api_name, status_code)
        super().__init__(message, "api", user_action, retry_possible)
    
    def _get_user_action(self, api_name: str, status_code: int) -> str:
        if api_name == "OpenAI":
            if status_code == 401:
                return "Please check your OpenAI API key in the configuration."
            elif status_code == 429:
                return "Rate limit reached. Please wait a moment and try again."
            elif status_code == 503:
                return "OpenAI service is temporarily unavailable. Please try again later."
        elif api_name == "YouTube":
            return "Failed to download YouTube content. Please verify the URL is correct and accessible."
        elif api_name == "Web":
            return "Failed to access the website. Please check the URL and your internet connection."
        
        return "Please check your internet connection and try again."


class ValidationError(KnowledgeHubError):
    """Input validation errors."""
    
    def __init__(self, message: str, field: str = None):
        self.field = field
        user_action = f"Please correct the {field} field." if field else "Please check your input."
        super().__init__(message, "validation", user_action, False)


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0, 
                      exponential: bool = True, exceptions: tuple = (Exception,)):
    """Decorator for retrying functions with exponential backoff."""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        break
                    
                    if exponential:
                        delay = base_delay * (2 ** attempt)
                    else:
                        delay = base_delay
                    
                    logging.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                                  f"Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)
            
            # If we get here, all retries failed
            if isinstance(last_exception, openai.APIError):
                raise APIError(
                    f"OpenAI API failed after {max_retries} attempts: {last_exception}",
                    "OpenAI",
                    getattr(last_exception, 'status_code', None)
                )
            elif isinstance(last_exception, (RequestException, Timeout, ConnectionError)):
                raise APIError(
                    f"Network request failed after {max_retries} attempts: {last_exception}",
                    "Web"
                )
            else:
                raise last_exception
        
        return wrapper
    return decorator


def validate_url(url: str) -> str:
    """Validate and normalize URL input."""
    if not url or not url.strip():
        raise ValidationError("URL cannot be empty", "URL")
    
    url = url.strip()
    
    # Add protocol if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Basic URL validation
    if not any(domain in url.lower() for domain in ['youtube.com', 'youtu.be']) and \
       not url.startswith(('http://', 'https://')):
        raise ValidationError("Invalid URL format", "URL")
    
    return url


def display_error(error: Exception, show_retry: bool = False) -> bool:
    """Display error message in Streamlit with appropriate styling and actions."""
    
    if isinstance(error, KnowledgeHubError):
        # Custom error with structured information
        st.error(f"**{error.error_type.title()} Error:** {error.message}")
        
        if error.user_action:
            st.info(f"**Suggested Action:** {error.user_action}")
        
        if show_retry and error.retry_possible:
            return st.button("🔄 Retry", type="secondary")
            
    else:
        # Generic error
        st.error(f"**Unexpected Error:** {str(error)}")
        if show_retry:
            return st.button("🔄 Retry", type="secondary")
    
    return False


def log_error(error: Exception, context: Dict[str, Any] = None):
    """Log error with context for debugging."""
    context_str = ""
    if context:
        context_str = " | Context: " + ", ".join([f"{k}={v}" for k, v in context.items()])
    
    logging.error(f"KnowledgeHub Error: {error}{context_str}", exc_info=True)


def get_error_recovery_suggestions(error: Exception) -> List[str]:
    """Get specific recovery suggestions based on error type."""
    suggestions = []
    
    if isinstance(error, APIError):
        if error.api_name == "OpenAI":
            suggestions.extend([
                "Verify your OpenAI API key is valid",
                "Check your OpenAI account billing status",
                "Try again in a few minutes if rate limited"
            ])
        elif error.api_name == "YouTube":
            suggestions.extend([
                "Ensure the YouTube URL is publicly accessible",
                "Try a different YouTube video",
                "Check if the video has captions available"
            ])
        elif error.api_name == "Web":
            suggestions.extend([
                "Verify the website URL is correct",
                "Check if the website requires authentication",
                "Try accessing the site in your browser first"
            ])
    
    elif isinstance(error, ValidationError):
        suggestions.extend([
            "Double-check the URL format",
            "Ensure the URL includes the protocol (https://)",
            "Try copying the URL directly from your browser"
        ])
    
    else:
        suggestions.extend([
            "Check your internet connection",
            "Restart the application if the issue persists",
            "Contact support if the problem continues"
        ])
    
    return suggestions


def create_error_context(operation: str, **kwargs) -> Dict[str, Any]:
    """Create error context for logging."""
    context = {"operation": operation}
    context.update(kwargs)
    return context