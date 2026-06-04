"""Application configuration from environment variables."""

import os

DOG_API_BASE_URL: str = os.getenv("DOG_API_BASE_URL", "https://dog.ceo/api")
DOG_API_TIMEOUT_SECONDS: float = float(os.getenv("DOG_API_TIMEOUT_SECONDS", "10"))
