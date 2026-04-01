# backend/server.py
from fastapi import FastAPI, APIRouter, HTTPException, Query, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from typing import List, Optional, Any
import time
from datetime import datetime, timezone
import cloudinary
import cloudinary.utils
from telegram import Bot
import httpx

from models import (
    Profile, ProfileCreate, ProfileUpdate,
    AdminUser, AdminLogin, AdminLoginResponse,
    ContactMessage, ContactMessageCreate
)
from auth import hash_password, verify_password, create_access_token, get_current_admin, security
from utils import calculate_distance, generate_fallback_distance, geocode_city_mock, slugify

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

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
if telegram_token:
    telegram_bot = Bot(token=telegram_token)
else:
    telegram_bot = None

# Create the main app
app = FastAPI()

ALLOWED_ORIGINS = {"http://localhost:3000", "http://127.0.0.1:3000"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(ALLOWED_ORIGINS),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def ensure_profile_response_shape(profile: dict) -> dict:
    """
    Normalize legacy/incomplete Mongo documents so they pass response model validation.
    """
    now_iso = datetime.now(timezone.utc).isoformat()

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
        "id": as_str(profile.get("id"), "0"),
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
        "createdAt": as_str(profile.get("createdAt"), now_iso),
        "updatedAt": as_str(profile.get("updatedAt"), now_iso),
    }

    provided_slug = as_str(profile.get("slug"), "")
    sanitized["slug"] = provided_slug or slugify(sanitized["name"] or sanitized["id"])
    return sanitized


# ==================== PROFILES ROUTES ====================

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
    """
    Get profiles with filters
    """
    try:
        query = {}
        
        if active_only:
            query["isActive"] = True
        
        if featured_only:
            query["isFeatured"] = True
        
        if min_age or max_age:
            query["age"] = {}
            if min_age:
                query["age"]["$gte"] = min_age
            if max_age:
                query["age"]["$lte"] = max_age
        
        if tags:
            tag_list = [t.strip() for t in tags.split(",")]
            query["tags"] = {"$in": tag_list}
        
        raw_profiles = await db.profiles.find(query, {"_id": 0}).to_list(length=1000)
        profiles = []
        for raw_profile in raw_profiles:
            try:
                profile = ensure_profile_response_shape(dict(raw_profile or {}))
                try:
                    profile["distance"] = generate_fallback_distance(city or "default", profile.get("id", "0"))
                except Exception:
                    logger.exception("Failed to generate fallback distance for profile_id=%s", profile.get("id"))
                    profile["distance"] = 10
                profiles.append(Profile(**profile))
            except Exception:
                logger.exception("Skipping malformed profile document: %s", raw_profile)
        
        # Sort profiles
        if sort_by == "nearest":
            profiles.sort(key=lambda x: getattr(x, "distance", 999))
        elif sort_by == "newest":
            profiles.sort(key=lambda x: getattr(x, "createdAt", ""), reverse=True)
        elif sort_by == "featured":
            profiles.sort(key=lambda x: getattr(x, "isFeatured", False), reverse=True)
        
        return [profile.model_dump() for profile in profiles]
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error in /api/profiles")
        raise HTTPException(status_code=500, detail="Internal server error") from exc

@api_router.get("/profiles/{profile_id}", response_model=Profile)
async def get_profile(profile_id: str, city: Optional[str] = Query(None)):
    """
    Get single profile by ID
    """
    profile = await db.profiles.find_one({"id": profile_id}, {"_id": 0})
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    profile = ensure_profile_response_shape(profile)
    
    # Calculate distance if city provided - always show as nearby
    if city:
        profile["distance"] = generate_fallback_distance(city, profile["id"])
    
    return profile

@api_router.post("/profiles", response_model=Profile, status_code=201)
async def create_profile(
    profile_data: ProfileCreate,
    current_admin: dict = Depends(get_current_admin)
):
    """
    Create new profile (admin only)
    """
    import uuid
    from datetime import datetime, timezone
    
    profile_dict = profile_data.model_dump()
    profile_dict["id"] = str(uuid.uuid4())
    profile_dict["slug"] = slugify(profile_data.name)
    profile_dict["createdAt"] = datetime.now(timezone.utc).isoformat()
    profile_dict["updatedAt"] = datetime.now(timezone.utc).isoformat()
    
    await db.profiles.insert_one(profile_dict)
    
    return Profile(**profile_dict)

