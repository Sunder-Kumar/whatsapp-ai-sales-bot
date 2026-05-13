from langdetect import detect
import re

# Custom Roman Urdu keywords based on common conversation patterns
ROMAN_URDU_KEYWORDS = [
    "bhai", "yaar", "kya", "hai", "hain", "mujhe", "aap", "tum",
    "kar", "nahi", "nhi", "hoga", "kitna", "price", "batao", "sir",
    "wala", "wali", "abhi", "thik", "theek", "ji", "bilkul", "zaroor",
    "send", "bhejo", "chahiye", "milega", "chalta", "chalega", "paise",
    "payment", "screenshot", "bhej", "diya", "ho", "gaya", "karo", "acha",
    "thek", "pkr", "rate"
]

# Keywords that trigger a human takeover
TAKEOVER_KEYWORDS = [
    "owner", "manager", "proprietor", "insan", "real person",
    "human", "banda", "khud baat karo", "tumhara owner", "admin",
    "call", "phn pe baat", "original", "scam"
]

def detect_language(text: str) -> str:
    """
    Detects if the message is in Roman Urdu, English, or Mixed.
    """
    if not text or len(text.strip()) < 2:
        return "mixed"

    text_lower = text.lower()
    
    # Layer 1: Check for Roman Urdu Keywords
    words = re.findall(r'\w+', text_lower)
    keyword_matches = sum(1 for word in words if word in ROMAN_URDU_KEYWORDS)
    
    # If 2 or more keywords match, it's highly likely Roman Urdu
    if keyword_matches >= 2:
        return "roman_urdu"
    
    # Layer 2: Use langdetect for English
    try:
        lang = detect(text)
        if lang == "en":
            return "english"
    except:
        pass
    
    return "mixed"

def should_takeover(text: str) -> bool:
    """
    Checks if the customer is asking for a human or showing frustration.
    """
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in TAKEOVER_KEYWORDS)

def get_language_instruction(language: str) -> str:
    """
    Returns the specific AI instruction based on the detected language.
    """
    instructions = {
        "roman_urdu": (
            "Reply in Roman Urdu (Urdu written using English letters). "
            "Use a casual, friendly tone. Use 'sir/bhai/ji' naturally. "
            "Keep sentences short and simple. Do not use Urdu script."
        ),
        "english": (
            "Reply in professional but friendly English. "
            "Keep it conversational and easy to understand."
        ),
        "mixed": (
            "Reply in a mix of Roman Urdu and English (Hinglish/Urdish) "
            "similar to how the customer is speaking."
        )
    }
    return instructions.get(language, instructions["mixed"])
