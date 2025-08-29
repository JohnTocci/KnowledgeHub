# Automated Personal Knowledge Hub

This Python script automates the process of learning and retention by capturing content from web articles and YouTube videos, summarizing it with AI, and saving it as a clean Markdown file in a local folder for your personal knowledge base (like Obsidian, Joplin, or any text editor).

---

## 💡 The Problem It Solves

We consume vast amounts of information online, but most of it is forgotten. This tool acts as an automated "read-it-later" service with a powerful summarization engine, creating a permanent, searchable, and personal library of the content that matters most to you, with almost zero effort.

---

## ✨ Features

-   **Dual Source Support:** Processes both standard web articles and YouTube videos.
-   **Intelligent Content Extraction:** Uses `newspaper3k` to cleanly scrape article text, ignoring ads and boilerplate.
-   **Video Transcription:** Downloads audio from YouTube videos and uses OpenAI's Whisper model for accurate transcription.
-   **AI-Powered Summarization:** Leverages a powerful language model (e.g., GPT-4o) to generate a concise summary, a bulleted list of key takeaways, and relevant tags for categorization.
-   **Automatic Note Creation:** Saves the structured output as a well-formatted Markdown (`.md`) file, ready for any note-taking app.
-   **Local First:** All your notes are saved directly to a folder on your computer, ensuring you own and control your data.

---

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

-   [Python 3.8+](https://www.python.org/downloads/)
-   [FFmpeg](https://ffmpeg.org/download.html) (Required for audio processing from videos). Make sure it's installed and accessible in your system's PATH.

---

## 🚀 Setup & Installation

1.  **Clone or Download the Project:**
    Get the project files onto your local machine.

2.  **Create a Virtual Environment:**
    Navigate to the project's root directory in your terminal and create a virtual environment to isolate dependencies.
    ```bash
    python -m venv .venv
    ```

3.  **Activate the Virtual Environment:**
    -   **Windows (CMD):**
        ```cmd
        .venv\Scripts\activate
        ```
    -   **macOS/Linux:**
        ```bash
        source .venv/bin/activate
        ```

4.  **Install Dependencies:**
    Install all the required Python packages from the `requirements.txt` file.
    ```bash
    pip install -r requirements.txt
    ```

5.  **Create the Environment File:**
    Create a `.env` file in the root directory to securely store your API key. Add the following line, replacing `sk-...` with your actual key:
    ```
    OPENAI_API_KEY="sk-YourActualApiKeyGoesHere"
    ```

---

## ⚙️ Configuration

The KnowledgeHub can be customized using a `config.json` file. If no configuration file exists, the application will use sensible defaults.

### Creating Your Configuration

1.  **Copy the example configuration:**
    ```bash
    cp config.example.json config.json
    ```

2.  **Edit the `config.json` file** to customize the following settings:

    -   **`knowledge_vault_path`**: The folder where your notes will be saved (default: `~/KnowledgeHub`)
    -   **`openai_model`**: The OpenAI model to use for summarization (default: `gpt-4o-mini`)
    -   **`whisper_model`**: The Whisper model for transcription (options: `tiny`, `base`, `small`, `medium`, `large`)
    -   **`date_format`**: Date format for timestamps (default: `%Y-%m-%d %H:%M`)
    -   **`filename_template`**: Template for saved file names (default: `{title}.md`)
    -   **`markdown_template`**: Customize the markdown file format
    -   **`youtube_download`**: YouTube audio download settings
    -   **`summarization_prompt`**: Customize the AI prompt for content summarization
    -   **`system_prompt`**: Customize the AI system prompt

### Example Configuration

```json
{
  "knowledge_vault_path": "~/Documents/MyKnowledgeBase",
  "openai_model": "gpt-4o-mini",
  "whisper_model": "small",
  "date_format": "%Y-%m-%d",
  "filename_template": "{title} - {timestamp}.md"
}
```

The application will automatically create the knowledge vault directory if it doesn't exist.

---

## ▶️ Usage

KnowledgeHub offers both a modern web interface and a command-line interface:

### 🌐 Web Interface (Recommended)

Launch the beautiful, modern web interface:

```bash
streamlit run streamlit_app.py
```

Then open your browser to `http://localhost:8501` to access the web interface.

**Features:**
- 📱 **Mobile-responsive design** - works perfectly on phones and tablets
- 🎨 **Visually appealing interface** with modern styling
- 📊 **Analytics dashboard** to track your knowledge vault
- 🔍 **Search and browse** your files with advanced filtering
- 📖 **Built-in file viewer** with markdown rendering
- ⚙️ **Configuration management** through the UI

### 💻 Command Line Interface

For power users who prefer the terminal:

```bash
python src/hub.py