import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()


def _db_uri():
    if os.getenv("DATABASE_URL"):
        return os.getenv("DATABASE_URL")
    return "mysql+pymysql://{u}:{p}@{h}/{d}?charset=utf8mb4".format(
        u=os.getenv("MYSQL_USER", ""), p=quote_plus(os.getenv("MYSQL_PASSWORD", "")),
        h=os.getenv("MYSQL_HOST", "127.0.0.1"), d=os.getenv("MYSQL_DATABASE", ""))


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = _db_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 8
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_MINUTES = 15
    TAX_RATE = 0.12
    RESORT_NAME = "Chaudhari's Resort"
    RESORT_ADDRESS = "1 Coastal Road, Goa, India"
