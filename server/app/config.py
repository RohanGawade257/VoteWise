import os
from dotenv import load_dotenv

# Load .env from the server/ directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

class Settings:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    PORT: int = int(os.getenv("PORT", 8080))
    ALLOWED_ORIGIN: str = os.getenv("ALLOWED_ORIGIN", "http://localhost:5173")
    ENABLE_GOOGLE_SEARCH_GROUNDING: bool = os.getenv("ENABLE_GOOGLE_SEARCH_GROUNDING", "false").lower() == "true"
    NODE_ENV: str = os.getenv("NODE_ENV", "development")

settings = Settings()
