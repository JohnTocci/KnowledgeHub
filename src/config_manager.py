"""
Configuration manager for KnowledgeHub.
Handles loading and validating configuration from config.json file.
"""
import json
import os
from pathlib import Path

class Config:
    """Configuration manager for KnowledgeHub application."""
    
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self):
        """Load configuration from file, falling back to defaults if file doesn't exist."""
        config_path = Path(self.config_file)
        
        # Default configuration
        default_config = {
            "knowledge_vault_path": "~/KnowledgeHub",
            "openai_model": "gpt-5-mini",
            "whisper_model": "medium",
            "date_format": "%Y-%m-%d %H:%M",
            "filename_template": "{title}.md",
            "markdown_template": {
                "header": "# {title}\n\n**Source:** [{url}]({url})\n**Date Processed:** {timestamp}\n\n---\n\n",
                "content": "{content}\n"
            },
            "youtube_download": {
                "format": "bestaudio/best",
                "audio_codec": "mp3",
                "audio_quality": "192"
            },
            "summarization_prompt": "Analyze the following text from a source titled \"{title}\".\n\nTEXT:\n\"{text}\"\n\nADDITIONAL CONTEXT:\n{context}\n\nBased on the text, please provide the following in a clear, well-structured format:\n1.  **Summary:** A concise summary of the main points.\n2.  **Key Takeaways:** A bulleted list of the most important insights or actionable items.\n3.  **Data Insights:** Extract any numerical data, statistics, dates, or quantifiable information and present as a table or list.\n4.  **Visual Elements:** If images were found, describe how they relate to the content and suggest relevant data visualizations.\n5.  **Suggested Tags:** A short, comma-separated list of 3-5 relevant keywords or tags for categorization.",
            "system_prompt": "You are an advanced AI assistant that summarizes content for a personal knowledge base. You excel at extracting data insights, identifying visual patterns, and creating structured summaries that include both textual analysis and data visualization suggestions."
        }
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                # Merge loaded config with defaults (loaded config takes precedence)
                merged_config = {**default_config, **loaded_config}
                # Ensure nested dictionaries are properly merged
                if "markdown_template" in loaded_config:
                    merged_config["markdown_template"] = {**default_config["markdown_template"], **loaded_config["markdown_template"]}
                if "youtube_download" in loaded_config:
                    merged_config["youtube_download"] = {**default_config["youtube_download"], **loaded_config["youtube_download"]}
                return merged_config
            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"⚠️  Warning: Could not load config file ({e}). Using defaults.")
                return default_config
        else:
            print(f"ℹ️  Config file '{config_path}' not found. Using default configuration.")
            return default_config
    
    def get(self, key, default=None):
        """Get a configuration value by key."""
        return self.config.get(key, default)
    
    def get_vault_path(self):
        """Get the knowledge vault path, expanding user home directory."""
        path = self.config.get("knowledge_vault_path", "~/KnowledgeHub")
        return os.path.expanduser(path)
    
    def get_openai_model(self):
        """Get the OpenAI model to use."""
        return self.config.get("openai_model", "gpt-5-mini")
    
    def get_whisper_model(self):
        """Get the Whisper model to use."""
        return self.config.get("whisper_model", "medium")
    
    def get_date_format(self):
        """Get the date format string."""
        return self.config.get("date_format", "%Y-%m-%d %H:%M")
    
    def get_filename_template(self):
        """Get the filename template."""
        return self.config.get("filename_template", "{title}.md")
    
    def get_markdown_template(self):
        """Get the markdown template."""
        return self.config.get("markdown_template", {
            "header": "# {title}\n\n**Source:** [{url}]({url})\n**Date Processed:** {timestamp}\n\n---\n\n",
            "content": "{content}\n"
        })
    
    def get_youtube_options(self):
        """Get YouTube download options."""
        return self.config.get("youtube_download", {
            "format": "bestaudio/best",
            "audio_codec": "mp3",
            "audio_quality": "192"
        })
    
    def get_summarization_prompt(self):
        """Get the AI summarization prompt template."""
        return self.config.get("summarization_prompt", 
            "Analyze the following text from a source titled \"{title}\".\n\nTEXT:\n\"{text}\"\n\nBased on the text, please provide the following in a clear, well-structured format:\n1.  **Summary:** A concise summary of the main points.\n2.  **Key Takeaways:** A bulleted list of the most important insights or actionable items.\n3.  **Suggested Tags:** A short, comma-separated list of 3-5 relevant keywords or tags for categorization.")
    
    def get_system_prompt(self):
        """Get the AI system prompt."""
        return self.config.get("system_prompt", "You are a helpful assistant that summarizes content for a personal knowledge base.")

# Global configuration instance
config = Config()