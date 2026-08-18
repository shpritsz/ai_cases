import openai
import os
import sys
from dotenv import load_dotenv

def get_runtime_base_dir():
	if getattr(sys, "frozen", False):
		return os.path.dirname(sys.executable)
	return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = get_runtime_base_dir()


def load_env_file():
	candidates = [
		os.path.join(BASE_DIR, ".env"),
		os.path.join(os.getcwd(), ".env"),
		os.path.join(getattr(sys, "_MEIPASS", BASE_DIR), ".env"),
	]
	for path in candidates:
		if os.path.exists(path):
			load_dotenv(dotenv_path=path)
			return
	# Fall back to default dotenv search behavior.
	load_dotenv()


load_env_file()
api_key = os.getenv("API_KEY")

client = openai.OpenAI(api_key=api_key)