import sqlite3
import json
from config import DB_PATH


def setup_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT,
            username TEXT
        )
    """)


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS suras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            audio TEXT,
            image_file_ids TEXT
        )
    """)
    conn.commit()
    conn.close()


def add_user(user_id, full_name, username):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    if not result:
        cursor.execute("INSERT INTO users (user_id, full_name, username) VALUES (?, ?, ?)",
                       (user_id, full_name, username))
        conn.commit()
    conn.close()


def get_users(offset=0, limit=5):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, full_name, username FROM users ORDER BY user_id LIMIT ? OFFSET ?", (limit, offset))
    users = cursor.fetchall()
    conn.close()
    return users


def get_users_count():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def add_sura(name, audio_file_id, image_file_ids: list):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    image_file_ids_json = json.dumps(image_file_ids)
    cursor.execute("INSERT OR REPLACE INTO suras (name, audio, image_file_ids) VALUES (?, ?, ?)",
                   (name, audio_file_id, image_file_ids_json))
    conn.commit()
    conn.close()


def get_all_sura_names():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM suras ORDER BY name")
    result = [row[0] for row in cursor.fetchall()]
    conn.close()
    return result


def get_sura_by_name(name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT audio, image_file_ids FROM suras WHERE name = ?", (name,))
    result = cursor.fetchone()
    conn.close()

    if result:
        audio_file_id, image_file_ids_json = result
        image_file_ids = json.loads(image_file_ids_json)
        return audio_file_id, image_file_ids
    return None, []




def get_all_sura_names():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM suras ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]


def get_sura_audio(sura_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT audio FROM suras WHERE name = ?", (sura_name,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def get_sura_images(sura_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT image_file_ids FROM suras WHERE name = ?", (sura_name,))
    result = cursor.fetchone()
    conn.close()

    if result:
        image_ids = json.loads(result[0])
        return image_ids
    return []


def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, full_name, username, status FROM users")
    users = cursor.fetchall()
    conn.close()
    return users



def update_user_status(user_id, status: bool):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET status = ? WHERE user_id = ?", (status, user_id))
    conn.commit()
    conn.close()


