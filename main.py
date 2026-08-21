from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, ContextTypes, filters,
    PreCheckoutQueryHandler
)
import requests
import json
import jwt
import time
import asyncio
from datetime import datetime, timedelta
from functools import lru_cache
import re
import string
import random
import aiohttp
import io
import sqlite3
import struct
import hashlib
import traceback
import logging
from copy import deepcopy
from html import escape
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import zlib
import base64
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ================= RUNTIME DATA DIRECTORY =================
# Railway: set DATA_DIR=/data when using a persistent volume.
# GitHub/local: defaults to the project directory.
DATA_DIR = Path(os.getenv("DATA_DIR", "/data" if Path("/data").is_dir() else "."))
DATA_DIR.mkdir(parents=True, exist_ok=True)

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

try:
    import brotli
    HAS_BROTLI = True
except ImportError:
    HAS_BROTLI = False

# ================= BOT TOKEN / OWNER =================
# Isi langsung di file ini sebelum menjalankan bot.
BOT_TOKEN = "ISI_TOKEN_BOT_ANDA_DI_SINI"
OWNER_ID = 0  # isi dengan Telegram numeric user ID owner

# ================= FIREBASE SERVICE ACCOUNT =================
# Firebase credentials are loaded from environment variables or a config file.
# Set these BEFORE running the bot, OR create a file named "firebase_config.json"
# in the same folder as this script with your service account JSON.

def _load_firebase_config():
    """Load Firebase config from env vars or firebase_config.json file"""
    import os

    # Try loading from firebase_config.json file first
    config_file = DATA_DIR / "firebase_config.json"
    if config_file.exists():
        try:
            with config_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return data, data.get("database_url", "")
        except Exception as e:
            logging.getLogger("BOOT").warning(f"Could not load firebase_config.json: {e}")

    # Try loading from environment variables
    env_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON", "")
    env_url = os.environ.get("FIREBASE_DATABASE_URL", "")

    if env_json:
        try:
            data = json.loads(env_json)
            return data, env_url or data.get("database_url", "")
        except Exception as e:
            logging.getLogger("BOOT").warning(f"Could not parse FIREBASE_SERVICE_ACCOUNT_JSON: {e}")

    # Return empty config — bot will use local fallback automatically
    return {}, ""

FIREBASE_SERVICE_ACCOUNT, FIREBASE_DATABASE_URL = _load_firebase_config()

# ================= ADMIN CONFIG =================
ADMIN_IDS = [OWNER_ID]

# ================= CPM CONFIG =================
CPM = {
    "CPM1": {
        "keys": [
            "AIzaSyAe_aOVT1gSfmHKBrorFvX4fRwN5nODXVA",
            "AIzaSyBW1ZbMiUeDZHYUO2bY8Bfnf5rRgrQGPTM"
        ],
        "rating": "https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserRating6"
    },
    "CPM2": {
        "key": "AIzaSyCQDz9rgjgmvmFkvVfmvr2-7fT4tfrzRRQ",
        "rating": "https://us-central1-cpm-2-7cea1.cloudfunctions.net/SetUserRating17_AppI"
    }
}

# ================= GAME EDITOR CONFIG =================
FK = "AIzaSyAe_aOVT1gSfmHKBrorFvX4fRwN5nODXVA"
LOAD_URL = "https://europe-west1-cp-multiplayer.cloudfunctions.net/GetPlayerRecords3"
SAVE_URL = "https://europe-west1-cp-multiplayer.cloudfunctions.net/SavePlayerRecordsPartially8"
RANK_URL = "https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserRating4"
MAX_MONEY = 50_000_000
MAX_COIN = 500_000
RATE_LIMIT_ACTIONS = 10
RATE_LIMIT_SECONDS = 60

# ================= BULK CONFIG =================
BULK_MAX_CONCURRENT = int(os.getenv("BULK_MAX_CONCURRENT", "20"))
BULK_RETRY_ATTEMPTS = 5
BULK_RETRY_DELAY = 2
BULK_RATE_LIMIT_DELAY = 0.8
BULK_MAX_ACCOUNTS = 10000
BULK_BATCH_SIZE = 1000
BULK_MODE_BOTH = "both"
BULK_MODE_EMAIL = "email"
BULK_MODE_PASS = "pass"
BULK_PASS_AUTO = "auto"
BULK_PASS_CUSTOM = "custom"
BULK_MAX_PARALLEL_JOBS = int(os.getenv("BULK_MAX_PARALLEL_JOBS", "2"))
_bulk_job_semaphore = None
_plan_cache = {}
_plan_cache_time = {}

# ================= KING RANK PAYLOAD =================
RATING_DATA = {
    "RatingData": {
        "t_distance": 2000000000,
        "time": 2000000000,
        "speed_banner": 2000000000,
        "gifts": 2000000000,
        "treasure": 2000000000,
        "cars": 2000000000,
        "race_win": 999,
        "levels": 2000000000,
        "drift": 2000000000,
        "run": 2000000000,
        "police": 2000000000,
        "block_post": 2000000000,
        "real_estate": 2000000000,
        "fuel": 2000000000,
        "car_trade": 2000000000,
        "car_exchange": 2000000000,
        "burnt_tire": 2000000000,
        "car_fix": 2000000000,
        "car_wash": 2000000000,
        "offroad": 2000000000,
        "passanger_distance": 2000000000,
        "reactions": 2000000000,
        "drift_max": 2000000000,
        "taxi": 2000000000,
        "delivery": 2000000000,
        "cargo": 2000000000,
        "push_ups": 2000000000,
        "slicer_cut": 2000000000,
        "car_collided": 2000000000,
        "new_type": 2000000000
    }
}

# ================= PRICING =================
PLAN_UNLIMITED_STARS = 100
PLAN_SINGLE_STARS = 5
PLAN_UNLIMITED = "unlimited"
PLAN_SINGLE = "single"
PLAN_NONE = "none"
PAYMENT_PROVIDER_TOKEN = ""
INVOICE_PAYLOAD_UNLIMITED = "bulk_unlimited_plan"
INVOICE_PAYLOAD_SINGLE = "bulk_single_plan"

# ================= STATES =================
EMAIL, PASSWORD = range(2)
ADMIN_MSG_INPUT = 2
ADMIN_SEARCH_INPUT = 4
ADMIN_BROADCAST_INPUT = 5
ADD_MEMBER_INPUT = 6
ADMIN_GRANT_BULK_INPUT = 7
LANG_SELECT = 20

# ================= BULK STATES =================
BULK_CPM_SELECT, BULK_FILE, BULK_PREFIX, BULK_DOMAIN, BULK_MODE_SELECT, BULK_PASS_TYPE, BULK_CUSTOM_PASS = range(10, 17)

# ================= GAME EDITOR STATES =================
G_EMAIL, G_PASS, G_MONEY, G_COIN, G_NAME, G_PID, G_WINS, G_LOSES = range(50, 58)

# ================= LOGGING =================
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("MERGED")

def make_http_connector(limit=50, ssl=False):
    """Create an aiohttp connector that avoids the threaded DNS resolver when aiodns is installed."""
    try:
        resolver = aiohttp.AsyncResolver()
        return aiohttp.TCPConnector(limit=limit, ssl=ssl, resolver=resolver)
    except Exception:
        return aiohttp.TCPConnector(limit=limit, ssl=ssl)

# ================= CACHE SYSTEM =================
_cache = {}
_cache_time = {}
CACHE_TTL = 60
_user_cache = {}
_banned_cache = {}
_banned_cache_time = 0
_bulk_job_semaphore = None

_firebase_token = None
_firebase_token_expiry = 0

# ================= FIREBASE TOKEN =================
def get_firebase_token():
    """Get a cached Firebase service-account access token without spawning threads."""
    global _firebase_token, _firebase_token_expiry
    if not _is_firebase_configured():
        return None
    if _firebase_token and time.time() < _firebase_token_expiry - 60:
        return _firebase_token
    try:
        now = int(time.time())
        payload = {
            "iss": FIREBASE_SERVICE_ACCOUNT["client_email"],
            "sub": FIREBASE_SERVICE_ACCOUNT["client_email"],
            "aud": FIREBASE_SERVICE_ACCOUNT["token_uri"],
            "iat": now,
            "exp": now + 3600,
            "scope": "https://www.googleapis.com/auth/firebase.database https://www.googleapis.com/auth/userinfo.email"
        }
        token = jwt.encode(payload, FIREBASE_SERVICE_ACCOUNT["private_key"], algorithm="RS256")
        r = requests.post(FIREBASE_SERVICE_ACCOUNT["token_uri"], data={
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": token
        }, timeout=15)
        if r.status_code == 200:
            data = r.json()
            _firebase_token = data["access_token"]
            _firebase_token_expiry = now + data.get("expires_in", 3600)
            return _firebase_token
        log.error("Firebase token request failed: HTTP %s", r.status_code)
    except Exception as e:
        log.error("Firebase token error: %s", e)
    return None

def fb_get(path):
    cache_key = f"get:{path}"
    if cache_key in _cache:
        if time.time() - _cache_time.get(cache_key, 0) < CACHE_TTL:
            return _cache[cache_key]
    token = get_firebase_token()
    if not token:
        return {}
    url = f"{FIREBASE_DATABASE_URL}{path}.json"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = requests.get(url, headers=headers, timeout=30)
        if r.status_code == 200:
            data = r.json() or {}
            _cache[cache_key] = data
            _cache_time[cache_key] = time.time()
            return data
    except Exception as e:
        print(f"Firebase GET Error: {e}")
    return {}

def fb_put(path, data):
    token = get_firebase_token()
    if not token:
        return False
    url = f"{FIREBASE_DATABASE_URL}{path}.json"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = requests.put(url, headers=headers, json=data, timeout=30)
        if r.status_code == 200:
            _invalidate_cache(path)
            return True
    except Exception as e:
        print(f"Firebase PUT Error: {e}")
    return False

def fb_patch(path, data):
    token = get_firebase_token()
    if not token:
        return False
    url = f"{FIREBASE_DATABASE_URL}{path}.json"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = requests.patch(url, headers=headers, json=data, timeout=30)
        if r.status_code == 200:
            _invalidate_cache(path)
            return True
    except Exception as e:
        print(f"Firebase PATCH Error: {e}")
    return False

def fb_delete(path):
    token = get_firebase_token()
    if not token:
        return False
    url = f"{FIREBASE_DATABASE_URL}{path}.json"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = requests.delete(url, headers=headers, timeout=30)
        if r.status_code == 200:
            _invalidate_cache(path)
            return True
    except Exception as e:
        print(f"Firebase DELETE Error: {e}")
    return False

def _invalidate_cache(path):
    keys_to_remove = [k for k in list(_cache.keys()) if path in k or k.startswith("get:")]
    for k in keys_to_remove:
        _cache.pop(k, None)
        _cache_time.pop(k, None)

# ================= LOCAL FALLBACK (No Firebase Setup Needed) =================
LOCAL_STORE_PATH = DATA_DIR / "local_bot_data.json"
_local_store_cache = None

def _is_firebase_configured():
    """Check if real Firebase credentials are set (not placeholders)"""
    return (
        bool(FIREBASE_SERVICE_ACCOUNT)
        and bool(FIREBASE_DATABASE_URL)
        and FIREBASE_SERVICE_ACCOUNT.get("project_id", "") != ""
        and FIREBASE_SERVICE_ACCOUNT.get("private_key", "") != ""
    )

def _load_local_store():
    global _local_store_cache
    if _local_store_cache is not None:
        return _local_store_cache
    try:
        if LOCAL_STORE_PATH.exists():
            with LOCAL_STORE_PATH.open("r", encoding="utf-8") as f:
                _local_store_cache = json.load(f)
        else:
            _local_store_cache = {}
    except Exception:
        _local_store_cache = {}
    return _local_store_cache

def _save_local_store(data):
    global _local_store_cache
    _local_store_cache = data
    try:
        with LOCAL_STORE_PATH.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log.error(f"Local store save error: {e}")

def _local_get(path):
    """Get data from local JSON store using dot-notation path"""
    store = _load_local_store()
    keys = path.replace("/", ".").strip(".").split(".")
    current = store
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return {}
    return current if current is not None else {}

def _local_put(path, data):
    """Put data into local JSON store"""
    store = _load_local_store()
    keys = path.replace("/", ".").strip(".").split(".")
    current = store
    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    current[keys[-1]] = data
    _save_local_store(store)
    return True

def _local_patch(path, data):
    """Patch (merge) data into local JSON store"""
    store = _load_local_store()
    keys = path.replace("/", ".").strip(".").split(".")
    current = store
    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    if keys[-1] not in current or not isinstance(current[keys[-1]], dict):
        current[keys[-1]] = {}
    if isinstance(data, dict):
        current[keys[-1]].update(data)
    else:
        current[keys[-1]] = data
    _save_local_store(store)
    return True

def _local_delete(path):
    """Delete data from local JSON store"""
    store = _load_local_store()
    keys = path.replace("/", ".").strip(".").split(".")
    current = store
    for key in keys[:-1]:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return True
    if isinstance(current, dict) and keys[-1] in current:
        del current[keys[-1]]
    _save_local_store(store)
    return True

# Override Firebase functions to use local fallback when not configured
_original_fb_get = fb_get
_original_fb_put = fb_put
_original_fb_patch = fb_patch
_original_fb_delete = fb_delete

def fb_get(path):
    if not _is_firebase_configured():
        return _local_get(path)
    return _original_fb_get(path)

def fb_put(path, data):
    if not _is_firebase_configured():
        return _local_put(path, data)
    return _original_fb_put(path, data)

def fb_patch(path, data):
    if not _is_firebase_configured():
        return _local_patch(path, data)
    return _original_fb_patch(path, data)

def fb_delete(path):
    if not _is_firebase_configured():
        return _local_delete(path)
    return _original_fb_delete(path)

# ================= GAME EDITOR CRYPTO =================
def make_xor_key(uid: str) -> bytes:
    chars = list(uid)
    if len(chars) >= 9: chars[1], chars[8] = chars[8], chars[1]
    if len(chars) >= 3: chars.pop(2)
    if len(chars) >= 5: chars.append(chars[4])
    return "".join(chars).encode("utf-8")

def xor_bytes(data: bytes, key: bytes) -> bytes:
    return bytes(data[i] ^ key[i % len(key)] for i in range(len(data)))

def decompress(data: bytes) -> Optional[bytes]:
    if HAS_BROTLI:
        try: return brotli.decompress(data)
        except: pass
    try: return zlib.decompress(data, zlib.MAX_WBITS | 16)
    except: pass
    try: return zlib.decompress(data)
    except: pass
    return None

def decrypt_aes(data: bytes, key: bytes) -> Optional[bytes]:
    if not HAS_CRYPTO: return None
    try:
        cipher = AES.new(key[:16], AES.MODE_CBC, b"\x00" * 16)
        return unpad(cipher.decrypt(data), 16)
    except: return None

def _md5(t): return hashlib.md5(t.encode()).digest()
def _sha1(t): return hashlib.sha1(t.encode()).digest()[:16]

def build_aes_keys(uid, password=None, email=None):
    keys = [_md5("olzhas_carparking")]
    if password: keys += [_md5(password), _sha1(password)]
    if uid:      keys += [_md5(uid), _sha1(uid)]
    if email:    keys.append(_md5(email))
    return keys

class Reader:
    def __init__(self, data):
        self.buf = data; self.pos = 0
    def has_bytes(self, n): return self.pos + n <= len(self.buf)
    def read_byte(self):
        if not self.has_bytes(1): return 0
        v = self.buf[self.pos]; self.pos += 1; return v
    def read_int(self):
        if not self.has_bytes(4): self.pos = len(self.buf); return 0
        v = struct.unpack_from("<i", self.buf, self.pos)[0]; self.pos += 4; return v
    def read_float(self):
        if not self.has_bytes(4): self.pos = len(self.buf); return 0.0
        v = struct.unpack_from("<f", self.buf, self.pos)[0]; self.pos += 4; return v
    def read_string(self):
        marker = self.read_int()
        if marker in (0, -1): return ""
        length = (-marker) - 1 if marker < -1 else marker
        if marker < -1: self.read_int()
        if length > 1_000_000: length = 1_000_000
        if not self.has_bytes(length): return ""
        text = self.buf[self.pos:self.pos + length].decode("utf-8", errors="replace")
        self.pos += length
        return text.replace("\x00", "").strip()
    def read_list(self, item_fn):
        count = self.read_int()
        if count <= 0 or count > 1_000_000: return []
        result = []
        for _ in range(count):
            if self.pos >= len(self.buf): break
            v = item_fn()
            if v is not None: result.append(v)
        return result
    def read_dict(self):
        count = self.read_int()
        if count <= 0 or count > 1_000_000: return {}
        d = {}
        for _ in range(count):
            if self.pos >= len(self.buf): break
            d[self.read_int()] = self.read_int()
        return d
    def read_equipment(self):
        if self.read_byte() == 0: return None
        return {
            "hair": self.read_list(self.read_int),
            "face": self.read_list(self.read_int),
            "beard": self.read_list(self.read_int),
            "cap": self.read_list(self.read_int),
            "mask": self.read_list(self.read_int),
            "top": self.read_list(self.read_int),
            "gloves": self.read_list(self.read_int),
            "bag": self.read_list(self.read_int),
            "pants": self.read_list(self.read_int),
            "shoes": self.read_list(self.read_int),
            "glasses": self.read_list(self.read_int),
            "SelectedEquipments": self.read_list(self.read_int),
            "Gender": self.read_int(),
        }

def parse_player(buf):
    r = Reader(buf)
    if r.read_byte() == 0: return None
    p = {}
    p["Name"] = r.read_string(); p["money"] = r.read_int()
    p["coin"] = r.read_int(); p["localID"] = r.read_string()
    p["boughtFsos"] = r.read_list(r.read_int)
    def read_friend():
        r.read_byte()
        return {"id": r.read_string(), "Name": r.read_string(), "accountID": r.read_string()}
    p["FriendsID"] = r.read_list(read_friend)
    p["LevelsDoneTime"] = r.read_list(r.read_float)
    p["floats"] = r.read_list(r.read_float)
    p["integers"] = r.read_list(r.read_int)
    p["fcar"] = r.read_list(r.read_int)
    p["favouriteWheels"] = r.read_list(r.read_int)
    p["favouriteVinyls"] = r.read_list(r.read_int)
    p["favouriteEmojis"] = r.read_list(r.read_int)
    p["personEquipmentsMale"] = r.read_equipment()
    p["personEquipmentsFemale"] = r.read_equipment()
    if r.read_byte() == 0:
        p["platesData"] = None
    else:
        def read_vinyl():
            r.read_byte()
            def rv(): return {"x": r.read_float(), "y": r.read_float(), "z": r.read_float()}
            return {"vectors": r.read_list(rv), "v": r.read_list(r.read_string),
                    "floats": r.read_list(r.read_float), "text": r.read_string()}
        def read_plate():
            r.read_byte()
            return {"plateId": r.read_int(), "frontCarId": r.read_int(),
                    "rearCarId": r.read_int(), "vinyls": r.read_list(read_vinyl)}
        p["platesData"] = {"allPlates": r.read_list(read_plate)}
    if r.read_byte() == 0:
        p["carIDnStatus"] = None
    else:
        p["carIDnStatus"] = {
            "carGeneratedIDs": r.read_list(r.read_string),
            "carStatus": r.read_list(r.read_int),
        }
    p["allData"] = r.read_string()
    p["flags"] = r.read_dict()
    p["animations"] = r.read_list(r.read_int)
    p["emojiPacks"] = r.read_list(r.read_int)
    p["wheels"] = r.read_list(r.read_int)
    p["boughtPoliceLights"] = r.read_list(r.read_int)
    p["boughtPoliceSirens"] = r.read_list(r.read_int)
    return p

def try_parse(buf):
    candidates = [buf]
    d1 = decompress(buf)
    if d1:
        candidates.append(d1)
        d2 = decompress(d1)
        if d2: candidates.append(d2)
    for c in candidates:
        if not c: continue
        if len(c) > 0 and c[0] in (17, 23, 24):
            try:
                p = parse_player(c)
                if p and p.get("Name") is not None: return p
            except: pass
        try:
            clean = c[3:] if (len(c) >= 3 and c[0] == 0xef and c[1] == 0xbb) else c
            if clean[0] == 123: return json.loads(clean.decode("utf-8"))
        except: pass
    return None

def decrypt_player_record(base64_text, uid, password=None, email=None):
    try: buf = base64.b64decode(base64_text)
    except: return {"success": False, "message": "Bad base64"}
    if len(buf) < 10: return {"success": False, "message": "Too small"}
    direct = try_parse(buf)
    if direct: return {"success": True, "record": direct}
    if uid:
        try:
            xp = xor_bytes(buf, make_xor_key(uid))
            d  = decompress(xp)
            if d:
                p = try_parse(d)
                if p: return {"success": True, "record": p}
        except: pass
    for key in build_aes_keys(uid or "", password, email):
        plain = decrypt_aes(buf, key)
        if not plain: continue
        p = try_parse(plain)
        if p: return {"success": True, "record": p}
    return {"success": False, "message": "Could not decrypt"}

class Writer:
    def __init__(self): self._p: List[bytes] = []
    def write_byte(self, v): self._p.append(bytes([v & 0xFF]))
    def write_int(self, v):  self._p.append(struct.pack("<i", int(v or 0)))
    def write_float(self, v): self._p.append(struct.pack("<f", float(v or 0.0)))
    def write_string(self, s):
        if s is None: self._p.append(struct.pack("<i", -1)); return
        s = str(s)
        if s == "": self._p.append(struct.pack("<i", 0)); return
        enc = s.encode("utf-8")
        self._p.append(struct.pack("<ii", -(len(enc)) - 1, len(s)) + enc)
    def write_list(self, lst, fn):
        if lst is None: self._p.append(struct.pack("<i", -1)); return
        self._p.append(struct.pack("<i", len(lst)))
        for item in lst: fn(item)
    def write_equipment(self, data):
        if not data: self.write_byte(0); return
        self.write_byte(13)
        for k in ["hair","face","beard","cap","mask","top","gloves","bag","pants","shoes","glasses","SelectedEquipments"]:
            self.write_list(data.get(k, []), self.write_int)
        self.write_int(data.get("Gender", 0))
    def write_plates(self, data):
        if not data: self.write_byte(0); return
        self.write_byte(1)
        plates = data.get("allPlates", [])
        self._p.append(struct.pack("<i", len(plates)))
        for plate in plates:
            self.write_byte(4)
            self.write_int(plate.get("plateId", 0))
            self.write_int(plate.get("frontCarId", 0))
            self.write_int(plate.get("rearCarId", 0))
            vinyls = plate.get("vinyls", [])
            self._p.append(struct.pack("<i", len(vinyls)))
            for vinyl in vinyls:
                self.write_byte(4)
                vecs = vinyl.get("vectors", [])
                self._p.append(struct.pack("<i", len(vecs)))
                for vec in vecs:
                    self._p.append(struct.pack("<fff", vec.get("x",0), vec.get("y",0), vec.get("z",0)))
                self.write_list(vinyl.get("v", []), self.write_string)
                self.write_list(vinyl.get("floats", []), self.write_float)
                self.write_string(vinyl.get("text", ""))
    def write_car_id_status(self, data):
        if not data: self.write_byte(0); return
        self.write_byte(2)
        self.write_list(data.get("carGeneratedIDs", []), self.write_string)
        self.write_list(data.get("carStatus", []), self.write_int)
    def to_bytes(self): return b"".join(self._p)

FIELD_MAPPING = [
    (1,"localID"),(2,"money"),(3,"Name"),(4,"coin"),(5,"allData"),
    (6,"boughtFsos"),(7,"boughtPoliceLights"),(8,"boughtPoliceSirens"),
    (9,"FriendsID"),(10,"LevelsDoneTime"),(11,"floats"),(12,"integers"),
    (13,"fcar"),(14,"favouriteWheels"),(15,"favouriteVinyls"),
    (16,"favouriteEmojis"),(18,"emojiPacks"),
    (41,"personEquipmentsMale"),(42,"personEquipmentsFemale"),
    (43,"platesData"),(44,"carIDnStatus"),(45,"flags"),
    (46,"animations"),(48,"wheels"),
]
INT_LIST_FIELDS   = {6,7,8,12,13,14,15,16,18,46,48}
FLOAT_LIST_FIELDS = {10,11}
ALWAYS_SEND       = {"allData"}

def _field_modified(nv, ov):
    if nv is None and ov is None: return False
    if nv is None or ov is None: return True
    if type(nv) != type(ov): return True
    if isinstance(nv, (dict,list)):
        return json.dumps(nv,sort_keys=True) != json.dumps(ov,sort_keys=True)
    return nv != ov

def serialize_field(fid, value):
    w = Writer()
    if fid in (1,3,5): w.write_string(value); return w.to_bytes()
    if fid in (2,4): w.write_int(value or 0); return w.to_bytes()
    if fid == 9:
        friends = value or []
        w._p.append(struct.pack("<i", len(friends)))
        for f in friends:
            w.write_byte(3)
            w.write_string((f or {}).get("id",""))
            w.write_string((f or {}).get("Name",""))
            w.write_string((f or {}).get("accountID",""))
        return w.to_bytes()
    if fid in INT_LIST_FIELDS: w.write_list(value or [], w.write_int); return w.to_bytes()
    if fid in FLOAT_LIST_FIELDS: w.write_list(value or [], w.write_float); return w.to_bytes()
    if fid in (41,42): w.write_equipment(value); return w.to_bytes()
    if fid == 43: w.write_plates(value); return w.to_bytes()
    if fid == 44: w.write_car_id_status(value); return w.to_bytes()
    if fid == 45:
        flags = value or {}
        w._p.append(struct.pack("<i", len(flags)))
        for k, v in flags.items():
            w.write_int(int(k)); w.write_int(int(v))
        return w.to_bytes()
    return None

def build_payload(record, uid, original=None):
    fields = []
    for fid, key in FIELD_MAPPING:
        value = record.get(key)
        if value is None: continue
        if key in ALWAYS_SEND:
            should = isinstance(value, str) and len(value) > 0
        elif original is not None:
            should = _field_modified(value, original.get(key))
        else:
            should = True
        if not should: continue
        raw = serialize_field(fid, value)
        if raw is not None: fields.append((fid, raw))
    parts = [struct.pack("<i", len(fields))]
    for fid, raw in fields:
        parts.append(struct.pack("<hi", fid, len(raw)))
        parts.append(raw)
    combined   = b"".join(parts)
    compressed = brotli.compress(combined) if HAS_BROTLI else zlib.compress(combined)
    encrypted  = xor_bytes(compressed, make_xor_key(uid))
    return base64.b64encode(encrypted).decode("ascii")

GAME_HEADERS = {
    "Accept": "*/*", "Accept-Encoding": "gzip",
    "Content-Type": "application/json",
    "User-Agent": "UnityPlayer/2022.3.62f2 (UnityWebRequest/1.0, libcurl/8.10.1-DEV)",
    "X-Unity-Version": "2022.3.62f2",
}

