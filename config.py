import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # AssemblyAI Configuration
    ASSEMBLY_AI_API_KEY = os.getenv("ASSEMBLY_AI_API_KEY", "your_assembly_ai_key_here")
    
    # Ollama Configuration
    OLLAMA_BASE_URL = "http://localhost:11434"
    OLLAMA_MODEL = "llama2:latest"
    EMBEDDING_MODEL = "llama2:latest"
    
    # Vector Database Configuration
    VECTOR_DB_PATH = "./chroma_db"
    COLLECTION_NAME = "meeting_transcripts"
    
    # Chunking Configuration
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    
    # Audio Configuration
    MAX_AUDIO_SIZE_MB = 250
    SUPPORTED_FORMATS = ['.mp3', '.wav', '.m4a', '.mp4', '.webm']
    
    # LLM Configuration
    TEMPERATURE = 0.3
    MAX_TOKENS = 2000
