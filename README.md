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

## Build Windows .exe (No Python Needed for Tester)

Build the release executable on your machine:

```bat
build_release.bat
```

Alternative in PowerShell (if script policy allows):

```powershell
powershell -ExecutionPolicy Bypass -File .\build_release.ps1
```

## Create Ready-to-Send ZIP Release (One Click)

Create both the executable and a timestamped ZIP archive in `releases\`:

```bat
cmd /c make_release_zip.bat
```

Alternative in PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\make_release_zip.ps1
```

Output example:

```text
releases\ai_cases_chatbot-win64-YYYYMMDD-HHMMSS.zip
```

After build, share the entire folder:

```text
dist\ai_cases_chatbot\
```

### What your colleague needs to do

1. Open the shared folder `dist\ai_cases_chatbot\`.
2. Copy `.env.example` to `.env`.
3. Edit `.env` and set a valid API key:

```properties
API_KEY=your_api_key_here
```

4. Start `ai_cases_chatbot.exe`.

Notes:
- No Python installation is required on your colleague's PC.
- Internet access is required for API calls and Analysportalen lookups.
- Do not share a real `.env` file containing a private key.

## Security

- The `.env` file and conversation logs are excluded from version control via `.gitignore`.
- **Never share your `.env` file or API keys publicly.**

## License

MIT License