class CPMNuker:
    def __init__(self):
        self.db_path = "cpm_tokens.db"
        self.cache: Dict[str, Dict] = {}
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as c:
            c.execute("""CREATE TABLE IF NOT EXISTS tokens (
                user_id INTEGER PRIMARY KEY, auth_token TEXT, email TEXT,
                password TEXT, refresh_token TEXT, firebase_uid TEXT,
                token_expires_at REAL)""")
            c.execute("""CREATE TABLE IF NOT EXISTS user_data (
                cache_key TEXT PRIMARY KEY, email TEXT, data_json TEXT)""")
            try: c.execute("ALTER TABLE tokens ADD COLUMN firebase_uid TEXT")
            except: pass
            c.commit()

    def _ck(self, uid, email=None):
        if email: return f"{uid}_{email}"
        td = self.get_token_data(uid)
        return f"{uid}_{td['email']}" if td and td.get("email") else str(uid)

    def save_token(self, uid, auth, email, pw=None, rt=None, fuid=None):
        with sqlite3.connect(self.db_path) as c:
            c.execute("""INSERT OR REPLACE INTO tokens
                (user_id,auth_token,email,password,refresh_token,firebase_uid,token_expires_at)
                VALUES (?,?,?,?,?,?,?)""",
                (uid, auth, email, pw, rt, fuid, time.time()+3600))
            c.commit()

    def get_token_data(self, uid):
        with sqlite3.connect(self.db_path) as c:
            row = c.execute("""SELECT auth_token,email,password,refresh_token,
                firebase_uid,token_expires_at FROM tokens WHERE user_id=?""", (uid,)).fetchone()
        if row:
            return {"auth_token":row[0],"email":row[1],"password":row[2],
                    "refresh_token":row[3],"firebase_uid":row[4],"token_expires_at":row[5]}
        return None

    def get_token(self, uid):
        td = self.get_token_data(uid)
        return {"auth_token":td["auth_token"],"email":td["email"]} if td else None

    def update_token(self, uid, auth, rt=None):
        exp = time.time()+3600
        with sqlite3.connect(self.db_path) as c:
            if rt: c.execute("UPDATE tokens SET auth_token=?,refresh_token=?,token_expires_at=? WHERE user_id=?",(auth,rt,exp,uid))
            else:  c.execute("UPDATE tokens SET auth_token=?,token_expires_at=? WHERE user_id=?",(auth,exp,uid))
            c.commit()

    def delete_token(self, uid):
        with sqlite3.connect(self.db_path) as c:
            c.execute("DELETE FROM tokens WHERE user_id=?",(uid,)); c.commit()
        for k in [k for k in self.cache if k.startswith(str(uid))]:
            del self.cache[k]

    def is_expired(self, uid):
        td = self.get_token_data(uid)
        return not td or not td.get("token_expires_at") or td["token_expires_at"] < time.time()

    def get_record(self, uid, email=None):
        ck = self._ck(uid, email)
        if ck not in self.cache:
            with sqlite3.connect(self.db_path) as c:
                row = c.execute("SELECT data_json FROM user_data WHERE cache_key=?",(ck,)).fetchone()
            if row:
                try: self.cache[ck] = json.loads(row[0])
                except: pass
        return self.cache.get(ck, {})

    def set_record(self, uid, data, email=None):
        ck = self._ck(uid, email)
        self.cache[ck] = data
        with sqlite3.connect(self.db_path) as c:
            c.execute("INSERT OR REPLACE INTO user_data (cache_key,email,data_json) VALUES (?,?,?)",
                      (ck, email, json.dumps(data))); c.commit()

    async def _post(self, url, payload, headers):
        try:
            h = {k:v for k,v in headers.items() if k.lower() != "host"}
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout, connector=make_http_connector(limit=20, ssl=False)) as s:
                async with s.post(url, json=payload, headers=h) as r:
                    text = await r.text()
                    try: return json.loads(text)
                    except: return {"raw": text, "status": r.status}
        except Exception as e:
            log.error(f"HTTP: {e}"); return None

    async def login(self, email, password):
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FK}"
        h = {"Accept":"*/*","Accept-Encoding":"gzip","Content-Type":"application/json",
             "User-Agent":"UnityPlayer/2022.3.62f2 (UnityWebRequest/1.0, libcurl/8.10.1-DEV)",
             "X-Unity-Version":"2022.3.62f2"}
        p = {"email":email,"password":password,"returnSecureToken":True,"clientType":"CLIENT_TYPE_ANDROID"}
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout, connector=make_http_connector(limit=20, ssl=False)) as s:
                async with s.post(url, json=p, headers=h) as resp:
                    text = await resp.text()
                    log.info(f"Login [{resp.status}] {email}: {text[:200]}")
                    try: r = json.loads(text)
                    except: return {"ok":False,"message":"NETWORK_ERROR"}
        except Exception as e:
            log.error(f"Login: {e}"); return {"ok":False,"message":"NETWORK_ERROR"}
        if "idToken" in r:
            return {"ok":True,"auth":r["idToken"],"refresh_token":r.get("refreshToken",""),"firebase_uid":r.get("localId","")}
        err = str(r.get("error",{}).get("message","")).upper()
        for k in ["EMAIL_NOT_FOUND","INVALID_PASSWORD","INVALID_LOGIN_CREDENTIALS","TOO_MANY_ATTEMPTS","USER_DISABLED","INVALID_EMAIL"]:
            if k in err: return {"ok":False,"message":k}
        return {"ok":False,"message":f"LOGIN_FAILED: {err[:60]}"}

    async def _refresh(self, uid):
        td = self.get_token_data(uid)
        if not td: return False,"NO_TOKEN"
        rt,em,pw = td.get("refresh_token"),td.get("email"),td.get("password")
        if rt:
            try:
                timeout = aiohttp.ClientTimeout(total=30)
                async with aiohttp.ClientSession(timeout=timeout, connector=make_http_connector(limit=20, ssl=False)) as s:
                    async with s.post(f"https://securetoken.googleapis.com/v1/token?key={FK}",
                        json={"grant_type":"refresh_token","refresh_token":rt},
                        headers={"Content-Type":"application/json"}) as resp:
                        r = await resp.json(content_type=None)
                        if r and r.get("id_token"):
                            self.update_token(uid,r["id_token"],r.get("refresh_token",rt))
                            return True,"OK"
            except: pass
        if em and pw:
            res = await self.login(em,pw)
            if res.get("ok"):
                self.save_token(uid,res["auth"],em,pw,res.get("refresh_token",""),res.get("firebase_uid",""))
                return True,"OK"
        return False,"REFRESH_FAILED"

    async def get_auth(self, uid):
        if self.is_expired(uid):
            ok,msg = await self._refresh(uid)
            if not ok: return False,msg,""
        td = self.get_token_data(uid)
        if td and td.get("auth_token"): return True,"OK",td["auth_token"]
        return False,"NO_TOKEN",""

    async def load(self, uid, force=False):
        td = self.get_token_data(uid)
        if not td: return False
        ck = self._ck(uid)
        if not force and ck in self.cache: return True
        ok,msg,auth = await self.get_auth(uid)
        if not ok: return False
        try:
            r = await self._post(LOAD_URL,{"data":None},{**GAME_HEADERS,"Authorization":f"Bearer {auth}"})
            if not r or not r.get("result"): return False
            dec = decrypt_player_record(r["result"],td.get("firebase_uid",""),td.get("password",""),td.get("email",""))
            if dec.get("success") and dec.get("record"):
                self.set_record(uid,dec["record"],td.get("email",""))
                log.info(f"Loaded {uid}: {dec['record'].get('Name')} ${dec['record'].get('money')}")
                return True
            return False
        except Exception as e:
            log.error(f"Load error: {e}"); return False

    def _ok(self, v):
        if v in (1,True): return True
        if v in (0,False): return False
        if isinstance(v,str):
            t=v.strip()
            if t=="1": return True
            if t=="0": return False
            try: return self._ok(json.loads(t))
            except: return False
        if isinstance(v,dict):
            for k in ("result","ok","success"):
                if k in v: return self._ok(v[k])
        return False

    async def _send(self, auth, record, fuid, original=None):
        if not fuid: return False,"NO_UID"
        try:
            payload = build_payload(record, fuid, original)
            r = await self._post(SAVE_URL,
                {"data":{"data":payload,"deviceId":fuid[:8]}},
                {**GAME_HEADERS,"Authorization":f"Bearer {auth}","Connection":"Keep-Alive",
                 "User-Agent":"Dalvik/2.1.0 (Linux; U; Android 12; Pixel 6 Build/SD1A.210817.036)"})
            if r and self._ok(r): return True,"OK"
            return False,f"SAVE_FAILED: {str(r)[:100]}"
        except Exception as e: return False,str(e)

    async def _save(self, uid, data):
        ok,msg,auth = await self.get_auth(uid)
        if not ok: return {"ok":False,"message":msg}
        td    = self.get_token_data(uid)
        fuid  = td.get("firebase_uid","") if td else ""
        email = td.get("email","") if td else ""
        orig  = self.get_record(uid,email) or None
        ok2,msg2 = await self._send(auth,data,fuid,orig)
        if ok2:
            self.set_record(uid,data,email)
            return {"ok":True}
        return {"ok":False,"message":msg2}

    async def _modify(self, uid, mods):
        await self.load(uid)
        td    = self.get_token_data(uid)
        email = td.get("email") if td else None
        d     = deepcopy(self.get_record(uid,email))
        if not d or not d.get("Name"):
            return {"ok":False,"message":"Could not load account data. Try Refresh first."}
        for k,v in mods.items():
            if k=="money": v=min(v,MAX_MONEY)
            if k=="coin":  v=min(v,MAX_COIN)
            d[k]=v
        return await self._save(uid,d)

    async def _set_floats(self, uid, indices_values):
        await self.load(uid)
        td    = self.get_token_data(uid)
        email = td.get("email") if td else None
        d     = deepcopy(self.get_record(uid,email))
        if not d or not d.get("Name"):
            return {"ok":False,"message":"Could not load account data. Try Refresh first."}
        fl = d.get("floats",[])
        max_idx = max(idx for idx,_ in indices_values)
        while len(fl) <= max_idx: fl.append(0.0)
        for idx,val in indices_values: fl[idx]=float(val)
        d["floats"]=fl
        return await self._save(uid,d)

    async def _set_integers(self, uid, indices_values):
        await self.load(uid)
        td    = self.get_token_data(uid)
        email = td.get("email") if td else None
        d     = deepcopy(self.get_record(uid,email))
        if not d or not d.get("Name"):
            return {"ok":False,"message":"Could not load account data. Try Refresh first."}
        it = d.get("integers",[])
        max_idx = max(idx for idx,_ in indices_values)
        while len(it) <= max_idx: it.append(0)
        for idx,val in indices_values: it[idx]=int(val)
        d["integers"]=it
        return await self._save(uid,d)

    async def set_money(self, uid, amount):
        return await self._modify(uid, {"money": min(amount, MAX_MONEY)})
    async def set_coin(self, uid, amount):
        return await self._modify(uid, {"coin": min(amount, MAX_COIN)})
    async def set_player_name(self, uid, name):
        return await self._modify(uid, {"Name": name})
    async def set_player_id(self, uid, pid):
        return await self._modify(uid, {"localID": pid.upper()})
    async def set_race_wins(self, uid, amount):
        return await self._set_floats(uid, [(8, float(amount))])
    async def set_race_loses(self, uid, amount):
        return await self._set_floats(uid, [(9, float(amount))])
    async def unlock_w16(self, uid):
        return await self._set_floats(uid, [(32, 1.0)])
    async def unlock_horns(self, uid):
        return await self._set_floats(uid, [(27,1.0),(28,1.0),(29,1.0),(30,1.0),(31,1.0)])
    async def disable_damage(self, uid):
        return await self._set_floats(uid, [(34, 1.0)])
    async def unlimited_fuel(self, uid):
        return await self._set_floats(uid, [(3, 1.0)])
    async def unlock_smoke(self, uid):
        return await self._set_floats(uid, [(33, 1.0)])
    async def unlock_animations(self, uid):
        await self.load(uid)
        td    = self.get_token_data(uid)
        email = td.get("email") if td else None
        d     = deepcopy(self.get_record(uid,email))
        if not d or not d.get("Name"):
            return {"ok":False,"message":"Could not load account data."}
        d["animations"] = list(set(d.get("animations",[]) + list(range(301))))
        return await self._save(uid,d)
    async def unlock_wheels(self, uid):
        await self.load(uid)
        td    = self.get_token_data(uid)
        email = td.get("email") if td else None
        d     = deepcopy(self.get_record(uid,email))
        if not d or not d.get("Name"):
            return {"ok":False,"message":"Could not load account data."}
        d["wheels"] = list(set(d.get("wheels",[]) + list(range(73,221))))
        it = d.get("integers",[])
        while len(it) < 113: it.append(0)
        for i in [0,1,2,3,4,5,110,111,112]: it[i]=1
        d["integers"]=it
        return await self._save(uid,d)
    async def unlock_houses(self, uid):
        return await self._set_integers(uid, [(8,1),(110,1),(111,1),(112,1)])
    async def complete_all_levels(self, uid):
        lvl = [0] + [120 if i==43 else 1 for i in range(1,110)]
        return await self._modify(uid, {"LevelsDoneTime": lvl})
    async def set_rank(self, uid):
        await self.load(uid)
        ok,msg,auth = await self.get_auth(uid)
        if not ok: return {"ok":False,"message":msg}
        rd = {"RatingData":{"time":1e22,"cars":1e16,"car_fix":1e13,"car_collided":1e12,
            "car_exchange":1e13,"car_trade":1e13,"car_wash":1e13,"slicer_cut":1e13,
            "drift_max":1e14,"drift":1e14,"cargo":1e5,"delivery":1e5,"race_win":3e20,
            "taxi":1e10,"levels":10000990000,"gifts":1e9,"fuel":1e10,"offroad":1e10,
            "speed_banner":1e9,"reactions":1e17,"run":1e9,"real_estate":1e9,
            "t_distance":1e10,"treasure":1e10,"block_post":1e10,"push_ups":1e12,
            "burnt_tire":1e10,"passanger_distance":1e8}}
        r = await self._post(RANK_URL,{"data":json.dumps(rd)},{**GAME_HEADERS,"Authorization":f"Bearer {auth}"})
        if r and self._ok(r): return {"ok":True}
        return {"ok":False,"message":"RANK_FAILED"}
    async def fix_account(self, uid):
        await self.load(uid)
        td    = self.get_token_data(uid)
        email = td.get("email") if td else None
        d     = deepcopy(self.get_record(uid,email))
        if not d or not d.get("Name"):
            return {"ok":False,"message":"Could not load account data."}
        bugs=0
        fl = (d.get("floats",[]))[:54]
        while len(fl)<54: fl.append(0.0)
        fixed_fl=[]
        for v in fl:
            if v in (1,1.0): fixed_fl.append(1.0)
            elif isinstance(v,(int,float)) and v>1: bugs+=1; fixed_fl.append(0.0)
            else: fixed_fl.append(float(v) if v else 0.0)
        it = (d.get("integers",[]))[:120]
        while len(it)<120: it.append(0)
        fixed_it=[]
        for v in it:
            if v==1: fixed_it.append(1)
            elif isinstance(v,(int,float)) and v>1: bugs+=1; fixed_it.append(0)
            else: fixed_it.append(int(v) if v else 0)
        d["floats"]=fixed_fl; d["integers"]=fixed_it
        result = await self._save(uid,d)
        return {"ok":True,"bugs_fixed":bugs} if result.get("ok") else {"ok":False,"message":"FIX_FAILED"}

nuker = CPMNuker()

# ================= LOCAL STORE (Game Editor) =================
STORE_PATH = DATA_DIR / "cpm_store.json"
DEFAULT_STORE = {
    "allowed_users": [], "vip_users": [], "admins": {},
    "pending": {}, "banned": [], "expiry": {},
    "stats": {"total_logins": 0, "total_actions": 0, "total_unlocks": 0},
    "admin_log": [], "users": {}, "daily_stats": {},
    "notes": {}, "warnings": {},
    "maintenance": False, "broadcast_history": [],
    "bot_photo": "",
}

def load_store():
    try:
        if STORE_PATH.exists():
            with STORE_PATH.open("r", encoding="utf-8") as f:
                data = json.load(f)
            for k, v in DEFAULT_STORE.items():
                if k not in data:
                    data[k] = deepcopy(v)
            data["admins"]        = {str(k): v for k, v in data.get("admins", {}).items()}
            data["allowed_users"] = list({int(x) for x in data.get("allowed_users", [])})
            data["vip_users"]     = list({int(x) for x in data.get("vip_users", [])})
            data["banned"]        = list({int(x) for x in data.get("banned", [])})
            return data
        save_store(DEFAULT_STORE)
        return deepcopy(DEFAULT_STORE)
    except Exception:
        save_store(DEFAULT_STORE)
        return deepcopy(DEFAULT_STORE)

def save_store(data):
    try:
        tmp = STORE_PATH.with_suffix(".json.tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        tmp.replace(STORE_PATH)
        return True
    except Exception as e:
        log.error(f"Save error: {e}")
        return False

STORE = load_store()
if OWNER_ID not in STORE["allowed_users"]:
    STORE["allowed_users"].append(OWNER_ID)
if str(OWNER_ID) not in STORE["admins"]:
    STORE["admins"][str(OWNER_ID)] = "owner"
save_store(STORE)

ALLOWED_USERS = list(STORE.get("allowed_users", []))
VIP_USERS     = list(STORE.get("vip_users", []))
ADMINS        = {int(k): v for k, v in STORE.get("admins", {}).items()}
BANNED        = list(STORE.get("banned", []))
PENDING       = STORE.get("pending", {})
EXPIRY        = STORE.get("expiry", {})
RATE_DATA     = {}
ADMIN_LEVELS  = {"owner": 100, "superadmin": 50, "admin": 10, "moderator": 5}

def is_allowed(uid):   return uid in ALLOWED_USERS
def is_banned(uid):    return uid in BANNED
def is_vip(uid):       return uid in VIP_USERS
def admin_level(uid):  return ADMIN_LEVELS.get(ADMINS.get(uid, ""), 0)
def admin_role(uid):   return ADMINS.get(uid, "")
def has_admin(uid, required="admin"):
    return admin_level(uid) >= ADMIN_LEVELS.get(required, 10)

def check_rate_limit(uid):
    now  = time.time()
    key  = str(uid)
    data = RATE_DATA.get(key, {"count": 0, "reset": now + RATE_LIMIT_SECONDS})
    if now > data["reset"]:
        data = {"count": 0, "reset": now + RATE_LIMIT_SECONDS}
    if data["count"] >= RATE_LIMIT_ACTIONS:
        return False, int(data["reset"] - now)
    data["count"] += 1
    RATE_DATA[key] = data
    return True, 0

# ================= BULK SYSTEM =================
async def set_rank(cpm, token):
    url = CPM[cpm]["rating"]
    payload = {"data": json.dumps(RATING_DATA)}
    headers = {
        "accept": "*/*",
        "content-type": "application/json",
        "user-agent": "com.aidana.cardriving.ios/4.8.9 iPhone/16.7.6 hw/iPhone10_6",
        "authorization": f"Bearer {token}"
    }
    try:
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout, connector=make_http_connector(limit=20, ssl=False)) as s:
            async with s.post(url, json=payload, headers=headers) as resp:
                if resp.status == 200:
                    return True
            payload_v2 = {"idToken": token, "data": json.dumps(RATING_DATA)}
            async with s.post(url, json=payload_v2, headers=headers) as resp2:
                if resp2.status == 200:
                    return True
            async with s.post(url, json={"idToken": token}, headers=headers) as resp3:
                if resp3.status == 200:
                    return True
        return False
    except Exception as e:
        print(f"[KING RANK ERROR] {e}")
        return False

def get_bulk_semaphore():
    global _bulk_job_semaphore
    if _bulk_job_semaphore is None:
        _bulk_job_semaphore = asyncio.Semaphore(BULK_MAX_PARALLEL_JOBS)
    return _bulk_job_semaphore

def gen_password(length=12):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choices(chars, k=length))

def parse_accounts(text):
    accounts = []
    seen = set()
    total_lines = 0
    for line in text.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        total_lines += 1
        for sep in [':', '|', ';', '\t', ' ']:
            parts = line.split(sep, 1)
            if len(parts) == 2:
                email_part = parts[0].strip().lower()
                pass_part = parts[1].strip()
                if '@' in email_part and pass_part and email_part not in seen:
                    seen.add(email_part)
                    accounts.append((email_part, pass_part))
                    break
    return accounts, total_lines

