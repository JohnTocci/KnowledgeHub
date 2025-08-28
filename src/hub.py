import whisper
import yt_dlp
import os
import openai
from newspaper import Article
import re
from datetime import datetime
from dotenv import load_dotenv
from config_manager import config
import requests
import urllib.parse
from PIL import Image
from io import BytesIO
import logging
from error_handler import (
    retry_with_backoff, APIError, ValidationError, KnowledgeHubError,
    validate_url, log_error, create_error_context
)

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@retry_with_backoff(max_retries=3, exceptions=(requests.RequestException, ConnectionError))
def get_article_text(url):
    """Downloads and extracts the clean text from a web article with images."""
    context = create_error_context("get_article_text", url=url)
    
    try:
        # Validate URL
        url = validate_url(url)
        
        article = Article(url)
        article.download()
        article.parse()
        
        # Validate extracted content
        if not article.text or len(article.text.strip()) < 50:
            raise APIError(
                "Article content is too short or empty. The website might require authentication or block automated access.",
                "Web"
            )
        
        if not article.title:
            article.title = "Untitled Article"
        
        extracted_data = {
            'text': article.text,
            'title': article.title,
            'authors': article.authors or [],
            'publish_date': article.publish_date,
            'top_image': article.top_image,
            'images': list(article.images) if article.images else [],
            'meta_description': article.meta_description or "",
            'meta_keywords': article.meta_keywords or []
        }
        
        logging.info(f"Article content fetched successfully: {len(extracted_data['text'])} chars, {len(extracted_data['images'])} images")
        
        return extracted_data
        
    except ValidationError:
        raise  # Re-raise validation errors as-is
    except requests.RequestException as e:
        log_error(e, context)
        raise APIError(f"Failed to download article: {str(e)}", "Web")
    except Exception as e:
        log_error(e, context)
        raise APIError(f"Failed to parse article content: {str(e)}", "Web")

def download_and_save_images(images, title, vault_path):
    """Download and save article images locally."""
    if not images:
        return []
    
    context = create_error_context("download_and_save_images", title=title, image_count=len(images))
    
    try:
        # Create images directory for this article
        sanitized_title = re.sub(r'[\\/*?:"<>|]', "", title)
        if not sanitized_title:
            sanitized_title = f"images_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        images_dir = os.path.join(vault_path, f"{sanitized_title}_images")
        os.makedirs(images_dir, exist_ok=True)
        
        saved_images = []
        
        # Limit to reasonable number of images
        max_images = min(len(images), 5)
        
        for i, img_url in enumerate(images[:max_images]):
            try:
                # Validate URL
                if not img_url or not img_url.startswith(('http://', 'https://')):
                    logging.warning(f"Skipping invalid image URL: {img_url}")
                    continue
                
                # Download with timeout and size limit
                response = requests.get(
                    img_url, 
                    timeout=15,
                    stream=True,
                    headers={'User-Agent': 'Mozilla/5.0 (compatible; KnowledgeHub/1.0)'}
                )
                
                if response.status_code != 200:
                    logging.warning(f"Failed to download image {img_url}: HTTP {response.status_code}")
                    continue
                
                # Check content length
                content_length = response.headers.get('content-length')
                if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB limit
                    logging.warning(f"Skipping large image {img_url}: {content_length} bytes")
                    continue
                
                # Determine file extension
                content_type = response.headers.get('content-type', '').lower()
                if 'jpeg' in content_type or 'jpg' in content_type:
                    ext = '.jpg'
                elif 'png' in content_type:
                    ext = '.png'
                elif 'gif' in content_type:
                    ext = '.gif'
                elif 'webp' in content_type:
                    ext = '.webp'
                else:
                    ext = '.jpg'  # Default
                
                # Save image
                filename = f"image_{i+1}{ext}"
                filepath = os.path.join(images_dir, filename)
                
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Verify the file was created and has content
                if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                    saved_images.append({
                        'filename': filename,
                        'path': filepath,
                        'url': img_url
                    })
                    logging.info(f"Saved image: {filename} ({os.path.getsize(filepath)} bytes)")
                else:
                    logging.warning(f"Failed to save image {filename}")
                    if os.path.exists(filepath):
                        os.remove(filepath)
                
            except requests.RequestException as e:
                logging.warning(f"Failed to download image {img_url}: {e}")
                continue
            except Exception as e:
                logging.warning(f"Unexpected error downloading image {img_url}: {e}")
                continue
        
        logging.info(f"Successfully downloaded {len(saved_images)} out of {len(images)} images")
        return saved_images
        
    except Exception as e:
        log_error(e, context)
        return []  # Return empty list instead of failing the entire process

