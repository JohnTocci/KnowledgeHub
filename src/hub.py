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

load_dotenv()

def get_article_text(url):
    """Downloads and extracts the clean text from a web article with images."""
    try:
        article = Article(url)
        article.download()
        article.parse()
        
        extracted_data = {
            'text': article.text,
            'title': article.title,
            'authors': article.authors,
            'publish_date': article.publish_date,
            'top_image': article.top_image,
            'images': list(article.images),
            'meta_description': article.meta_description,
            'meta_keywords': article.meta_keywords
        }
        
        print("✅ Article content fetched successfully.")
        print(f"📸 Found {len(extracted_data['images'])} images")
        
        return extracted_data
    except Exception as e:
        print(f"❌ Failed to fetch article content: {e}")
        return None

def download_and_save_images(images, title, vault_path):
    """Download and save article images locally."""
    if not images:
        return []
    
    # Create images directory for this article
    sanitized_title = re.sub(r'[\\/*?:"<>|]', "", title)
    images_dir = os.path.join(vault_path, f"{sanitized_title}_images")
    os.makedirs(images_dir, exist_ok=True)
    
    saved_images = []
    for i, img_url in enumerate(images[:5]):  # Limit to 5 images
        try:
            response = requests.get(img_url, timeout=10)
            if response.status_code == 200:
                # Determine file extension
                content_type = response.headers.get('content-type', '')
                if 'jpeg' in content_type or 'jpg' in content_type:
                    ext = '.jpg'
                elif 'png' in content_type:
                    ext = '.png'
                elif 'gif' in content_type:
                    ext = '.gif'
                else:
                    ext = '.jpg'  # Default
                
                # Save image
                filename = f"image_{i+1}{ext}"
                filepath = os.path.join(images_dir, filename)
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                saved_images.append({
                    'filename': filename,
                    'path': filepath,
                    'url': img_url
                })
                print(f"📸 Saved image: {filename}")
                
        except Exception as e:
            print(f"❌ Failed to download image {img_url}: {e}")
            continue
    
    return saved_images

def get_youtube_transcription(url):
    """Downloads a YouTube video's audio and transcribes it."""
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
        print(f"✅ Using FFmpeg from: {ffmpeg_location}")


    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            video_title = info_dict.get('title', 'Unknown Video Title')
        
        print("✅ YouTube audio downloaded.")
        
        print("Transcribing audio... (this may take a moment)")
        model = whisper.load_model(config.get_whisper_model())
        result = model.transcribe("temp_audio.mp3")
        transcription = result["text"]
        
        print("✅ Transcription complete.")

        os.remove("temp_audio.mp3")
        
        return transcription, video_title
    except Exception as e:
        print(f"❌ Error processing YouTube video: {e}")
        return None, None

client = openai.OpenAI()

def summarize_text(text, title, additional_context=""):
    """Uses OpenAI's API to summarize text, extract takeaways, and suggest tags."""
    print("🤖 Calling AI for summarization...")
    
    prompt = config.get_summarization_prompt().format(
        title=title, 
        text=text,
        context=additional_context if additional_context else "No additional context provided."
    )
    
    try:
        response = client.chat.completions.create(
            model=config.get_openai_model(),
            messages=[
                {"role": "system", "content": config.get_system_prompt()},
                {"role": "user", "content": prompt}
            ]
        )
        print("✅ AI summary received.")
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ Error calling OpenAI API: {e}")
        return None
    
def save_as_markdown(content, title, url, saved_images=None, metadata=None):
    """Saves the content as a Markdown file with image references."""
    # Sanitize the title to make it a valid filename
    sanitized_title = re.sub(r'[\\/*?:"<>|]', "", title)
    
    # Get filename template and format it
    filename_template = config.get_filename_template()
    filename = filename_template.format(title=sanitized_title)
    
    # Ensure directory exists
    vault_path = config.get_vault_path()
    os.makedirs(vault_path, exist_ok=True)
    
    filepath = os.path.join(vault_path, filename)
    
    # Format the final content for the Markdown file
    timestamp = datetime.now().strftime(config.get_date_format())
    
    # Get markdown template
    markdown_template = config.get_markdown_template()
    header = markdown_template['header'].format(title=title, url=url, timestamp=timestamp)
    
    # Add metadata section if available
    metadata_section = ""
    if metadata:
        metadata_section += "\n## 📋 Metadata\n\n"
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
        images_section += "\n## 🖼️ Related Images\n\n"
        for img in saved_images:
            # Use relative path for markdown
            relative_path = f"{sanitized_title}_images/{img['filename']}"
            images_section += f"![{img['filename']}]({relative_path})\n\n"
            images_section += f"*Source: [Original Image]({img['url']})*\n\n"
    
    content_section = markdown_template['content'].format(content=content)
    
    markdown_content = header + metadata_section + content_section + images_section
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        print(f"✅ Note saved successfully to: {filepath}")
        return filepath
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        return None
        
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