def get_key_for_index(cpm, index):
    if cpm == "CPM1":
        keys = CPM["CPM1"]["keys"]
        # 🔑 KEY ROTATION: 1000 accounts per key
        # Key 1: accounts 0-999, 2000-2999, 4000-4999...
        # Key 2: accounts 1000-1999, 3000-3999, 5000-5999...
        key_index = (index // 1000) % len(keys)
        return keys[key_index]
    else:
        return CPM["CPM2"]["key"]

async def change_one_account(session, key, old_email, old_pass, new_email, new_pass, mode, semaphore):
    async with semaphore:
        login_endpoint = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={key}"
        update_endpoint = f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={key}"
        last_error = "UNKNOWN"
        for attempt in range(BULK_RETRY_ATTEMPTS):
            try:
                await asyncio.sleep(BULK_RATE_LIMIT_DELAY)
                async with session.post(login_endpoint, json={
                    "email": old_email, "password": old_pass, "returnSecureToken": True
                }) as r:
                    data = await r.json()
                if "idToken" not in data:
                    err = data.get("error", {}).get("message", "LOGIN_FAILED")
                    last_error = err
                    if "INVALID_PASSWORD" in err or "EMAIL_NOT_FOUND" in err:
                        return "fail", old_email, err
                    await asyncio.sleep(BULK_RETRY_DELAY * (attempt + 1))
                    continue
                token = data["idToken"]
                changed = []
                if mode in (BULK_MODE_BOTH, BULK_MODE_EMAIL):
                    await asyncio.sleep(BULK_RATE_LIMIT_DELAY)
                    async with session.post(update_endpoint, json={
                        "idToken": token, "email": new_email, "returnSecureToken": True
                    }) as r:
                        email_resp = await r.json()
                    if "idToken" in email_resp:
                        token = email_resp["idToken"]
                        changed.append("email")
                    else:
                        err = email_resp.get("error", {}).get("message", "EMAIL_FAIL")
                        last_error = err
                        if "EMAIL_EXISTS" in err:
                            return "fail", old_email, "EMAIL_EXISTS"
                        if attempt < BULK_RETRY_ATTEMPTS - 1:
                            await asyncio.sleep(BULK_RETRY_DELAY * (attempt + 1))
                            continue
                        return "fail", old_email, err
                if mode in (BULK_MODE_BOTH, BULK_MODE_PASS):
                    await asyncio.sleep(BULK_RATE_LIMIT_DELAY)
                    async with session.post(update_endpoint, json={
                        "idToken": token, "password": new_pass, "returnSecureToken": True
                    }) as r:
                        pass_resp = await r.json()
                    if "idToken" in pass_resp:
                        changed.append("pass")
                    else:
                        err = pass_resp.get("error", {}).get("message", "PASS_FAIL")
                        last_error = err
                        if attempt < BULK_RETRY_ATTEMPTS - 1:
                            await asyncio.sleep(BULK_RETRY_DELAY * (attempt + 1))
                            continue
                        if "email" in changed:
                            return "partial", old_email, f"Email OK | Pass Fail: {err}"
                        return "fail", old_email, err
                if mode == BULK_MODE_BOTH:
                    return "ok", old_email, f"{new_email}:{new_pass}"
                elif mode == BULK_MODE_EMAIL:
                    return "ok", old_email, f"{new_email} (pass: {old_pass})"
                else:
                    return "ok", old_email, f"{old_email}:{new_pass}"
            except Exception as e:
                last_error = str(e)
                if attempt < BULK_RETRY_ATTEMPTS - 1:
                    await asyncio.sleep(BULK_RETRY_DELAY * (attempt + 1))
                    continue
        return "fail", old_email, last_error

# ================= LANGUAGES =================
LANGUAGES = {
    "en": {
        "flag": "🇬🇧", "name": "English",
        "welcome": (
            "╔══════════════════════╗\n"
            " ⚡😈𝘾𝙋𝙈 𝙈𝙊𝘿𝙕 𝙑𝙄𝙋 𝙏𝙊𝙊𝙇 😈⚡\n"
            "╚══════════════════════╝\n\n"
            "💎 📊𝙎𝙏𝘼𝙏𝙐𝙎 : 🟢𝙊𝙉𝙇𝙄𝙉𝙀🟢 💎\n"
            "⚡ 𝙎𝙀𝘾𝙐𝙍𝙄𝙏𝙔 🔐: 𝙀𝙉𝙃𝘼𝙉𝘾𝙀𝘿⚡\n"
            "🔥 𝙑𝙀𝙍𝙎𝙄𝙊𝙉🌐: ⚡ 𝙑𝙀𝙍𝙎𝙄𝙊𝙉 2.0𝙑⚡\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🔰 𝙎𝙀𝙇𝙀𝘾𝙏 𝘾𝙋𝙈 𝙈𝙊𝘿𝙀 🔰\n"
            "━━━━━━━━━━━━━━━━━━━━"
        ),
        "enter_email": "📧 𝙀𝙉𝙏𝙀𝙍 𝙀𝙈𝘼𝙄𝙇:",
        "enter_password": "🔑 𝙀𝙉𝙏𝙀𝙍 𝙋𝘼𝙎𝙎𝙒𝙊𝙍𝘿:",
        "session_expired": "❌ 𝙎𝙀𝙎𝙎𝙄𝙊𝙉 𝙀𝙓𝙋𝙄𝙍𝙀𝘿. 𝙋𝙇𝙀𝘼𝙎𝙀 /𝙨𝙩𝙖𝙧𝙩 𝘼𝙂𝘼𝙄𝙉",
        "login_success": "💎 𝙇𝙊𝙂𝙄𝙉 𝙎𝙐𝘾𝘾𝙀𝙎𝙎 💎",
        "king_active": "👑 𝙆𝙄𝙉𝙂 𝙍𝘼𝙉𝙆 𝘼𝘾𝙏𝙄𝙑𝙀",
        "king_failed": "❌ 𝙁𝘼𝙄𝙇𝙀𝘿 𝙏𝙊 𝘼𝘾𝙏𝙄𝙑𝘼𝙏𝙀 𝙍𝘼𝙉𝙆",
        "login_again": "❌ 𝙋𝙇𝙀𝘼𝙎𝙀 𝙇𝙊𝙂𝙄𝙉 𝘼𝙂𝘼𝙄𝙉",
        "enter_new_email": "✉️ 𝙀𝙉𝙏𝙀𝙍 𝙉𝙀𝙒 𝙀𝙈𝘼𝙄𝙇",
        "enter_new_pass": "🔑 𝙀𝙉𝙏𝙀𝙍 𝙉𝙀𝙒 𝙋𝘼𝙎𝙎𝙒𝙊𝙍𝘿",
        "logout_success": "❌ 𝙇𝙊𝙂𝙊𝙐𝙏 𝙎𝙐𝘾𝘾𝙀𝙎𝙎",
        "email_updated": "✅ 𝙀𝙈𝘼𝙄𝙇 𝙐𝙋𝘿𝘼𝙏𝙀𝘿 ✅",
        "pass_updated": "✅ 𝙋𝘼𝙎𝙎𝙒𝙊𝙍𝘿 𝙐𝙋𝘿𝘼𝙏𝙀𝘿 ✅",
        "email_exists": "❌ 𝙀𝙈𝘼𝙄𝙇 𝘼𝙇𝙍𝙀𝘼𝘿𝙔 𝙍𝙀𝙂𝙄𝙎𝙏𝙍𝙀𝘿\n\n✉️ 𝙀𝙉𝙏𝙀𝙍 𝘼𝙉𝙊𝙏𝙃𝙀𝙍 𝙀𝙈𝘼𝙄𝙇:",
        "login_failed": "❌ 𝙇𝙊𝙂𝙄𝙉 𝙁𝘼𝙄𝙇𝙀𝘿",
        "error": "❌ 𝙀𝙍𝙍𝙊𝙍",
        "banned": "🚫 𝙔𝙊𝙐 𝘼𝙍𝙀 𝘽𝘼𝙉𝙉𝙀𝘿 𝙁𝙍𝙊𝙈 𝙐𝙎𝙄𝙉𝙂 𝙏𝙃𝙄𝙎 𝘽𝙊𝙏",
        "btn_king": "👑 KING RANK",
        "btn_cemail": "✉️ CHANGE EMAIL", "btn_cpass": "🔑 CHANGE PASSWORD",
        "btn_logout": "❌ LOGOUT",
        "btn_bulk": "⚡ BULK ACCOUNT CHANGER ⚡",
        "btn_gedit": "🎮 GAME EDITOR",
    },
    "pt_br": {
        "flag": "🇧🇷", "name": "Português (BR)",
        "welcome": (
            "╔══════════════════════╗\n"
            " ⚡😈𝘾𝙋𝙈 𝙈𝙊𝘿𝙕 𝙑𝙄𝙋 𝙏𝙊𝙊𝙇 😈⚡\n"
            "╚══════════════════════╝\n\n"
            "💎 📊𝙎𝙏𝘼𝙏𝙐𝙎 : 🟢𝙊𝙉𝙇𝙄𝙉𝙀🟢 💎\n"
            "⚡ 𝙎𝙀𝘾𝙐𝙍𝘼𝙉𝘾𝘼 🔐: 𝘼𝙋𝙍𝙄𝙈𝙊𝙍𝘼𝘿𝘼⚡\n"
            "🔥 𝙑𝙀𝙍𝙎𝘼𝙊🌐: ⚡ 𝙑𝙀𝙍𝙎𝘼𝙊 2.0𝙑⚡\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🔰 𝙎𝙀𝙇𝙀𝘾𝙄𝙊𝙉𝙀 𝙊 𝙈𝙊𝘿𝙊 𝘾𝙋𝙈 🔰\n"
            "━━━━━━━━━━━━━━━━━━━━"
        ),
        "enter_email": "📧 𝙄𝙉𝙎𝙄𝙍𝘼 𝙊 𝙀𝙈𝘼𝙄𝙇:",
        "enter_password": "🔑 𝙄𝙉𝙎𝙄𝙍𝘼 𝘼 𝙎𝙀𝙉𝙃𝘼:",
        "session_expired": "❌ 𝙎𝙀𝙎𝙎𝘼𝙊 𝙀𝙓𝙋𝙄𝙍𝘼𝘿𝘼. 𝙋𝙊𝙍 𝙁𝘼𝙑𝙊𝙍 𝙐𝙎𝙀 /𝙨𝙩𝙖𝙧𝙩 𝙉𝙊𝙑𝘼𝙈𝙀𝙉𝙏𝙀",
        "login_success": "💎 𝙇𝙊𝙂𝙄𝙉 𝘽𝙀𝙈-𝙎𝙐𝘾𝙀𝘿𝙄𝘿𝙊 💎",
        "king_active": "👑 𝙍𝘼𝙉𝙆 𝙍𝙀𝙄 𝘼𝙏𝙄𝙑𝙊",
        "king_failed": "❌ 𝙁𝘼𝙇𝙃𝘼 𝘼𝙊 𝘼𝙏𝙄𝙑𝘼𝙍 𝙍𝘼𝙉𝙆",
        "login_again": "❌ 𝙋𝙊𝙍 𝙁𝘼𝙑𝙊𝙍 𝙁𝘼Ç𝘼 𝙇𝙊𝙂𝙄𝙉 𝙉𝙊𝙑𝘼𝙈𝙀𝙉𝙏𝙀",
        "enter_new_email": "✉️ 𝙄𝙉𝙎𝙄𝙍𝘼 𝙊 𝙉𝙊𝙑𝙊 𝙀𝙈𝘼𝙄𝙇",
        "enter_new_pass": "🔑 𝙄𝙉𝙎𝙄𝙍𝘼 𝘼 𝙉𝙊𝙑𝘼 𝙎𝙀𝙉𝙃𝘼",
        "logout_success": "❌ 𝙇𝙊𝙂𝙊𝙐𝙏 𝘽𝙀𝙈-𝙎𝙐𝘾𝙀𝘿𝙄𝘿𝙊",
        "email_updated": "✅ 𝙀𝙈𝘼𝙄𝙇 𝘼𝙏𝙐𝘼𝙇𝙄𝙕𝘼𝘿𝙊 ✅",
        "pass_updated": "✅ 𝙎𝙀𝙉𝙃𝘼 𝘼𝙏𝙐𝘼𝙇𝙄𝙕𝘼𝘿𝘼 ✅",
        "email_exists": "❌ 𝙀𝙈𝘼𝙄𝙇 𝙅𝘼 𝙍𝙀𝙂𝙄𝙎𝙏𝙍𝘼𝘿𝙊\n\n✉️ 𝙄𝙉𝙎𝙄𝙍𝘼 𝙊𝙐𝙏𝙍𝙊 𝙀𝙈𝘼𝙄𝙇:",
        "login_failed": "❌ 𝙁𝘼𝙇𝙃𝘼 𝙉𝙊 𝙇𝙊𝙂𝙄𝙉",
        "error": "❌ 𝙀𝙍𝙍𝙊",
        "banned": "🚫 𝙑𝙊𝘾𝙀 𝙀𝙎𝙏𝘼 𝘽𝘼𝙉𝙄𝘿𝙊 𝘿𝙀 𝙐𝙎𝘼𝙍 𝙀𝙎𝙏𝙀 𝘽𝙊𝙏",
        "btn_king": "👑 RANK REI",
        "btn_cemail": "✉️ TROCAR EMAIL", "btn_cpass": "🔑 TROCAR SENHA",
        "btn_logout": "❌ SAIR",
        "btn_bulk": "⚡ MUDANÇA DE CONTAS EM MASSA ⚡",
        "btn_gedit": "🎮 EDITOR DE JOGO",
    },
    "es_eu": {
        "flag": "🇪🇸", "name": "Español (EU)",
        "welcome": (
            "╔══════════════════════╗\n"
            " ⚡😈𝘾𝙋𝙈 𝙈𝙊𝘿𝙕 𝙑𝙄𝙋 𝙏𝙊𝙊𝙇 😈⚡\n"
            "╚══════════════════════╝\n\n"
            "💎 📊𝙀𝙎𝙏𝘼𝘿𝙊 : 🟢𝙀𝙉 𝙇𝙄́𝙉𝙀𝘼🟢 💎\n"
            "⚡ 𝙎𝙀𝙂𝙐𝙍𝙄𝘿𝘼𝘿 🔐: 𝙈𝙀𝙅𝙊𝙍𝘼𝘿𝘼⚡\n"
            "🔥 𝙑𝙀𝙍𝙎𝙄𝙊́𝙉🌐: ⚡ 𝙑𝙀𝙍𝙎𝙄𝙊́𝙉 2.0𝙑⚡\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🔰 𝙎𝙀𝙇𝙀𝘾𝘾𝙄𝙊𝙉𝘼 𝙈𝙊𝘿𝙊 𝘾𝙋𝙈 🔰\n"
            "━━━━━━━━━━━━━━━━━━━━"
        ),
        "enter_email": "📧 𝙄𝙉𝙏𝙍𝙊𝘿𝙐𝘾𝙀 𝙀𝙇 𝙀𝙈𝘼𝙄𝙇:",
        "enter_password": "🔑 𝙄𝙉𝙏𝙍𝙊𝘿𝙐𝘾𝙀 𝙇𝘼 𝘾𝙊𝙉𝙏𝙍𝘼𝙎𝙀𝙉̃𝘼:",
        "session_expired": "❌ 𝙎𝙀𝙎𝙄𝙊́𝙉 𝙀𝙓𝙋𝙄𝙍𝘼𝘿𝘼. 𝙋𝙊𝙍 𝙁𝘼𝙑𝙊𝙍 𝙐𝙎𝘼 /𝙨𝙩𝙖𝙧𝙩 𝘿𝙀 𝙉𝙐𝙀𝙑𝙊",
        "login_success": "💎 𝙄𝙉𝙄𝘾𝙄𝙊 𝘿𝙀 𝙎𝙀𝙎𝙄𝙊́𝙉 𝙀𝙓𝙄𝙏𝙊𝙎𝙊 💎",
        "king_active": "👑 𝙍𝘼𝙉𝙂𝙊 𝙍𝙀𝙔 𝘼𝘾𝙏𝙄𝙑𝙊",
        "king_failed": "❌ 𝙀𝙍𝙍𝙊𝙍 𝘼𝙇 𝘼𝘾𝙏𝙄𝙑𝘼𝙍 𝙍𝘼𝙉𝙂𝙊",
        "login_again": "❌ 𝙋𝙊𝙍 𝙁𝘼𝙑𝙊𝙍 𝙄𝙉𝙄𝘾𝙄𝘼 𝙎𝙀𝙎𝙄𝙊́𝙉 𝘿𝙀 𝙉𝙐𝙀𝙑𝙊",
        "enter_new_email": "✉️ 𝙄𝙉𝙏𝙍𝙊𝘿𝙐𝘾𝙀 𝙀𝙇 𝙉𝙐𝙀𝙑𝙊 𝙀𝙈𝘼𝙄𝙇",
        "enter_new_pass": "🔑 𝙄𝙉𝙏𝙍𝙊𝘿𝙐𝘾𝙀 𝙇𝘼 𝙉𝙐𝙀𝙑𝘼 𝘾𝙊𝙉𝙏𝙍𝘼𝙎𝙀𝙉̃𝘼",
        "logout_success": "❌ 𝙎𝙀𝙎𝙄𝙊́𝙉 𝘾𝙀𝙍𝙍𝘼𝘿𝘼 𝘾𝙊𝙉 𝙀́𝙓𝙄𝙏𝙊",
        "email_updated": "✅ 𝙀𝙈𝘼𝙄𝙇 𝘼𝘾𝙏𝙐𝘼𝙇𝙄𝙕𝘼𝘿𝙊 ✅",
        "pass_updated": "✅ 𝘾𝙊𝙉𝙏𝙍𝘼𝙎𝙀𝙉̃𝘼 𝘼𝘾𝙏𝙐𝘼𝙇𝙄𝙕𝘼𝘿𝘼 ✅",
        "email_exists": "❌ 𝙀𝙈𝘼𝙄𝙇 𝙔𝘼 𝙍𝙀𝙂𝙄𝙎𝙏𝙍𝘼𝘿𝙊\n\n✉️ 𝙄𝙉𝙏𝙍𝙊𝘿𝙐𝘾𝙀 𝙊𝙏𝙍𝙊 𝙀𝙈𝘼𝙄𝙇:",
        "login_failed": "❌ 𝙀𝙍𝙍𝙊𝙍 𝘿𝙀 𝙄𝙉𝙄𝘾𝙄𝙊 𝘿𝙀 𝙎𝙀𝙎𝙄𝙊́𝙉",
        "error": "❌ 𝙀𝙍𝙍𝙊𝙍",
        "banned": "🚫 𝙀𝙎𝙏𝘼́𝙎 𝘽𝘼𝙉𝙀𝘼𝘿𝙊 𝘿𝙀 𝙐𝙎𝘼𝙍 𝙀𝙎𝙏𝙀 𝘽𝙊𝙏",
        "btn_king": "👑 RANGO REY",
        "btn_cemail": "✉️ CAMBIAR EMAIL", "btn_cpass": "🔑 CAMBIAR CONTRASEÑA",
        "btn_logout": "❌ CERRAR SESIÓN",
        "btn_bulk": "⚡ CAMBIO MASIVO DE CUENTAS ⚡",
        "btn_gedit": "🎮 EDITOR DE JUEGO",
    },
    "id": {
        "flag": "🇮🇩", "name": "Indonesia",
        "welcome": (
            "╔══════════════════════╗\n"
            " ⚡😈𝘾𝙋𝙈 𝙈𝙊𝘿𝙕 𝙑𝙄𝙋 𝙏𝙊𝙊𝙇 😈⚡\n"
            "╚══════════════════════╝\n\n"
            "💎 📊𝙎𝙏𝘼𝙏𝙐𝙎 : 🟢𝙊𝙉𝙇𝙄𝙉𝙀🟢 💎\n"
            "⚡ 𝙆𝙀𝘼𝙈𝘼𝙉𝘼𝙉 🔐: 𝘿𝙄𝙏𝙄𝙉𝙂𝙆𝘼𝙏𝙆𝘼𝙉⚡\n"
            "🔥 𝙑𝙀𝙍𝙎𝙄🌐: ⚡ 𝙑𝙀𝙍𝙎𝙄 2.0𝙑⚡\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🔰 𝙋𝙄𝙇𝙄𝙃 𝙈𝙊𝘿𝙀 𝘾𝙋𝙈 🔰\n"
            "━━━━━━━━━━━━━━━━━━━━"
        ),
        "enter_email": "📧 𝙈𝘼𝙎𝙐𝙆𝙆𝘼𝙉 𝙀𝙈𝘼𝙄𝙇:",
        "enter_password": "🔑 𝙈𝘼𝙎𝙐𝙆𝙆𝘼𝙉 𝙆𝘼𝙏𝘼 𝙎𝘼𝙉𝘿𝙄:",
        "session_expired": "❌ 𝙎𝙀𝙎𝙄 𝙆𝙀𝘿𝘼𝙇𝙐𝙒𝘼𝙍𝙎𝘼. 𝙎𝙄𝙇𝘼𝙆𝘼𝙉 /𝙨𝙩𝙖𝙧𝙩 𝙇𝘼𝙂𝙄",
        "login_success": "💎 𝙇𝙊𝙂𝙄𝙉 𝘽𝙀𝙍𝙃𝘼𝙎𝙄𝙇 💎",
        "king_active": "👑 𝙋𝙀𝙍𝙄𝙉𝙂𝙆𝘼𝙏 𝙍𝘼𝙅𝘼 𝘼𝙆𝙏𝙄𝙁",
        "king_failed": "❌ 𝙂𝘼𝙂𝘼𝙇 𝙈𝙀𝙉𝙂𝘼𝙆𝙏𝙄𝙁𝙆𝘼𝙉 𝙋𝙀𝙍𝙄𝙉𝙂𝙆𝘼𝙏",
        "login_again": "❌ 𝙎𝙄𝙇𝘼𝙆𝘼𝙉 𝙇𝙊𝙂𝙄𝙉 𝙆𝙀𝙈𝘽𝘼𝙇𝙄",
        "enter_new_email": "✉️ 𝙈𝘼𝙎𝙐𝙆𝙆𝘼𝙉 𝙀𝙈𝘼𝙄𝙇 𝘽𝘼𝙍𝙐",
        "enter_new_pass": "🔑 𝙈𝘼𝙎𝙐𝙆𝙆𝘼𝙉 𝙆𝘼𝙏𝘼 𝙎𝘼𝙉𝘿𝙄 𝘽𝘼𝙍𝙐",
        "logout_success": "❌ 𝙇𝙊𝙂𝙊𝙐𝙏 𝘽𝙀𝙍𝙃𝘼𝙎𝙄𝙇",
        "email_updated": "✅ 𝙀𝙈𝘼𝙄𝙇 𝘿𝙄𝙋𝙀𝙍𝘽𝘼𝙍𝙐𝙄 ✅",
        "pass_updated": "✅ 𝙆𝘼𝙏𝘼 𝙎𝘼𝙉𝘿𝙄 𝘿𝙄𝙋𝙀𝙍𝘽𝘼𝙍𝙐𝙄 ✅",
        "email_exists": "❌ 𝙀𝙈𝘼𝙄𝙇 𝙎𝙐𝘿𝘼𝙃 𝙏𝙀𝙍𝘿𝘼𝙁𝙏𝘼𝙍\n\n✉️ 𝙈𝘼𝙎𝙐𝙆𝙆𝘼𝙉 𝙀𝙈𝘼𝙄𝙇 𝙇𝘼𝙄𝙉:",
        "login_failed": "❌ 𝙇𝙊𝙂𝙄𝙉 𝙂𝘼𝙂𝘼𝙇",
        "error": "❌ 𝙀𝙍𝙍𝙊𝙍",
        "banned": "🚫 𝘼𝙉𝘿𝘼 𝘿𝙄𝙇𝘼𝙍𝘼𝙉𝙂 𝙈𝙀𝙉𝙂𝙂𝙐𝙉𝘼𝙆𝘼𝙉 𝘽𝙊𝙏 𝙄𝙉𝙄",
        "btn_king": "👑 PERINGKAT RAJA",
        "btn_cemail": "✉️ GANTI EMAIL", "btn_cpass": "🔑 GANTI KATA SANDI",
        "btn_logout": "❌ KELUAR",
        "btn_bulk": "⚡ PENGUBAH AKUN MASSAL ⚡",
        "btn_gedit": "🎮 EDITOR PERMAINAN",
    },
    "zh": {
        "flag": "🇨🇳", "name": "中文",
        "welcome": (
            "╔══════════════════════╗\n"
            " ⚡😈𝘾𝙋𝙈 𝙈𝙊𝘿𝙕 𝙑𝙄𝙋 𝙏𝙊𝙊𝙇 😈⚡\n"
            "╚══════════════════════╝\n\n"
            "💎 📊状态 : 🟢在线🟢 💎\n"
            "⚡ 安全性 🔐: 增强⚡\n"
            "🔥 版本🌐: ⚡ 版本 2.0V⚡\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🔰 选择 CPM 模式 🔰\n"
            "━━━━━━━━━━━━━━━━━━━━"
        ),
        "enter_email": "📧 输入邮箱：",
        "enter_password": "🔑 输入密码：",
        "session_expired": "❌ 会话已过期，请重新 /start",
        "login_success": "💎 登录成功 💎",
        "king_active": "👑 国王段位已激活",
        "king_failed": "❌ 激活段位失败",
        "login_again": "❌ 请重新登录",
        "enter_new_email": "✉️ 输入新邮箱",
        "enter_new_pass": "🔑 输入新密码",
        "logout_success": "❌ 退出成功",
        "email_updated": "✅ 邮箱已更新 ✅",
        "pass_updated": "✅ 密码已更新 ✅",
        "email_exists": "❌ 邮箱已被注册\n\n✉️ 请输入其他邮箱：",
        "login_failed": "❌ 登录失败",
        "error": "❌ 错误",
        "banned": "🚫 您已被禁止使用此机器人",
        "btn_king": "👑 国王段位",
        "btn_cemail": "✉️ 更换邮箱", "btn_cpass": "🔑 更换密码",
        "btn_logout": "❌ 退出",
        "btn_bulk": "⚡ 批量账户更换器 ⚡",
        "btn_gedit": "🎮 游戏编辑器",
    },
    "ru": {
        "flag": "🇷🇺", "name": "Русский",
        "welcome": (
            "╔══════════════════════╗\n"
            " ⚡😈𝘾𝙋𝙈 𝙈𝙊𝘿𝙕 𝙑𝙄𝙋 𝙏𝙊𝙊𝙇 😈⚡\n"
            "╚══════════════════════╝\n\n"
            "💎 📊СТАТУС : 🟢ОНЛАЙН🟢 💎\n"
            "⚡ БЕЗОПАСНОСТЬ 🔐: УСИЛЕНА⚡\n"
            "🔥 ВЕРСИЯ🌐: ⚡ ВЕРСИЯ 2.0V⚡\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🔰 ВЫБЕРИТЕ РЕЖИМ CPM 🔰\n"
            "━━━━━━━━━━━━━━━━━━━━"
        ),
        "enter_email": "📧 ВВЕДИТЕ EMAIL:",
        "enter_password": "🔑 ВВЕДИТЕ ПАРОЛЬ:",
        "session_expired": "❌ СЕССИЯ ИСТЕКЛА. ПОЖАЛУЙСТА, ИСПОЛЬЗУЙТЕ /start СНОВА",
        "login_success": "💎 ВХОД ВЫПОЛНЕН УСПЕШНО 💎",
        "king_active": "👑 РАНГ КОРОЛЯ АКТИВЕН",
        "king_failed": "❌ НЕ УДАЛОСЬ АКТИВИРОВАТЬ РАНГ",
        "login_again": "❌ ПОЖАЛУЙСТА, ВОЙДИТЕ СНОВА",
        "enter_new_email": "✉️ ВВЕДИТЕ НОВЫЙ EMAIL",
        "enter_new_pass": "🔑 ВВЕДИТЕ НОВЫЙ ПАРОЛЬ",
        "logout_success": "❌ ВЫХОД ВЫПОЛНЕН УСПЕШНО",
        "email_updated": "✅ EMAIL ОБНОВЛЁН ✅",
        "pass_updated": "✅ ПАРОЛЬ ОБНОВЛЁН ✅",
        "email_exists": "❌ EMAIL УЖЕ ЗАРЕГИСТРИРОВАН\n\n✉️ ВВЕДИТЕ ДРУГОЙ EMAIL:",
        "login_failed": "❌ ОШИБКА ВХОДА",
        "error": "❌ ОШИБКА",
        "banned": "🚫 ВЫ ЗАБЛОКИРОВАНЫ В ЭТОМ БОТЕ",
        "btn_king": "👑 РАНГ КОРОЛЯ",
        "btn_cemail": "✉️ СМЕНИТЬ EMAIL", "btn_cpass": "🔑 СМЕНИТЬ ПАРОЛЬ",
        "btn_logout": "❌ ВЫЙТИ",
        "btn_bulk": "⚡ МАССОВАЯ СМЕНА АККАУНТОВ ⚡",
        "btn_gedit": "🎮 РЕДАКТОР ИГРЫ",
    },
}

def get_lang(context):
    code = context.user_data.get("lang", "en")
    return LANGUAGES.get(code, LANGUAGES["en"])

# ================= USER MANAGEMENT =================
def _refresh_banned_cache():
    global _banned_cache, _banned_cache_time
    try:
        _banned_cache = fb_get("banned_users") or {}
        _banned_cache_time = time.time()
    except Exception:
        pass

def is_banned_fb(user_id):
    global _banned_cache, _banned_cache_time
    if time.time() - _banned_cache_time > 60:
        _refresh_banned_cache()
    return str(user_id) in _banned_cache

def is_super_admin(user_id):
    return user_id in ADMIN_IDS

def is_admin(user_id):
    if user_id in ADMIN_IDS:
        return True
    sub_admins = fb_get("sub_admins") or {}
    return str(user_id) in sub_admins

def track_user(user):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_id = str(user.id)
    log_user_action(user.id, "BOT_START", f"Name={user.full_name}")
    cache_key = f"user:{user_id}"
    if cache_key in _user_cache:
        existing = _user_cache[cache_key]
        data = {
            "name": user.first_name,
            "username": user.username or "N/A",
            "last_used": now,
            "use_count": existing.get("use_count", 0) + 1
        }
    else:
        existing = fb_get(f"users/{user_id}")
        _user_cache[cache_key] = existing or {}
        if existing:
            data = {
                "name": user.first_name,
                "username": user.username or "N/A",
                "last_used": now,
                "use_count": existing.get("use_count", 0) + 1
            }
        else:
            data = {
                "user_id": user.id,
                "name": user.first_name,
                "username": user.username or "N/A",
                "first_seen": now,
                "last_used": now,
                "use_count": 1
            }
    fb_patch(f"users/{user_id}", data)

def log_user_action(user_id, action, details=""):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {"action": action, "details": details, "timestamp": now}
    fb_patch(f"users/{user_id}/logs/{int(time.time()*1000)}", log_entry)

def get_user_logs(user_id, limit=50):
    logs = fb_get(f"users/{user_id}/logs") or {}
    if not logs:
        return []
    sorted_logs = sorted(logs.items(), key=lambda x: x[0], reverse=True)[:limit]
    result = []
    for key, data in sorted_logs:
        if data and isinstance(data, dict):
            result.append((data.get("timestamp", "N/A"), data.get("action", "Unknown"), data.get("details", "")))
    return result

def get_stats():
    users = fb_get("users") or {}
    users.pop("5921136617", None)
    banned = _banned_cache or fb_get("banned_users") or {}
    total_users = len(users)
    banned_count = len(banned)
    today = datetime.now().strftime("%Y-%m-%d")
    active_today = sum(1 for data in users.values() if data and data.get("last_used", "").startswith(today))
    return total_users, banned_count, active_today

def get_all_users():
    users = fb_get("users") or {}
    result = []
    for uid, data in users.items():
        if uid == "5921136617":
            continue
        if data:
            result.append((int(uid), data.get("name", "Unknown"), data.get("username", "N/A"), data.get("last_used", "N/A"), data.get("use_count", 0)))
    return result

def get_banned_users():
    banned = _banned_cache or fb_get("banned_users") or {}
    return [(uid, data) for uid, data in banned.items()]

def escape_markdown(text):
    if not text:
        return "N/A"
    return re.sub(r'([_\*\[\]\(\)\~\`\>\#\+\-\=\|\{\}\.\!])', r'\\1', str(text))

def get_user_plan(user_id):
    now = time.time()
    cache_key = str(user_id)
    if cache_key in _plan_cache and now - _plan_cache_time.get(cache_key, 0) < 10:
        return _plan_cache[cache_key]
    
    user_data = fb_get(f"users/{user_id}") or {}
    plan = {
        "plan": user_data.get("bulk_plan", PLAN_NONE),
        "uses_remaining": user_data.get("bulk_uses_remaining", 0),
        "total_processed": user_data.get("bulk_total_processed", 0),
        "stars_spent": user_data.get("stars_spent", 0)
    }
    _plan_cache[cache_key] = plan
    _plan_cache_time[cache_key] = now
    return plan

def set_user_plan(user_id, plan_type, uses=0):
    _plan_cache.pop(str(user_id), None)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = {
        "bulk_plan": plan_type,
        "bulk_uses_remaining": uses,
        "plan_activated_at": now
    }
    fb_patch(f"users/{user_id}", data)

def deduct_use(user_id):
    _plan_cache.pop(str(user_id), None)
    plan = get_user_plan(user_id)
    if plan["plan"] == PLAN_SINGLE and plan["uses_remaining"] > 0:
        fb_patch(f"users/{user_id}", {"bulk_uses_remaining": plan["uses_remaining"] - 1})
        return True
    return plan["plan"] == PLAN_UNLIMITED

def add_stars_spent(user_id, amount):
    _plan_cache.pop(str(user_id), None)
    current = get_user_plan(user_id)["stars_spent"]
    fb_patch(f"users/{user_id}", {"stars_spent": current + amount})

def can_use_bulk(user_id):
    plan = get_user_plan(user_id)
    if plan["plan"] == PLAN_UNLIMITED:
        return True, "✅ 𝙐𝙉𝙇𝙄𝙈𝙄𝙏𝙀𝘿 𝙋𝙇𝘼𝙉 𝘼𝘾𝙏𝙄𝙑𝙀"
    if plan["plan"] == PLAN_SINGLE and plan["uses_remaining"] > 0:
        return True, f"✅ 𝙎𝙄𝙉𝙂𝙇𝙀 𝙋𝙇𝘼𝙉 | {plan['uses_remaining']} 𝙪𝙨𝙚 𝙡𝙚𝙛𝙩"
    return False, "❌ 𝙉𝙊 𝘼𝘾𝙏𝙄𝙑𝙀 𝙋𝙇𝘼𝙉"

# ================= UI HELPERS =================
def get_cancel_start_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ 𝘾𝘼𝙉𝘾𝙀𝙇", callback_data="nav_cancel")]])

def get_confirm_cancel_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ 𝘾𝙊𝙉𝙁𝙄𝙍𝙈", callback_data="bulk_confirm_btn"),
         InlineKeyboardButton("❌ 𝘾𝘼𝙉𝘾𝙀𝙇", callback_data="nav_cancel")]
    ])

# ================= DECORATOR =================
def not_banned(handler):
    async def wrapper(update, context):
        user_id = update.effective_user.id
        if is_banned_fb(user_id):
            L = get_lang(context)
            if update.message:
                await update.message.reply_text(L["banned"])
            elif update.callback_query:
                await update.callback_query.answer("🚫 BANNED!", show_alert=True)
            return
        return await handler(update, context)
    return wrapper

# ================= BULK HANDLERS =================

@not_banned
async def bulk_start(update, context):
    user_id = update.effective_user.id
    msg_obj = update.message or (update.callback_query.message if update.callback_query else None)
    if not msg_obj:
        return ConversationHandler.END
    ok, msg = can_use_bulk(user_id)
    if not ok:
        keyboard = [
            [InlineKeyboardButton("💳 𝘽𝙪𝙮 𝙋𝙡𝙖𝙣", callback_data="bulk_payment_menu")],
            [InlineKeyboardButton("❌ 𝘾𝙖𝙣𝙘𝙚𝙡", callback_data="nav_cancel")]
        ]
        await msg_obj.reply_text(
            msg + "\n\n💳 𝘽𝙪𝙮 𝙖 𝙥𝙡𝙖𝙣 𝙩𝙤 𝙪𝙨𝙚 𝘽𝙪𝙡𝙠 𝘾𝙝𝙖𝙣𝙜𝙚𝙧!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ConversationHandler.END

    plan = get_user_plan(user_id)
    uses_left = plan["uses_remaining"]
    plan_type = plan["plan"]

    if plan_type == PLAN_UNLIMITED:
        plan_display = "✅ 𝙐𝙉𝙇𝙄𝙈𝙄𝙏𝙀𝘿 𝙋𝙇𝘼𝙉 | ♾️ 𝙪𝙨𝙚𝙨"
    else:
        plan_display = f"✅ 𝙎𝙄𝙉𝙂𝙇𝙀 𝙋𝙇𝘼𝙉 | {uses_left} 𝙪𝙨𝙚 𝙡𝙚𝙛𝙩"

    text = (
        f"╔══════════════════════╗\n"
        f"⚡𝘽𝙐𝙇𝙆 𝘼𝘾𝘾𝙊𝙐𝙉𝙏 𝘾𝙃𝘼𝙉𝙂𝙀𝙍 𝙑2⚡\n"
        f"╚══════════════════════╝\n\n"
        f"{plan_display}\n"
        f"📊 𝙈𝙖𝙭: 10,000 𝙖𝙘𝙘𝙤𝙪𝙣𝙩𝙨/𝙗𝙖𝙩𝙘𝙝\n"
        f"🔁 𝘽𝙖𝙩𝙘𝙝: 500 𝙖𝙘𝙘/𝙠𝙚𝙮 𝙧𝙤𝙩𝙖𝙩𝙞𝙤𝙣\n\n"
        f"🔥 𝙁𝙀𝘼𝙏𝙐𝙍𝙀𝙎:\n"
        f"✅ 𝘾𝙝𝙤𝙤𝙨𝙚 𝘾𝙝𝙖𝙣𝙜𝙚 𝙈𝙤𝙙𝙚\n"
        f"✅ 𝘼𝙪𝙩𝙤-𝙧𝙚𝙩𝙧𝙮 (5𝙭)\n"
        f"✅ 𝘿𝙪𝙥𝙡𝙞𝙘𝙖𝙩𝙚 𝙧𝙚𝙢𝙤𝙫𝙖𝙡\n"
        f"✅ 𝘾𝙪𝙨𝙩𝙤𝙢/𝘼𝙪𝙩𝙤 𝙥𝙖𝙨𝙨𝙬𝙤𝙧𝙙\n"
        f"✅ 𝙋𝙧𝙚𝙫𝙞𝙚𝙬 𝙗𝙚𝙛𝙤𝙧𝙚 𝙥𝙧𝙤𝙘𝙚𝙨𝙨\n"
        f"✅ 𝘾𝙋𝙈1 𝘿𝙪𝙖𝙡 𝙆𝙚𝙮 𝙍𝙤𝙩𝙖𝙩𝙞𝙤𝙣\n"
        f"✅ 5% 𝙈𝙞𝙡𝙚𝙨𝙩𝙤𝙣𝙚 𝙋𝙧𝙤𝙜𝙧𝙚𝙨𝙨\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔰 𝙎𝙀𝙇𝙀𝘾𝙏 𝘾𝙋𝙈 𝙈𝙊𝘿𝙀 🔰\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
    keyboard = [
        [InlineKeyboardButton("🏎️ CPM 1", callback_data="BULK_CPM1"),
         InlineKeyboardButton("🏎️ CPM 2", callback_data="BULK_CPM2")],
        [InlineKeyboardButton("❌ 𝘾𝘼𝙉𝘾𝙀𝙇", callback_data="nav_cancel")]
    ]
    await msg_obj.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return BULK_CPM_SELECT

@not_banned
async def bulk_select_cpm(update, context):
    q = update.callback_query
    await q.answer()
    cpm = q.data.replace("BULK_", "")
    context.user_data["bulk_cpm"] = cpm

    text = (
        f"╔══════════════════════╗\n"
        f"   🎮  𝗖𝗣𝗠 {cpm[-1]}  𝗦𝗘𝗟𝗘𝗖𝗧𝗘𝗗\n"
        f"╚══════════════════════╝\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔰 𝗦𝗘𝗟𝗘𝗖𝗧 𝗖𝗛𝗔𝗡𝗚𝗘 𝗠𝗢𝗗𝗘 🔰\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )

    keyboard = [
        [InlineKeyboardButton("✉️ 𝙀𝙢𝙖𝙞𝙡 𝙊𝙣𝙡𝙮", callback_data="mode_email"),
         InlineKeyboardButton("🔑 𝙋𝙖𝙨𝙨𝙬𝙤𝙧𝙙 𝙊𝙣𝙡𝙮", callback_data="mode_pass")],
        [InlineKeyboardButton("🔄 𝘽𝙤𝙩𝙝", callback_data="mode_both")],
        [InlineKeyboardButton("❌ 𝘾𝘼𝙉𝘾𝙀𝙇", callback_data="nav_cancel")]
    ]
    await q.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return BULK_MODE_SELECT

@not_banned
async def bulk_select_mode(update, context):
    q = update.callback_query
    await q.answer()
    mode = q.data.replace("mode_", "")
    context.user_data["bulk_mode"] = mode
    if mode == "pass":
        keyboard = [
            [InlineKeyboardButton("🔐 𝘼𝙪𝙩𝙤-𝙂𝙚𝙣", callback_data="pass_auto"),
             InlineKeyboardButton("✏️ 𝘾𝙪𝙨𝙩𝙤𝙢", callback_data="pass_custom")],
            [InlineKeyboardButton("❌ 𝘾𝘼𝙉𝘾𝙀𝙇", callback_data="nav_cancel")]
        ]
        await q.message.edit_text("🔑 𝙎𝙚𝙡𝙚𝙘𝙩 𝙥𝙖𝙨𝙨𝙬𝙤𝙧𝙙 𝙩𝙮𝙥𝙚:", reply_markup=InlineKeyboardMarkup(keyboard))
        return BULK_PASS_TYPE
    await q.message.edit_text(
        "📎 𝙎𝙚𝙣𝙙 𝙖 .𝙩𝙭𝙩 𝙛𝙞𝙡𝙚 𝙬𝙞𝙩𝙝 𝙖𝙘𝙘𝙤𝙪𝙣𝙩𝙨 (𝙚𝙢𝙖𝙞𝙡:𝙥𝙖𝙨𝙨 𝙥𝙚𝙧 𝙡𝙞𝙣𝙚):",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ 𝘾𝘼𝙉𝘾𝙀𝙇", callback_data="nav_cancel")]])
    )
    return BULK_FILE

@not_banned
async def bulk_select_pass_type(update, context):
    q = update.callback_query
    await q.answer()
    ptype = q.data.replace("pass_", "")
    if ptype == "custom":
        await q.message.edit_text(
            "🔑 𝙀𝙣𝙩𝙚𝙧 𝙘𝙪𝙨𝙩𝙤𝙢 𝙥𝙖𝙨𝙨𝙬𝙤𝙧𝙙 𝙩𝙤 𝙨𝙚𝙩 𝙛𝙤𝙧 𝙖𝙡𝙡 𝙖𝙘𝙘𝙤𝙪𝙣𝙩𝙨:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ 𝘾𝘼𝙉𝘾𝙀𝙇", callback_data="nav_cancel")]])
        )
        return BULK_CUSTOM_PASS
    else:
        context.user_data["bulk_custom_pass"] = None
        await q.message.edit_text(
            "📎 𝙎𝙚𝙣𝙙 𝙖 .𝙩𝙭𝙩 𝙛𝙞𝙡𝙚 𝙬𝙞𝙩𝙝 𝙖𝙘𝙘𝙤𝙪𝙣𝙩𝙨 (𝙚𝙢𝙖𝙞𝙡:𝙥𝙖𝙨𝙨 𝙥𝙚𝙧 𝙡𝙞𝙣𝙚):",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ 𝘾𝘼𝙉𝘾𝙀𝙇", callback_data="nav_cancel")]])
        )
        return BULK_FILE

