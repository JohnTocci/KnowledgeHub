import whisper
import yt_dlp
import os
import openai
from newspaper import Article
import re
from datetime import datetime
from dotenv import load_dotenv

KNOWLEDGE_VAULT_PATH = r"C:\Users\johnt\OneDrive\Documents\MyKnowledgeHub\KnowledgeHub"
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
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
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
        model = whisper.load_model("medium") # "base" is fast and good, "medium" is better
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
    
    prompt = f"""
    Analyze the following text from a source titled "{title}".

    TEXT:
    "{text}"

    Based on the text, please provide the following in a clear, well-structured format:
    1.  **Summary:** A concise summary of the main points.
    2.  **Key Takeaways:** A bulleted list of the most important insights or actionable items.
    3.  **Suggested Tags:** A short, comma-separated list of 3-5 relevant keywords or tags for categorization.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes content for a personal knowledge base."},
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
    filename = f"{sanitized_title}.md"
    filepath = os.path.join(KNOWLEDGE_VAULT_PATH, filename)
    
    # Format the final content for the Markdown file
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    markdown_content = f"""# {title}

**Source:** [{url}]({url})
**Date Processed:** {timestamp}

---

{content}
"""
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        print(f"✅ Note saved successfully to: {filepath}")
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        
def main():
    """The main function to run the knowledge hub script."""
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