@retry_with_backoff(max_retries=2, exceptions=(Exception,))
def get_youtube_transcription(url):
    """Downloads a YouTube video's audio and transcribes it."""
    context = create_error_context("get_youtube_transcription", url=url)
    
    try:
        # Validate URL
        url = validate_url(url)
        if not any(domain in url.lower() for domain in ['youtube.com', 'youtu.be']):
            raise ValidationError("URL must be a valid YouTube video link", "URL")
        
        youtube_options = config.get_youtube_options()
        
        ydl_opts = {
            'format': youtube_options['format'],
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': youtube_options['audio_codec'],
                'preferredquality': youtube_options['audio_quality'],
            }],
            'outtmpl': 'temp_audio.%(ext)s',
            'quiet': True,
        }
        
        # Check for custom ffmpeg location in config and add it if it exists
        ffmpeg_location = config.get("ffmpeg_location")
        if ffmpeg_location:
            ydl_opts['ffmpeg_location'] = ffmpeg_location
            logging.info(f"Using FFmpeg from: {ffmpeg_location}")

        # Download video audio
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                video_title = info_dict.get('title', 'Unknown Video Title')
            
            logging.info("YouTube audio downloaded successfully")
        except Exception as e:
            raise APIError(f"Failed to download YouTube audio: {str(e)}", "YouTube")
        
        # Check if audio file was created
        if not os.path.exists("temp_audio.mp3"):
            raise APIError("Audio file was not created properly", "YouTube")
        
        # Transcribe audio
        try:
            logging.info("Starting transcription...")
            model = whisper.load_model(config.get_whisper_model())
            result = model.transcribe("temp_audio.mp3")
            transcription = result["text"]
            
            if not transcription or len(transcription.strip()) < 10:
                raise APIError("Transcription resulted in empty or very short text", "YouTube")
            
            logging.info(f"Transcription complete: {len(transcription)} characters")
        except Exception as e:
            raise APIError(f"Failed to transcribe audio: {str(e)}", "YouTube")
        finally:
            # Clean up audio file
            if os.path.exists("temp_audio.mp3"):
                os.remove("temp_audio.mp3")
        
        return transcription, video_title
        
    except ValidationError:
        raise  # Re-raise validation errors as-is
    except APIError:
        raise  # Re-raise API errors as-is
    except Exception as e:
        log_error(e, context)
        # Clean up any leftover files
        if os.path.exists("temp_audio.mp3"):
            os.remove("temp_audio.mp3")
        raise APIError(f"Unexpected error during YouTube processing: {str(e)}", "YouTube")

client = openai.OpenAI()

