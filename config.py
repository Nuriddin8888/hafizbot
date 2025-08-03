from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
admin_ids = os.getenv("ADMIN_IDS")
ADMIN_IDS = list(map(int, admin_ids.split(",")))
DB_PATH = os.getenv("DB_PATH")