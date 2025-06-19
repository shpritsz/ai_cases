# AI Chatbot for Interactive Clinical Case Studies in Biomedicine

This project is a Python-based AI chatbot designed to facilitate interactive clinical case studies in biomedicine. The chatbot provides a conversational interface for exploring biomedical scenarios, supporting both learning and assessment.

## Features

- Chatbot interface using OpenAI or similar APIs
- Designed for interactive clinical case studies in biomedicine
- Environment variable support via `.env` file
- Conversation logging to text files

## Setup

1. **Clone the repository:**
   ```sh
   git clone https://github.com/shpritsz/ai_cases.git
   cd ai_cases
   ```

2. **Create and activate a virtual environment:**
   ```sh
   python -m venv .venv
   # On Windows (PowerShell):
   .venv\Scripts\Activate
   # On macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

4. **Add your API key:**
   - Copy `.env.example` to `.env` and add your API key.

## Usage

Run the chatbot:
```sh
python chatbot.py
```

## Security

- The `.env` file and conversation logs are excluded from version control via `.gitignore`.
- **Never share your `.env` file or API keys publicly.**

## License

MIT License
