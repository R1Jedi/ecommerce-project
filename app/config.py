import os
from dotenv import load_dotenv

load_dotenv()

# Auth
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

# Database
DATABASE_URL = os.getenv("DATABASE_URL")

# YooKassa
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")
YOOKASSA_RETURN_URL = os.getenv("YOOKASSA_RETURN_URL", "http://localhost:8000/")
