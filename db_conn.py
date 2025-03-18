import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from .env file
load_dotenv()

url: str = os.getenv('supa_url')
key: str =  os.getenv('supa_key')

supabase: Client = create_client(url, key)
