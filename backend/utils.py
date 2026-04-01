import math
import hashlib
from typing import Optional

def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate distance between two points using Haversine formula
    Returns distance in kilometers
    """
    R = 6371  # Earth's radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return round(distance, 1)

def generate_fallback_distance(city: str, profile_id: str) -> float:
    """
    Generate deterministic fallback distance based on city and profile_id
    Always returns same value for same inputs
    """
    combined = f"{city}_{profile_id}"
    hash_value = int(hashlib.md5(combined.encode()).hexdigest(), 16)
    # Generate distance between 0.5 and 15 km
    distance = 0.5 + (hash_value % 145) / 10.0
    return round(distance, 1)

def geocode_city_mock(city: str) -> Optional[dict]:
    """
    Mock geocoding - returns coordinates for major Russian cities
    Falls back to Moscow coordinates
    """
    cities = {
        "москва": {"lat": 55.7558, "lng": 37.6173},
        "санкт-петербург": {"lat": 59.9311, "lng": 30.3609},
        "новосибирск": {"lat": 55.0084, "lng": 82.9357},
        "екатеринбург": {"lat": 56.8389, "lng": 60.6057},
        "казань": {"lat": 55.8304, "lng": 49.0661},
        "нижний новгород": {"lat": 56.2965, "lng": 43.9361},
        "челябинск": {"lat": 55.1644, "lng": 61.4368},
        "самара": {"lat": 53.2001, "lng": 50.1500},
        "омск": {"lat": 54.9885, "lng": 73.3242},
        "ростов-на-дону": {"lat": 47.2357, "lng": 39.7015},
        "уфа": {"lat": 54.7388, "lng": 55.9721},
        "красноярск": {"lat": 56.0153, "lng": 92.8932},
        "воронеж": {"lat": 51.6605, "lng": 39.2005},
        "пермь": {"lat": 58.0105, "lng": 56.2502},
        "волгоград": {"lat": 48.7080, "lng": 44.5133},
    }
    
    city_lower = city.lower().strip()
    if city_lower in cities:
        return cities[city_lower]
    
    # Default to Moscow
    return {"lat": 55.7558, "lng": 37.6173}

def slugify(text: str) -> str:
    """
    Convert text to URL-friendly slug
    """
    import re
    from transliterate import translit
    
    try:
        # Transliterate Cyrillic to Latin
        text = translit(text, 'ru', reversed=True)
    except:
        pass
    
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    text = text.strip('-')
    return text