@api_router.put("/profiles/{profile_id}", response_model=Profile)
async def update_profile(
    profile_id: str,
    profile_data: ProfileUpdate,
    current_admin: dict = Depends(get_current_admin)
):
    """
    Update profile (admin only)
    """
    from datetime import datetime, timezone
    
    existing = await db.profiles.find_one({"id": profile_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    update_dict = {k: v for k, v in profile_data.model_dump().items() if v is not None}
    update_dict["updatedAt"] = datetime.now(timezone.utc).isoformat()
    
    if "name" in update_dict:
        update_dict["slug"] = slugify(update_dict["name"])
    
    await db.profiles.update_one({"id": profile_id}, {"$set": update_dict})
    
    updated = await db.profiles.find_one({"id": profile_id}, {"_id": 0})
    return Profile(**updated)

@api_router.delete("/profiles/{profile_id}")
async def delete_profile(
    profile_id: str,
    current_admin: dict = Depends(get_current_admin)
):
    """
    Delete profile (admin only)
    """
    result = await db.profiles.delete_one({"id": profile_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return {"message": "Profile deleted successfully"}


# ==================== ADMIN AUTH ROUTES ====================

@api_router.post("/admin/login", response_model=AdminLoginResponse)
async def admin_login(credentials: AdminLogin):
    """
    Admin login
    """
    admin = await db.admin_users.find_one({"username": credentials.username}, {"_id": 0})
    
    if not admin or not verify_password(credentials.password, admin["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"username": admin["username"], "id": admin["id"]})
    
    return AdminLoginResponse(token=token, username=admin["username"])

@api_router.get("/admin/me")
async def get_admin_me(current_admin: dict = Depends(get_current_admin)):
    """
    Get current admin info
    """
    return current_admin

@api_router.get("/admin/stats")
async def get_admin_stats(current_admin: dict = Depends(get_current_admin)):
    """
    Get admin statistics
    """
    total_profiles = await db.profiles.count_documents({})
    active_profiles = await db.profiles.count_documents({"isActive": True})
    featured_profiles = await db.profiles.count_documents({"isFeatured": True})
    total_messages = await db.contact_messages.count_documents({})
    
    return {
        "total_profiles": total_profiles,
        "active_profiles": active_profiles,
        "featured_profiles": featured_profiles,
        "total_messages": total_messages
    }


# ==================== CONTACT ROUTES ====================

@api_router.post("/contact")
async def submit_contact(message_data: ContactMessageCreate):
    """
    Submit contact form
    """
    import uuid
    from datetime import datetime, timezone
    
    message_dict = message_data.model_dump()
    message_dict["id"] = str(uuid.uuid4())
    message_dict["createdAt"] = datetime.now(timezone.utc).isoformat()
    
    # Save to database
    await db.contact_messages.insert_one(message_dict)
    
    # Send to Telegram
    if telegram_bot and telegram_chat_id:
        try:
            telegram_message = f"""
🆕 Новое сообщение с сайта

👤 Имя: {message_data.name}
📧 Email: {message_data.email}
📱 Телефон: {message_data.phone}

💬 Сообщение:
{message_data.message}
"""
            await telegram_bot.send_message(chat_id=telegram_chat_id, text=telegram_message)
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
    
    return {"message": "Message sent successfully", "id": message_dict["id"]}


# ==================== CLOUDINARY ROUTES ====================

@api_router.get("/cloudinary/signature")
async def generate_cloudinary_signature(
    resource_type: str = Query("image", regex="^(image|video)$"),
    folder: str = Query("profiles"),
    current_admin: dict = Depends(get_current_admin)
):
    """
    Generate Cloudinary signature for upload (admin only)
    """
    ALLOWED_FOLDERS = ("profiles", "gallery")
    if folder not in ALLOWED_FOLDERS:
        raise HTTPException(status_code=400, detail="Invalid folder path")
    
    timestamp = int(time.time())
    params = {
        "timestamp": timestamp,
        "folder": folder,
        "resource_type": resource_type
    }
    
    signature = cloudinary.utils.api_sign_request(
        params,
        os.getenv("CLOUDINARY_API_SECRET")
    )
    
    return {
        "signature": signature,
        "timestamp": timestamp,
        "cloud_name": os.getenv("CLOUDINARY_CLOUD_NAME"),
        "api_key": os.getenv("CLOUDINARY_API_KEY"),
        "folder": folder,
        "resource_type": resource_type
    }


# ==================== HEALTH CHECK ====================

@api_router.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "L'Aura API",
        "version": "1.0.0",
        "status": "running"
    }

@api_router.get("/health")
async def health():
    """Health check endpoint for monitoring"""
    try:
        # Check database connection
        await db.command("ping")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "ok",
        "database": db_status,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# Include the router in the main app
app.include_router(api_router)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning("HTTPException on %s: %s", request.url.path, exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.middleware("http")
async def force_cors_headers(request: Request, call_next):
    response = await call_next(request)
    origin = request.headers.get("origin")
    if origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Vary"] = "Origin"
    return response

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()