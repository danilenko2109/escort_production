import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path
import uuid
from datetime import datetime, timezone
from auth import hash_password

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Russian female names
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
    "Интеллигентная красавица для премиального досуга",
    "Элегантная девушка с модельной внешностью",
    "Изысканная компаньонка высокого уровня",
    "Утонченная леди для взыскательных джентльменов",
    "Стильная и образованная спутница"
]

DESCRIPTIONS_FULL = [
    "Позвольте представить вам воплощение утонченности и шарма. Я предлагаю незабываемое время в компании образованной и элегантной леди. Мои интересы включают искусство, путешествия и изысканную кухню. Я создам атмосферу комфорта и взаимопонимания на любом мероприятии.",
    "Я - профессиональная модель и приятная собеседница. Мое образование и жизненный опыт позволяют мне быть интересной компаньонкой в любой ситуации. Я ценю качество, стиль и конфиденциальность. Буду рада стать вашей спутницей на важном мероприятии или приятном вечере.",
    "Высокий уровень культуры, безупречные манеры и элегантный стиль - это обо мне. Я предпочитаю общество интеллигентных мужчин, которые ценят качественное общение и приятное времяпрепровождение. Гарантирую полную конфиденциальность и индивидуальный подход.",
    "Меня отличает естественная красота, природное обаяние и умение создавать особенную атмосферу. Я с удовольствием составлю вам компанию на деловом ужине, культурном мероприятии или в путешествии. Владею несколькими языками и разбираюсь в современном искусстве.",
]

# Image placeholders from design guidelines
IMAGES = [
    "https://images.unsplash.com/photo-1759933512107-e02a1328190d?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NjZ8MHwxfHNlYXJjaHwzfHxmYXNoaW9uJTIwbW9kZWwlMjBlZGl0b3JpYWwlMjBwb3J0cmFpdCUyMGRhcmslMjBiYWNrZ3JvdW5kfGVufDB8fHx8MTc3NDg3OTYzMnww&ixlib=rb-4.1.0&q=85",
    "https://images.unsplash.com/photo-1766299231533-27fb998d1a6e?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NjZ8MHwxfHNlYXJjaHwxfHxmYXNoaW9uJTIwbW9kZWwlMjBlZGl0b3JpYWwlMjBwb3J0cmFpdCUyMGRhcmslMjBiYWNrZ3JvdW5kfGVufDB8fHx8MTc3NDg3OTYzMnww&ixlib=rb-4.1.0&q=85",
    "https://static.prod-images.emergentagent.com/jobs/f41ef10d-503e-475e-a135-ee7599651f36/images/6cc07ea180d262dab3293a3e173fdbbebfab68ec1593280c70cb4430b2aba179.png"
]

async def seed_database():
    print("🌱 Starting database seed...")
    
    # Clear existing data
    await db.profiles.delete_many({})
    await db.admin_users.delete_many({})
    await db.contact_messages.delete_many({})
    
    print("✅ Cleared existing data")
    
    # Create admin user
    admin_user = {
        "id": str(uuid.uuid4()),
        "username": "admin",
        "password_hash": hash_password("admin123"),
        "createdAt": datetime.now(timezone.utc).isoformat()
    }
    await db.admin_users.insert_one(admin_user)
    print("✅ Created admin user (username: admin, password: admin123)")
    
    # Create profiles
    profiles = []
    import random
    
    for i, name in enumerate(NAMES):
        city_data = random.choice(CITIES)
        city_name, base_lat, base_lng = city_data
        
        # Add small random offset to coordinates
        lat = base_lat + random.uniform(-0.1, 0.1)
        lng = base_lng + random.uniform(-0.1, 0.1)
        
        profile = {
            "id": str(uuid.uuid4()),
            "slug": f"profile-{i+1}",
            "name": name,
            "age": random.randint(21, 32),
            "city": city_name,
            "country": "Россия",
            "descriptionShort": random.choice(DESCRIPTIONS_SHORT),
            "descriptionFull": random.choice(DESCRIPTIONS_FULL),
            "images": [random.choice(IMAGES) for _ in range(random.randint(1, 3))],
            "height": random.randint(165, 180),
            "weight": random.randint(50, 65),
            "languages": random.sample(LANGUAGES, random.randint(2, 4)),
            "tags": random.sample(TAGS, random.randint(2, 5)),
            "lat": lat,
            "lng": lng,
            "isActive": True,
            "isFeatured": i < 5,  # First 5 are featured
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat()
        }
        profiles.append(profile)
    
    await db.profiles.insert_many(profiles)
    print(f"✅ Created {len(profiles)} profiles")
    
    print("🎉 Database seed completed!")
    print("\n📝 Admin credentials:")
    print("   Username: admin")
    print("   Password: admin123")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_database())
