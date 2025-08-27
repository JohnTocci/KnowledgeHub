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

Before running the script for the first time, you need to configure the destination for your notes.

-   Open the `hub.py` file.
-   Find the `KNOWLEDGE_VAULT_PATH` variable.
-   **Change the path** to the absolute path of the folder where you want your notes to be saved.

    ```python
    # Example for Windows
    KNOWLEDGE_VAULT_PATH = r"C:\Users\YourName\Documents\MyNotes"

    # Example for macOS/Linux
    KNOWLEDGE_VAULT_PATH = "/Users/yourname/Documents/MyNotes"
    ```
    *The script will automatically create this folder if it doesn't exist.*

---

## ▶️ Usage

With your virtual environment activated, simply run the script from the root directory:

```bash
python hub.py