import pytesseract
from PIL import Image
import cv2
import numpy as np
import os

# Keywords to detect if an image is a payment receipt
PAYMENT_KEYWORDS = [
    "easypaisa", "jazzcash", "jazz cash", "binance",
    "hbl", "meezan", "bank", "transaction", "transfer",
    "rs.", "pkr", "amount", "txid", "tx id", "ref no",
    "reference", "receipt", "payment", "paid", "sending",
    "successful", "sent"
]

# Keywords to detect payment intent in text messages
PAYMENT_TEXT_KEYWORDS = [
    "payment kar di", "paid", "bhej diya", "sent kar diya",
    "transfer ho gaya", "screenshot bhej raha", "check kar lo",
    "payment ho gai", "kar diya", "send kar diya"
]

def preprocess_image(image_path):
    """
    Prepares the image for better OCR results.
    """
    if not os.path.exists(image_path):
        return None

    # Load image
    img = cv2.imread(image_path)
    if img is None:
        return None

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Thresholding to get a black and white image
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    
    return thresh

def extract_text_from_image(image_path):
    """
    Runs Tesseract OCR on the image.
    """
    processed_img = preprocess_image(image_path)
    if processed_img is None:
        return ""

    try:
        # Tesseract needs a PIL image or a path
        text = pytesseract.image_to_string(processed_img)
        return text.strip()
    except Exception as e:
        print(f"OCR Error: {e}")
        return ""

def is_payment_receipt(image_path):
    """
    Checks if an image is likely a payment receipt.
    """
    text = extract_text_from_image(image_path)
    text_lower = text.lower()
    
    found_keywords = [kw for kw in PAYMENT_KEYWORDS if kw in text_lower]
    return len(found_keywords) >= 2, text  # Require at least 2 keywords for confidence

def is_payment_intent_text(text):
    """
    Checks if a text message indicates a payment has been made.
    """
    if not text:
        return False
    text_lower = text.lower()
    return any(kw in text_lower for kw in PAYMENT_TEXT_KEYWORDS)
