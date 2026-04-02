from fastapi import FastAPI, APIRouter, HTTPException, Query, Depends, Request
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
import json
import os
import logging
import sqlite3
import threading
from pathlib import Path
from typing import List, Optional, Any
import time
from datetime import datetime, timezone
import uuid

import cloudinary
import cloudinary.utils
from telegram import Bot

from models import (
    Profile, ProfileCreate, ProfileUpdate,
    AdminLogin, AdminLoginResponse,
    ContactMessageCreate
)
from auth import hash_password, verify_password, create_access_token, get_current_admin
from utils import generate_fallback_distance, slugify

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cloudinary config
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

# Telegram bot
telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
telegram_bot = Bot(token=telegram_token) if telegram_token and telegram_token != "your_bot_token" else None

# Create the main app
app = FastAPI()

DEFAULT_ORIGINS = {
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
}
CONFIG_ORIGINS = {o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()}
ALLOWED_ORIGINS = sorted(DEFAULT_ORIGINS | CONFIG_ORIGINS)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_profile_response_shape(profile: dict) -> dict:
    """Normalize records so they pass response model validation."""

    def as_str(value: Any, default: str) -> str:
        if value is None:
            return default
        value = str(value).strip()
        return value if value else default

    def as_int(value: Any, default: int) -> int:
        try:
            if value is None:
                return default
            return int(value)
        except (TypeError, ValueError):
            return default

    def as_float(value: Any, default: float) -> float:
        try:
            if value is None:
                return default
            return float(value)
        except (TypeError, ValueError):
            return default

    def as_bool(value: Any, default: bool) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"true", "1", "yes"}:
                return True
            if lowered in {"false", "0", "no"}:
                return False
        if isinstance(value, (int, float)):
            return bool(value)
        return default

    def as_str_list(value: Any) -> List[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            stripped = value.strip()
            return [stripped] if stripped else []
        return []

    sanitized = {
        "id": as_str(profile.get("id"), str(uuid.uuid4())),
        "name": as_str(profile.get("name"), "Без имени"),
        "age": as_int(profile.get("age"), 18),
        "city": as_str(profile.get("city"), "Не указан"),
        "country": as_str(profile.get("country"), "Россия"),
        "descriptionShort": as_str(profile.get("descriptionShort"), ""),
        "descriptionFull": as_str(profile.get("descriptionFull"), ""),
        "images": as_str_list(profile.get("images")),
        "height": as_int(profile.get("height"), 170),
        "weight": as_int(profile.get("weight"), 60),
        "languages": as_str_list(profile.get("languages")),
        "tags": as_str_list(profile.get("tags")),
        "lat": as_float(profile.get("lat"), 55.7558),
        "lng": as_float(profile.get("lng"), 37.6173),
        "isActive": as_bool(profile.get("isActive"), True),
        "isFeatured": as_bool(profile.get("isFeatured"), False),
        "createdAt": as_str(profile.get("createdAt"), now_iso()),
        "updatedAt": as_str(profile.get("updatedAt"), now_iso()),
    }
    provided_slug = as_str(profile.get("slug"), "")
    sanitized["slug"] = provided_slug or slugify(sanitized["name"] or sanitized["id"])
    return sanitized


class SQLiteStore:
    def __init__(self):
        self.db_path = os.getenv("SQLITE_DB_PATH", str(ROOT_DIR / "app.db"))
        self._lock = threading.Lock()
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _loads_list(value: Any) -> List[str]:
        if value in (None, ""):
            return []
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else []
        except (TypeError, json.JSONDecodeError):
            return []

    @staticmethod
    def _profile_from_row(row: sqlite3.Row) -> dict:
        return ensure_profile_response_shape(
            {
                "id": row["id"],
                "slug": row["slug"],
                "name": row["name"],
                "age": row["age"],
                "city": row["city"],
                "country": row["country"],
                "descriptionShort": row["descriptionShort"],
                "descriptionFull": row["descriptionFull"],
                "images": SQLiteStore._loads_list(row["images"]),
                "height": row["height"],
                "weight": row["weight"],
                "languages": SQLiteStore._loads_list(row["languages"]),
                "tags": SQLiteStore._loads_list(row["tags"]),
                "lat": row["lat"],
                "lng": row["lng"],
                "isActive": bool(row["isActive"]),
                "isFeatured": bool(row["isFeatured"]),
                "createdAt": row["createdAt"],
                "updatedAt": row["updatedAt"],
            }
        )

    def _init_db(self):
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS admin_users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    createdAt TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS profiles (
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

                CREATE TABLE IF NOT EXISTS contact_messages (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    message TEXT NOT NULL,
                    createdAt TEXT NOT NULL
                );
                """
            )
        self.seed_defaults_if_empty()

    def seed_defaults_if_empty(self):
        with self._connect() as conn:
            has_admin = conn.execute("SELECT COUNT(*) AS cnt FROM admin_users").fetchone()["cnt"] > 0
            profiles_count = conn.execute("SELECT COUNT(*) AS cnt FROM profiles").fetchone()["cnt"]

            if not has_admin:
                created = now_iso()
                conn.execute(
                    "INSERT INTO admin_users (id, username, password_hash, createdAt) VALUES (?, ?, ?, ?)",
                    (str(uuid.uuid4()), "admin", hash_password("admin123"), created),
                )

            if profiles_count == 0:
                created = now_iso()
                default_profiles = [
                    {
                        "id": str(uuid.uuid4()),
                        "name": "Анастасия",
                        "slug": "anastasiya",
                        "age": 24,
                        "city": "Москва",
                        "descriptionShort": "Премиальная компаньонка",
                        "descriptionFull": "Элегантная и приятная собеседница для ваших мероприятий.",
                        "images": ["https://images.unsplash.com/photo-1494790108377-be9c29b29330"],
                        "height": 172,
                        "weight": 54,
                        "languages": ["Русский", "English"],
                        "tags": ["VIP", "Премиум"],
                        "lat": 55.75,
                        "lng": 37.61,
                        "isActive": True,
                        "isFeatured": True,
                        "createdAt": created,
                        "updatedAt": created,
                    },
                    {
                        "id": str(uuid.uuid4()),
                        "name": "София",
                        "slug": "sofiya",
                        "age": 26,
                        "city": "Санкт-Петербург",
                        "descriptionShort": "Яркая модель для светских событий",
                        "descriptionFull": "Стильная и тактичная, легко поддерживаю интеллектуальную беседу.",
                        "images": ["https://images.unsplash.com/photo-1487412720507-e7ab37603c6f"],
                        "height": 169,
                        "weight": 52,
                        "languages": ["Русский", "Français"],
                        "tags": ["Элитная", "Модель"],
                        "lat": 59.93,
                        "lng": 30.36,
                        "isActive": True,
                        "isFeatured": False,
                        "createdAt": created,
                        "updatedAt": created,
                    },
                ]
                for profile in default_profiles:
                    self.insert_profile(profile)

    def list_profiles(self) -> List[dict]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM profiles").fetchall()
        return [self._profile_from_row(row) for row in rows]

    def get_profile(self, profile_id: str) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,)).fetchone()
        return self._profile_from_row(row) if row else None

    def insert_profile(self, profile: dict) -> dict:
        profile = ensure_profile_response_shape(profile)
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO profiles (
                    id, slug, name, age, city, country, descriptionShort, descriptionFull,
                    images, height, weight, languages, tags, lat, lng,
                    isActive, isFeatured, createdAt, updatedAt
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    profile["id"],
                    profile["slug"],
                    profile["name"],
                    profile["age"],
                    profile["city"],
                    profile["country"],
                    profile["descriptionShort"],
                    profile["descriptionFull"],
                    json.dumps(profile["images"], ensure_ascii=False),
                    profile["height"],
                    profile["weight"],
                    json.dumps(profile["languages"], ensure_ascii=False),
                    json.dumps(profile["tags"], ensure_ascii=False),
                    profile["lat"],
                    profile["lng"],
                    int(profile["isActive"]),
                    int(profile["isFeatured"]),
                    profile["createdAt"],
                    profile["updatedAt"],
                ),
            )
        return profile

    def update_profile(self, profile_id: str, update_dict: dict) -> Optional[dict]:
        existing = self.get_profile(profile_id)
        if not existing:
            return None

        merged = {**existing, **update_dict, "id": profile_id}
        merged = ensure_profile_response_shape(merged)

        with self._lock, self._connect() as conn:
            conn.execute(
                """
                UPDATE profiles
                SET slug = ?, name = ?, age = ?, city = ?, country = ?, descriptionShort = ?, descriptionFull = ?,
                    images = ?, height = ?, weight = ?, languages = ?, tags = ?, lat = ?, lng = ?,
                    isActive = ?, isFeatured = ?, createdAt = ?, updatedAt = ?
                WHERE id = ?
                """,
                (
                    merged["slug"],
                    merged["name"],
                    merged["age"],
                    merged["city"],
                    merged["country"],
                    merged["descriptionShort"],
                    merged["descriptionFull"],
                    json.dumps(merged["images"], ensure_ascii=False),
                    merged["height"],
                    merged["weight"],
                    json.dumps(merged["languages"], ensure_ascii=False),
                    json.dumps(merged["tags"], ensure_ascii=False),
                    merged["lat"],
                    merged["lng"],
                    int(merged["isActive"]),
                    int(merged["isFeatured"]),
                    merged["createdAt"],
                    merged["updatedAt"],
                    profile_id,
                ),
            )
        return merged

    def delete_profile(self, profile_id: str) -> bool:
        with self._lock, self._connect() as conn:
            cursor = conn.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
            return cursor.rowcount > 0

    def get_admin_by_username(self, username: str) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM admin_users WHERE username = ?", (username,)).fetchone()
        return dict(row) if row else None

    def save_contact_message(self, message_dict: dict):
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO contact_messages (id, name, email, phone, message, createdAt) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    message_dict["id"],
                    message_dict["name"],
                    message_dict["email"],
                    message_dict["phone"],
                    message_dict["message"],
                    message_dict["createdAt"],
                ),
            )

    def stats(self) -> dict:
        with self._connect() as conn:
            total_profiles = conn.execute("SELECT COUNT(*) AS cnt FROM profiles").fetchone()["cnt"]
            active_profiles = conn.execute("SELECT COUNT(*) AS cnt FROM profiles WHERE isActive = 1").fetchone()["cnt"]
            featured_profiles = conn.execute("SELECT COUNT(*) AS cnt FROM profiles WHERE isFeatured = 1").fetchone()["cnt"]
            total_messages = conn.execute("SELECT COUNT(*) AS cnt FROM contact_messages").fetchone()["cnt"]

        return {
            "total_profiles": total_profiles,
            "active_profiles": active_profiles,
            "featured_profiles": featured_profiles,
            "total_messages": total_messages,
        }


store = SQLiteStore()


def get_profile_or_404(profile_id: str) -> dict:
    profile = store.get_profile(profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@api_router.get("/profiles", response_model=List[Profile])
async def get_profiles(
    city: Optional[str] = Query(None),
    min_age: Optional[int] = Query(None),
    max_age: Optional[int] = Query(None),
    tags: Optional[str] = Query(None),
    active_only: bool = Query(True),
    sort_by: str = Query("nearest"),
    featured_only: bool = Query(False)
):
    profiles = store.list_profiles()

    if active_only:
        profiles = [p for p in profiles if p.get("isActive")]
    if featured_only:
        profiles = [p for p in profiles if p.get("isFeatured")]
    if min_age is not None:
        profiles = [p for p in profiles if int(p.get("age", 0)) >= min_age]
    if max_age is not None:
        profiles = [p for p in profiles if int(p.get("age", 0)) <= max_age]
    if tags:
        tag_list = {t.strip() for t in tags.split(",") if t.strip()}
        profiles = [p for p in profiles if tag_list.intersection(set(p.get("tags", [])))]

    for profile in profiles:
        profile["distance"] = generate_fallback_distance(city or "default", profile.get("id", "0"))

    if sort_by == "nearest":
        profiles.sort(key=lambda x: x.get("distance", 999))
    elif sort_by == "newest":
        profiles.sort(key=lambda x: x.get("createdAt", ""), reverse=True)
    elif sort_by == "featured":
        profiles.sort(key=lambda x: x.get("isFeatured", False), reverse=True)

    return [Profile(**profile).model_dump() for profile in profiles]


@api_router.get("/profiles/{profile_id}", response_model=Profile)
async def get_profile(profile_id: str, city: Optional[str] = Query(None)):
    profile = ensure_profile_response_shape(get_profile_or_404(profile_id))
    if city:
        profile["distance"] = generate_fallback_distance(city, profile["id"])
    return profile


@api_router.post("/profiles", response_model=Profile, status_code=201)
async def create_profile(profile_data: ProfileCreate, current_admin: dict = Depends(get_current_admin)):
    profile_dict = ensure_profile_response_shape(profile_data.model_dump())
    profile_dict["id"] = str(uuid.uuid4())
    profile_dict["slug"] = slugify(profile_data.name)
    profile_dict["createdAt"] = now_iso()
    profile_dict["updatedAt"] = now_iso()

    try:
        created = store.insert_profile(profile_dict)
    except sqlite3.IntegrityError:
        profile_dict["slug"] = f"{profile_dict['slug']}-{profile_dict['id'][:8]}"
        created = store.insert_profile(profile_dict)

    return Profile(**created)


@api_router.put("/profiles/{profile_id}", response_model=Profile)
async def update_profile(profile_id: str, profile_data: ProfileUpdate, current_admin: dict = Depends(get_current_admin)):
    update_dict = {k: v for k, v in profile_data.model_dump().items() if v is not None}
    update_dict["updatedAt"] = now_iso()
    if "name" in update_dict:
        update_dict["slug"] = slugify(update_dict["name"])

    try:
        updated = store.update_profile(profile_id, update_dict)
    except sqlite3.IntegrityError:
        update_dict["slug"] = f"{update_dict.get('slug', 'profile')}-{profile_id[:8]}"
        updated = store.update_profile(profile_id, update_dict)

    if updated is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    return Profile(**updated)


@api_router.delete("/profiles/{profile_id}")
async def delete_profile(profile_id: str, current_admin: dict = Depends(get_current_admin)):
    deleted = store.delete_profile(profile_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"message": "Profile deleted successfully"}


@api_router.post("/admin/login", response_model=AdminLoginResponse)
async def admin_login(credentials: AdminLogin):
    admin = store.get_admin_by_username(credentials.username)
    if not admin or not verify_password(credentials.password, admin["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"username": admin["username"], "id": admin["id"]})
    return AdminLoginResponse(token=token, username=admin["username"])


@api_router.get("/admin/me")
async def get_admin_me(current_admin: dict = Depends(get_current_admin)):
    return current_admin


@api_router.get("/admin/stats")
async def get_admin_stats(current_admin: dict = Depends(get_current_admin)):
    return store.stats()


@api_router.post("/contact")
async def submit_contact(message_data: ContactMessageCreate):
    message_dict = message_data.model_dump()
    message_dict["id"] = str(uuid.uuid4())
    message_dict["createdAt"] = now_iso()
    store.save_contact_message(message_dict)

    if telegram_bot and telegram_chat_id and telegram_chat_id != "your_chat_id":
        try:
            telegram_message = (
                f"🆕 Новое сообщение с сайта\n\n"
                f"👤 Имя: {message_data.name}\n"
                f"📧 Email: {message_data.email}\n"
                f"📱 Телефон: {message_data.phone}\n\n"
                f"💬 Сообщение:\n{message_data.message}"
            )
            await telegram_bot.send_message(chat_id=telegram_chat_id, text=telegram_message)
        except Exception as exc:
            logger.error("Failed to send Telegram message: %s", exc)

    return {"message": "Message sent successfully", "id": message_dict["id"]}


@api_router.get("/cloudinary/signature")
async def generate_cloudinary_signature(
    resource_type: str = Query("image", pattern="^(image|video)$"),
    folder: str = Query("profiles"),
    current_admin: dict = Depends(get_current_admin)
):
    allowed_folders = ("profiles", "gallery")
    if folder not in allowed_folders:
        raise HTTPException(status_code=400, detail="Invalid folder path")

    api_secret = os.getenv("CLOUDINARY_API_SECRET")
    if not api_secret:
        raise HTTPException(status_code=503, detail="Cloudinary is not configured")

    timestamp = int(time.time())
    params = {"timestamp": timestamp, "folder": folder, "resource_type": resource_type}
    signature = cloudinary.utils.api_sign_request(params, api_secret)

    return {
        "signature": signature,
        "timestamp": timestamp,
        "cloud_name": os.getenv("CLOUDINARY_CLOUD_NAME"),
        "api_key": os.getenv("CLOUDINARY_API_KEY"),
        "folder": folder,
        "resource_type": resource_type,
    }


@api_router.get("/")
async def root():
    return {"message": "L'Aura API", "version": "1.2.0", "status": "running"}


@api_router.get("/health")
async def health():
    stats = store.stats()
    return {
        "status": "ok",
        "database": "sqlite",
        "timestamp": now_iso(),
        "profiles": stats["total_profiles"],
        "db_path": store.db_path,
    }


app.include_router(api_router)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning("HTTPException on %s: %s", request.url.path, exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