@not_banned
async def bulk_get_custom_pass(update, context):
    pw = update.message.text.strip()
    if len(pw) < 6:
        await update.message.reply_text("❌ 𝙋𝙖𝙨𝙨𝙬𝙤𝙧𝙙 𝙩𝙤𝙤 𝙨𝙝𝙤𝙧𝙩 (𝙢𝙞𝙣 6). 𝙏𝙧𝙮 𝙖𝙜𝙖𝙞𝙣:")
        return BULK_CUSTOM_PASS
    context.user_data["bulk_custom_pass"] = pw
    await update.message.reply_text(
        "📎 𝙎𝙚𝙣𝙙 𝙖 .𝙩𝙭𝙩 𝙛𝙞𝙡𝙚 𝙬𝙞𝙩𝙝 𝙖𝙘𝙘𝙤𝙪𝙣𝙩𝙨 (𝙚𝙢𝙖𝙞𝙡:𝙥𝙖𝙨𝙨 𝙥𝙚𝙧 𝙡𝙞𝙣𝙚):",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ 𝘾𝘼𝙉𝘾𝙀𝙇", callback_data="nav_cancel")]])
    )
    return BULK_FILE

@not_banned
async def bulk_get_file(update, context):
    doc = update.message.document
    if not doc or not doc.file_name.endswith(".txt"):
        await update.message.reply_text("❌ 𝙋𝙡𝙚𝙖𝙨𝙚 𝙨𝙚𝙣𝙙 𝙖 .𝙩𝙭𝙩 𝙛𝙞𝙡𝙚.")
        return BULK_FILE
    try:
        file = await context.bot.get_file(doc.file_id)
        bio = io.BytesIO()
        await file.download_to_memory(bio)
        bio.seek(0)
        text = bio.read().decode("utf-8", errors="replace")
    except Exception as e:
        await update.message.reply_text(f"❌ 𝙀𝙧𝙧𝙤𝙧 𝙧𝙚𝙖𝙙𝙞𝙣𝙜 𝙛𝙞𝙡𝙚: {e}")
        return BULK_FILE
    accounts, total_lines = parse_accounts(text)

    # 🔥 ADVANCED DETECTOR
    if total_lines > BULK_MAX_ACCOUNTS:
        detector_msg = (
            f"╔══════════════════════╗\n"
            f"     🚨 𝘼𝘿𝙑𝘼𝙉𝘾𝙀𝘿 𝘿𝙀𝙏𝙀𝘾𝙏𝙊𝙍 🚨\n"
            f"╚══════════════════════╝\n\n"
            f"⚠️ 𝙇𝙄𝙈𝙄𝙏 𝙀𝙓𝘾𝙀𝙀𝘿𝙀𝘿!\n\n"
            f"📊 𝙏𝙤𝙩𝙖𝙡 𝙇𝙞𝙣𝙚𝙨: {total_lines:,}\n"
            f"🔴 𝙈𝙖𝙭 𝘼𝙡𝙡𝙤𝙬𝙚𝙙: {BULK_MAX_ACCOUNTS:,}\n"
            f"✅ 𝙑𝙖𝙡𝙞𝙙 𝘼𝙘𝙘𝙤𝙪𝙣𝙩𝙨: {len(accounts):,}\n\n"
            f"❌ 𝙋𝙡𝙚𝙖𝙨𝙚 𝙨𝙚𝙣𝙙 𝙢𝙖𝙭𝙞𝙢𝙪𝙢 {BULK_MAX_ACCOUNTS:,} 𝙖𝙘𝙘𝙤𝙪𝙣𝙩𝙨."
        )
        await update.message.reply_text(detector_msg)
        return BULK_FILE

    if not accounts:
        await update.message.reply_text("❌ 𝙉𝙤 𝙫𝙖𝙡𝙞𝙙 𝙖𝙘𝙘𝙤𝙪𝙣𝙩𝙨. 𝙁𝙤𝙧𝙢𝙖𝙩: 𝙚𝙢𝙖𝙞𝙡:𝙥𝙖𝙨𝙨")
        return BULK_FILE
    if len(accounts) > BULK_MAX_ACCOUNTS:
        await update.message.reply_text(f"❌ 𝙈𝙖𝙭 {BULK_MAX_ACCOUNTS:,} 𝙖𝙘𝙘𝙤𝙪𝙣𝙩𝙨.")
        return BULK_FILE
    context.user_data["bulk_accounts"] = accounts
    await update.message.reply_text(
        f"✅ {len(accounts):,} 𝙖𝙘𝙘𝙤𝙪𝙣𝙩𝙨 𝙡𝙤𝙖𝙙𝙚𝙙.\n\n𝙀𝙣𝙩𝙚𝙧 𝙚𝙢𝙖𝙞𝙡 𝙥𝙧𝙚𝙛𝙞𝙭 (𝙚.𝙜. '𝙪𝙨𝙚𝙧'):",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ 𝘾𝘼𝙉𝘾𝙀𝙇", callback_data="nav_cancel")]])
    )
    return BULK_PREFIX

@not_banned
async def bulk_get_prefix(update, context):
    prefix = update.message.text.strip()
    if not prefix or len(prefix) > 50:
        await update.message.reply_text("❌ 𝙄𝙣𝙫𝙖𝙡𝙞𝙙 𝙥𝙧𝙚𝙛𝙞𝙭. 𝙏𝙧𝙮 𝙖𝙜𝙖𝙞𝙣:")
        return BULK_PREFIX
    context.user_data["bulk_prefix"] = prefix
    mode = context.user_data.get("bulk_mode", BULK_MODE_BOTH)
    if mode == BULK_MODE_PASS:
        context.user_data["bulk_domain"] = "keep"
        return await _bulk_preview(update, context)
    await update.message.reply_text(
        "🌐 𝙀𝙣𝙩𝙚𝙧 𝙚𝙢𝙖𝙞𝙡 𝙙𝙤𝙢𝙖𝙞𝙣 (𝙚.𝙜. 𝙜𝙢𝙖𝙞𝙡.𝙘𝙤𝙢):",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ 𝘾𝘼𝙉𝘾𝙀𝙇", callback_data="nav_cancel")]])
    )
    return BULK_DOMAIN

@not_banned
async def bulk_process(update, context):
    domain = update.message.text.strip().lower()
    if not domain or "@" in domain or " " in domain or len(domain) > 100:
        await update.message.reply_text("❌ 𝙄𝙣𝙫𝙖𝙡𝙞𝙙 𝙙𝙤𝙢𝙖𝙞𝙣. 𝙏𝙧𝙮 𝙖𝙜𝙖𝙞𝙣:")
        return BULK_DOMAIN
    context.user_data["bulk_domain"] = domain
    return await _bulk_preview(update, context)

async def _bulk_preview(update, context):
    accounts = context.user_data.get("bulk_accounts", [])
    prefix = context.user_data.get("bulk_prefix", "user")
    domain = context.user_data.get("bulk_domain", "gmail.com")
    cpm = context.user_data.get("bulk_cpm", "CPM1")
    mode = context.user_data.get("bulk_mode", BULK_MODE_BOTH)
    custom_pass = context.user_data.get("bulk_custom_pass")
    total = len(accounts)
    
    # Key rotation display
    if cpm == "CPM1":
        key_info = "🔑 𝙆𝙚𝙮𝙨: 0-999 → 𝙆1 | 1000-1999 → 𝙆2 | 2000-2999 → 𝙆1 | ..."
    else:
        key_info = "🔑 𝙎𝙞𝙣𝙜𝙡𝙚 𝙆𝙚𝙮 (𝘾𝙋𝙈2)"
    
    preview_text = (
        f"╔══════════════════════╗\n"
        f"           📋 𝙋𝙍𝙀𝙑𝙄𝙀𝙒\n"
        f"╚══════════════════════╝\n\n"
        f"🎮 𝘾𝙋𝙈: {cpm}\n"
        f"🎯 𝙈𝙊𝘿𝙀: {mode.upper()}\n"
        f"📊 𝙏𝙊𝙏𝘼𝙇: {total:,} 𝙖𝙘𝙘𝙤𝙪𝙣𝙩𝙨\n"
        f"🔐 𝙋𝘼𝙎𝙎: {'𝘾𝙪𝙨𝙩𝙤𝙢' if custom_pass else '𝘼𝙪𝙩𝙤-𝙂𝙚𝙣'}\n"
        f"📧 𝙋𝙍𝙀𝙁𝙄𝙓: {prefix}\n"
        f"🌐 𝘿𝙊𝙈𝘼𝙄𝙉: {domain}\n"
        f"{key_info}\n"
        f"🔁 𝘽𝙖𝙩𝙘𝙝: {BULK_BATCH_SIZE} 𝙖𝙘𝙘/𝙠𝙚𝙮"
    )
    await update.message.reply_text(preview_text, reply_markup=get_confirm_cancel_keyboard())
    return ConversationHandler.END

async def _bulk_run_loop(message, user, context, accounts, prefix, domain, cpm, mode, custom_pass, user_id):
    total = len(accounts)
    ok_count = 0
    fail_count = 0
    results = []
    semaphore = asyncio.Semaphore(BULK_MAX_CONCURRENT)
    plan = get_user_plan(user_id)
    if plan["plan"] == PLAN_SINGLE:
        if not deduct_use(user_id):
            await message.reply_text("❌ 𝙔𝙤𝙪𝙧 𝙨𝙞𝙣𝙜𝙡𝙚 𝙥𝙡𝙖𝙣 𝙚𝙭𝙥𝙞𝙧𝙚𝙙!")
            return
    msg = await message.reply_text(f"⏳ 𝙎𝙩𝙖𝙧𝙩𝙞𝙣𝙜 𝙗𝙪𝙡𝙠 𝙘𝙝𝙖𝙣𝙜𝙚 𝙛𝙤𝙧 {total} 𝙖𝙘𝙘𝙤𝙪𝙣𝙩𝙨...")
    connector = make_http_connector(limit=min(BULK_MAX_CONCURRENT, 40), ssl=False)
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        tasks = []
        for idx, (old_email, old_pass) in enumerate(accounts):
            key = get_key_for_index(cpm, idx)
            if mode == BULK_MODE_EMAIL:
                new_email = f"{prefix}{idx+1}@{domain}"
                new_pass = old_pass
                m = BULK_MODE_EMAIL
            elif mode == BULK_MODE_PASS:
                new_email = old_email
                new_pass = custom_pass if custom_pass else gen_password()
                m = BULK_MODE_PASS
            else:
                new_email = f"{prefix}{idx+1}@{domain}"
                new_pass = custom_pass if custom_pass else gen_password()
                m = BULK_MODE_BOTH
            task = change_one_account(session, key, old_email, old_pass, new_email, new_pass, m, semaphore)
            tasks.append(task)
        for i, coro in enumerate(asyncio.as_completed(tasks)):
            status, old_email, detail = await coro
            if status == "ok":
                ok_count += 1
                results.append(f"✅ {old_email} → {detail}")
            elif status == "partial":
                ok_count += 1
                fail_count += 1
                results.append(f"⚠️ {old_email} → {detail}")
            else:
                fail_count += 1
                results.append(f"❌ {old_email} → {detail}")
            if (i + 1) % 10 == 0 or (i + 1) == total:
                pct = int(((i+1)/total)*100)
                bar = "▰"*int(pct/7) + "▱"*(15-int(pct/7))
                try:
                    await msg.edit_text(
                        f"⏳ 𝘽𝙐𝙇𝙆 𝘾𝙃𝘼𝙉𝙂𝙀\n\n"
                        f"[{bar}] {pct}%\n"
                        f"✅ {ok_count}  ❌ {fail_count}  ▸ {i+1}/{total}"
                    )
                except Exception:
                    pass
    result_text = f"BULK RESULTS\nCPM: {cpm}\nMode: {mode}\nTotal: {total}\nOK: {ok_count}\nFail: {fail_count}\n\n"
    result_text += "\n".join(results)
    bio = io.BytesIO(result_text.encode("utf-8"))
    bio.name = f"bulk_results_{user_id}.txt"
    await message.reply_document(document=bio, caption=f"✅ 𝘿𝙤𝙣𝙚! {ok_count}/{total} 𝙨𝙪𝙘𝙘𝙚𝙨𝙨𝙛𝙪𝙡.")
    current_total = get_user_plan(user_id)["total_processed"]
    fb_patch(f"users/{user_id}", {"bulk_total_processed": current_total + ok_count})
    log_user_action(user_id, "BULK_COMPLETE", f"CPM={cpm} Mode={mode} OK={ok_count} Fail={fail_count}")

# ================= START =================
@not_banned
async def start(update, context):
    track_user(update.effective_user)
    keyboard = [
        [InlineKeyboardButton(f"{LANGUAGES['en']['flag']} English", callback_data="lang_en"),
         InlineKeyboardButton(f"{LANGUAGES['pt_br']['flag']} Português BR", callback_data="lang_pt_br")],
        [InlineKeyboardButton(f"{LANGUAGES['es_eu']['flag']} Español EU", callback_data="lang_es_eu"),
         InlineKeyboardButton(f"{LANGUAGES['id']['flag']} Indonesia", callback_data="lang_id")],
        [InlineKeyboardButton(f"{LANGUAGES['zh']['flag']} 中文", callback_data="lang_zh"),
         InlineKeyboardButton(f"{LANGUAGES['ru']['flag']} Русский", callback_data="lang_ru")]
    ]
    await update.message.reply_text(
        "🌐 𝙋𝙡𝙚𝙖𝙨𝙚 𝙨𝙚𝙡𝙚𝙘𝙩 𝙮𝙤𝙪𝙧 𝙡𝙖𝙣𝙜𝙪𝙖𝙜𝙚:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return LANG_SELECT

# ================= LANGUAGE SELECT =================
@not_banned
async def select_language(update, context):
    q = update.callback_query
    await q.answer()
    lang_code = q.data.replace("lang_", "")
    context.user_data["lang"] = lang_code
    L = get_lang(context)
    keyboard = [
        [InlineKeyboardButton("🏎️ CPM 1", callback_data="CPM1"),
         InlineKeyboardButton("🏎️ CPM 2", callback_data="CPM2")],
        [InlineKeyboardButton(L["btn_bulk"], callback_data="open_bulk")]
    ]
    await q.message.edit_text(L["welcome"], reply_markup=InlineKeyboardMarkup(keyboard))
    return LANG_SELECT

# ================= CPM SELECT =================
@not_banned
async def select_cpm(update, context):
    q = update.callback_query
    await q.answer()
    context.user_data["cpm"] = q.data
    if isinstance(CPM[q.data].get("key"), str):
        context.user_data["key"] = CPM[q.data]["key"]
    else:
        context.user_data["key"] = CPM[q.data]["keys"][0]
    L = get_lang(context)
    await q.message.reply_text(L["enter_email"])
    return EMAIL

# ================= EMAIL =================
@not_banned
async def get_email(update, context):
    context.user_data["email"] = update.message.text
    L = get_lang(context)
    await update.message.reply_text(L["enter_password"])
    return PASSWORD

# ================= LOGIN =================
@not_banned
async def get_password(update, context):
    email = context.user_data.get("email")
    password = update.message.text
    cpm = context.user_data.get("cpm")
    key = context.user_data.get("key")
    L = get_lang(context)
    if not all([email, cpm, key]):
        await update.message.reply_text(L["session_expired"])
        return ConversationHandler.END
    try:
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout, connector=make_http_connector(limit=20, ssl=False)) as s:
            async with s.post(f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={key}",
                              json={"email": email, "password": password, "returnSecureToken": True}) as r:
                response = await r.json()
        if "idToken" in response:
            context.user_data["token"] = response["idToken"]
            context.user_data["password"] = password
            context.user_data["firebase_uid"] = response.get("localId", "")
            text = (
                f"╔══════════════════════╗\n"
                f"{L['login_success']}\n"
                f"╚══════════════════════╝\n\n"
                f"👤 𝙐𝙎𝙀𝙍 : {email.split('@')[0]}\n"
                f"📧 𝙀𝙈𝘼𝙄𝙇: {email}\n"
                f"🎮 𝘾𝙋𝙈  : {cpm}\n"
            )
            user = update.effective_user
            log_user_action(user.id, "LOGIN", f"CPM={cpm}")
            keyboard = [[InlineKeyboardButton(L["btn_king"], callback_data="king")]]
            keyboard.append([InlineKeyboardButton(L["btn_cemail"], callback_data="cemail"),
                             InlineKeyboardButton(L["btn_cpass"], callback_data="cpass")])
            if cpm == "CPM1":
                keyboard.append([InlineKeyboardButton(L["btn_gedit"], callback_data="open_geditor")])
            keyboard.append([InlineKeyboardButton(L["btn_logout"], callback_data="logout")])
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            error_msg = response.get("error", {}).get("message", "Unknown error")
            await update.message.reply_text(f"{L['login_failed']}: {error_msg}")
    except Exception as e:
        await update.message.reply_text(f"{L['error']}: {str(e)}")
    return ConversationHandler.END

# ================= MENU =================
@not_banned
async def menu(update, context):
    q = update.callback_query
    await q.answer()
    action = q.data
    L = get_lang(context)
    if action == "cemail":
        context.user_data["mode"] = "email"
        await q.message.reply_text(L["enter_new_email"])
    elif action == "cpass":
        context.user_data["mode"] = "pass"
        await q.message.reply_text(L["enter_new_pass"])
    elif action == "king":
        cpm = context.user_data.get("cpm")
        token = context.user_data.get("token")
        if cpm and cpm in CPM and token:
            if await set_rank(cpm, token):
                log_user_action(update.effective_user.id, "KING_RANK", f"CPM={cpm}")
                await q.message.reply_text(L["king_active"])
            else:
                await q.message.reply_text(L["king_failed"])
        else:
            await q.message.reply_text(L["login_again"])
    elif action == "logout":
        log_user_action(update.effective_user.id, "LOGOUT", "User logged out")
        lang_backup = context.user_data.get("lang", "en")
        context.user_data.clear()
        context.user_data["lang"] = lang_backup
        await q.message.reply_text(L["logout_success"])

# ================= TEXT HANDLER =================
@not_banned
async def text_handler(update, context):
    if not update.message or not update.message.text:
        return
    mode = context.user_data.get("mode")
    email = context.user_data.get("email")
    token = context.user_data.get("token")
    key = context.user_data.get("key")
    L = get_lang(context)
    user = update.effective_user

    # Admin actions from buttons
    admin_action = context.user_data.get("admin_action")
    if admin_action and is_admin(user.id):
        text = update.message.text.strip()
        if admin_action == "ban":
            try:
                target_id = int(text)
                fb_patch(f"banned_users/{target_id}", {"banned_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "banned_by": user.id})
                await update.message.reply_text(f"🚫 𝙐𝙨𝙚𝙧 {target_id} 𝘽𝘼𝙉𝙉𝙀𝘿!")
                log_user_action(user.id, "ADMIN_BAN", f"Banned user {target_id}")
            except ValueError:
                await update.message.reply_text("❌ 𝙄𝙣𝙫𝙖𝙡𝙞𝙙 𝙪𝙨𝙚𝙧 𝙄𝘿!")
            context.user_data.pop("admin_action", None)
            return
        elif admin_action == "unban":
            try:
                target_id = int(text)
                fb_delete(f"banned_users/{target_id}")
                await update.message.reply_text(f"✅ 𝙐𝙨𝙚𝙧 {target_id} 𝙐𝙉𝘽𝘼𝙉𝙉𝙀𝘿!")
                log_user_action(user.id, "ADMIN_UNBAN", f"Unbanned user {target_id}")
            except ValueError:
                await update.message.reply_text("❌ 𝙄𝙣𝙫𝙖𝙡𝙞𝙙 𝙪𝙨𝙚𝙧 𝙄𝘿!")
            context.user_data.pop("admin_action", None)
            return
        elif admin_action == "broadcast":
            message_text = text
            users = get_all_users()

            async def send_one(uid):
                try:
                    await context.bot.send_message(uid, f"📢 𝘼𝙉𝙉𝙊𝙐𝙉𝘾𝙀𝙈𝙀𝙉𝙏:\n\n{message_text}")
                    return True
                except Exception:
                    return False

            sent = 0
            failed = 0
            batch_size = 30
            for i in range(0, len(users), batch_size):
                batch = users[i:i+batch_size]
                tasks = [send_one(uid) for uid, _, _, _, _ in batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for r in results:
                    if r is True:
                        sent += 1
                    else:
                        failed += 1
                await asyncio.sleep(0.5)

            await update.message.reply_text(f"✅ 𝘽𝙧𝙤𝙖𝙙𝙘𝙖𝙨𝙩 𝙘𝙤𝙢𝙥𝙡𝙚𝙩𝙚!\n📤 𝙎𝙚𝙣𝙩: {sent}\n❌ 𝙁𝙖𝙞𝙡𝙚𝙙: {failed}")
            log_user_action(user.id, "ADMIN_BROADCAST", f"Sent to {sent} users, failed {failed}")
            context.user_data.pop("admin_action", None)
            return
        elif admin_action == "search":
            query = text.lower()
            users = get_all_users()
            results = []
            for uid, name, username, last_used, use_count in users:
                if query in str(uid).lower() or query in name.lower() or query in username.lower():
                    results.append((uid, name, username, last_used, use_count))
            if not results:
                await update.message.reply_text("📭 𝙉𝙤 𝙧𝙚𝙨𝙪𝙡𝙩𝙨 𝙛𝙤𝙪𝙣𝙙.")
            else:
                text_result = f"🔍 𝙎𝙀𝘼𝙍𝘾𝙃 𝙍𝙀𝙎𝙐𝙇𝙏𝙎 ({len(results)}):\n\n"
                for uid, name, username, last_used, use_count in results[:20]:
                    text_result += f"🆔 {uid} | {escape_markdown(name)} | @{escape_markdown(username)} | {last_used} | {use_count}x\n"
                await update.message.reply_text(text_result, parse_mode=ParseMode.MARKDOWN)
            context.user_data.pop("admin_action", None)
            return
        elif admin_action == "logs":
            try:
                target_id = int(text)
                logs = get_user_logs(target_id, 20)
                if not logs:
                    await update.message.reply_text("📭 𝙉𝙤 𝙡𝙤𝙜𝙨 𝙛𝙤𝙪𝙣𝙙.")
                else:
                    text_result = f"📋 𝙇𝙊𝙂𝙎 𝙁𝙊𝙍 𝙐𝙎𝙀𝙍 {target_id}:\n\n"
                    for ts, action, details in logs:
                        text_result += f"🕐 {ts} | {action}\n"
                        if details:
                            text_result += f"   {details}\n"
                    await update.message.reply_text(text_result)
            except ValueError:
                await update.message.reply_text("❌ 𝙄𝙣𝙫𝙖𝙡𝙞𝙙 𝙪𝙨𝙚𝙧 𝙄𝘿!")
            context.user_data.pop("admin_action", None)
            return
        elif admin_action == "grant":
            try:
                target_id = int(text)
                set_user_plan(target_id, PLAN_UNLIMITED, 0)
                await update.message.reply_text(f"✅ 𝙐𝙨𝙚𝙧 {target_id} 𝙜𝙧𝙖𝙣𝙩𝙚𝙙 𝙪𝙣𝙡𝙞𝙢𝙞𝙩𝙚𝙙 𝙗𝙪𝙡𝙠!")
                log_user_action(user.id, "ADMIN_GRANT", f"Granted unlimited to {target_id}")
            except ValueError:
                await update.message.reply_text("❌ 𝙄𝙣𝙫𝙖𝙡𝙞𝙙 𝙪𝙨𝙚𝙧 𝙄𝘿!")
            context.user_data.pop("admin_action", None)
            return

    # Game Editor text inputs
    gmode = context.user_data.get("gmode")
    if gmode:
        await handle_game_editor_text(update, context)
        return

    if mode == "email" and token and key:
        new_email = update.message.text
        try:
            timeout = aiohttp.ClientTimeout(total=20)
            async with aiohttp.ClientSession(timeout=timeout, connector=make_http_connector(limit=20, ssl=False)) as s:
                async with s.post(f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={key}",
                                  json={"idToken": token, "email": new_email, "returnSecureToken": True}) as r:
                    resp = await r.json()
            error_msg = resp.get("error", {}).get("message", "")
            if error_msg == "EMAIL_EXISTS":
                await update.message.reply_text(L["email_exists"])
            elif error_msg:
                await update.message.reply_text(f"{L['error']}: {error_msg}")
                context.user_data["mode"] = None
            else:
                old_email = context.user_data.get("email", "N/A")
                context.user_data["email"] = new_email
                if "idToken" in resp:
                    context.user_data["token"] = resp["idToken"]
                context.user_data["mode"] = None
                await update.message.reply_text(L["email_updated"])
                log_user_action(user.id, "CHANGE_EMAIL")
        except Exception as e:
            await update.message.reply_text(f"{L['error']}: {str(e)}")
    elif mode == "pass" and token and key:
        new_pass = update.message.text
        try:
            timeout = aiohttp.ClientTimeout(total=20)
            async with aiohttp.ClientSession(timeout=timeout, connector=make_http_connector(limit=20, ssl=False)) as s:
                async with s.post(f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={key}",
                                  json={"idToken": token, "password": new_pass, "returnSecureToken": True}) as r:
                    resp_pass = await r.json()
            if "idToken" in resp_pass:
                context.user_data["token"] = resp_pass["idToken"]
            context.user_data["mode"] = None
            await update.message.reply_text(L["pass_updated"])
            cur_email = context.user_data.get("email", "N/A")
            log_user_action(user.id, "CHANGE_PASSWORD")
        except Exception as e:
            await update.message.reply_text(f"{L['error']}: {str(e)}")

# ================= GAME EDITOR =================
B = "━" * 22

def gedit_dashboard(record, email, uid):
    name   = record.get("Name","Unknown")
    pid    = record.get("localID","—")
    money  = record.get("money",0)
    coin   = record.get("coin",0)
    floats = record.get("floats",[])
    wheels = record.get("wheels",[])
    anims  = record.get("animations",[])
    wins   = int(floats[8]) if len(floats)>8 else 0
    loses  = int(floats[9]) if len(floats)>9 else 0
    levels = record.get("LevelsDoneTime",[])
    done   = sum(1 for x in levels if x and x>0) if levels else 0
    friends= len(record.get("FriendsID",[]))
    return (
        f"{B}\n  🏠  𝗚𝗔𝗠𝗘 𝗘𝗗𝗜𝗧𝗢𝗥\n{B}\n\n"
        f"  ╭──── 𝗔𝗖𝗖𝗢𝗨𝗡𝗧 ────╮\n"
        f"  │ 📧 {email}\n"
        f"  │ 👤 {name}\n"
        f"  │ 🆔 {pid}\n"
        f"  ╰─────────────────╯\n\n"
        f"  ╭──── 𝗦𝗧𝗔𝗧𝗦 ──────╮\n"
        f"  │ 💰 ${money:,}\n"
        f"  │ 🪙 {coin:,} coins\n"
        f"  │ 🏆 {wins:,}W / {loses:,}L\n"
        f"  │ 🎮 {done} levels done\n"
        f"  │ 🛞 {len(wheels)} wheels\n"
        f"  │ 🎭 {len(anims)} animations\n"
        f"  │ 👥 {friends} friends\n"
        f"  ╰─────────────────╯\n\n"
        f"  ▸ Select an option below:"
    )

@not_banned
async def open_geditor(update, context):
    q = update.callback_query
    await q.answer()
    uid = update.effective_user.id
    token = context.user_data.get("token")
    email = context.user_data.get("email")
    password = context.user_data.get("password")
    fuid = context.user_data.get("firebase_uid")
    if not token:
        await q.message.reply_text("❌ 𝙋𝙇𝙀𝘼𝙎𝙀 𝙇𝙊𝙂𝙄𝙉 𝙁𝙄𝙍𝙎𝙏")
        return
    # Save token to nuker
    nuker.save_token(uid, token, email, password, "", fuid)
    msg = await q.message.reply_text("⏳ 𝙇𝙊𝘼𝘿𝙄𝙉𝙂 𝘼𝘾𝘾𝙊𝙐𝙉𝙏 𝘿𝘼𝙏𝘼...")
    loaded = await nuker.load(uid, force=True)
    if loaded:
        record = nuker.get_record(uid, email)
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💰 Money", callback_data="gedit_money_menu"),
             InlineKeyboardButton("🪙 Coins", callback_data="gedit_coin_menu")],
            [InlineKeyboardButton("⚡ Features", callback_data="gedit_feat_menu"),
             InlineKeyboardButton("🔧 Settings", callback_data="gedit_sett_menu")],
            [InlineKeyboardButton("🔄 Refresh", callback_data="gedit_refresh"),
             InlineKeyboardButton("🔙 Back", callback_data="gedit_back")],
        ])
        await msg.edit_text(gedit_dashboard(record, email, uid), reply_markup=keyboard, parse_mode=ParseMode.HTML)
    else:
        await msg.edit_text("⚠️ 𝘾𝙊𝙐𝙇𝘿 𝙉𝙊𝙏 𝙇𝙊𝘼𝘿 𝘿𝘼𝙏𝘼. 𝙏𝙧𝙮 𝙖𝙜𝙖𝙞𝙣.")