@retry_with_backoff(max_retries=3, exceptions=(openai.APIError, openai.RateLimitError, openai.InternalServerError))
def summarize_text(text, title, additional_context=""):
    """Uses OpenAI's API to summarize text, extract takeaways, and suggest tags."""
    context = create_error_context("summarize_text", title=title, text_length=len(text))
    
    try:
        # Validate inputs
        if not text or len(text.strip()) < 10:
            raise ValidationError("Text content is too short to summarize", "content")
        
        if not title:
            title = "Untitled Content"
        
        # Truncate text if too long (OpenAI has token limits)
        max_chars = 50000  # Approximate token limit safety
        if len(text) > max_chars:
            text = text[:max_chars] + "... [Content truncated for processing]"
            logging.warning(f"Text truncated to {max_chars} characters for API processing")
        
        logging.info("Calling OpenAI for summarization...")
        
        prompt = config.get_summarization_prompt().format(
            title=title, 
            text=text,
            context=additional_context if additional_context else "No additional context provided."
        )
        
        response = client.chat.completions.create(
            model=config.get_openai_model(),
            messages=[
                {"role": "system", "content": config.get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4000
        )
        
        summary = response.choices[0].message.content
        
        if not summary or len(summary.strip()) < 20:
            raise APIError("Received empty or very short summary from OpenAI", "OpenAI")
        
        logging.info("AI summary received successfully")
        return summary
        
    except ValidationError:
        raise  # Re-raise validation errors as-is
    except openai.AuthenticationError as e:
        log_error(e, context)
        raise APIError("Invalid OpenAI API key", "OpenAI", 401)
    except openai.RateLimitError as e:
        log_error(e, context)
        raise APIError("OpenAI rate limit exceeded", "OpenAI", 429)
    except openai.InternalServerError as e:
        log_error(e, context)
        raise APIError("OpenAI service temporarily unavailable", "OpenAI", 503)
    except openai.APIError as e:
        log_error(e, context)
        raise APIError(f"OpenAI API error: {str(e)}", "OpenAI", getattr(e, 'status_code', None))
    except Exception as e:
        log_error(e, context)
        raise APIError(f"Unexpected error during summarization: {str(e)}", "OpenAI")
    
def save_as_markdown(content, title, url, saved_images=None, metadata=None):
    """Saves the content as a Markdown file with image references."""
    context = create_error_context("save_as_markdown", title=title, url=url)
    
    try:
        # Validate inputs
        if not content or len(content.strip()) < 10:
            raise ValidationError("Content is too short to save", "content")
        
        if not title:
            title = "Untitled Content"
        
        # Sanitize the title to make it a valid filename
        sanitized_title = re.sub(r'[\\/*?:"<>|]', "", title)
        if not sanitized_title:
            sanitized_title = f"content_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Get filename template and format it
        filename_template = config.get_filename_template()
        filename = filename_template.format(title=sanitized_title)
        
        # Ensure .md extension
        if not filename.endswith('.md'):
            filename += '.md'
        
        # Ensure directory exists
        vault_path = config.get_vault_path()
        os.makedirs(vault_path, exist_ok=True)
        
        filepath = os.path.join(vault_path, filename)
        
        # Handle duplicate filenames
        counter = 1
        original_filepath = filepath
        while os.path.exists(filepath):
            name, ext = os.path.splitext(original_filepath)
            filepath = f"{name}_{counter}{ext}"
            counter += 1
        
        # Format the final content for the Markdown file
        timestamp = datetime.now().strftime(config.get_date_format())
        
        # Get markdown template
        markdown_template = config.get_markdown_template()
        header = markdown_template['header'].format(title=title, url=url, timestamp=timestamp)
        
        # Add metadata section if available
        metadata_section = ""
        if metadata:
            metadata_section += "\n## Metadata\n\n"
            if metadata.get('authors'):
                metadata_section += f"**Authors:** {', '.join(metadata['authors'])}\n\n"
            if metadata.get('publish_date'):
                metadata_section += f"**Published:** {metadata['publish_date']}\n\n"
            if metadata.get('meta_description'):
                metadata_section += f"**Description:** {metadata['meta_description']}\n\n"
            if metadata.get('meta_keywords'):
                metadata_section += f"**Keywords:** {', '.join(metadata['meta_keywords'])}\n\n"
        
        # Add images section if available
        images_section = ""
        if saved_images:
            images_section += "\n## Related Images\n\n"
            for img in saved_images:
                # Use relative path for markdown
                relative_path = f"{sanitized_title}_images/{img['filename']}"
                images_section += f"![{img['filename']}]({relative_path})\n\n"
                images_section += f"*Source: [Original Image]({img['url']})*\n\n"
        
        content_section = markdown_template['content'].format(content=content)
        
        markdown_content = header + metadata_section + content_section + images_section
        
        # Write file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        
        logging.info(f"Note saved successfully to: {filepath}")
        return filepath
        
    except ValidationError:
        raise  # Re-raise validation errors as-is
    except PermissionError as e:
        log_error(e, context)
        raise KnowledgeHubError(
            f"Permission denied when saving file: {str(e)}",
            "filesystem",
            "Check that you have write permissions to the knowledge vault directory"
        )
    except OSError as e:
        log_error(e, context)
        raise KnowledgeHubError(
            f"File system error when saving: {str(e)}",
            "filesystem",
            "Check available disk space and directory permissions"
        )
    except Exception as e:
        log_error(e, context)
        raise KnowledgeHubError(f"Unexpected error saving file: {str(e)}", "filesystem")
        
def main():
    """The main function to run the knowledge hub script."""
    print(f"📂 Knowledge Vault: {config.get_vault_path()}")
    print(f"🤖 AI Model: {config.get_openai_model()}")
    print(f"🎤 Whisper Model: {config.get_whisper_model()}")
    print("---")
    
    input_url = input("Enter a URL (article or YouTube): ")
    
    if "youtube.com" in input_url or "youtu.be" in input_url:
        print("YouTube URL detected.")
        text, title = get_youtube_transcription(input_url)
        saved_images = []
        metadata = {}
        additional_context = "Content source: YouTube video transcription"
    else:
        print("Article URL detected.")
        article_data = get_article_text(input_url)
        if article_data:
            text = article_data['text']
            title = article_data['title']
            
            # Download images
            vault_path = config.get_vault_path()
            saved_images = download_and_save_images(article_data['images'], title, vault_path)
            
            # Prepare metadata
            metadata = {
                'authors': article_data['authors'],
                'publish_date': article_data['publish_date'],
                'meta_description': article_data['meta_description'],
                'meta_keywords': article_data['meta_keywords']
            }
            
            # Prepare additional context for AI
            additional_context = f"""
            Content source: Web article
            Number of images found: {len(article_data['images'])}
            Authors: {', '.join(article_data['authors']) if article_data['authors'] else 'Unknown'}
            Publication date: {article_data['publish_date'] if article_data['publish_date'] else 'Unknown'}
            Meta description: {article_data['meta_description'] if article_data['meta_description'] else 'None'}
            """
        else:
            text, title = None, None
            saved_images = []
            metadata = {}
            additional_context = ""

    if text and title:
        ai_summary = summarize_text(text, title, additional_context)
        if ai_summary:
            save_as_markdown(ai_summary, title, input_url, saved_images, metadata)

if __name__ == "__main__":
    main()