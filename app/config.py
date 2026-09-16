import os

from dotenv import load_dotenv

load_dotenv()

API_KEY_HMAC_SECRET_V1 = os.getenv("API_KEY_HMAC_SECRET_V1")

if API_KEY_HMAC_SECRET_V1 is None:
    raise RuntimeError("API_KEY_HMAC_SECRET_V1 is not set")

if len(API_KEY_HMAC_SECRET_V1) < 22:
    raise RuntimeError("API_KEY_HMAC_SECRET_V1 is not secure")
