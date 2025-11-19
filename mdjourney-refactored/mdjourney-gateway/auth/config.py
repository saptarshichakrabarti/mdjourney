import os

# --- Configuration ---
GATEWAY_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(GATEWAY_DIR, "..", "..", "..", "auth", "data"))

DATABASE_URL = os.path.join(DATA_DIR, "mdjourney.db")
# This should be loaded securely, e.g., from a file or environment variable
with open(os.path.join(DATA_DIR, "jwt-private.pem"), "rb") as f:
    SECRET_KEY = f.read()
with open(os.path.join(DATA_DIR, "jwt-public.pem"), "rb") as f:
    PUBLIC_KEY = f.read()
ALGORITHM = "RS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