@not_banned
async def gedit_refresh(update, context):
    q = update.callback_query
    await q.answer("🔄")
    uid = q.from_user.id
    email = context.user_data.get("email")
    await nuker.load(uid, force=True)
    record = nuker.get_record(uid, email)
    if record and record.get("Name"):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💰 Money", callback_data="gedit_money_menu"),
             InlineKeyboardButton("🪙 Coins", callback_data="gedit_coin_menu")],
            [InlineKeyboardButton("⚡ Features", callback_data="gedit_feat_menu"),
             InlineKeyboardButton("🔧 Settings", callback_data="gedit_sett_menu")],
            [InlineKeyboardButton("🔄 Refresh", callback_data="gedit_refresh"),
             InlineKeyboardButton("🔙 Back", callback_data="gedit_back")],
        ])
        try:
            await q.message.edit_text(gedit_dashboard(record, email, uid), reply_markup=keyboard, parse_mode=ParseMode.HTML)
        except Exception:
            await q.message.reply_text(gedit_dashboard(record, email, uid), reply_markup=keyboard, parse_mode=ParseMode.HTML)
    else:
        try:
            await q.message.edit_text("⚠️ 𝘾𝙊𝙐𝙇𝘿 𝙉𝙊𝙏 𝙇𝙊𝘼𝘿.")
        except Exception:
            await q.message.reply_text("⚠️ 𝘾𝙊𝙐𝙇𝘿 𝙉𝙊𝙏 𝙇𝙊𝘼𝘿.")

@not_banned
async def gedit_back(update, context):
    q = update.callback_query
    await q.answer()
    L = get_lang(context)
    email = context.user_data.get("email", "")
    cpm = context.user_data.get("cpm", "")
    text = (
        f"╔══════════════════════╗\n"
        f"{L['login_success']}\n"
        f"╚══════════════════════╝\n\n"
        f"👤 𝙐𝙎𝙀𝙍 : {email.split('@')[0] if email else 'N/A'}\n"
        f"📧 𝙀𝙈𝘼𝙄𝙇: {email}\n"
        f"🎮 𝘾𝙋𝙈  : {cpm}\n"
    )
    keyboard = [[InlineKeyboardButton(L["btn_king"], callback_data="king")]]
    keyboard.append([InlineKeyboardButton(L["btn_cemail"], callback_data="cemail"),
                     InlineKeyboardButton(L["btn_cpass"], callback_data="cpass")])
    if cpm == "CPM1":
        keyboard.append([InlineKeyboardButton(L["btn_gedit"], callback_data="open_geditor")])
    keyboard.append([InlineKeyboardButton(L["btn_logout"], callback_data="logout")])
    await q.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

@not_banned
async def gedit_money_menu(update, context):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    ok, wait = check_rate_limit(uid)
    if not ok:
        await q.answer(f"⏳ 𝙒𝙖𝙞𝙩 {wait}s", show_alert=True)
        return
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("$1M", callback_data="gedit_m_1000000"),
         InlineKeyboardButton("$5M", callback_data="gedit_m_5000000"),
         InlineKeyboardButton("$10M", callback_data="gedit_m_10000000")],
        [InlineKeyboardButton("$25M", callback_data="gedit_m_25000000"),
         InlineKeyboardButton("$50M", callback_data="gedit_m_50000000")],
        [InlineKeyboardButton("✏ Custom", callback_data="gedit_m_custom")],
        [InlineKeyboardButton("◂ Back", callback_data="gedit_refresh")],
    ])
    await q.message.edit_text(f"{B}\n  💰  𝗠𝗢𝗡𝗘𝗬\n{B}\n\n  Max: $50,000,000", reply_markup=keyboard)

@not_banned
async def gedit_coin_menu(update, context):
    q = update.callback_query
    await q.answer()
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("100K", callback_data="gedit_c_100000"),
         InlineKeyboardButton("250K", callback_data="gedit_c_250000"),
         InlineKeyboardButton("500K", callback_data="gedit_c_500000")],
        [InlineKeyboardButton("✏ Custom", callback_data="gedit_c_custom")],
        [InlineKeyboardButton("◂ Back", callback_data="gedit_refresh")],
    ])
    await q.message.edit_text(f"{B}\n  🪙  𝗖𝗢𝗜𝗡𝗦\n{B}\n\n  Max: 500,000", reply_markup=keyboard)

@not_banned
async def gedit_feat_menu(update, context):
    q = update.callback_query
    await q.answer()
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚗 W16", callback_data="gedit_f_w16"),
         InlineKeyboardButton("🔊 Horns", callback_data="gedit_f_horns")],
        [InlineKeyboardButton("🛡 No Dmg", callback_data="gedit_f_damage"),
         InlineKeyboardButton("⛽ Fuel", callback_data="gedit_f_fuel")],
        [InlineKeyboardButton("💨 Smoke", callback_data="gedit_f_smoke"),
         InlineKeyboardButton("🎭 Anims", callback_data="gedit_f_anims")],
        [InlineKeyboardButton("🛞 Wheels", callback_data="gedit_f_wheels"),
         InlineKeyboardButton("🏠 Houses", callback_data="gedit_f_houses")],
        [InlineKeyboardButton("🎮 Levels", callback_data="gedit_f_levels"),
         InlineKeyboardButton("🏅 Rank", callback_data="gedit_f_rank")],
        [InlineKeyboardButton("🚀 ★ UNLOCK ALL ★", callback_data="gedit_f_all")],
        [InlineKeyboardButton("◂ Back", callback_data="gedit_refresh")],
    ])
    await q.message.edit_text(f"{B}\n  ⚡  𝗙𝗘𝗔𝗧𝗨𝗥𝗘𝗦\n{B}\n\n  Select a feature:", reply_markup=keyboard)

@not_banned
async def gedit_sett_menu(update, context):
    q = update.callback_query
    await q.answer()
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✏ Name", callback_data="gedit_s_name"),
         InlineKeyboardButton("🆔 Player ID", callback_data="gedit_s_pid")],
        [InlineKeyboardButton("🏆 Wins", callback_data="gedit_s_wins"),
         InlineKeyboardButton("😞 Loses", callback_data="gedit_s_loses")],
        [InlineKeyboardButton("🔧 Fix Account", callback_data="gedit_s_fix")],
        [InlineKeyboardButton("◂ Back", callback_data="gedit_refresh")],
    ])
    await q.message.edit_text(f"{B}\n  🔧  𝗦𝗘𝗧𝗧𝗜𝗡𝗚𝗦\n{B}\n\n  Modify your account:", reply_markup=keyboard)

# --- Money / Coin callbacks ---
@not_banned
async def gedit_money_cb(update, context):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    val = q.data.replace("gedit_m_", "")
    if val == "custom":
        context.user_data["gmode"] = "money"
        try:
            await q.message.edit_text(f"{B}\n  💰  𝗖𝗨𝗦𝗧𝗢𝗠\n{B}\n\n  Enter amount (1 — 50,000,000):", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◂ Cancel", callback_data="gedit_money_menu")]]))
        except Exception:
            await q.message.reply_text(f"{B}\n  💰  𝗖𝗨𝗦𝗧𝗢𝗠\n{B}\n\n  Enter amount (1 — 50,000,000):", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◂ Cancel", callback_data="gedit_money_menu")]]))
        return
    amount = int(val)
    try:
        msg = await q.message.edit_text(f"  ⏳ Setting ${amount:,}...")
    except Exception:
        msg = await q.message.reply_text(f"  ⏳ Setting ${amount:,}...")
    r = await nuker.set_money(uid, amount)
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("◂ Back", callback_data="gedit_refresh")]])
    if r.get("ok"):
        try:
            await msg.edit_text(f"{B}\n  ✅  𝗠𝗢𝗡𝗘𝗬 𝗦𝗘𝗧\n{B}\n\n  💰 ${amount:,}", reply_markup=kb)
        except Exception:
            await msg.reply_text(f"{B}\n  ✅  𝗠𝗢𝗡𝗘𝗬 𝗦𝗘𝗧\n{B}\n\n  💰 ${amount:,}", reply_markup=kb)
    else:
        try:
            await msg.edit_text(f"{B}\n  ❌  𝗙𝗔𝗜𝗟𝗘𝗗\n{B}\n\n  {r.get('message','')}", reply_markup=kb)
        except Exception:
            await msg.reply_text(f"{B}\n  ❌  𝗙𝗔𝗜𝗟𝗘𝗗\n{B}\n\n  {r.get('message','')}", reply_markup=kb)

@not_banned
async def gedit_coin_cb(update, context):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    val = q.data.replace("gedit_c_", "")
    if val == "custom":
        context.user_data["gmode"] = "coin"
        try:
            await q.message.edit_text(f"{B}\n  🪙  𝗖𝗨𝗦𝗧𝗢𝗠\n{B}\n\n  Enter amount (1 — 500,000):", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◂ Cancel", callback_data="gedit_coin_menu")]]))
        except Exception:
            await q.message.reply_text(f"{B}\n  🪙  𝗖𝗨𝗦𝗧𝗢𝗠\n{B}\n\n  Enter amount (1 — 500,000):", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◂ Cancel", callback_data="gedit_coin_menu")]]))
        return
    amount = int(val)
    try:
        msg = await q.message.edit_text(f"  ⏳ Setting {amount:,} coins...")
    except Exception:
        msg = await q.message.reply_text(f"  ⏳ Setting {amount:,} coins...")
    r = await nuker.set_coin(uid, amount)
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("◂ Back", callback_data="gedit_refresh")]])
    if r.get("ok"):
        try:
            await msg.edit_text(f"{B}\n  ✅  𝗖𝗢𝗜𝗡𝗦 𝗦𝗘𝗧\n{B}\n\n  🪙 {amount:,} coins", reply_markup=kb)
        except Exception:
            await msg.reply_text(f"{B}\n  ✅  𝗖𝗢𝗜𝗡𝗦 𝗦𝗘𝗧\n{B}\n\n  🪙 {amount:,} coins", reply_markup=kb)
    else:
        try:
            await msg.edit_text(f"{B}\n  ❌  𝗙𝗔𝗜𝗟𝗘𝗗\n{B}\n\n  {r.get('message','')}", reply_markup=kb)
        except Exception:
            await msg.reply_text(f"{B}\n  ❌  𝗙𝗔𝗜𝗟𝗘𝗗\n{B}\n\n  {r.get('message','')}", reply_markup=kb)

# --- Feature callbacks ---
FEAT_MAP = {
    "gedit_f_w16":    ("🚗 W16 Engine",    nuker.unlock_w16),
    "gedit_f_horns":  ("🔊 Horns",         nuker.unlock_horns),
    "gedit_f_damage": ("🛡 No Damage",     nuker.disable_damage),
    "gedit_f_fuel":   ("⛽ Unlimited Fuel", nuker.unlimited_fuel),
    "gedit_f_smoke":  ("💨 Smoke",         nuker.unlock_smoke),
    "gedit_f_anims":  ("🎭 Animations",    nuker.unlock_animations),
    "gedit_f_wheels": ("🛞 Wheels",        nuker.unlock_wheels),
    "gedit_f_houses": ("🏠 Houses",        nuker.unlock_houses),
    "gedit_f_levels": ("🎮 All Levels",    nuker.complete_all_levels),
    "gedit_f_rank":   ("🏅 Max Rank",      nuker.set_rank),
}

@not_banned
async def gedit_feat_cb(update, context):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    fname, fn = FEAT_MAP[q.data]
    try:
        msg = await q.message.edit_text(f"  ⏳ Applying {fname}...")
    except Exception:
        msg = await q.message.reply_text(f"  ⏳ Applying {fname}...")
    r = await fn(uid)
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("◂ Back", callback_data="gedit_feat_menu")]])
    if r.get("ok"):
        try:
            await msg.edit_text(f"{B}\n  ✅  {fname} ✔\n{B}", reply_markup=kb)
        except Exception:
            await msg.reply_text(f"{B}\n  ✅  {fname} ✔\n{B}", reply_markup=kb)
    else:
        try:
            await msg.edit_text(f"{B}\n  ❌  {fname} ✗\n{B}\n\n  {r.get('message','')}", reply_markup=kb)
        except Exception:
            await msg.reply_text(f"{B}\n  ❌  {fname} ✗\n{B}\n\n  {r.get('message','')}", reply_markup=kb)

@not_banned
async def gedit_f_all(update, context):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    msg = await q.message.edit_text(f"{B}\n  🚀  𝗨𝗡𝗟𝗢𝗖𝗞𝗜𝗡𝗚 𝗔𝗟𝗟\n{B}\n\n  ⏳ Loading account...")
    await nuker.load(uid, force=True)
    ALL = list(FEAT_MAP.values())
    total = len(ALL)
    done = 0; failed = 0; results = []
    for i, (name, fn) in enumerate(ALL):
        pct = int(((i+1)/total)*100)
        bar = "▰"*int(pct/7) + "▱"*(15-int(pct/7))
        try:
            await msg.edit_text(
                f"{B}\n  🚀  𝗨𝗡𝗟𝗢𝗖𝗞𝗜𝗡𝗚 𝗔𝗟𝗟\n{B}\n\n"
                f"  [{bar}] {pct}%\n"
                f"  ✔ {done}  ✗ {failed}  ▸ {i+1}/{total}\n\n"
                f"  ⏳ {name}")
        except: pass
        r = await fn(uid)
        if r.get("ok"): done += 1; results.append(f"  ✔ {name}")
        else: failed += 1; results.append(f"  ✗ {name}")
        await asyncio.sleep(0.3)
    try:
        await msg.edit_text(
            f"{B}\n  🎉  𝗖𝗢𝗠𝗣𝗟𝗘𝗧𝗘\n{B}\n\n"
            f"  [▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰] 100%\n\n"
            f"  ✔ {done}/{total}  ✗ {failed}/{total}\n\n"
            + "\n".join(results), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◂ Home", callback_data="gedit_refresh")]]))
    except: pass

# --- Settings callbacks ---
@not_banned
async def gedit_sett_cb(update, context):
    q = update.callback_query
    await q.answer()
    action = q.data
    uid = q.from_user.id
    if action == "gedit_s_name":
        context.user_data["gmode"] = "name"
        try:
            await q.message.edit_text(f"{B}\n  ✏  𝗖𝗛𝗔𝗡𝗚𝗘 𝗡𝗔𝗠𝗘\n{B}\n\n  Enter new name:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◂ Cancel", callback_data="gedit_sett_menu")]]))
        except Exception:
            await q.message.reply_text(f"{B}\n  ✏  𝗖𝗛𝗔𝗡𝗚𝗘 𝗡𝗔𝗠𝗘\n{B}\n\n  Enter new name:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◂ Cancel", callback_data="gedit_sett_menu")]]))
    elif action == "gedit_s_pid":
        context.user_data["gmode"] = "pid"
        try:
            await q.message.edit_text(f"{B}\n  🆔  𝗣𝗟𝗔𝗬𝗘𝗥 𝗜𝗗\n{B}\n\n  Enter your new in-game Player ID:\n  (This is your display ID, NOT your password)", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◂ Cancel", callback_data="gedit_sett_menu")]]))
        except Exception:
            await q.message.reply_text(f"{B}\n  🆔  𝗣𝗟𝗔𝗬𝗘𝗥 𝗜𝗗\n{B}\n\n  Enter your new in-game Player ID:\n  (This is your display ID, NOT your password)", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◂ Cancel", callback_data="gedit_sett_menu")]]))
    elif action == "gedit_s_wins":
        context.user_data["gmode"] = "wins"
        try:
            await q.message.edit_text(f"{B}\n  🏆  𝗦𝗘𝗧 𝗪𝗜𝗡𝗦\n{B}\n\n  Enter win count:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◂ Cancel", callback_data="gedit_sett_menu")]]))
        except Exception:
            await q.message.reply_text(f"{B}\n  🏆  𝗦𝗘𝗧 𝗪𝗜𝗡𝗦\n{B}\n\n  Enter win count:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◂ Cancel", callback_data="gedit_sett_menu")]]))
    elif action == "gedit_s_loses":
        context.user_data["gmode"] = "loses"
        try:
            await q.message.edit_text(f"{B}\n  😞  𝗦𝗘𝗧 𝗟𝗢𝗦𝗘𝗦\n{B}\n\n  Enter loss count:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◂ Cancel", callback_data="gedit_sett_menu")]]))
        except Exception:
            await q.message.reply_text(f"{B}\n  😞  𝗦𝗘𝗧 𝗟𝗢𝗦𝗘𝗦\n{B}\n\n  Enter loss count:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◂ Cancel", callback_data="gedit_sett_menu")]]))
    elif action == "gedit_s_fix":
        try:
            msg = await q.message.edit_text("  ⏳ Loading & fixing account...")
        except Exception:
            msg = await q.message.reply_text("  ⏳ Loading & fixing account...")
        r = await nuker.fix_account(uid)
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("◂ Back", callback_data="gedit_refresh")]])
        if r.get("ok"):
            try:
                await msg.edit_text(f"{B}\n  ✅  𝗔𝗖𝗖𝗢𝗨𝗡𝗧 𝗙𝗜𝗫𝗘𝗗\n{B}\n\n  ✔ {r.get('bugs_fixed',0)} bugs fixed", reply_markup=kb)
            except Exception:
                await msg.reply_text(f"{B}\n  ✅  𝗔𝗖𝗖𝗢𝗨𝗡𝗧 𝗙𝗜𝗫𝗘𝗗\n{B}\n\n  ✔ {r.get('bugs_fixed',0)} bugs fixed", reply_markup=kb)
        else:
            try:
                await msg.edit_text(f"{B}\n  ❌  𝗙𝗔𝗜𝗟𝗘𝗗\n{B}\n\n  {r.get('message','')}", reply_markup=kb)
            except Exception:
                await msg.reply_text(f"{B}\n  ❌  𝗙𝗔𝗜𝗟𝗘𝗗\n{B}\n\n  {r.get('message','')}", reply_markup=kb)

# --- Game Editor Text Handler ---
async def handle_game_editor_text(update, context):
    uid = update.effective_user.id
    gmode = context.user_data.pop("gmode", None)
    text = update.message.text.strip()
    if gmode == "money":
        try:
            a = int(text.replace(",", "").replace(" ", ""))
            assert 1 <= a <= MAX_MONEY
        except:
            await update.message.reply_text("  ✗ Enter 1 — 50,000,000", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◂ Back", callback_data="gedit_money_menu")]]))
            return
        msg = await update.message.reply_text(f"  ⏳ Setting ${a:,}...")
        r = await nuker.set_money(uid, a)
        if r.get("ok"):
            await msg.edit_text(f"{B}\n  ✅  𝗠𝗢𝗡𝗘𝗬 𝗦𝗘𝗧\n{B}\n\n  💰 ${a:,}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◂ Back", callback_data="gedit_refresh")]]))
        else:
            await msg.edit_text(f"{B}\n  ❌  𝗙𝗔𝗜𝗟𝗘𝗗\n{B}\n\n  {r.get('message','')}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◂ Back", callback_data="gedit_refresh")]]))
    elif gmode == "coin":
        try:
            a = int(text.replace(",", "").replace(" ", ""))
            assert 1 <= a <= MAX_COIN
        except:
            await update.message.reply_text("  ✗ Enter 1 — 500,000", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◂ Back", callback_data="gedit_coin_menu")]]))
            return
        msg = await update.message.reply_text(f"  ⏳ Setting {a:,} coins...")
        r = await nuker.set_coin(uid, a)
        if r.get("ok"):
            await msg.edit_text(f"{B}\n  ✅  𝗖𝗢𝗜𝗡𝗦 𝗦𝗘𝗧\n{B}\n\n  🪙 {a:,} coins", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◂ Back", callback_data="gedit_refresh")]]))
        else:
            await msg.edit_text(f"{B}\n  ❌  𝗙𝗔𝗜𝗟𝗘𝗗\n{B}\n\n  {r.get('message','')}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◂ Back", callback_data="gedit_refresh")]]))
    elif gmode == "name":
        name = text
        if not name or len(name) > 100:
            await update.message.reply_text("  ✗ 1-100 characters.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◂ Back", callback_data="gedit_sett_menu")]]))
            return
        msg = await update.message.reply_text("  ⏳ Setting name...")
        r = await nuker.set_player_name(uid, name)
        if r.get("ok"):
            await msg.edit_text(f"{B}\n  ✅  𝗡𝗔𝗠𝗘 𝗨𝗣𝗗𝗔𝗧𝗘𝗗\n{B}\n\n  ✔ {name}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◂ Back", callback_data="gedit_refresh")]]))
        else:
            await msg.edit_text(f"{B}\n  ❌  𝗙𝗔𝗜𝗟𝗘𝗗\n{B}\n\n  {r.get('message','')}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◂ Back", callback_data="gedit_refresh")]]))
    elif gmode == "pid":
        pid = text
        clean = re.sub(r'\[\w+\]','',pid)
        if not clean or len(clean) < 4 or len(clean) > 100:
            await update.message.reply_text("  ✗ 4-100 characters.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◂ Back", callback_data="gedit_sett_menu")]]))
            return
        msg = await update.message.reply_text("  ⏳ Setting ID...")
        r = await nuker.set_player_id(uid, pid)
        if r.get("ok"):
            await msg.edit_text(f"{B}\n  ✅  𝗜𝗗 𝗨𝗣𝗗𝗔𝗧𝗘𝗗\n{B}\n\n  ✔ {pid.upper()}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◂ Back", callback_data="gedit_refresh")]]))
        else:
            await msg.edit_text(f"{B}\n  ❌  𝗙𝗔𝗜𝗟𝗘𝗗\n{B}\n\n  {r.get('message','')}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◂ Back", callback_data="gedit_refresh")]]))
    elif gmode == "wins":
        try:
            v = int(text); assert v >= 0
        except:
            await update.message.reply_text("  ✗ Invalid number.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◂ Back", callback_data="gedit_sett_menu")]]))
            return
        msg = await update.message.reply_text("  ⏳ Setting wins...")
        r = await nuker.set_race_wins(uid, v)
        if r.get("ok"):
            await msg.edit_text(f"{B}\n  ✅  𝗪𝗜𝗡𝗦 𝗨𝗣𝗗𝗔𝗧𝗘𝗗\n{B}\n\n  🏆 {v:,} wins", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◂ Back", callback_data="gedit_refresh")]]))
        else:
            await msg.edit_text(f"{B}\n  ❌  𝗙𝗔𝗜𝗟𝗘𝗗\n{B}\n\n  {r.get('message','')}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◂ Back", callback_data="gedit_refresh")]]))
    elif gmode == "loses":
        try:
            v = int(text); assert v >= 0
        except:
            await update.message.reply_text("  ✗ Invalid number.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◂ Back", callback_data="gedit_sett_menu")]]))
            return
        msg = await update.message.reply_text("  ⏳ Setting loses...")
        r = await nuker.set_race_loses(uid, v)
        if r.get("ok"):
            await msg.edit_text(f"{B}\n  ✅  𝗟𝗢𝗦𝗘𝗦 𝗨𝗣𝗗𝗔𝗧𝗘𝗗\n{B}\n\n  😞 {v:,} loses", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◂ Back", callback_data="gedit_refresh")]]))
        else:
            await msg.edit_text(f"{B}\n  ❌  𝗙𝗔𝗜𝗟𝗘𝗗\n{B}\n\n  {r.get('message','')}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◂ Back", callback_data="gedit_refresh")]]))

