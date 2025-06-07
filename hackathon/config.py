import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
