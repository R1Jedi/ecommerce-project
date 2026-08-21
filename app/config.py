import os
from dotenv import load_dotenv

load_dotenv()

# Auth
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

# Database
DATABASE_URL = os.getenv("DATABASE_URL")