@not_banned
async def bulk_confirm(update, context):
    q = update.callback_query
    await q.answer()
    if "bulk_accounts" not in context.user_data:
        keyboard = [
            [InlineKeyboardButton("🚀 𝙎𝙩𝙖𝙧𝙩 𝘽𝙪𝙡𝙠", callback_data="start_bulk")],
            [InlineKeyboardButton("❌ 𝘾𝙖𝙣𝙘𝙚𝙡", callback_data="nav_cancel")]
        ]
        await q.message.reply_text("❌ 𝙉𝙊 𝘼𝘾𝙏𝙄𝙑𝙀 𝘽𝙐𝙇𝙆 𝙎𝙀𝙎𝙎𝙄𝙊𝙉!", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    accounts = context.user_data.get("bulk_accounts", [])
    prefix = context.user_data.get("bulk_prefix", "user")
    domain = context.user_data.get("bulk_domain", "gmail.com")
    cpm = context.user_data.get("bulk_cpm", "CPM1")
    mode = context.user_data.get("bulk_mode", BULK_MODE_BOTH)
    custom_pass = context.user_data.get("bulk_custom_pass")
    user_id = q.from_user.id
    await _bulk_run_loop(q.message, q.from_user, context, accounts, prefix, domain, cpm, mode, custom_pass, user_id)
    context.user_data.pop("bulk_accounts", None)
    context.user_data.pop("bulk_domain", None)
    context.user_data.pop("bulk_prefix", None)
    context.user_data.pop("bulk_custom_pass", None)

@not_banned
async def bulk_process_password_only(update, context):
    accounts = context.user_data.get("bulk_accounts", [])
    cpm = context.user_data.get("bulk_cpm", "CPM1")
    mode = context.user_data.get("bulk_mode", BULK_MODE_PASS)
    custom_pass = context.user_data.get("bulk_custom_pass")
    user_id = update.effective_user.id
    if not accounts:
        keyboard = [
            [InlineKeyboardButton("🚀 𝙎𝙩𝙖𝙧𝙩 𝘽𝙪𝙡𝙠", callback_data="start_bulk")],
            [InlineKeyboardButton("❌ 𝘾𝙖𝙣𝙘𝙚𝙡", callback_data="nav_cancel")]
        ]
        await update.message.reply_text("❌ 𝙎𝙀𝙎𝙎𝙄𝙊𝙉 𝙀𝙓𝙋𝙄𝙍𝙀𝘿.", reply_markup=InlineKeyboardMarkup(keyboard))
        return ConversationHandler.END
    total = len(accounts)
    plan = get_user_plan(user_id)
    if plan["plan"] == PLAN_SINGLE:
        if not deduct_use(user_id):
            await update.message.reply_text("❌ 𝙔𝙤𝙪𝙧 𝙨𝙞𝙣𝙜𝙡𝙚 𝙥𝙡𝙖𝙣 𝙚𝙭𝙥𝙞𝙧𝙚𝙙. 𝘽𝙪𝙮 𝙖𝙜𝙖𝙞𝙣!", reply_markup=get_cancel_start_keyboard())
            return ConversationHandler.END
    context.user_data["bulk_domain"] = "password_only"
    context.user_data["bulk_prefix"] = "keep"
    preview_text = (
        f"╔══════════════════════╗\n"
        f"           📋 𝙋𝙍𝙀𝙑𝙄𝙀𝙒\n"
        f"╚══════════════════════╝\n\n"
        f"🎮 𝘾𝙋𝙈: {cpm}\n"
        f"🎯 𝙈𝙊𝘿𝙀: 𝙋𝘼𝙎𝙎𝙒𝙊𝙍𝘿 𝙊𝙉𝙇𝙔\n"
        f"📊 𝙏𝙊𝙏𝘼𝙇: {total:,} 𝙖𝙘𝙘𝙤𝙪𝙣𝙩𝙨\n"
        f"🔐 𝙋𝘼𝙎𝙎: {'𝘾𝙪𝙨𝙩𝙤𝙢' if custom_pass else '𝘼𝙪𝙩𝙤-𝙂𝙚𝙣'}\n"
        f"🔁 𝘽𝙖𝙩𝙘𝙝: {BULK_BATCH_SIZE} 𝙖𝙘𝙘/𝙠𝙚𝙮"
    )
    await update.message.reply_text(preview_text, reply_markup=get_confirm_cancel_keyboard())
    return ConversationHandler.END

# ================= PAYMENT HANDLERS =================
async def payment_menu(update, context):
    q = update.callback_query
    await q.answer()
    text = (
        f"╔══════════════════════╗\n"
        f"💎 𝘽𝙐𝙔 𝘽𝙐𝙇𝙆 𝙋𝙇𝘼𝙉 💎\n"
        f"╚══════════════════════╝\n\n"
        f"🎯 𝘾𝙃𝙊𝙊𝙎𝙀 𝙔𝙊𝙐𝙍 𝙋𝙇𝘼𝙉:\n\n"
        f"⭐ {PLAN_SINGLE_STARS} 𝙎𝙩𝙖𝙧𝙨 → 1 𝙏𝙞𝙢𝙚 𝙐𝙨𝙚\n"
        f"   ✅ 1 𝙗𝙪𝙡𝙠 𝙘𝙝𝙖𝙣𝙜𝙚 𝙨𝙚𝙨𝙨𝙞𝙤𝙣\n\n"
        f"⭐ {PLAN_UNLIMITED_STARS} 𝙎𝙩𝙖𝙧𝙨 → 𝙐𝙣𝙡𝙞𝙢𝙞𝙩𝙚𝙙\n"
        f"   ✅ 𝙐𝙣𝙡𝙞𝙢𝙞𝙩𝙚𝙙 𝙗𝙪𝙡𝙠 𝙘𝙝𝙖𝙣𝙜𝙚𝙨\n"
        f"   ✅ 𝙉𝙤 𝙡𝙞𝙢𝙞𝙩𝙨\n"
        f"   ✅ 𝙋𝙧𝙞𝙤𝙧𝙞𝙩𝙮 𝙨𝙪𝙥𝙥𝙤𝙧𝙩"
    )
    keyboard = [
        [InlineKeyboardButton(f"⭐ {PLAN_SINGLE_STARS} 𝙎𝙩𝙖𝙧𝙨 (1𝙭)", callback_data="pay_single")],
        [InlineKeyboardButton(f"⭐ {PLAN_UNLIMITED_STARS} 𝙎𝙩𝙖𝙧𝙨 (𝙐𝙣𝙡𝙞𝙢𝙞𝙩𝙚𝙙)", callback_data="pay_unlimited")],
        [InlineKeyboardButton("❌ 𝘾𝘼𝙉𝘾𝙀𝙇", callback_data="nav_cancel")]
    ]
    await q.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def payment_single(update, context):
    q = update.callback_query
    await q.answer()
    user_id = q.from_user.id
    text = (
        f"╔══════════════════════╗\n"
        f"⭐ {PLAN_SINGLE_STARS} 𝙎𝙩𝙖𝙧𝙨 - 1𝙭 𝙋𝙇𝘼𝙉\n"
        f"╚══════════════════════╝\n\n"
        f"💎 𝙒𝙝𝙖𝙩 𝙮𝙤𝙪 𝙜𝙚𝙩:\n"
        f"✅ 1 𝘽𝙪𝙡𝙠 𝘼𝙘𝙘𝙤𝙪𝙣𝙩 𝘾𝙝𝙖𝙣𝙜𝙚\n"
        f"✅ 𝙐𝙥 𝙩𝙤 {BULK_MAX_ACCOUNTS:,} 𝙖𝙘𝙘𝙤𝙪𝙣𝙩𝙨\n"
        f"✅ 𝘿𝙪𝙖𝙡 𝙆𝙚𝙮 𝙍𝙤𝙩𝙖𝙩𝙞𝙤𝙣\n"
        f"✅ 𝘼𝙪𝙩𝙤-𝙧𝙚𝙩𝙧𝙮\n\n"
        f"🛒 𝘾𝙡𝙞𝙘𝙠 𝙗𝙚𝙡𝙤𝙬 𝙩𝙤 𝙥𝙖𝙮:"
    )
    keyboard = [[
        InlineKeyboardButton(f"💳 𝙋𝘼𝙔 {PLAN_SINGLE_STARS} 𝙎𝙩𝙖𝙧𝙨", callback_data="buy_single")
    ], [
        InlineKeyboardButton("❌ 𝘾𝘼𝙉𝘾𝙀𝙇", callback_data="nav_cancel")
    ]]
    await q.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def payment_unlimited(update, context):
    q = update.callback_query
    await q.answer()
    text = (
        f"╔══════════════════════╗\n"
        f"⭐ {PLAN_UNLIMITED_STARS} 𝙎𝙩𝙖𝙧𝙨 - 𝙐𝙉𝙇𝙄𝙈𝙄𝙏𝙀𝘿\n"
        f"╚══════════════════════╝\n\n"
        f"💎 𝙒𝙝𝙖𝙩 𝙮𝙤𝙪 𝙜𝙚𝙩:\n"
        f"✅ 𝙐𝙣𝙡𝙞𝙢𝙞𝙩𝙚𝙙 𝘽𝙪𝙡𝙠 𝘾𝙝𝙖𝙣𝙜𝙚𝙨\n"
        f"✅ 𝙐𝙥 𝙩𝙤 {BULK_MAX_ACCOUNTS:,} 𝙖𝙘𝙘𝙤𝙪𝙣𝙩𝙨/𝙗𝙖𝙩𝙘𝙝\n"
        f"✅ 𝘿𝙪𝙖𝙡 𝙆𝙚𝙮 𝙍𝙤𝙩𝙖𝙩𝙞𝙤𝙣\n"
        f"✅ 𝘼𝙪𝙩𝙤-𝙧𝙚𝙩𝙧𝙮\n"
        f"✅ 𝙋𝙧𝙞𝙤𝙧𝙞𝙩𝙮 𝙎𝙪𝙥𝙥𝙤𝙧𝙩\n"
        f"✅ 𝙉𝙤 𝙀𝙭𝙥𝙞𝙧𝙮\n\n"
        f"🛒 𝘾𝙡𝙞𝙘𝙠 𝙗𝙚𝙡𝙤𝙬 𝙩𝙤 𝙥𝙖𝙮:"
    )
    keyboard = [[
        InlineKeyboardButton(f"💳 𝙋𝘼𝙔 {PLAN_UNLIMITED_STARS} 𝙎𝙩𝙖𝙧𝙨", callback_data="buy_unlimited")
    ], [
        InlineKeyboardButton("❌ 𝘾𝘼𝙉𝘾𝙀𝙇", callback_data="nav_cancel")
    ]]
    await q.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def buy_single(update, context):
    q = update.callback_query
    await q.answer()
    prices = [LabeledPrice("1x Bulk Plan", PLAN_SINGLE_STARS)]
    await context.bot.send_invoice(
        chat_id=q.from_user.id,
        title="⭐ 1x Bulk Account Changer",
        description="1 time use of bulk account changer for CPM1/CPM2",
        payload=INVOICE_PAYLOAD_SINGLE,
        provider_token=PAYMENT_PROVIDER_TOKEN,
        currency="XTR",
        prices=prices,
        start_parameter="buy_single"
    )

async def buy_unlimited(update, context):
    q = update.callback_query
    await q.answer()
    prices = [LabeledPrice("Unlimited Bulk Plan", PLAN_UNLIMITED_STARS)]
    await context.bot.send_invoice(
        chat_id=q.from_user.id,
        title="⭐ Unlimited Bulk Account Changer",
        description="Unlimited bulk account changes for CPM1/CPM2",
        payload=INVOICE_PAYLOAD_UNLIMITED,
        provider_token=PAYMENT_PROVIDER_TOKEN,
        currency="XTR",
        prices=prices,
        start_parameter="buy_unlimited"
    )

async def precheckout(update, context):
    q = update.pre_checkout_query
    if q.invoice_payload in (INVOICE_PAYLOAD_SINGLE, INVOICE_PAYLOAD_UNLIMITED):
        await q.answer(ok=True)
    else:
        await q.answer(ok=False, error_message="Invalid payment payload")

async def payment_success(update, context):
    payment = update.message.successful_payment
    user_id = update.effective_user.id
    if payment.invoice_payload == INVOICE_PAYLOAD_SINGLE:
        set_user_plan(user_id, PLAN_SINGLE, 1)
        add_stars_spent(user_id, PLAN_SINGLE_STARS)
        log_user_action(user_id, "PAYMENT", f"Single plan purchased for {PLAN_SINGLE_STARS} stars")
        keyboard = [[InlineKeyboardButton("🚀 𝙎𝙩𝙖𝙧𝙩 𝘽𝙪𝙡𝙠", callback_data="start_bulk")]]
        await update.message.reply_text(
            f"╔══════════════════════╗\n"
            f"💎 𝙋𝘼𝙔𝙈𝙀𝙉𝙏 𝙎𝙐𝘾𝘾𝙀𝙎𝙎! 💎\n"
            f"╚══════════════════════╝\n\n"
            f"✅ 𝙋𝙡𝙖𝙣: 1𝙭 𝘽𝙪𝙡𝙠 𝘾𝙝𝙖𝙣𝙜𝙚\n"
            f"⭐ 𝙎𝙩𝙖𝙧𝙨: {PLAN_SINGLE_STARS}\n"
            f"🎯 𝙐𝙨𝙚𝙨: 1\n\n"
            f"🚀 𝘾𝙡𝙞𝙘𝙠 𝙗𝙚𝙡𝙤𝙬 𝙩𝙤 𝙨𝙩𝙖𝙧𝙩!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    elif payment.invoice_payload == INVOICE_PAYLOAD_UNLIMITED:
        set_user_plan(user_id, PLAN_UNLIMITED, 0)
        add_stars_spent(user_id, PLAN_UNLIMITED_STARS)
        log_user_action(user_id, "PAYMENT", f"Unlimited plan purchased for {PLAN_UNLIMITED_STARS} stars")
        keyboard = [[InlineKeyboardButton("🚀 𝙎𝙩𝙖𝙧𝙩 𝘽𝙪𝙡𝙠", callback_data="start_bulk")]]
        await update.message.reply_text(
            f"╔══════════════════════╗\n"
            f"💎 𝙋𝘼𝙔𝙈𝙀𝙉𝙏 𝙎𝙐𝘾𝘾𝙀𝙎𝙎! 💎\n"
            f"╚══════════════════════╝\n\n"
            f"✅ 𝙋𝙡𝙖𝙣: 𝙐𝙣𝙡𝙞𝙢𝙞𝙩𝙚𝙙 𝘽𝙪𝙡𝙠\n"
            f"⭐ 𝙎𝙩𝙖𝙧𝙨: {PLAN_UNLIMITED_STARS}\n"
            f"🎯 𝙐𝙨𝙚𝙨: 𝙐𝙣𝙡𝙞𝙢𝙞𝙩𝙚𝙙\n\n"
            f"🚀 𝘾𝙡𝙞𝙘𝙠 𝙗𝙚𝙡𝙤𝙬 𝙩𝙤 𝙨𝙩𝙖𝙧𝙩!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ============================================================
# ADMIN PANEL
# ============================================================

async def admin_panel(update, context):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        if update.message:
            await update.message.reply_text("🚫 𝙔𝙊𝙐 𝘼𝙍𝙀 𝙉𝙊𝙏 𝘼𝙉 𝘼𝘿𝙈𝙄𝙉")
        return

    total, banned, active_today = get_stats()
    text = (
        f"╔══════════════════════╗\n"
        f"   ⚡😈 𝘼𝘿𝙈𝙄𝙉 𝙋𝘼𝙉𝙀𝙇 😈⚡\n"
        f"╚══════════════════════╝\n\n"
        f"📊 𝙏𝙊𝙏𝘼𝙇 𝙐𝙎𝙀𝙍𝙎: {total}\n"
        f"🚫 𝘽𝘼𝙉𝙉𝙀𝘿: {banned}\n"
        f"✅ 𝘼𝘾𝙏𝙄𝙑𝙀 𝙏𝙊𝘿𝘼𝙔: {active_today}\n\n"
        f"🎯 𝙎𝙀𝙇𝙀𝘾𝙏 𝙊𝙋𝙏𝙄𝙊𝙉:"
    )
    keyboard = [
        [InlineKeyboardButton("📋 𝗨𝗦𝗘𝗥 𝗟𝗜𝗦𝗧", callback_data="admin_users")],
        [InlineKeyboardButton("🚫 𝗕𝗔𝗡𝗡𝗘𝗗 𝗨𝗦𝗘𝗥𝗦", callback_data="admin_banned")],
        [InlineKeyboardButton("📢 𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧", callback_data="admin_broadcast")],
        [InlineKeyboardButton("📊 𝗦𝗧𝗔𝗧𝗦", callback_data="admin_stats")],
        [InlineKeyboardButton("⚡ 𝗚𝗥𝗔𝗡𝗧 𝗕𝗨𝗟𝗞 𝗕𝗬 𝗜𝗗", callback_data="admin_grant_bulk")],
        [InlineKeyboardButton("⚡ 𝗕𝗨𝗟𝗞 𝗔𝗖𝗖𝗢𝗨𝗡𝗧 𝗖𝗛𝗔𝗡𝗚𝗘𝗥 ⚡", callback_data="open_bulk")]
    ]
    if is_super_admin(update.effective_user.id):
        keyboard.append([InlineKeyboardButton("👑 𝗔𝗗𝗗 𝗔𝗗𝗠𝗜𝗡 𝗠𝗘𝗠𝗕𝗘𝗥", callback_data="admin_add_member")])

    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        try:
            await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception:
            await update.callback_query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_user_list(update, context):
    q = update.callback_query
    await q.answer("Loading...")
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await q.message.reply_text("🚫 𝘼𝘿𝙈𝙄𝙉 𝙊𝙉𝙇𝙔")
        return

    try:
        await q.message.edit_text("⏳ 𝙇𝙊𝘼𝘿𝙄𝙉𝙂 𝙐𝙎𝙀𝙍𝙎...")
    except:
        pass

    users = get_all_users()
    if not users:
        try:
            await q.message.edit_text("❌ 𝙉𝙊 𝙐𝙎𝙀𝙍𝙎 𝙁𝙊𝙐𝙉𝘿")
        except Exception:
            await q.message.reply_text("❌ 𝙉𝙊 𝙐𝙎𝙀𝙍𝙎 𝙁𝙊𝙐𝙉𝘿")
        return

    users.sort(key=lambda x: x[3] if x[3] != "N/A" else "", reverse=True)
    context.user_data["admin_users"] = users
    context.user_data["admin_page"] = 0
    context.user_data.pop("is_search", None)
    context.user_data.pop("search_query", None)
    await show_user_choose_page(q.message, context)

async def show_user_choose_page(message, context, is_search=False):
    users = context.user_data.get("admin_users", [])
    page = context.user_data.get("admin_page", 0)
    per_page = 5
    total_pages = max(1, (len(users) + per_page - 1) // per_page)
    page = min(max(page, 0), total_pages - 1)
    context.user_data["admin_page"] = page
    start = page * per_page
    end = start + per_page
    page_users = users[start:end]

    title = "🔍 𝙎𝙀𝘼𝙍𝘾𝙃 𝙍𝙀𝙎𝙐𝙇𝙏𝙎" if is_search else "📋 𝘾𝙃𝙊𝙊𝙎𝙀 𝘼 𝙐𝙎𝙀𝙍"
    text = f"{title} (𝙋𝙖𝙜𝙚 {page + 1}/{total_pages})\n"
    text += f"👥 𝙏𝙤𝙩𝙖𝙡: {len(users)} 𝙪𝙨𝙚𝙧𝙨\n"
    text += "━" * 20 + "\n\n"

    keyboard = []
    keyboard.append([InlineKeyboardButton("🔍 𝗦𝗘𝗔𝗥𝗖𝗛 𝗨𝗦𝗘𝗥", callback_data="admin_search")])

    for idx, (uid, name, username, last_used, use_count) in enumerate(page_users, start=1):
        status = "🚫" if is_banned(uid) else "✅"
        text += f"{idx}. {status} {name}\n"
        text += f"   🆔 {uid} | 📊 {use_count}x\n"
        text += f"   👤 @{username} | 📅 {last_used}\n\n"
        ban_status = "🚫 BANNED" if is_banned(uid) else "✅ ACTIVE"
        keyboard.append([InlineKeyboardButton(
            f"{idx}. 👤 {name} ({ban_status})",
            callback_data=f"choose_user_{uid}"
        )])

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅️ 𝗣𝗥𝗘𝗩", callback_data="user_prev"))
    if end < len(users):
        nav_row.append(InlineKeyboardButton("➡️ 𝗡𝗘𝗫𝗧", callback_data="user_next"))
    if nav_row:
        keyboard.append(nav_row)
    if is_search:
        keyboard.append([InlineKeyboardButton("🔍 𝗦𝗘𝗔𝗥𝗖𝗛 𝗔𝗚𝗔𝗜𝗡", callback_data="admin_search")])
    keyboard.append([InlineKeyboardButton("🔙 𝗕𝗔𝗖𝗞 𝗧𝗢 𝗔𝗗𝗠𝗜𝗡", callback_data="admin_back")])

    try:
        await message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception:
        try:
            await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception as e2:
            print(f"Show user choose page error: {e2}")

async def user_page_nav(update, context):
    q = update.callback_query
    await q.answer()
    action = q.data
    current_page = context.user_data.get("admin_page", 0)
    if action == "user_prev":
        context.user_data["admin_page"] = max(0, current_page - 1)
    elif action == "user_next":
        context.user_data["admin_page"] = current_page + 1
    is_search = context.user_data.get("is_search", False)
    await show_user_choose_page(q.message, context, is_search=is_search)

async def admin_search_start(update, context):
    q = update.callback_query
    await q.answer("Search mode")
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await q.message.reply_text("🚫 𝘼𝘿𝙈𝙄𝙉 𝙊𝙉𝙇𝙔")
        return ConversationHandler.END

    text = (
        "🔍 𝙎𝙀𝘼𝙍𝘾𝙃 𝙐𝙎𝙀𝙍\n\n"
        "📝 𝙏𝙔𝙋𝙀 𝙩𝙤 𝙨𝙚𝙖𝙧𝙘𝙝:\n"
        "• 𝙉𝙖𝙢𝙚 (𝙚.𝙜. 𝙅𝙤𝙝𝙣)\n"
        "• 𝙐𝙨𝙚𝙧𝙣𝙖𝙢𝙚 (𝙚.𝙜. @𝙟𝙤𝙝𝙣)\n"
        "• 𝙐𝙨𝙚𝙧 𝙄𝘿 (𝙚.𝙜. 123456789)\n\n"
        "❌ 𝘾𝙖𝙣𝙘𝙚𝙡 𝙠𝙚 𝙡𝙞𝙮𝙚 /𝙘𝙖𝙣𝙘𝙚𝙡 𝙡𝙞𝙠𝙝𝙤"
    )
    keyboard = [[InlineKeyboardButton("❌ 𝗖𝗔𝗡𝗖𝗘𝗟", callback_data="admin_back")]]
    try:
        await q.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception:
        await q.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return ADMIN_SEARCH_INPUT

async def admin_search_process(update, context):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("🚫 𝘼𝘿𝙈𝙄𝙉 𝙊𝙉𝙇𝙔")
        return ConversationHandler.END

    query = update.message.text.lower().strip()
    users = get_all_users()
    results = [
        (uid, name, username, last_used, use_count)
        for uid, name, username, last_used, use_count in users
        if query in str(uid).lower() or query in name.lower()
        or query in username.lower() or query in f"@{username}".lower()
    ]

    if not results:
        keyboard = [
            [InlineKeyboardButton("🔍 𝗦𝗘𝗔𝗥𝗖𝗛 𝗔𝗚𝗔𝗜𝗡", callback_data="admin_search")],
            [InlineKeyboardButton("🔙 𝗕𝗔𝗖𝗞", callback_data="admin_back")]
        ]
        await update.message.reply_text(
            "❌ 𝙉𝙊 𝙐𝙎𝙀𝙍𝙎 𝙁𝙊𝙐𝙉𝘿\n\n𝙏𝙧𝙮 𝙙𝙞𝙛𝙛𝙚𝙧𝙚𝙣𝙩 𝙨𝙚𝙖𝙧𝙘𝙝 𝙩𝙚𝙧𝙢𝙨.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ConversationHandler.END

    context.user_data["admin_users"] = results
    context.user_data["admin_page"] = 0
    context.user_data["is_search"] = True
    context.user_data["search_query"] = query
    await show_user_choose_page(update.message, context, is_search=True)
    return ConversationHandler.END

async def choose_user_action(update, context):
    q = update.callback_query
    await q.answer()
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await q.message.reply_text("🚫 𝘼𝘿𝙈𝙄𝙉 𝙊𝙉𝙇𝙔")
        return

    target_id = q.data.replace("choose_user_", "")
    user_data = fb_get(f"users/{target_id}") or {}
    if not user_data:
        await q.answer("❌ User not found!", show_alert=True)
        return

    context.user_data["selected_user_id"] = target_id
    context.user_data["selected_user_name"] = user_data.get("name", "Unknown")

    name = user_data.get("name", "Unknown")
    username = user_data.get("username", "N/A")
    last_used = user_data.get("last_used", "N/A")
    use_count = user_data.get("use_count", 0)
    is_banned_status = is_banned(int(target_id))

    plan = get_user_plan(int(target_id))
    current_plan = plan["plan"].upper() if plan["plan"] != PLAN_NONE else "❌ 𝙉𝙊𝙉𝙀"
    uses_left = plan["uses_remaining"] if plan["plan"] == PLAN_SINGLE else ("♾️" if plan["plan"] == PLAN_UNLIMITED else "0")

    text = (
        f"╔══════════════════════╗\n"
        f"       👤 𝙐𝙎𝙀𝙍 𝘿𝙀𝙏𝘼𝙄𝙇𝙎\n"
        f"╚══════════════════════╝\n\n"
        f"📛 𝙉𝘼𝙈𝙀: {name}\n"
        f"👤 𝙐𝙎𝙀𝙍𝙉𝘼𝙈𝙀: @{username}\n"
        f"🆔 𝙄𝘿: {target_id}\n"
        f"📊 𝙐𝙎𝙀 𝘾𝙊𝙐𝙉𝙏: {use_count}x\n"
        f"📅 𝙇𝘼𝙎𝙏 𝙐𝙎𝙀𝘿: {last_used}\n\n"
        f"𝙎𝙏𝘼𝙏𝙐𝙎: {'🚫 𝘽𝘼𝙉𝙉𝙀𝘿' if is_banned_status else '✅ 𝘼𝘾𝙏𝙄𝙑𝙀'}\n"
        f"⚡ 𝘽𝙐𝙇𝙆 𝙋𝙇𝘼𝙉: {current_plan} ({uses_left} 𝙪𝙨𝙚𝙨)\n\n"
        f"🎯 𝙎𝙀𝙇𝙀𝘾𝙏 𝘼𝘾𝙏𝙄𝙊𝙉:"
    )
    keyboard = []
    if is_banned_status:
        keyboard.append([InlineKeyboardButton("✅ 𝗨𝗡𝗕𝗔𝗡 𝗨𝗦𝗘𝗥", callback_data=f"act_unban_{target_id}")])
    else:
        keyboard.append([InlineKeyboardButton("🚫 𝗕𝗔𝗡 𝗨𝗦𝗘𝗥", callback_data=f"act_ban_{target_id}")])
    keyboard.append([InlineKeyboardButton("💬 𝗦𝗘𝗡𝗗 𝗠𝗘𝗦𝗦𝗔𝗚𝗘", callback_data=f"act_msg_{target_id}")])
    keyboard.append([InlineKeyboardButton("⚡ 𝗚𝗥𝗔𝗡𝗧 𝗕𝗨𝗟𝗞 𝗔𝗖𝗖𝗘𝗦𝗦", callback_data=f"act_grant_bulk_{target_id}")])
    keyboard.append([InlineKeyboardButton("📋 𝗨𝗦𝗘𝗥 𝗟𝗢𝗚𝗦", callback_data=f"user_logs_{target_id}")])
    keyboard.append([InlineKeyboardButton("🔙 𝗕𝗔𝗖𝗞 𝗧𝗢 𝗟𝗜𝗦𝗧", callback_data="admin_users")])
    keyboard.append([InlineKeyboardButton("🏠 𝗔𝗗𝗠𝗜𝗡 𝗛𝗢𝗠𝗘", callback_data="admin_back")])

    try:
        await q.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception:
        await q.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def grant_bulk_menu(update, context):
    q = update.callback_query
    await q.answer()
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await q.message.reply_text("🚫 𝘼𝘿𝙈𝙄𝙉 𝙊𝙉𝙇𝙔")
        return

    target_id = q.data.replace("act_grant_bulk_", "")
    target_data = fb_get(f"users/{target_id}") or {}
    name = target_data.get("name", "Unknown")

    plan = get_user_plan(int(target_id))
    current_plan = plan["plan"].upper() if plan["plan"] != PLAN_NONE else "❌ 𝙉𝙊𝙉𝙀"
    uses = plan["uses_remaining"] if plan["plan"] == PLAN_SINGLE else ("♾️" if plan["plan"] == PLAN_UNLIMITED else "0")

    text = (
        f"╔══════════════════════╗\n"
        f"   ⚡ 𝙂𝙍𝘼𝙉𝙏 𝘽𝙐𝙇𝙆 𝘼𝘾𝘾𝙀𝙎𝙎\n"
        f"╚══════════════════════╝\n\n"
        f"👤 𝙐𝙨𝙚𝙧: {name}\n"
        f"🆔 𝙄𝘿: {target_id}\n\n"
        f"📊 𝘾𝙪𝙧𝙧𝙚𝙣𝙩 𝙋𝙡𝙖𝙣: {current_plan}\n"
        f"🔢 𝙐𝙨𝙚𝙨 𝙇𝙚𝙛𝙩: {uses}\n\n"
        f"🎯 𝙎𝙚𝙡𝙚𝙘𝙩 𝙋𝙡𝙖𝙣 𝙩𝙤 𝙂𝙧𝙖𝙣𝙩:"
    )

    keyboard = [
        [InlineKeyboardButton("♾️ 𝙐𝙉𝙇𝙄𝙈𝙄𝙏𝙀𝘿", callback_data=f"grant_bulk_{target_id}_unlimited")],
        [InlineKeyboardButton("1️⃣ 1 𝙐𝙎𝙀", callback_data=f"grant_bulk_{target_id}_single")],
        [InlineKeyboardButton("5️⃣ 5 𝙐𝙎𝙀𝙎", callback_data=f"grant_bulk_{target_id}_5x")],
        [InlineKeyboardButton("🔟 10 𝙐𝙎𝙀𝙎", callback_data=f"grant_bulk_{target_id}_10x")],
        [InlineKeyboardButton("5️⃣0️⃣ 50 𝙐𝙎𝙀𝙎", callback_data=f"grant_bulk_{target_id}_50x")],
        [InlineKeyboardButton("1️⃣0️⃣0️⃣ 100 𝙐𝙎𝙀𝙎", callback_data=f"grant_bulk_{target_id}_100x")],
        [InlineKeyboardButton("🔴 𝙍𝙀𝙑𝙊𝙆𝙀 𝘼𝘾𝘾𝙀𝙎𝙎", callback_data=f"grant_bulk_{target_id}_revoke")],
        [InlineKeyboardButton("🔙 𝘽𝘼𝘾𝙆", callback_data=f"choose_user_{target_id}")]
    ]

    try:
        await q.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception:
        await q.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def grant_bulk_execute(update, context):
    q = update.callback_query
    await q.answer()
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await q.message.reply_text("🚫 𝘼𝘿𝙈𝙄𝙉 𝙊𝙉𝙇𝙔")
        return

    match = re.match(r"^grant_bulk_(\d+)_(.+)$", q.data)
    if not match:
        await q.answer("❌ Invalid callback data", show_alert=True)
        return

    target_id = match.group(1)
    plan_type = match.group(2)

    target_data = fb_get(f"users/{target_id}") or {}
    name = target_data.get("name", "Unknown")
    admin_name = update.effective_user.full_name

    try:
        if plan_type == "revoke":
            fb_patch(f"users/{target_id}", {
                "bulk_plan": PLAN_NONE,
                "bulk_uses_remaining": 0
            })
            msg = (
                f"╔══════════════════════╗\n"
                f"  🔴 𝘽𝙐𝙇𝙆 𝘼𝘾𝘾𝙀𝙎𝙎 𝙍𝙀𝙑𝙊𝙆𝙀𝘿\n"
                f"╚══════════════════════╝\n\n"
                f"👤 𝙐𝙨𝙚𝙧: {name}\n"
                f"🆔 𝙄𝘿: {target_id}\n\n"
                f"✅ 𝘼𝙘𝙘𝙚𝙨𝙨 𝙝𝙖𝙨 𝙗𝙚𝙚𝙣 𝙧𝙚𝙫𝙤𝙠𝙚𝙙."
            )
            user_msg = (
                f"╔══════════════════════╗\n"
                f"   ⚠️ 𝘽𝙐𝙇𝙆 𝘼𝘾𝘾𝙀𝙎𝙎 𝙍𝙀𝙑𝙊𝙆𝙀𝘿\n"
                f"╚══════════════════════╝\n\n"
                f"𝙔𝙤𝙪𝙧 𝙗𝙪𝙡𝙠 𝙖𝙘𝙘𝙤𝙪𝙣𝙩 𝙘𝙝𝙖𝙣𝙜𝙚𝙧 𝙖𝙘𝙘𝙚𝙨𝙨 𝙝𝙖𝙨 𝙗𝙚𝙚𝙣 𝙧𝙚𝙫𝙤𝙠𝙚𝙙 𝙗𝙮 𝙖𝙙𝙢𝙞𝙣.\n\n"
                f"🛒 𝙋𝙪𝙧𝙘𝙝𝙖𝙨𝙚 𝙖 𝙥𝙡𝙖𝙣 𝙩𝙤 𝙪𝙨𝙚 𝙖𝙜𝙖𝙞𝙣."
            )
        elif plan_type == "unlimited":
            set_user_plan(int(target_id), PLAN_UNLIMITED, 999999)
            msg = (
                f"╔══════════════════════╗\n"
                f"    ♾️ 𝙐𝙉𝙇𝙄𝙈𝙄𝙏𝙀𝘿 𝙂𝙍𝘼𝙉𝙏𝙀𝘿\n"
                f"╚══════════════════════╝\n\n"
                f"👤 𝙐𝙨𝙚𝙧: {name}\n"
                f"🆔 𝙄𝘿: {target_id}\n\n"
                f"✅ 𝙐𝙨𝙚𝙧 𝙘𝙖𝙣 𝙣𝙤𝙬 𝙪𝙨𝙚 /𝙗𝙪𝙡𝙠 𝙪𝙣𝙡𝙞𝙢𝙞𝙩𝙚𝙙 𝙩𝙞𝙢𝙚𝙨."
            )
            user_msg = (
                f"╔══════════════════════╗\n"
                f"   🎉 𝘽𝙐𝙇𝙆 𝘼𝘾𝘾𝙀𝙎𝙎 𝙂𝙍𝘼𝙉𝙏𝙀𝘿!\n"
                f"╚══════════════════════╝\n\n"
                f"📦 𝙋𝙡𝙖𝙣: 𝙐𝙉𝙇𝙄𝙈𝙄𝙏𝙀𝘿\n"
                f"⚡ 𝙔𝙤𝙪 𝙘𝙖𝙣 𝙣𝙤𝙬 𝙪𝙨𝙚 /𝙗𝙪𝙡𝙠\n\n"
                f"𝙀𝙣𝙟𝙤𝙮!"
            )
        else:
            uses = 1
            if plan_type.endswith("x"):
                try:
                    uses = int(plan_type[:-1])
                except ValueError:
                    uses = 1

            set_user_plan(int(target_id), PLAN_SINGLE, uses)
            msg = (
                f"╔══════════════════════╗\n"
                f"  ✅ 𝘽𝙐𝙇𝙆 𝘼𝘾𝘾𝙀𝙎𝙎 𝙂𝙍𝘼𝙉𝙏𝙀𝘿\n"
                f"╚══════════════════════╝\n\n"
                f"👤 𝙐𝙨𝙚𝙧: {name}\n"
                f"🆔 𝙄𝘿: {target_id}\n"
                f"📦 𝙋𝙡𝙖𝙣: {uses} 𝙐𝙨𝙚𝙨\n\n"
                f"✅ 𝙐𝙨𝙚𝙧 𝙘𝙖𝙣 𝙣𝙤𝙬 𝙪𝙨𝙚 /𝙗𝙪𝙡𝙠."
            )
            user_msg = (
                f"╔══════════════════════╗\n"
                f"  🎉 𝘽𝙐𝙇𝙆 𝘼𝘾𝘾𝙀𝙎𝙎 𝙂𝙍𝘼𝙉𝙏𝙀𝘿!\n"
                f"╚══════════════════════╝\n\n"
                f"📦 𝙋𝙡𝙖𝙣: {uses} 𝙐𝙨𝙚𝙨\n"
                f"⚡ 𝙔𝙤𝙪 𝙘𝙖𝙣 𝙣𝙤𝙬 𝙪𝙨𝙚 /𝙗𝙪𝙡𝙠\n\n"
                f"𝙀𝙣𝙟𝙤𝙮!"
            )

        # Notify user
        try:
            await context.bot.send_message(chat_id=int(target_id), text=user_msg)
        except Exception as e:
            msg += f"\n\n⚠️ 𝘾𝙤𝙪𝙡𝙙 𝙣𝙤𝙩 𝙣𝙤𝙩𝙞𝙛𝙮 𝙪𝙨𝙚𝙧: {str(e)}"

        keyboard = [[InlineKeyboardButton("🔙 𝘽𝘼𝘾𝙆", callback_data=f"choose_user_{target_id}")]]
        try:
            await q.message.edit_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception:
            await q.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

    except Exception as e:
        await q.answer(f"❌ 𝙀𝙧𝙧𝙤𝙧: {str(e)}", show_alert=True)

async def ban_user_button(update, context):
    q = update.callback_query
    await q.answer()
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await q.message.reply_text("🚫 𝘼𝘿𝙈𝙄𝙉 𝙊𝙉𝙇𝙔")
        return
    target_id = q.data.replace("act_ban_", "")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_data = fb_get(f"users/{target_id}")
    if not user_data:
        await q.answer("❌ User not found!", show_alert=True)
        return
    fb_put(f"banned_users/{target_id}", {"banned_at": now, "banned_by": user_id, "reason": "Banned via Admin Panel"})
    await q.answer(f"🚫 Banned {user_data.get('name', 'Unknown')}!", show_alert=True)
    await choose_user_action(update, context)

async def unban_user_button(update, context):
    q = update.callback_query
    await q.answer()
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await q.message.reply_text("🚫 𝘼𝘿𝙈𝙄𝙉 𝙊𝙉𝙇𝙔")
        return
    target_id = q.data.replace("act_unban_", "")
    user_data = fb_get(f"users/{target_id}") or {}
    fb_delete(f"banned_users/{target_id}")
    await q.answer(f"✅ Unbanned {user_data.get('name', 'Unknown')}!", show_alert=True)
    await choose_user_action(update, context)

async def msg_user_button(update, context):
    q = update.callback_query
    await q.answer()
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await q.message.reply_text("🚫 𝘼𝘿𝙈𝙄𝙉 𝙊𝙉𝙇𝙔")
        return ConversationHandler.END

    target_id_str = q.data.replace("act_msg_", "")
    try:
        target_id = int(target_id_str)
    except ValueError:
        await q.answer("❌ Invalid user ID!", show_alert=True)
        return ConversationHandler.END

    user_data = fb_get(f"users/{target_id_str}")
    if not user_data:
        await q.answer("❌ User not found!", show_alert=True)
        return ConversationHandler.END

    context.user_data["msg_target_id"] = target_id
    context.user_data["msg_target_name"] = user_data.get("name", "Unknown")

    text = (
        f"💬 𝙈𝙀𝙎𝙎𝘼𝙂𝙀 𝙏𝙊: {user_data.get('name', 'Unknown')}\n"
        f"🆔 𝙄𝘿: {target_id}\n\n"
        f"📝 𝙏𝙔𝙋𝙀 𝙔𝙊𝙐𝙍 𝙈𝙀𝙎𝙎𝘼𝙂𝙀:"
    )
    keyboard = [[InlineKeyboardButton("❌ 𝗖𝗔𝗡𝗖𝗘𝗟", callback_data=f"choose_user_{target_id}")]]
    try:
        await q.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception:
        await q.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return ADMIN_MSG_INPUT

async def msg_user_send(update, context):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("🚫 𝘼𝘿𝙈𝙄𝙉 𝙊𝙉𝙇𝙔")
        return ConversationHandler.END

    target_id = context.user_data.get("msg_target_id")
    target_name = context.user_data.get("msg_target_name", "Unknown")
    message = update.message.text

    if not target_id:
        await update.message.reply_text("❌ 𝙉𝙊 𝙏𝘼𝙍𝙂𝙀𝙏 𝙐𝙎𝙀𝙍 𝙎𝙀𝙇𝙀𝘾𝙏𝙀𝘿")
        return ConversationHandler.END

    try:
        await context.bot.send_message(
            chat_id=int(target_id),
            text=(
                f"╔══════════════════════╗\n"
                f"   💬 𝙋𝙀𝙍𝙎𝙊𝙉𝘼𝙇 𝙈𝙀𝙎𝙎𝘼𝙂𝙀 💬\n"
                f"╚══════════════════════╝\n\n"
                f"{message}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"📨 𝙎𝙚𝙣𝙩 𝙗𝙮 𝘼𝙙𝙢𝙞𝙣\n"
                f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
        )
        await update.message.reply_text(
            f"✅ 𝙈𝙀𝙎𝙎𝘼𝙂𝙀 𝙎𝙀𝙉𝙏!\n\n"
            f"👤 𝙏𝙊: {target_name}\n"
            f"🆔 𝙄𝘿: {target_id}"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ 𝙀𝙍𝙍𝙊𝙍: {str(e)}")

    context.user_data.pop("msg_target_id", None)
    context.user_data.pop("msg_target_name", None)
    return ConversationHandler.END

async def admin_banned_list(update, context):
    q = update.callback_query
    await q.answer()
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await q.message.reply_text("🚫 𝘼𝘿𝙈𝙄𝙉 𝙊𝙉𝙇𝙔")
        return

    banned = get_banned_users()
    if not banned:
        try:
            await q.message.edit_text("✅ 𝙉𝙊 𝘽𝘼𝙉𝙉𝙀𝘿 𝙐𝙎𝙀𝙍𝙎")
        except Exception:
            await q.message.reply_text("✅ 𝙉𝙊 𝘽𝘼𝙉𝙉𝙀𝘿 𝙐𝙎𝙀𝙍𝙎")
        return

    text = "🚫 𝘽𝘼𝙉𝙉𝙀𝘿 𝙐𝙎𝙀𝙍𝙎:\n\n"
    keyboard = []
    for uid, ban_data in banned[:15]:
        user_data = fb_get(f"users/{uid}") or {}
        name = user_data.get("name", "Unknown")
        banned_at = ban_data.get("banned_at", "N/A") if isinstance(ban_data, dict) else "N/A"
        reason = ban_data.get("reason", "N/A") if isinstance(ban_data, dict) else "N/A"
        text += f"🚫 {name}\n🆔 {uid}\n📌 {reason}\n🕐 {banned_at}\n\n"
        keyboard.append([InlineKeyboardButton(f"✅ 𝗨𝗡𝗕𝗔𝗡 {name}", callback_data=f"act_unban_{uid}")])
    keyboard.append([InlineKeyboardButton("🔙 𝗕𝗔𝗖𝗞", callback_data="admin_back")])

    try:
        await q.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception:
        await q.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_broadcast_start(update, context):
    q = update.callback_query
    await q.answer()
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await q.message.reply_text("🚫 𝘼𝘿𝙈𝙄𝙉 𝙊𝙉𝙇𝙔")
        return ConversationHandler.END

    text = (
        "📢 𝘽𝙍𝙊𝘼𝘿𝘾𝘼𝙎𝙏 𝙈𝙊𝘿𝙀\n\n"
        "📝 𝙏𝙔𝙋𝙀 𝙔𝙊𝙐𝙍 𝙈𝙀𝙎𝙎𝘼𝙂𝙀:\n"
        "𝙀𝙉𝙏𝙀𝙍 𝙈𝙀𝙎𝙎𝘼𝙂𝙀 𝙁𝙊𝙍 𝘼𝙇𝙇 𝙐𝙎𝙀𝙍𝙎🫂\n\n"
        "❌ Send /cancel to cancel"
    )
    keyboard = [[InlineKeyboardButton("❌ 𝗖𝗔𝗡𝗖𝗘𝗟", callback_data="admin_back")]]
    try:
        await q.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception:
        await q.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return ADMIN_BROADCAST_INPUT

async def admin_broadcast_send(update, context):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("🚫 𝘼𝘿𝙈𝙄𝙉 𝙊𝙉𝙇𝙔")
        return ConversationHandler.END

    message = update.message.text
    users = get_all_users()
    sent = 0
    failed = 0
    valid_users = [u for u in users if isinstance(u[0], int) and u[0] > 0]

    if not valid_users:
        await update.message.reply_text("❌ 𝙉𝙊 𝙑𝘼𝙇𝙄𝘿 𝙐𝙎𝙀𝙍𝙎 𝙁𝙊𝙐𝙉𝘿")
        return ConversationHandler.END

    status_msg = await update.message.reply_text(f"📢 𝙎𝙀𝙉𝘿𝙄𝙉𝙂... 0/{len(valid_users)}")

    for i, user in enumerate(valid_users):
        uid = user[0]
        if not is_banned(uid):
            try:
                await context.bot.send_message(
                    chat_id=uid,
                    text=(
                        f"╔══════════════════════╗\n"
                        f"     📢 𝘼𝙉𝙉𝙊𝙐𝙉𝘾𝙀𝙈𝙀𝙉𝙏 📢\n"
                        f"╚══════════════════════╝\n\n"
                        f"{message}\n\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"📨 𝙎𝙚𝙣𝙩 𝙗𝙮 𝘼𝙙𝙢𝙞𝙣\n"
                        f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                    )
                )
                sent += 1
            except Exception as e:
                print(f"Broadcast failed for {uid}: {e}")
                failed += 1
        if i % 5 == 0:
            try:
                await status_msg.edit_text(f"📢 𝙎𝙀𝙉𝘿𝙄𝙉𝙂... {i+1}/{len(valid_users)}\n✅ 𝙎𝙚𝙣𝙩: {sent}\n❌ 𝙁𝙖𝙞𝙡𝙚𝙙: {failed}")
            except Exception:
                pass

    result = (
        f"✅ 𝘽𝙍𝙊𝘼𝘿𝘾𝘼𝙎𝙏 𝘾𝙊𝙈𝙋𝙇𝙀𝙏𝙀!\n\n"
        f"📨 𝙎𝙀𝙉𝙏: {sent}\n"
        f"❌ 𝙁𝘼𝙄𝙇𝙀𝘿: {failed}\n"
        f"👥 𝙏𝙊𝙏𝘼𝙇: {len(valid_users)}"
    )
    try:
        await status_msg.edit_text(result)
    except Exception:
        await update.message.reply_text(result)
    return ConversationHandler.END

async def admin_stats(update, context):
    q = update.callback_query
    await q.answer()
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await q.message.reply_text("🚫 𝘼𝘿𝙈𝙄𝙉 𝙊𝙉𝙇𝙔")
        return

    total, banned, active_today = get_stats()
    users = get_all_users()
    total_uses = sum(u[4] for u in users)

    text = (
        f"📊 𝙎𝙏𝘼𝙏𝙄𝙎𝙏𝙄𝘾𝙎\n\n"
        f"👥 𝙏𝙊𝙏𝘼𝙇 𝙐𝙎𝙀𝙍𝙎: {total}\n"
        f"🚫 𝘽𝘼𝙉𝙉𝙀𝘿: {banned}\n"
        f"✅ 𝘼𝘾𝙏𝙄𝙑𝙀 𝙏𝙊𝘿𝘼𝙔: {active_today}\n"
        f"📈 𝙍𝙀𝙏𝙀𝙉𝙏𝙄𝙊𝙉: {total - banned}\n"
        f"🔄 𝙏𝙊𝙏𝘼𝙇 𝙐𝙎𝙀𝙎: {total_uses}\n"
        f"📊 𝘼𝙑𝙂 𝙐𝙎𝙀𝙎/𝙐𝙎𝙀𝙍: {total_uses // max(total, 1)}"
    )
    keyboard = [[InlineKeyboardButton("🔙 𝗕𝗔𝗖𝗞", callback_data="admin_back")]]
    try:
        await q.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception:
        await q.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_back(update, context):
    q = update.callback_query
    await q.answer()
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await q.message.reply_text("🚫 𝘼𝘿𝙈𝙄𝙉 𝙊𝙉𝙇𝙔")
        return

    for key in ["admin_users", "admin_page", "msg_target_id", "msg_target_name",
                "selected_user_id", "selected_user_name", "is_search", "search_query"]:
        context.user_data.pop(key, None)

    total, banned, active_today = get_stats()
    text = (
        f"╔══════════════════════╗\n"
        f"    ⚡😈 𝘼𝘿𝙈𝙄𝙉 𝙋𝘼𝙉𝙀𝙇 😈⚡\n"
        f"╚══════════════════════╝\n\n"
        f"📊 𝙏𝙊𝙏𝘼𝙇 𝙐𝙎𝙀𝙍𝙎: {total}\n"
        f"🚫 𝘽𝘼𝙉𝙉𝙀𝘿: {banned}\n"
        f"✅ 𝘼𝘾𝙏𝙄𝙑𝙀 𝙏𝙊𝘿𝘼𝙔: {active_today}\n\n"
        f"🎯 𝙎𝙀𝙇𝙀𝘾𝙏 𝙊𝙋𝙏𝙄𝙊𝙉:"
    )
    keyboard = [
        [InlineKeyboardButton("📋 𝗨𝗦𝗘𝗥 𝗟𝗜𝗦𝗧", callback_data="admin_users")],
        [InlineKeyboardButton("🚫 𝗕𝗔𝗡𝗡𝗘𝗗 𝗨𝗦𝗘𝗥𝗦", callback_data="admin_banned")],
        [InlineKeyboardButton("📢 𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧", callback_data="admin_broadcast")],
        [InlineKeyboardButton("📊 𝗦𝗧𝗔𝗧𝗦", callback_data="admin_stats")],
        [InlineKeyboardButton("⚡ 𝗚𝗥𝗔𝗡𝗧 𝗕𝗨𝗟𝗞 𝗕𝗬 𝗜𝗗", callback_data="admin_grant_bulk")],
        [InlineKeyboardButton("⚡ 𝗕𝗨𝗟𝗞 𝗔𝗖𝗖𝗢𝗨𝗡𝗧 𝗖𝗛𝗔𝗡𝗚𝗘𝗥 ⚡", callback_data="open_bulk")]
    ]
    if is_super_admin(q.from_user.id):
        keyboard.append([InlineKeyboardButton("👑 𝗔𝗗𝗗 𝗔𝗗𝗠𝗜𝗡 𝗠𝗘𝗠𝗕𝗘𝗥", callback_data="admin_add_member")])
    try:
        await q.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception:
        await q.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# ============================================================
# ADD ADMIN MEMBER
# ============================================================

async def admin_add_member_start(update, context):
    q = update.callback_query
    await q.answer()
    user_id = update.effective_user.id
    if not is_super_admin(user_id):
        await q.answer("🚫 ACCESS DENIED!", show_alert=True)
        return ConversationHandler.END

    sub_admins = fb_get("sub_admins") or {}
    members_text = ""
    keyboard = []

    if sub_admins:
        for uid, info in sub_admins.items():
            name = info.get("name", "Unknown") if isinstance(info, dict) else "Unknown"
            added_at = info.get("added_at", "N/A") if isinstance(info, dict) else "N/A"
            members_text += f"👤 {name} | 🆔 {uid}\n📅 {added_at}\n\n"
            keyboard.append([InlineKeyboardButton(f"🗑️ Remove {name}", callback_data=f"remove_member_{uid}")])
    else:
        members_text = "No admin members yet\n\n"

    keyboard.append([InlineKeyboardButton("➕ 𝗔𝗗𝗗 𝗡𝗘𝗪 𝗠𝗘𝗠𝗕𝗘𝗥", callback_data="add_member_input")])
    keyboard.append([InlineKeyboardButton("🔙 𝗕𝗔𝗖𝗞", callback_data="admin_back")])

    text = (
        f"╔═════════════════════╗\n"
        f"     👑 𝘼𝘿𝙈𝙄𝙉 𝙈𝙀𝙈𝘽𝙀𝙍𝙎\n"
        f"╚═════════════════════╝\n\n"
        f"{members_text}━━━━━━━━━━━━━━━━━━━━\n"
        f"➕ 𝙏𝙊 𝘼𝘿𝘿 𝙉𝙀𝙒 𝙈𝙀𝙈𝘽𝙀𝙍\n"
        f"🗑️ 𝙏𝙊 𝙍𝙀𝙈𝙊𝙑𝙀 𝙈𝙀𝙈𝘽𝙀𝙍"
    )
    try:
        await q.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception:
        await q.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END

async def admin_remove_member(update, context):
    q = update.callback_query
    await q.answer()
    user_id = update.effective_user.id
    if not is_super_admin(user_id):
        await q.answer("🚫 ACCESS DENIED!", show_alert=True)
        return
    target_id = q.data.replace("remove_member_", "")
    user_data = fb_get(f"sub_admins/{target_id}") or {}
    name = user_data.get("name", "Unknown") if isinstance(user_data, dict) else "Unknown"
    fb_delete(f"sub_admins/{target_id}")
    await q.answer(f"✅ {name} removed!", show_alert=True)
    await admin_add_member_start(update, context)

async def admin_add_member_input_prompt(update, context):
    q = update.callback_query
    await q.answer()
    user_id = update.effective_user.id
    if not is_super_admin(user_id):
        await q.answer("🚫 ACCESS DENIED!", show_alert=True)
        return ConversationHandler.END

    text = (
        "╔══════════════════════╗\n"
        "     ➕ 𝘼𝘿𝘿 𝙉𝙀𝙒 𝙈𝙀𝙈𝘽𝙀𝙍\n"
        "╚══════════════════════╝\n\n"
        "📝 𝙎𝙀𝙉𝘿 𝙐𝙎𝙀𝙍 𝙏𝙂 𝙄𝘿:\n"
        "(𝙐𝙎𝙀𝙍 𝙈𝙐𝙎𝙏 𝙃𝘼𝙑𝙀 𝙐𝙎𝙀𝘿 𝘽𝙊𝙏 𝙁𝙄𝙍𝙎𝙏)\n\n"
        "🔢 𝙀𝙭𝙖𝙢𝙥𝙡𝙚: 123456789"
    )
    keyboard = [[InlineKeyboardButton("🔙 𝗕𝗔𝗖𝗞", callback_data="admin_add_member")]]
    try:
        await q.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception:
        await q.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return ADD_MEMBER_INPUT

async def admin_add_member_process(update, context):
    user_id = update.effective_user.id
    if not is_super_admin(user_id):
        await update.message.reply_text("🚫 𝘼𝘾𝘾𝙀𝙎𝙎 𝘿𝙀𝙉𝙄𝙀𝘿")
        return ConversationHandler.END

    raw = update.message.text.strip()
    if raw.startswith("-"):
        target_id = raw[1:].strip()
        fb_delete(f"sub_admins/{target_id}")
        await update.message.reply_text(f"✅ 𝘼𝘿𝙈𝙄𝙉 𝙈𝙀𝙈𝘽𝙀𝙍 𝙍𝙀𝙈𝙊𝙑𝙀𝘿\n🆔 ID: {target_id}")
        return ConversationHandler.END

    try:
        target_id = int(raw)
    except ValueError:
        await update.message.reply_text("❌ 𝙄𝙉𝙑𝘼𝙇𝙄𝘿 𝙄𝘿! 𝙀𝙣𝙩𝙚𝙧 𝙖 𝙫𝙖𝙡𝙞𝙙 𝙏𝙚𝙡𝙚𝙜𝙧𝙖𝙢 𝙐𝙨𝙚𝙧 𝙄𝘿 (𝙣𝙪𝙢𝙗𝙚𝙧𝙨 𝙤𝙣𝙡𝙮)")
        return ADD_MEMBER_INPUT

    user_data = fb_get(f"users/{target_id}") or {}
    name = user_data.get("name", "Unknown") if user_data else "Unknown"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fb_put(f"sub_admins/{target_id}", {"name": name, "added_by": user_id, "added_at": now})
    await update.message.reply_text(
        f"✅ 𝘼𝘿𝙈𝙄𝙉 𝘼𝘾𝘾𝙀𝙎𝙎 𝙂𝙍𝘼𝙉𝙏𝙀𝘿!\n\n"
        f"👤 𝙉𝘼𝙈𝙀: {name}\n"
        f"🆔 𝙄𝘿: {target_id}\n\n"
        f"ℹ️ 𝙏𝙤 𝙧𝙚𝙢𝙤𝙫𝙚: 𝙨𝙚𝙣𝙙 -{target_id}"
    )
    return ConversationHandler.END

async def admin_nav_fallback(update, context):
    q = update.callback_query
    await q.answer()
    data = q.data
    if data == "admin_back":
        await admin_back(update, context)
    elif data == "admin_users":
        await admin_user_list(update, context)
    elif data == "admin_banned":
        await admin_banned_list(update, context)
    elif data == "admin_stats":
        await admin_stats(update, context)
    elif data == "admin_search":
        pass
    elif data.startswith("choose_user_"):
        await choose_user_action(update, context)
    elif data.startswith("act_ban_"):
        await ban_user_button(update, context)
    elif data.startswith("act_unban_"):
        await unban_user_button(update, context)
    elif data in ("user_prev", "user_next"):
        await user_page_nav(update, context)
    else:
        await q.message.reply_text("❌ 𝙄𝙉𝙑𝘼𝙇𝙄𝘿 𝘼𝘾𝙏𝙄𝙊𝙉")
    return ConversationHandler.END

# ================= PAYMENT HANDLERS =================
async def bulk_payment_menu(update, context):
    q = update.callback_query
    await q.answer()

    user_id = update.effective_user.id
    plan = get_user_plan(user_id)

    text = (
        f"╔══════════════════════╗\n"
        f"        💎 𝘽𝙐𝙇𝙆 𝙋𝙇𝘼𝙉𝙎\n"
        f"╚══════════════════════╝\n\n"
        f"📊 𝙔𝙊𝙐𝙍 𝙎𝙏𝘼𝙏𝙐𝙎:\n"
        f"• 𝙋𝙡𝙖𝙣: {plan['plan'].upper() if plan['plan'] != PLAN_NONE else '❌ 𝙉𝙊𝙉𝙀'}\n"
        f"• 𝙐𝙨𝙚𝙨 𝙇𝙚𝙛𝙩: {plan['uses_remaining'] if plan['plan'] == PLAN_SINGLE else '♾️'}\n"
        f"• 𝙏𝙤𝙩𝙖𝙡 𝘼𝙘𝙘 𝙋𝙧𝙤𝙘𝙚𝙨𝙨𝙚𝙙: {plan['total_processed']}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🛒 𝘼𝙑𝘼𝙄𝙇𝘼𝘽𝙇𝙀 𝙋𝙇𝘼𝙉𝙎:\n\n"
        f"⭐ {PLAN_SINGLE_STARS} 𝙎𝙩𝙖𝙧𝙨 → 1 𝙏𝙞𝙢𝙚 𝘽𝙪𝙡𝙠\n"
        f"   ✅ 1 𝘽𝙪𝙡𝙠 𝙊𝙥𝙚𝙧𝙖𝙩𝙞𝙤𝙣\n"
        f"   ✅ 𝙈𝙖𝙭 10,000 𝘼𝙘𝙘𝙤𝙪𝙣𝙩𝙨\n\n"
        f"⭐ {PLAN_UNLIMITED_STARS} 𝙎𝙩𝙖𝙧𝙨 → 𝙐𝙣𝙡𝙞𝙢𝙞𝙩𝙚𝙙\n"
        f"   ✅ 𝙐𝙣𝙡𝙞𝙢𝙞𝙩𝙚𝙙 𝘽𝙪𝙡𝙠 𝘾𝙝𝙖𝙣𝙜𝙚𝙨\n"
        f"   ✅ 𝙈𝙖𝙭 10,000/𝙗𝙖𝙩𝙘𝙝\n"
        f"   ✅ 𝙇𝙞𝙛𝙚𝙩𝙞𝙢𝙚 𝘼𝙘𝙘𝙚𝙨𝙨\n\n"
        f"🎯 𝙎𝙀𝙇𝙀𝘾𝙏 𝙋𝙇𝘼𝙉:"
    )

    keyboard = [
        [InlineKeyboardButton(f"⭐ {PLAN_SINGLE_STARS} 𝙎𝙏𝘼𝙍𝙎 (1𝙭)", callback_data="buy_single")],
        [InlineKeyboardButton(f"⭐ {PLAN_UNLIMITED_STARS} 𝙎𝙏𝘼𝙍𝙎 (𝙐𝙉𝙇𝙄𝙈𝙄𝙏𝙀𝘿)", callback_data="buy_unlimited")],
        [InlineKeyboardButton("🔙 𝘽𝘼𝘾𝙆", callback_data="open_bulk")]
    ]

    try:
        await q.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception:
        await q.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def send_stars_invoice(update, context, plan_type):
    user_id = update.effective_user.id

    if plan_type == PLAN_UNLIMITED:
        title = "🔥 𝘽𝙪𝙡𝙠 𝘼𝙘𝙘𝙤𝙪𝙣𝙩 𝘾𝙝𝙖𝙣𝙜𝙚𝙧 - 𝙐𝙣𝙡𝙞𝙢𝙞𝙩𝙚𝙙"
        description = "𝙐𝙣𝙡𝙞𝙢𝙞𝙩𝙚𝙙 𝘽𝙪𝙡𝙠 𝘼𝙘𝙘𝙤𝙪𝙣𝙩 𝘾𝙝𝙖𝙣𝙜𝙚𝙨\n𝙈𝙖𝙭 10,000 𝙖𝙘𝙘𝙤𝙪𝙣𝙩𝙨 𝙥𝙚𝙧 𝙗𝙖𝙩𝙘𝙝\n𝙇𝙞𝙛𝙚𝙩𝙞𝙢𝙚 𝘼𝙘𝙘𝙚𝙨𝙨"
        payload = INVOICE_PAYLOAD_UNLIMITED
        price = PLAN_UNLIMITED_STARS
    else:
        title = "⚡ 𝘽𝙪𝙡𝙠 𝘼𝙘𝙘𝙤𝙪𝙣𝙩 𝘾𝙝𝙖𝙣𝙜𝙚𝙧 - 1𝙭"
        description = "1 𝙏𝙞𝙢𝙚 𝘽𝙪𝙡𝙠 𝘼𝙘𝙘𝙤𝙪𝙣𝙩 𝘾𝙝𝙖𝙣𝙜𝙚\n𝙈𝙖𝙭 10,000 𝙖𝙘𝙘𝙤𝙪𝙣𝙩𝙨"
        payload = INVOICE_PAYLOAD_SINGLE
        price = PLAN_SINGLE_STARS

    prices = [LabeledPrice(label="Telegram Stars", amount=price)]

    await context.bot.send_invoice(
        chat_id=update.effective_chat.id,
        title=title,
        description=description,
        payload=payload,
        provider_token=PAYMENT_PROVIDER_TOKEN,
        currency="XTR",
        prices=prices,
        start_parameter=f"bulk_{plan_type}_{user_id}",
        need_name=False,
        need_phone_number=False,
        need_email=False,
        need_shipping_address=False,
        is_flexible=False
    )

async def buy_plan_callback(update, context):
    q = update.callback_query
    await q.answer()

    plan_type = PLAN_UNLIMITED if "unlimited" in q.data else PLAN_SINGLE
    await send_stars_invoice(update, context, plan_type)

async def precheckout_callback(update, context):
    query = update.pre_checkout_query
    payload = query.invoice_payload

    if payload in (INVOICE_PAYLOAD_UNLIMITED, INVOICE_PAYLOAD_SINGLE):
        await query.answer(ok=True)
    else:
        await query.answer(ok=False, error_message="❌ 𝙄𝙣𝙫𝙖𝙡𝙞𝙙 𝙥𝙖𝙮𝙢𝙚𝙣𝙩 𝙥𝙖𝙮𝙡𝙤𝙖𝙙")

async def successful_payment_callback(update, context):
    payment = update.message.successful_payment
    payload = payment.invoice_payload
    user_id = update.effective_user.id
    user = update.effective_user

    if payload == INVOICE_PAYLOAD_UNLIMITED:
        set_user_plan(user_id, PLAN_UNLIMITED, 999999)
        add_stars_spent(user_id, PLAN_UNLIMITED_STARS)
        plan_name = "𝙐𝙉𝙇𝙄𝙈𝙄𝙏𝙀𝘿"
        stars = PLAN_UNLIMITED_STARS
    elif payload == INVOICE_PAYLOAD_SINGLE:
        set_user_plan(user_id, PLAN_SINGLE, 1)
        add_stars_spent(user_id, PLAN_SINGLE_STARS)
        plan_name = "𝙎𝙄𝙉𝙂𝙇𝙀 (1𝙭)"
        stars = PLAN_SINGLE_STARS
    else:
        return

    await update.message.reply_text(
        f"╔══════════════════════╗\n"
        f".   🎉 𝙋𝘼𝙔𝙈𝙀𝙉𝙏 𝙎𝙐𝘾𝘾𝙀𝙎𝙎!\n"
        f"╚══════════════════════╝\n\n"
        f"⭐ 𝙎𝙩𝙖𝙧𝙨 𝙋𝙖𝙞𝙙: {stars}\n"
        f"📦 𝙋𝙡𝙖𝙣: {plan_name}\n\n"
        f"✅ 𝘼𝙘𝙩𝙞𝙫𝙖𝙩𝙚𝙙!\n"
        f"𝙐𝙨𝙚"
    )

# ================= BULK PROCESSING HELPERS =================
async def admin_grant_bulk_start(update, context):
    q = update.callback_query
    await q.answer("Grant Bulk Mode")
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await q.message.reply_text("🚫 𝘼𝘿𝙈𝙄𝙉 𝙊𝙉𝙇𝙔")
        return ConversationHandler.END

    text = (
        "╔══════════════════════╗\n"
        "   ⚡ 𝙂𝙍𝘼𝙉𝙏 𝘽𝙐𝙇𝙆 𝘽𝙔 𝙄𝘿\n"
        "╚══════════════════════╝\n\n"
        "📝 𝙎𝙀𝙉𝘿 𝙐𝙎𝙀𝙍 𝘾𝙃𝘼𝙏 𝙄𝘿:\n"
        "(𝙏𝙚𝙡𝙚𝙜𝙧𝙖𝙢 𝙐𝙨𝙚𝙧 𝙄𝘿 𝙣𝙪𝙢𝙗𝙚𝙧)\n\n"
        "🔢 𝙀𝙭𝙖𝙢𝙥𝙡𝙚: 123456789\n\n"
        "❌ Send /cancel to cancel"
    )
    keyboard = [[InlineKeyboardButton("❌ 𝗖𝗔𝗡𝗖𝗘𝗟", callback_data="admin_back")]]
    try:
        await q.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception:
        await q.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return ADMIN_GRANT_BULK_INPUT

async def admin_grant_bulk_process(update, context):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("🚫 𝘼𝘿𝙈𝙄𝙉 𝙊𝙉𝙇𝙔")
        return ConversationHandler.END

    raw = update.message.text.strip()
    try:
        target_id = int(raw)
    except ValueError:
        await update.message.reply_text(
            "❌ 𝙄𝙉𝙑𝘼𝙇𝙄𝘿 𝙄𝘿! 𝙀𝙣𝙩𝙚𝙧 𝙖 𝙫𝙖𝙡𝙞𝙙 𝙏𝙚𝙡𝙚𝙜𝙧𝙖𝙢 𝙐𝙨𝙚𝙧 𝙄𝘿 (𝙣𝙪𝙢𝙗𝙚𝙧𝙨 𝙤𝙣𝙡𝙮)",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ 𝗖𝗔𝗡𝗖𝗘𝗟", callback_data="admin_back")]])
        )
        return ADMIN_GRANT_BULK_INPUT

    target_data = fb_get(f"users/{target_id}") or {}
    if not target_data:
        await update.message.reply_text(
            "❌ 𝙐𝙎𝙀𝙍 𝙉𝙊𝙏 𝙁𝙊𝙐𝙉𝘿!\n\n"
            "𝙏𝙝𝙞𝙨 𝙪𝙨𝙚𝙧 𝙝𝙖𝙨 𝙣𝙚𝙫𝙚𝙧 𝙪𝙨𝙚𝙙 𝙩𝙝𝙚 𝙗𝙤𝙩.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 𝗕𝗔𝗖𝗞", callback_data="admin_back")]])
        )
        return ConversationHandler.END

    name = target_data.get("name", "Unknown")
    context.user_data["grant_bulk_target_id"] = target_id
    context.user_data["grant_bulk_target_name"] = name

    plan = get_user_plan(int(target_id))
    current_plan = plan["plan"].upper() if plan["plan"] != PLAN_NONE else "❌ 𝙉𝙊𝙉𝙀"
    uses = plan["uses_remaining"] if plan["plan"] == PLAN_SINGLE else ("♾️" if plan["plan"] == PLAN_UNLIMITED else "0")

    text = (
        f"╔══════════════════════╗\n"
        f"   ⚡ 𝙂𝙍𝘼𝙉𝙏 𝘽𝙐𝙇𝙆 𝘼𝘾𝘾𝙀𝙎𝙎\n"
        f"╚══════════════════════╝\n\n"
        f"👤 𝙐𝙨𝙚𝙧: {name}\n"
        f"🆔 𝙄𝘿: {target_id}\n\n"
        f"📊 𝘾𝙪𝙧𝙧𝙚𝙣𝙩 𝙋𝙡𝙖𝙣: {current_plan}\n"
        f"🔢 𝙐𝙨𝙚𝙨 𝙇𝙚𝙛𝙩: {uses}\n\n"
        f"🎯 𝙎𝙚𝙡𝙚𝙘𝙩 𝙋𝙡𝙖𝙣 𝙩𝙤 𝙂𝙧𝙖𝙣𝙩:"
    )

    keyboard = [
        [InlineKeyboardButton("♾️ 𝙐𝙉𝙇𝙄𝙈𝙄𝙏𝙀𝘿", callback_data=f"grant_bulk_id_{target_id}_unlimited")],
        [InlineKeyboardButton("1️⃣ 1 𝙐𝙎𝙀", callback_data=f"grant_bulk_id_{target_id}_single")],
        [InlineKeyboardButton("5️⃣ 5 𝙐𝙎𝙀𝙎", callback_data=f"grant_bulk_id_{target_id}_5x")],
        [InlineKeyboardButton("🔟 10 𝙐𝙎𝙀𝙎", callback_data=f"grant_bulk_id_{target_id}_10x")],
        [InlineKeyboardButton("5️⃣0️⃣ 50 𝙐𝙎𝙀𝙎", callback_data=f"grant_bulk_id_{target_id}_50x")],
        [InlineKeyboardButton("1️⃣0️⃣0️⃣ 100 𝙐𝙎𝙀𝙎", callback_data=f"grant_bulk_id_{target_id}_100x")],
        [InlineKeyboardButton("🔴 𝙍𝙀𝙑𝙊𝙆𝙀 𝘼𝘾𝘾𝙀𝙎𝙎", callback_data=f"grant_bulk_id_{target_id}_revoke")],
        [InlineKeyboardButton("🔙 𝘼𝘿𝙈𝙄𝙉 𝙋𝘼𝙉𝙀𝙇", callback_data="admin_back")]
    ]

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END

async def grant_bulk_by_id_execute(update, context):
    q = update.callback_query
    await q.answer()
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await q.message.reply_text("🚫 𝘼𝘿𝙈𝙄𝙉 𝙊𝙉𝙇𝙔")
        return

    match = re.match(r"^grant_bulk_id_(\d+)_(.+)$", q.data)
    if not match:
        await q.answer("❌ Invalid callback data", show_alert=True)
        return

    target_id = match.group(1)
    plan_type = match.group(2)

    target_data = fb_get(f"users/{target_id}") or {}
    name = target_data.get("name", "Unknown")
    admin_name = update.effective_user.full_name

    try:
        if plan_type == "revoke":
            fb_patch(f"users/{target_id}", {
                "bulk_plan": PLAN_NONE,
                "bulk_uses_remaining": 0
            })
            msg = (
                "╔══════════════════════╗\n"
                "  🔴 𝘽𝙐𝙇𝙆 𝘼𝘾𝘾𝙀𝙎𝙎 𝙍𝙀𝙑𝙊𝙆𝙀𝘿\n"
                "╚══════════════════════╝\n\n"
                f"👤 𝙐𝙨𝙚𝙧: {name}\n"
                f"🆔 𝙄𝘿: {target_id}\n\n"
                "✅ 𝘼𝙘𝙘𝙚𝙨𝙨 𝙝𝙖𝙨 𝙗𝙚𝙚𝙣 𝙧𝙚𝙫𝙤𝙠𝙚𝙙."
            )
            user_msg = (
                "╔══════════════════════╗\n"
                "   ⚠️ 𝘽𝙐𝙇𝙆 𝘼𝘾𝘾𝙀𝙎𝙎 𝙍𝙀𝙑𝙊𝙆𝙀𝘿\n"
                "╚══════════════════════╝\n\n"
                "𝙔𝙤𝙪𝙧 𝙗𝙪𝙡𝙠 𝙖𝙘𝙘𝙤𝙪𝙣𝙩 𝙘𝙝𝙖𝙣𝙜𝙚𝙧 𝙖𝙘𝙘𝙚𝙨𝙨 𝙝𝙖𝙨 𝙗𝙚𝙚𝙣 𝙧𝙚𝙫𝙤𝙠𝙚𝙙 𝙗𝙮 𝙖𝙙𝙢𝙞𝙣.\n\n"
                "🛒 𝙋𝙪𝙧𝙘𝙝𝙖𝙨𝙚 𝙖 𝙥𝙡𝙖𝙣 𝙩𝙤 𝙪𝙨𝙚 𝙖𝙜𝙖𝙞𝙣."
            )
        elif plan_type == "unlimited":
            set_user_plan(int(target_id), PLAN_UNLIMITED, 999999)
            msg = (
                "╔══════════════════════╗\n"
                "    ♾️ 𝙐𝙉𝙇𝙄𝙈𝙄𝙏𝙀𝘿 𝙂𝙍𝘼𝙉𝙏𝙀𝘿\n"
                "╚══════════════════════╝\n\n"
                f"👤 𝙐𝙨𝙚𝙧: {name}\n"
                f"🆔 𝙄𝘿: {target_id}\n\n"
                "✅ 𝙐𝙨𝙚𝙧 𝙘𝙖𝙣 𝙣𝙤𝙬 𝙪𝙨𝙚 /𝙗𝙪𝙡𝙠 𝙪𝙣𝙡𝙞𝙢𝙞𝙩𝙚𝙙 𝙩𝙞𝙢𝙚𝙨."
            )
            user_msg = (
                "╔══════════════════════╗\n"
                "   🎉 𝘽𝙐𝙇𝙆 𝘼𝘾𝘾𝙀𝙎𝙎 𝙂𝙍𝘼𝙉𝙏𝙀𝘿!\n"
                "╚══════════════════════╝\n\n"
                "📦 𝙋𝙡𝙖𝙣: 𝙐𝙉𝙇𝙄𝙈𝙄𝙏𝙀𝘿\n"
                "⚡ 𝙔𝙤𝙪 𝙘𝙖𝙣 𝙣𝙤𝙬 𝙪𝙨𝙚 /𝙗𝙪𝙡𝙠\n\n"
                "𝙀𝙣𝙟𝙤𝙮!"
            )
        else:
            uses = 1
            if plan_type.endswith("x"):
                try:
                    uses = int(plan_type[:-1])
                except ValueError:
                    uses = 1

            set_user_plan(int(target_id), PLAN_SINGLE, uses)
            msg = (
                "╔══════════════════════╗\n"
                "  ✅ 𝘽𝙐𝙇𝙆 𝘼𝘾𝘾𝙀𝙎𝙎 𝙂𝙍𝘼𝙉𝙏𝙀𝘿\n"
                "╚══════════════════════╝\n\n"
                f"👤 𝙐𝙨𝙚𝙧: {name}\n"
                f"🆔 𝙄𝘿: {target_id}\n"
                f"📦 𝙋𝙡𝙖𝙣: {uses} 𝙐𝙨𝙚𝙨\n\n"
                "✅ 𝙐𝙨𝙚𝙧 𝙘𝙖𝙣 𝙣𝙤𝙬 𝙪𝙨𝙚 /𝙗𝙪𝙡𝙠."
            )
            user_msg = (
                "╔══════════════════════╗\n"
                "  🎉 𝘽𝙐𝙇𝙆 𝘼𝘾𝘾𝙀𝙎𝙎 𝙂𝙍𝘼𝙉𝙏𝙀𝘿!\n"
                "╚══════════════════════╝\n\n"
                f"📦 𝙋𝙡𝙖𝙣: {uses} 𝙐𝙨𝙚𝙨\n"
                "⚡ 𝙔𝙤𝙪 𝙘𝙖𝙣 𝙣𝙤𝙬 𝙪𝙨𝙚 /𝙗𝙪𝙡𝙠\n\n"
                "𝙀𝙣𝙟𝙤𝙮!"
            )

        # Notify user
        try:
            await context.bot.send_message(chat_id=int(target_id), text=user_msg)
        except Exception as e:
            msg += f"\n\n⚠️ 𝘾𝙤𝙪𝙡𝙙 𝙣𝙤𝙩 𝙣𝙤𝙩𝙞𝙛𝙮 𝙪𝙨𝙚𝙧: {str(e)}"

        keyboard = [[InlineKeyboardButton("🔙 𝘼𝘿𝙈𝙄𝙉 𝙋𝘼𝙉𝙀𝙇", callback_data="admin_back")]]
        try:
            await q.message.edit_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception:
            await q.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

    except Exception as e:
        await q.answer(f"❌ 𝙀𝙧𝙧𝙤𝙧: {str(e)}", show_alert=True)

# ================= MAIN =================
async def open_bulk_nav(update, context):
    """Navigate to bulk changer from any menu"""
    q = update.callback_query
    await q.answer()
    # Just route to bulk_start equivalent
    user_id = update.effective_user.id
    can_use, status_msg = can_use_bulk(user_id)

    if not can_use:
        text = (
            f"╔══════════════════════╗\n"
            f"⚡𝘽𝙐𝙇𝙆 𝘼𝘾𝘾𝙊𝙐𝙉𝙏 𝘾𝙃𝘼𝙉𝙂𝙀𝙍 𝙑2⚡\n"
            f"╚══════════════════════╝\n\n"
            f"❌ 𝙉𝙊 𝘼𝘾𝙏𝙄𝙑𝙀 𝙋𝙇𝘼𝙉\n\n"
            f"🛒 𝙋𝙐𝙍𝘾𝙃𝘼𝙎𝙀 𝘼 𝙋𝙇𝘼𝙉 𝙏𝙊 𝙐𝙎𝙀 𝘽𝙐𝙇𝙆:\n\n"
            f"⭐ {PLAN_SINGLE_STARS} 𝙎𝙩𝙖𝙧𝙨 → 1 𝙏𝙞𝙢𝙚\n"
            f"⭐ {PLAN_UNLIMITED_STARS} 𝙎𝙩𝙖𝙧𝙨 → 𝙐𝙣𝙡𝙞𝙢𝙞𝙩𝙚𝙙\n\n"
            f"🎯 𝘾𝙡𝙞𝙘𝙠 𝙗𝙚𝙡𝙤𝙬 𝙩𝙤 𝙗𝙪𝙮:"
        )
        keyboard = [
            [InlineKeyboardButton(f"💎 𝘽𝙐𝙔 𝙋𝙇𝘼𝙉", callback_data="bulk_payment_menu")],
            [InlineKeyboardButton("❌ 𝘾𝘼𝙉𝘾𝙀𝙇", callback_data="nav_cancel")]
        ]
        await q.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return ConversationHandler.END

    text = (
        f"╔══════════════════════╗\n"
        f"⚡𝘽𝙐𝙇𝙆 𝘼𝘾𝘾𝙊𝙐𝙉𝙏 𝘾𝙃𝘼𝙉𝙂𝙀𝙍 𝙑2⚡\n"
        f"╚══════════════════════╝\n\n"
        f"{status_msg}\n"
        f"📊 𝙈𝙖𝙭: {BULK_MAX_ACCOUNTS:,} 𝙖𝙘𝙘𝙤𝙪𝙣𝙩𝙨/𝙗𝙖𝙩𝙘𝙝\n"
        f"🔁 𝘽𝙖𝙩𝙘𝙝: {BULK_BATCH_SIZE} 𝙖𝙘𝙘/𝙠𝙚𝙮 𝙧𝙤𝙩𝙖𝙩𝙞𝙤𝙣\n\n"
        f"🔥 𝙁𝙀𝘼𝙏𝙐𝙍𝙀𝙎:\n"
        f"✅ 𝘾𝙝𝙤𝙤𝙨𝙚 𝘾𝙝𝙖𝙣𝙜𝙚 𝙈𝙤𝙙𝙚\n"
        f"✅ 𝘼𝙪𝙩𝙤-𝙧𝙚𝙩𝙧𝙮 (5𝙭)\n"
        f"✅ 𝘿𝙪𝙥𝙡𝙞𝙘𝙖𝙩𝙚 𝙧𝙚𝙢𝙤𝙫𝙖𝙡\n"
        f"✅ 𝘾𝙪𝙨𝙩𝙤𝙢/𝘼𝙪𝙩𝙤 𝙥𝙖𝙨𝙨𝙬𝙤𝙧𝙙\n"
        f"✅ 𝙋𝙧𝙚𝙫𝙞𝙚𝙬 𝙗𝙚𝙛𝙤𝙧𝙚 𝙥𝙧𝙤𝙘𝙚𝙨𝙨\n"
        f"✅ 𝘾𝙋𝙈1 𝘿𝙪𝙖𝙡 𝙆𝙚𝙮 𝙍𝙤𝙩𝙖𝙩𝙞𝙤𝙣\n"
        f"✅ 5% 𝙈𝙞𝙡𝙚𝙨𝙩𝙤𝙣𝙚 𝙋𝙧𝙤𝙜𝙧𝙚𝙨𝙨\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔰 𝙎𝙀𝙇𝙀𝘾𝙏 𝘾𝙋𝙈 𝙈𝙊𝘿𝙀 🔰\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
    keyboard = [[
        InlineKeyboardButton("🏎️ 𝘽𝙐𝙇𝙆 𝘾𝙋𝙈1", callback_data="BULK_CPM1"),
        InlineKeyboardButton("🏎️ 𝘽𝙐𝙇𝙆 𝘾𝙋𝙈2", callback_data="BULK_CPM2")
    ], [
        InlineKeyboardButton("❌ 𝘾𝘼𝙉𝘾𝙀𝙇", callback_data="nav_cancel")
    ]]
    await q.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return BULK_CPM_SELECT
  
async def nav_cancel(update, context):
    """Cancel button press handler"""
    q = update.callback_query
    if q:
        await q.answer("❌ Cancelled")
        try:
            await q.message.edit_text("❌ 𝙊𝙋𝙀𝙍𝘼𝙏𝙄𝙊𝙉 𝘾𝘼𝙉𝘾𝙀𝙇𝙇𝙀𝘿")
        except Exception:
            pass
    # Clear active conversation data
    keys_to_clear = [
        "mode", "gmode", "email", "password", "cpm", "key", "token",
        "firebase_uid", "bulk_cpm", "bulk_mode", "bulk_accounts",
        "bulk_prefix", "bulk_domain", "bulk_custom_pass", "admin_action",
        "msg_target_id", "msg_target_name", "selected_user_id",
        "selected_user_name", "grant_bulk_target_id", "grant_bulk_target_name"
    ]
    for k in keys_to_clear:
        context.user_data.pop(k, None)
    return ConversationHandler.END

async def cmd_cancel(update, context):
    """/cancel command handler"""
    await update.message.reply_text("❌ 𝙊𝙋𝙀𝙍𝘼𝙏𝙄𝙊𝙉 𝘾𝘼𝙉𝘾𝙀𝙇𝙇𝙀𝘿")
    keys_to_clear = [
        "mode", "gmode", "email", "password", "cpm", "key", "token",
        "firebase_uid", "bulk_cpm", "bulk_mode", "bulk_accounts",
        "bulk_prefix", "bulk_domain", "bulk_custom_pass", "admin_action",
        "msg_target_id", "msg_target_name", "selected_user_id",
        "selected_user_name", "grant_bulk_target_id", "grant_bulk_target_name"
    ]
    for k in keys_to_clear:
        context.user_data.pop(k, None)
    return ConversationHandler.END

def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN belum diisi di bagian BOT TOKEN / OWNER pada file ini.")
    if not ADMIN_IDS and OWNER_ID:
        ADMIN_IDS.append(OWNER_ID)
    log.info("Starting bot; Firebase=%s; data_dir=%s", _is_firebase_configured(), DATA_DIR)
    app = Application.builder().token(BOT_TOKEN).build()

    # Main CPM login conversation
    cpm_conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANG_SELECT: [
                CallbackQueryHandler(select_language, pattern="^lang_"),
                CallbackQueryHandler(select_cpm, pattern="^(CPM1|CPM2)$"),
                # REMOVED: open_bulk_nav from here — now handled by bulk_conv entry point
            ],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_password)],
        },
        fallbacks=[
            CallbackQueryHandler(nav_cancel, pattern="^nav_cancel$"),
            CommandHandler("cancel", cmd_cancel),
            CommandHandler("start", start),
        ],
    )

    # Bulk conversation
    bulk_conv = ConversationHandler(
        entry_points=[
            CommandHandler("bulk", bulk_start),
            CallbackQueryHandler(bulk_start, pattern="^start_bulk$"),
            CallbackQueryHandler(bulk_start, pattern="^open_bulk$"),  # FIXED: main menu bulk button
        ],
        states={
            BULK_CPM_SELECT: [CallbackQueryHandler(bulk_select_cpm, pattern="^BULK_CPM")],
            BULK_MODE_SELECT: [CallbackQueryHandler(bulk_select_mode, pattern="^mode_")],
            BULK_PASS_TYPE: [CallbackQueryHandler(bulk_select_pass_type, pattern="^pass_")],
            BULK_CUSTOM_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, bulk_get_custom_pass)],
            BULK_FILE: [MessageHandler(filters.Document.ALL, bulk_get_file)],
            BULK_PREFIX: [MessageHandler(filters.TEXT & ~filters.COMMAND, bulk_get_prefix)],
            BULK_DOMAIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, bulk_process)],
        },
        fallbacks=[
            CallbackQueryHandler(nav_cancel, pattern="^nav_cancel$"),
            CommandHandler("cancel", cmd_cancel),
            CommandHandler("start", start), 
        ],
    )

    app.add_handler(cpm_conv)
    app.add_handler(bulk_conv)

    # Admin conversation handler
    admin_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(msg_user_button, pattern=r"^act_msg_\d+$"),
            CallbackQueryHandler(admin_broadcast_start, pattern="^admin_broadcast$"),
            CallbackQueryHandler(admin_add_member_input_prompt, pattern="^add_member_input$"),
            CallbackQueryHandler(admin_grant_bulk_start, pattern="^admin_grant_bulk$")
        ],
        states={
            ADMIN_MSG_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, msg_user_send),
                CallbackQueryHandler(admin_nav_fallback, pattern=".*")
            ],
            ADMIN_BROADCAST_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_broadcast_send),
                CallbackQueryHandler(admin_nav_fallback, pattern=".*")
            ],
            ADMIN_SEARCH_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_search_process),
                CallbackQueryHandler(admin_nav_fallback, pattern=".*")
            ],
            ADD_MEMBER_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_member_process),
                CallbackQueryHandler(admin_nav_fallback, pattern=".*")
            ],
            ADMIN_GRANT_BULK_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_grant_bulk_process),
                CallbackQueryHandler(admin_nav_fallback, pattern=".*")
            ],
        },
        fallbacks=[
            CallbackQueryHandler(admin_nav_fallback, pattern=".*"),
            CommandHandler("cancel", cmd_cancel),
            CommandHandler("start", start), 
        ]
    )

    app.add_handler(admin_conv)

    # Callbacks — FIXED: gedit_f_all moved BEFORE gedit_feat_cb and pattern fixed
    app.add_handler(CallbackQueryHandler(menu, pattern="^(cemail|cpass|king|logout)$"))
    app.add_handler(CallbackQueryHandler(open_geditor, pattern="^open_geditor$"))
    app.add_handler(CallbackQueryHandler(gedit_refresh, pattern="^gedit_refresh$"))
    app.add_handler(CallbackQueryHandler(gedit_back, pattern="^gedit_back$"))
    app.add_handler(CallbackQueryHandler(gedit_money_menu, pattern="^gedit_money_menu$"))
    app.add_handler(CallbackQueryHandler(gedit_coin_menu, pattern="^gedit_coin_menu$"))
    app.add_handler(CallbackQueryHandler(gedit_feat_menu, pattern="^gedit_feat_menu$"))
    app.add_handler(CallbackQueryHandler(gedit_sett_menu, pattern="^gedit_sett_menu$"))
    app.add_handler(CallbackQueryHandler(gedit_money_cb, pattern="^gedit_m_"))
    app.add_handler(CallbackQueryHandler(gedit_coin_cb, pattern="^gedit_c_"))
    app.add_handler(CallbackQueryHandler(gedit_f_all, pattern="^gedit_f_all$"))  # FIXED: before gedit_feat_cb
    app.add_handler(CallbackQueryHandler(gedit_feat_cb, pattern="^gedit_f_(?!all)"))  # FIXED: excludes gedit_f_all
    app.add_handler(CallbackQueryHandler(gedit_sett_cb, pattern="^gedit_s_"))
    
    # Admin panel callbacks
    app.add_handler(CallbackQueryHandler(choose_user_action, pattern=r"^choose_user_\d+$"))
    app.add_handler(CallbackQueryHandler(ban_user_button, pattern=r"^act_ban_\d+$"))
    app.add_handler(CallbackQueryHandler(unban_user_button, pattern=r"^act_unban_\d+$"))
    app.add_handler(CallbackQueryHandler(grant_bulk_menu, pattern=r"^act_grant_bulk_\d+$"))
    app.add_handler(CallbackQueryHandler(grant_bulk_execute, pattern=r"^grant_bulk_\d+_.+$"))
    app.add_handler(CallbackQueryHandler(grant_bulk_by_id_execute, pattern=r"^grant_bulk_id_\d+_.+$"))
    app.add_handler(CallbackQueryHandler(user_page_nav, pattern="^(user_prev|user_next)$"))
    app.add_handler(CallbackQueryHandler(admin_search_start, pattern="^admin_search$"))
    app.add_handler(CallbackQueryHandler(admin_user_list, pattern="^admin_users$"))
    app.add_handler(CallbackQueryHandler(admin_banned_list, pattern="^admin_banned$"))
    app.add_handler(CallbackQueryHandler(admin_stats, pattern="^admin_stats$"))
    app.add_handler(CallbackQueryHandler(admin_back, pattern="^admin_back$"))
    app.add_handler(CallbackQueryHandler(admin_add_member_start, pattern="^admin_add_member$"))
    app.add_handler(CallbackQueryHandler(admin_remove_member, pattern=r"^remove_member_\d+$"))

    app.add_handler(CallbackQueryHandler(nav_cancel, pattern="^nav_cancel$"))
    app.add_handler(CallbackQueryHandler(open_bulk_nav, pattern="^open_bulk$"))
    app.add_handler(CallbackQueryHandler(bulk_confirm, pattern="^bulk_confirm_btn$"))
    app.add_handler(CallbackQueryHandler(payment_menu, pattern="^bulk_payment_menu$"))
    app.add_handler(CallbackQueryHandler(payment_single, pattern="^pay_single$"))
    app.add_handler(CallbackQueryHandler(payment_unlimited, pattern="^pay_unlimited$"))
    app.add_handler(CallbackQueryHandler(buy_single, pattern="^buy_single$"))
    app.add_handler(CallbackQueryHandler(buy_unlimited, pattern="^buy_unlimited$"))

    # Payment
    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, payment_success))

    # Admin commands
    app.add_handler(CommandHandler("admin", admin_panel))

    # Text handler for game editor + settings
    app.add_handler(CommandHandler("cancel", cmd_cancel))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("🤖 Bot started!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()