import whisper
import yt_dlp
import os
import openai
from newspaper import Article
import re
from datetime import datetime
from dotenv import load_dotenv
from config_manager import config

load_dotenv()

def get_article_text(url):
    """Downloads and extracts the clean text from a web article."""
    try:
        article = Article(url)
        article.download()
        article.parse()
        print("✅ Article content fetched successfully.")
        return article.text, article.title
    except Exception as e:
        print(f"❌ Failed to fetch article content: {e}")
        return None, None

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

def summarize_text(text, title):
    """Uses OpenAI's API to summarize text, extract takeaways, and suggest tags."""
    print("🤖 Calling AI for summarization...")
    
    prompt = config.get_summarization_prompt().format(title=title, text=text)
    
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
    
def save_as_markdown(content, title, url):
    """Saves the content as a Markdown file."""
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
    content_section = markdown_template['content'].format(content=content)
    
    markdown_content = header + content_section
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        print(f"✅ Note saved successfully to: {filepath}")
        return filepath
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        
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
    else:
        print("Article URL detected.")
        text, title = get_article_text(input_url)

    if text and title:
        ai_summary = summarize_text(text, title)
        if ai_summary:
            save_as_markdown(ai_summary, title, input_url)

if __name__ == "__main__":
    main()