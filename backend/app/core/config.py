from pydantic_settings import BaseSettings
from pydantic import ValidationError
from dotenv import load_dotenv

load_dotenv()   #讀取.env

class Settings(BaseSettings):
    SECRET_KEY: str
    DATABASE_URL: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"
    
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    RESEND_API_KEY: str
    
settings = Settings()

if __name__ == "__main__":
    print("--- Running Config Unit Test ---")
    try:
        print("✅ Config loaded successfully!")
        print(f"DATABASE_URL: {settings.DATABASE_URL}")
        print(f"ALGORITHM: {settings.ALGORITHM}")
        print(f"SECRET_KEY loaded: {'*' * 8}") 
    except ValidationError as e:
        print("❌ ERROR: Config validation failed!")
        print("Please ensure you have a .env file in the project root with all required variables.")
        print("\nDetails:")
        print(e)