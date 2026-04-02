import json
import os
import random
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

import bcrypt
from utils import slugify

ROOT_DIR = Path(__file__).parent
DB_PATH = os.getenv("SQLITE_DB_PATH", str(ROOT_DIR / "app.db"))

NAMES = [
    "Анастасия", "Виктория", "Александра", "Екатерина", "Мария",
    "Дарья", "Полина", "Елена", "Ольга", "Наталья",
    "Ирина", "Юлия", "Анна", "София", "Кристина",
    "Валерия", "Алина", "Ксения", "Вероника", "Диана"
]

CITIES = [
    ("Москва", 55.7558, 37.6173),
    ("Санкт-Петербург", 59.9311, 30.3609),
    ("Новосибирск", 55.0084, 82.9357),
    ("Екатеринбург", 56.8389, 60.6057),
    ("Казань", 55.8304, 49.0661),
    ("Нижний Новгород", 56.2965, 43.9361),
    ("Челябинск", 55.1644, 61.4368),
    ("Самара", 53.2001, 50.1500),
    ("Ростов-на-Дону", 47.2357, 39.7015),
    ("Уфа", 54.7388, 55.9721),
]

TAGS = [
    "Премиум", "VIP", "Элитная", "Модель", "Фотомодель",
    "Эскорт", "Сопровождение", "Деловая встреча", "Вечеринка",
    "Путешествие", "Мероприятие", "Новая", "Популярная"
]

LANGUAGES = ["Русский", "Английский", "Французский", "Немецкий", "Итальянский", "Испанский"]

DESCRIPTIONS_SHORT = [
    "Утонченная и элегантная компаньонка для особенных вечеров",
    "Изысканная леди с безупречными манерами",
    "Харизматичная и образованная собеседница",
    "Стильная модель для деловых и светских мероприятий",
    "Очаровательная спутница с европейским шармом",
]

DESCRIPTIONS_FULL = [
    "Позвольте представить вам воплощение утонченности и шарма. Я предлагаю незабываемое время в компании образованной и элегантной леди.",
    "Я - профессиональная модель и приятная собеседница. Мое образование и жизненный опыт позволяют быть интересной компаньонкой в любой ситуации.",
    "Высокий уровень культуры, безупречные манеры и элегантный стиль - это обо мне. Гарантирую полную конфиденциальность.",
]

IMAGES = [
    "https://images.unsplash.com/photo-1759933512107-e02a1328190d",
    "https://images.unsplash.com/photo-1766299231533-27fb998d1a6e",
    "https://images.unsplash.com/photo-1494790108377-be9c29b29330",
]




def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def recreate_schema(conn: sqlite3.Connection):
    conn.executescript(
        """
        DROP TABLE IF EXISTS contact_messages;
        DROP TABLE IF EXISTS profiles;
        DROP TABLE IF EXISTS admin_users;

        CREATE TABLE admin_users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            createdAt TEXT NOT NULL
        );

        CREATE TABLE profiles (
            id TEXT PRIMARY KEY,
            slug TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            city TEXT NOT NULL,
            country TEXT NOT NULL,
            descriptionShort TEXT NOT NULL,
            descriptionFull TEXT NOT NULL,
            images TEXT NOT NULL,
            height INTEGER NOT NULL,
            weight INTEGER NOT NULL,
            languages TEXT NOT NULL,
            tags TEXT NOT NULL,
            lat REAL NOT NULL,
            lng REAL NOT NULL,
            isActive INTEGER NOT NULL DEFAULT 1,
            isFeatured INTEGER NOT NULL DEFAULT 0,
            createdAt TEXT NOT NULL,
            updatedAt TEXT NOT NULL
        );

        CREATE TABLE contact_messages (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            message TEXT NOT NULL,
            createdAt TEXT NOT NULL
        );
        """
    )


def seed_database():
    print(f"🌱 Starting SQLite seed: {DB_PATH}")

    with get_conn() as conn:
        recreate_schema(conn)

        admin_user = {
            "id": str(uuid.uuid4()),
            "username": "admin",
            "password_hash": hash_password("admin123"),
            "createdAt": now_iso(),
        }
        conn.execute(
            "INSERT INTO admin_users (id, username, password_hash, createdAt) VALUES (?, ?, ?, ?)",
            (admin_user["id"], admin_user["username"], admin_user["password_hash"], admin_user["createdAt"]),
        )

        profiles = []
        for i, name in enumerate(NAMES):
            city_name, base_lat, base_lng = random.choice(CITIES)
            lat = base_lat + random.uniform(-0.1, 0.1)
            lng = base_lng + random.uniform(-0.1, 0.1)
            profile_id = str(uuid.uuid4())
            profile = {
                "id": profile_id,
                "slug": f"{slugify(name)}-{i+1}",
                "name": name,
                "age": random.randint(21, 32),
                "city": city_name,
                "country": "Россия",
                "descriptionShort": random.choice(DESCRIPTIONS_SHORT),
                "descriptionFull": random.choice(DESCRIPTIONS_FULL),
                "images": json.dumps([random.choice(IMAGES) for _ in range(random.randint(1, 3))], ensure_ascii=False),
                "height": random.randint(165, 180),
                "weight": random.randint(50, 65),
                "languages": json.dumps(random.sample(LANGUAGES, random.randint(2, 4)), ensure_ascii=False),
                "tags": json.dumps(random.sample(TAGS, random.randint(2, 5)), ensure_ascii=False),
                "lat": lat,
                "lng": lng,
                "isActive": 1,
                "isFeatured": 1 if i < 5 else 0,
                "createdAt": now_iso(),
                "updatedAt": now_iso(),
            }
            profiles.append(profile)

        conn.executemany(
            """
            INSERT INTO profiles (
                id, slug, name, age, city, country, descriptionShort, descriptionFull, images,
                height, weight, languages, tags, lat, lng, isActive, isFeatured, createdAt, updatedAt
            ) VALUES (
                :id, :slug, :name, :age, :city, :country, :descriptionShort, :descriptionFull, :images,
                :height, :weight, :languages, :tags, :lat, :lng, :isActive, :isFeatured, :createdAt, :updatedAt
            )
            """,
            profiles,
        )

    print(f"✅ Created admin user (admin/admin123)")
    print(f"✅ Created {len(profiles)} profiles")
    print("🎉 SQLite seed completed")


if __name__ == "__main__":
    seed_database()
