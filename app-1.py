#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
⚡🎮 MASKYYOFFC NEON GAMING - CPM1 + CPM2 ULTIMATE 🎮⚡
MERGED - CPM2 activations, cloning, and car unlocking from old code
"""

import requests
import csv
import time
import json
import telebot
import random
import base64
import sys
import os
import string
import struct
import brotli
import hashlib
import zlib
import sqlite3
import asyncio
import aiohttp
import threading
from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from telebot import types
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ═══════════════════════════════════════════════════════════
# 🌐 FLASK WEB SERVER FOR RENDER DEPLOYMENT
# ═══════════════════════════════════════════════════════════

from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "bot": "𝗠𝗮𝘀𝗞𝘆𝘆𝗢𝗙𝗙𝗖 || 𝗕𝗢𝗧",
        "version": "1.0.0",
        "uptime": "running"
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

def run_flask():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# Start Flask in a separate thread
flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()

# ═══════════════════════════════════════════════════════════
# 🔑 TOKENS & KEYS
# ═══════════════════════════════════════════════════════════

BOT_TOKEN = '8965382935:AAG7mpjOgtziaGlvgJI9SEc2Co1_4y5lVNE'
bot = telebot.TeleBot(BOT_TOKEN)

ADMIN_IDS = [8700382637]
ALLOWED_KEYS = ["KYYBOT", "MIAUUBOT", "MASKYYOFFC"]
CHANNEL_ID = "-1004468356174"
CHANNEL_LINK = "https://t.me/MasKyyOFFC"
OWNER_CONTACT = "https://t.me/MasKyyOfficial"

# ═══════════════════════════════════════════════════════════
# 📡 API SETTINGS
# ═══════════════════════════════════════════════════════════

# CPM1 - from cpm_nuker.py
FK = "AIzaSyAe_aOVT1gSfmHKBrorFvX4fRwN5nODXVA"
LOAD_URL = "https://europe-west1-cp-multiplayer.cloudfunctions.net/GetPlayerRecords3"
SAVE_URL = "https://europe-west1-cp-multiplayer.cloudfunctions.net/SavePlayerRecordsPartially8"
RANK_URL = "https://us-central1-cp-multiplayer.cloudfunctions.net/SetUserRating5"
MAX_MONEY = 50_000_000
MAX_COIN = 500_000

GAME_HEADERS = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip",
    "Content-Type": "application/json",
    "User-Agent": "UnityPlayer/2022.3.62f2 (UnityWebRequest/1.0, libcurl/8.10.1-DEV)",
    "X-Unity-Version": "2022.3.62f2",
}

# CPM2 - old
CPM2_API_KEY = 'AIzaSyCQDz9rgjgmvmFkvVfmvr2-7fT4tfrzRRQ'
CPM2_BASE = 'https://europe-west1-cpm-2-7cea1.cloudfunctions.net'
CPM2_OG_KEY = '320b93f3e7f4410aa52ce24da363ad04'
CPM2_VERSION = '1.3.2.3'
CPM2_CLIENT_HASH = 'F05A72840B40DC4FAADF539C5E38062527AE6422'
CPM2_BUNDLE_ID = 'com.olzhas.carparking.multyplayer2'
CPM2_OG_BASE = 'https://cpm-2.ogames.kz/api'
CPM2_KEY_ADD = '12345678'
CPM2_IV_ADD = '01234567'
CPM2_USER_AGENT = 'UnityPlayer/2022.3.62f2 (UnityWebRequest/1.0, libcurl/8.10.1-DEV)'
FB_SIGNUP_CPM2 = f'https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={CPM2_API_KEY}'

HAS_CRYPTO = True
HAS_BROTLI = True

# ═══════════════════════════════════════════════════════════
# 🔑 KEY TRACKING
# ═══════════════════════════════════════════════════════════

KEY_USAGE = {}  # {key: [list of user_ids]}
KEY_USAGE_COUNT = {}  # {key: count}
KEY_USERS_DETAILS = {}  # {key: {user_id: {"username": "...", "first_name": "...", "used_at": "..."}}}
TIME_KEYS = {}  # {key: {"expires": datetime, "duration": hours, "used": False, "user_id": None, "created_by": None, "key_type": "time"}}
TRIAL_KEYS = {}  # legacy trial keys
FREE_TRIAL_USERS = {}  # track free trial usage

# ═══════════════════════════════════════════════════════════
# ENCRYPTION / DECRYPTION FUNCTIONS (from cpm_nuker.py)
# ═══════════════════════════════════════════════════════════

def make_xor_key(uid: str) -> bytes:
    chars = list(str(uid or ""))
    if len(chars) >= 9:
        chars[1], chars[8] = chars[8], chars[1]
    if len(chars) >= 3:
        chars.pop(2)
    if len(chars) >= 5:
        chars.append(chars[4])
    key = "".join(chars).encode("utf-8")
    return key or b"0"

def xor_bytes(data: bytes, key: bytes) -> bytes:
    return bytes(data[i] ^ key[i % len(key)] for i in range(len(data)))

def decompress(data: bytes):
    if HAS_BROTLI:
        try:
            return brotli.decompress(data)
        except Exception:
            pass
    for args in ((zlib.MAX_WBITS | 16,), tuple()):
        try:
            return zlib.decompress(data, *args)
        except Exception:
            pass
    return None

def decrypt_aes(data: bytes, key: bytes):
    if not HAS_CRYPTO:
        return None
    try:
        cipher = AES.new(key[:16], AES.MODE_CBC, b"\x00" * 16)
        return unpad(cipher.decrypt(data), 16)
    except Exception:
        return None

def _md5(text: str) -> bytes:
    return hashlib.md5(str(text).encode()).digest()

def _sha1(text: str) -> bytes:
    return hashlib.sha1(str(text).encode()).digest()[:16]

def build_aes_keys(uid: str, password: str = None, email: str = None) -> list:
    keys = [_md5("olzhas_carparking")]
    if password:
        keys.extend([_md5(password), _sha1(password)])
    if uid:
        keys.extend([_md5(uid), _sha1(uid)])
    if email:
        keys.append(_md5(email))
    return keys

class Reader:
    def __init__(self, data: bytes):
        self.buf = data
        self.pos = 0

    def has_bytes(self, n: int) -> bool:
        return self.pos + n <= len(self.buf)

    def read_byte(self) -> int:
        if not self.has_bytes(1):
            return 0
        value = self.buf[self.pos]
        self.pos += 1
        return value

    def read_int(self) -> int:
        if not self.has_bytes(4):
            self.pos = len(self.buf)
            return 0
        value = struct.unpack_from("<i", self.buf, self.pos)[0]
        self.pos += 4
        return value

    def read_float(self) -> float:
        if not self.has_bytes(4):
            self.pos = len(self.buf)
            return 0.0
        value = struct.unpack_from("<f", self.buf, self.pos)[0]
        self.pos += 4
        return value

    def read_string(self) -> str:
        marker = self.read_int()
        if marker in (0, -1):
            return ""
        length = (-marker) - 1 if marker < -1 else marker
        if marker < -1:
            self.read_int()
        length = max(0, min(length, 1000000))
        if not self.has_bytes(length):
            return ""
        text = self.buf[self.pos:self.pos + length].decode("utf-8", errors="replace")
        self.pos += length
        return text.replace("\x00", "").strip()

    def read_list(self, item_fn):
        count = self.read_int()
        if count <= 0 or count > 1000000:
            return []
        result = []
        for _ in range(count):
            if self.pos >= len(self.buf):
                break
            value = item_fn()
            if value is not None:
                result.append(value)
        return result

    def read_dict(self) -> dict:
        count = self.read_int()
        if count <= 0 or count > 1000000:
            return {}
        result = {}
        for _ in range(count):
            if self.pos >= len(self.buf):
                break
            result[self.read_int()] = self.read_int()
        return result

    def read_equipment(self):
        if self.read_byte() == 0:
            return None
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

def parse_player(buf: bytes) -> dict:
    r = Reader(buf)
    if r.read_byte() == 0:
        return None
    player = {}
    player["Name"] = r.read_string()
    player["money"] = r.read_int()
    player["coin"] = r.read_int()
    player["localID"] = r.read_string()
    player["boughtFsos"] = r.read_list(r.read_int)

    def read_friend():
        r.read_byte()
        return {"id": r.read_string(), "Name": r.read_string(), "accountID": r.read_string()}

    player["FriendsID"] = r.read_list(read_friend)
    player["LevelsDoneTime"] = r.read_list(r.read_float)
    player["floats"] = r.read_list(r.read_float)
    player["integers"] = r.read_list(r.read_int)
    player["fcar"] = r.read_list(r.read_int)
    player["favouriteWheels"] = r.read_list(r.read_int)
    player["favouriteVinyls"] = r.read_list(r.read_int)
    player["favouriteEmojis"] = r.read_list(r.read_int)
    player["personEquipmentsMale"] = r.read_equipment()
    player["personEquipmentsFemale"] = r.read_equipment()

    if r.read_byte() == 0:
        player["platesData"] = None
    else:
        def read_vinyl():
            r.read_byte()
            def rv():
                return {"x": r.read_float(), "y": r.read_float(), "z": r.read_float()}
            return {"vectors": r.read_list(rv), "v": r.read_list(r.read_string),
                    "floats": r.read_list(r.read_float), "text": r.read_string()}
        def read_plate():
            r.read_byte()
            return {"plateId": r.read_int(), "frontCarId": r.read_int(),
                    "rearCarId": r.read_int(), "vinyls": r.read_list(read_vinyl)}
        player["platesData"] = {"allPlates": r.read_list(read_plate)}

    if r.read_byte() == 0:
        player["carIDnStatus"] = None
    else:
        player["carIDnStatus"] = {
            "carGeneratedIDs": r.read_list(r.read_string),
            "carStatus": r.read_list(r.read_int),
        }
    player["allData"] = r.read_string()
    player["flags"] = r.read_dict()
    player["animations"] = r.read_list(r.read_int)
    player["emojiPacks"] = r.read_list(r.read_int)
    player["wheels"] = r.read_list(r.read_int)
    player["boughtPoliceLights"] = r.read_list(r.read_int)
    player["boughtPoliceSirens"] = r.read_list(r.read_int)
    return player

def try_parse(buf: bytes) -> dict:
    candidates = [buf]
    first = decompress(buf)
    if first:
        candidates.append(first)
        second = decompress(first)
        if second:
            candidates.append(second)
    for candidate in candidates:
        if not candidate:
            continue
        if candidate and candidate[0] in (17, 23, 24):
            try:
                parsed = parse_player(candidate)
                if parsed and parsed.get("Name") is not None:
                    return parsed
            except Exception:
                pass
        try:
            clean = candidate[3:] if len(candidate) >= 3 and candidate[:2] == b"\xef\xbb" else candidate
            if clean and clean[0] == 123:
                return json.loads(clean.decode("utf-8"))
        except Exception:
            pass
    return None

def decrypt_player_record(base64_text: str, uid: str, password: str = None, email: str = None) -> dict:
    try:
        buf = base64.b64decode(base64_text)
    except Exception:
        return {"success": False, "message": "Bad base64"}
    if len(buf) < 10:
        return {"success": False, "message": "Too small"}

    direct = try_parse(buf)
    if direct:
        return {"success": True, "record": direct}

    if uid:
        try:
            decoded = decompress(xor_bytes(buf, make_xor_key(uid)))
            if decoded:
                parsed = try_parse(decoded)
                if parsed:
                    return {"success": True, "record": parsed}
        except Exception:
            pass

    for key in build_aes_keys(uid or "", password, email):
        plain = decrypt_aes(buf, key)
        if not plain:
            continue
        parsed = try_parse(plain)
        if parsed:
            return {"success": True, "record": parsed}
    return {"success": False, "message": "Could not decrypt"}

class Writer:
    def __init__(self):
        self._p: List[bytes] = []

    def write_byte(self, v):
        self._p.append(bytes([int(v or 0) & 0xFF]))

    def write_int(self, v):
        self._p.append(struct.pack("<i", int(v or 0)))

    def write_float(self, v):
        self._p.append(struct.pack("<f", float(v or 0.0)))

    def write_string(self, s):
        if s is None:
            self._p.append(struct.pack("<i", -1))
            return
        s = str(s)
        if s == "":
            self._p.append(struct.pack("<i", 0))
            return
        enc = s.encode("utf-8")
        self._p.append(struct.pack("<ii", -(len(enc)) - 1, len(s)) + enc)

    def write_list(self, lst, fn):
        if lst is None:
            self._p.append(struct.pack("<i", -1))
            return
        self._p.append(struct.pack("<i", len(lst)))
        for item in lst:
            fn(item)

    def write_equipment(self, data):
        if not data:
            self.write_byte(0)
            return
        self.write_byte(13)
        for key in ["hair", "face", "beard", "cap", "mask", "top", "gloves", "bag", "pants", "shoes", "glasses", "SelectedEquipments"]:
            self.write_list(data.get(key, []), self.write_int)
        self.write_int(data.get("Gender", 0))

    def write_plates(self, data):
        if not data:
            self.write_byte(0)
            return
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
                    self._p.append(struct.pack("<fff", vec.get("x", 0), vec.get("y", 0), vec.get("z", 0)))
                self.write_list(vinyl.get("v", []), self.write_string)
                self.write_list(vinyl.get("floats", []), self.write_float)
                self.write_string(vinyl.get("text", ""))

    def write_car_id_status(self, data):
        if not data:
            self.write_byte(0)
            return
        self.write_byte(2)
        self.write_list(data.get("carGeneratedIDs", []), self.write_string)
        self.write_list(data.get("carStatus", []), self.write_int)

    def to_bytes(self):
        return b"".join(self._p)

FIELD_MAPPING = [
    (1, "localID"), (2, "money"), (3, "Name"), (4, "coin"), (5, "allData"),
    (6, "boughtFsos"), (7, "boughtPoliceLights"), (8, "boughtPoliceSirens"),
    (9, "FriendsID"), (10, "LevelsDoneTime"), (11, "floats"), (12, "integers"),
    (13, "fcar"), (14, "favouriteWheels"), (15, "favouriteVinyls"),
    (16, "favouriteEmojis"), (18, "emojiPacks"),
    (41, "personEquipmentsMale"), (42, "personEquipmentsFemale"),
    (43, "platesData"), (44, "carIDnStatus"), (45, "flags"),
    (46, "animations"), (48, "wheels"),
]
INT_LIST_FIELDS = {6, 7, 8, 12, 13, 14, 15, 16, 18, 46, 48}
FLOAT_LIST_FIELDS = {10, 11}
ALWAYS_SEND = {"allData"}

def _field_modified(new_value, old_value) -> bool:
    if new_value is None and old_value is None:
        return False
    if new_value is None or old_value is None:
        return True
    if type(new_value) != type(old_value):
        return True
    if isinstance(new_value, (dict, list)):
        return json.dumps(new_value, sort_keys=True) != json.dumps(old_value, sort_keys=True)
    return new_value != old_value

def serialize_field(fid: int, value: Any) -> Optional[bytes]:
    w = Writer()
    if fid in (1, 3, 5):
        w.write_string(value)
        return w.to_bytes()
    if fid in (2, 4):
        w.write_int(value or 0)
        return w.to_bytes()
    if fid == 9:
        friends = value or []
        w._p.append(struct.pack("<i", len(friends)))
        for friend in friends:
            friend = friend or {}
            w.write_byte(3)
            w.write_string(friend.get("id", ""))
            w.write_string(friend.get("Name", ""))
            w.write_string(friend.get("accountID", ""))
        return w.to_bytes()
    if fid in INT_LIST_FIELDS:
        w.write_list(value or [], w.write_int)
        return w.to_bytes()
    if fid in FLOAT_LIST_FIELDS:
        w.write_list(value or [], w.write_float)
        return w.to_bytes()
    if fid in (41, 42):
        w.write_equipment(value)
        return w.to_bytes()
    if fid == 43:
        w.write_plates(value)
        return w.to_bytes()
    if fid == 44:
        w.write_car_id_status(value)
        return w.to_bytes()
    if fid == 45:
        flags = value or {}
        w._p.append(struct.pack("<i", len(flags)))
        for key, val in flags.items():
            w.write_int(int(key))
            w.write_int(int(val))
        return w.to_bytes()
    return None

def build_payload(record: Dict[str, Any], uid: str, original: Optional[Dict[str, Any]] = None,
                  force_fields: Optional[set] = None) -> str:
    force_fields = set(force_fields or [])
    fields = []
    for fid, key in FIELD_MAPPING:
        value = record.get(key)
        if value is None:
            continue
        if key in ALWAYS_SEND:
            should_send = isinstance(value, str) and len(value) > 0
        elif key in force_fields:
            should_send = True
        elif original is not None:
            should_send = _field_modified(value, original.get(key))
        else:
            should_send = True
        if not should_send:
            continue
        raw = serialize_field(fid, value)
        if raw is not None:
            fields.append((fid, raw))

    parts = [struct.pack("<i", len(fields))]
    for fid, raw in fields:
        parts.append(struct.pack("<hi", fid, len(raw)))
        parts.append(raw)
    combined = b"".join(parts)
    compressed = brotli.compress(combined) if HAS_BROTLI else zlib.compress(combined)
    encrypted = xor_bytes(compressed, make_xor_key(uid))
    return base64.b64encode(encrypted).decode("ascii")

# ═══════════════════════════════════════════════════════════
# 📦 CPMNuker Class (from cpm_nuker.py - for new activations)
# ═══════════════════════════════════════════════════════════

class CPMNuker:
    def __init__(self, db_path: str = "cpm_tokens.db"):
        self.db_path = db_path
        self.cache: Dict[str, Dict[str, Any]] = {}
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as c:
            c.execute("""CREATE TABLE IF NOT EXISTS tokens (
                user_id INTEGER PRIMARY KEY,
                auth_token TEXT,
                email TEXT,
                password TEXT,
                refresh_token TEXT,
                firebase_uid TEXT,
                token_expires_at REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
            c.execute("""CREATE TABLE IF NOT EXISTS user_data (
                cache_key TEXT PRIMARY KEY,
                email TEXT,
                data_json TEXT,
                saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
            c.execute("""CREATE TABLE IF NOT EXISTS backups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                label TEXT,
                data_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
            for stmt in (
                "ALTER TABLE tokens ADD COLUMN firebase_uid TEXT",
                "ALTER TABLE tokens ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "ALTER TABLE user_data ADD COLUMN saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            ):
                try:
                    c.execute(stmt)
                except Exception:
                    pass
            c.commit()

    def _ck(self, uid: int, email: Optional[str] = None) -> str:
        if email:
            return f"{uid}_{email}"
        td = self.get_token_data(uid)
        return f"{uid}_{td['email']}" if td and td.get("email") else str(uid)

    def save_token(self, uid: int, auth: str, email: str, pw: Optional[str] = None,
                   rt: Optional[str] = None, fuid: Optional[str] = None):
        with sqlite3.connect(self.db_path) as c:
            c.execute("""INSERT OR REPLACE INTO tokens
                (user_id, auth_token, email, password, refresh_token, firebase_uid, token_expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (uid, auth, email, pw, rt, fuid, time.time() + 3600))
            c.commit()

    def get_token_data(self, uid: int) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as c:
            row = c.execute("""SELECT auth_token, email, password, refresh_token, firebase_uid, token_expires_at
                               FROM tokens WHERE user_id=?""", (uid,)).fetchone()
        if not row:
            return None
        return {
            "auth_token": row[0], "email": row[1], "password": row[2],
            "refresh_token": row[3], "firebase_uid": row[4], "token_expires_at": row[5]
        }

    def get_token(self, uid: int) -> Optional[Dict[str, str]]:
        td = self.get_token_data(uid)
        return {"auth_token": td["auth_token"], "email": td["email"]} if td else None

    def update_token(self, uid: int, auth: str, rt: Optional[str] = None):
        with sqlite3.connect(self.db_path) as c:
            if rt:
                c.execute("UPDATE tokens SET auth_token=?, refresh_token=?, token_expires_at=? WHERE user_id=?",
                          (auth, rt, time.time() + 3600, uid))
            else:
                c.execute("UPDATE tokens SET auth_token=?, token_expires_at=? WHERE user_id=?",
                          (auth, time.time() + 3600, uid))
            c.commit()

    def delete_token(self, uid: int):
        with sqlite3.connect(self.db_path) as c:
            c.execute("DELETE FROM tokens WHERE user_id=?", (uid,))
            c.commit()
        for key in [k for k in self.cache if k.startswith(str(uid))]:
            del self.cache[key]

    def is_expired(self, uid: int) -> bool:
        td = self.get_token_data(uid)
        return not td or not td.get("token_expires_at") or td["token_expires_at"] < time.time()

    def get_record(self, uid: int, email: Optional[str] = None) -> Dict[str, Any]:
        ck = self._ck(uid, email)
        if ck not in self.cache:
            with sqlite3.connect(self.db_path) as c:
                row = c.execute("SELECT data_json FROM user_data WHERE cache_key=?", (ck,)).fetchone()
            if row:
                try:
                    self.cache[ck] = json.loads(row[0])
                except Exception:
                    pass
        return self.cache.get(ck, {})

    def set_record(self, uid: int, data: Dict[str, Any], email: Optional[str] = None):
        ck = self._ck(uid, email)
        self.cache[ck] = data
        with sqlite3.connect(self.db_path) as c:
            c.execute("INSERT OR REPLACE INTO user_data (cache_key, email, data_json) VALUES (?, ?, ?)",
                      (ck, email, json.dumps(data)))
            c.commit()

    async def _post(self, url: str, payload: Dict[str, Any], headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
        try:
            clean_headers = {k: v for k, v in headers.items() if k.lower() != "host"}
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout, connector=aiohttp.TCPConnector(ssl=False)) as s:
                async with s.post(url, json=payload, headers=clean_headers) as resp:
                    text = await resp.text()
                    try:
                        return json.loads(text)
                    except Exception:
                        return {"raw": text, "status": resp.status}
        except Exception as exc:
            print(f"HTTP error: {exc}")
            return None

    async def login(self, email: str, password: str) -> Dict[str, Any]:
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FK}"
        headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip",
            "Content-Type": "application/json",
            "User-Agent": "UnityPlayer/2022.3.62f2 (UnityWebRequest/1.0, libcurl/8.10.1-DEV)",
            "X-Unity-Version": "2022.3.62f2",
        }
        payload = {"email": email, "password": password, "returnSecureToken": True, "clientType": "CLIENT_TYPE_ANDROID"}
        result = await self._post(url, payload, headers)
        if not result:
            return {"ok": False, "message": "NETWORK_ERROR"}
        if "idToken" in result:
            return {
                "ok": True,
                "message": "OK",
                "auth": result["idToken"],
                "refresh_token": result.get("refreshToken", ""),
                "firebase_uid": result.get("localId", ""),
            }
        err = str(result.get("error", {}).get("message", "")).upper()
        for key in ["EMAIL_NOT_FOUND", "INVALID_PASSWORD", "INVALID_LOGIN_CREDENTIALS", "TOO_MANY_ATTEMPTS", "USER_DISABLED", "INVALID_EMAIL"]:
            if key in err:
                return {"ok": False, "message": key}
        return {"ok": False, "message": f"LOGIN_FAILED: {err[:80]}"}

    async def account_login(self, email: str, password: str) -> Dict[str, Any]:
        return await self.login(email, password)

    async def _refresh(self, uid: int) -> Tuple[bool, str]:
        td = self.get_token_data(uid)
        if not td:
            return False, "NO_TOKEN"
        rt, em, pw = td.get("refresh_token"), td.get("email"), td.get("password")
        if rt:
            try:
                result = await self._post(
                    f"https://securetoken.googleapis.com/v1/token?key={FK}",
                    {"grant_type": "refresh_token", "refresh_token": rt},
                    {"Content-Type": "application/json"},
                )
                if result and result.get("id_token"):
                    self.update_token(uid, result["id_token"], result.get("refresh_token", rt))
                    return True, "OK"
            except Exception:
                pass
        if em and pw:
            result = await self.login(em, pw)
            if result.get("ok"):
                self.save_token(uid, result["auth"], em, pw, result.get("refresh_token", ""), result.get("firebase_uid", ""))
                return True, "OK"
        return False, "REFRESH_FAILED"

    async def get_auth(self, uid: int) -> Tuple[bool, str, str]:
        if self.is_expired(uid):
            ok, msg = await self._refresh(uid)
            if not ok:
                return False, msg, ""
        td = self.get_token_data(uid)
        if td and td.get("auth_token"):
            return True, "OK", td["auth_token"]
        return False, "NO_TOKEN", ""

    async def load(self, uid: int, force: bool = False) -> bool:
        td = self.get_token_data(uid)
        if not td:
            return False
        ck = self._ck(uid)
        if not force and ck in self.cache:
            return True
        ok, msg, auth = await self.get_auth(uid)
        if not ok:
            print(f"load: no valid token for {uid}: {msg}")
            return False
        result = await self._post(LOAD_URL, {"data": None}, {**GAME_HEADERS, "Authorization": f"Bearer {auth}"})
        if not result or not result.get("result"):
            print(f"load: empty/invalid response for {uid}: {str(result)[:200]}")
            return False
        decoded = decrypt_player_record(result["result"], td.get("firebase_uid", ""), td.get("password", ""), td.get("email", ""))
        if decoded.get("success") and decoded.get("record"):
            self.set_record(uid, decoded["record"], td.get("email", ""))
            print(f"Loaded {uid}: {decoded['record'].get('Name')}")
            return True
        print(f"load: decrypt failed for {uid}: {decoded.get('message')}")
        return False

    async def load_account(self, uid: int, force: bool = False) -> bool:
        return await self.load(uid, force)

    def _ok(self, value: Any) -> bool:
        if value in (1, True):
            return True
        if value in (0, False, None):
            return False
        if isinstance(value, str):
            text = value.strip()
            if text == "1":
                return True
            if text == "0":
                return False
            try:
                return self._ok(json.loads(text))
            except Exception:
                return False
        if isinstance(value, dict):
            for key in ("result", "ok", "success"):
                if key in value:
                    return self._ok(value[key])
        return False

    async def _send(self, auth: str, record: Dict[str, Any], fuid: str,
                    original: Optional[Dict[str, Any]] = None,
                    force_fields: Optional[set] = None) -> Tuple[bool, str]:
        if not fuid:
            return False, "NO_FIREBASE_UID"
        try:
            payload = build_payload(record, fuid, original, force_fields=force_fields)
            result = await self._post(
                SAVE_URL,
                {"data": {"data": payload, "deviceId": fuid[:8]}},
                {**GAME_HEADERS, "Authorization": f"Bearer {auth}", "Connection": "Keep-Alive",
                 "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 12; Pixel 6 Build/SD1A.210817.036)"},
            )
            if result and self._ok(result):
                return True, "OK"
            return False, f"SAVE_FAILED: {str(result)[:160]}"
        except Exception as exc:
            return False, str(exc)

    async def _save(self, uid: int, data: Dict[str, Any], force_fields: Optional[set] = None) -> Dict[str, Any]:
        ok, msg, auth = await self.get_auth(uid)
        if not ok:
            return {"ok": False, "message": msg}
        td = self.get_token_data(uid)
        fuid = td.get("firebase_uid", "") if td else ""
        email = td.get("email", "") if td else ""
        original = self.get_record(uid, email) or None
        ok2, msg2 = await self._send(auth, data, fuid, original, force_fields=force_fields)
        if ok2:
            self.set_record(uid, data, email)
            return {"ok": True, "message": "OK"}
        return {"ok": False, "message": msg2}

    async def _modify(self, uid: int, mods: Dict[str, Any], force_fields: Optional[set] = None) -> Dict[str, Any]:
        await self.load(uid)
        td = self.get_token_data(uid)
        email = td.get("email") if td else None
        data = deepcopy(self.get_record(uid, email))
        if not data or data.get("Name") is None:
            return {"ok": False, "message": "Could not load account data. Try logging in again or refreshing first."}
        for key, value in mods.items():
            if key == "money":
                value = min(int(value), MAX_MONEY)
            if key == "coin":
                value = min(int(value), MAX_COIN)
            data[key] = value
        forced = set(force_fields or mods.keys())
        return await self._save(uid, data, force_fields=forced)

    async def _set_floats(self, uid: int, indices_values: List[Tuple[int, float]]) -> Dict[str, Any]:
        await self.load(uid)
        td = self.get_token_data(uid)
        email = td.get("email") if td else None
        data = deepcopy(self.get_record(uid, email))
        if not data or data.get("Name") is None:
            return {"ok": False, "message": "Could not load account data. Try logging in again or refreshing first."}
        floats = data.get("floats", [])
        max_idx = max(idx for idx, _ in indices_values)
        while len(floats) <= max_idx:
            floats.append(0.0)
        for idx, value in indices_values:
            floats[idx] = float(value)
        data["floats"] = floats
        return await self._save(uid, data, force_fields={"floats"})

    async def _set_integers(self, uid: int, indices_values: List[Tuple[int, int]]) -> Dict[str, Any]:
        await self.load(uid)
        td = self.get_token_data(uid)
        email = td.get("email") if td else None
        data = deepcopy(self.get_record(uid, email))
        if not data or data.get("Name") is None:
            return {"ok": False, "message": "Could not load account data. Try logging in again or refreshing first."}
        integers = data.get("integers", [])
        max_idx = max(idx for idx, _ in indices_values)
        while len(integers) <= max_idx:
            integers.append(0)
        for idx, value in indices_values:
            integers[idx] = int(value)
        data["integers"] = integers
        return await self._save(uid, data, force_fields={"integers"})

    async def set_money(self, uid: int, amount: int) -> Dict[str, Any]:
        return await self._modify(uid, {"money": min(int(amount), MAX_MONEY)}, force_fields={"money"})

    async def set_coin(self, uid: int, amount: int) -> Dict[str, Any]:
        return await self._modify(uid, {"coin": min(int(amount), MAX_COIN)}, force_fields={"coin"})

    async def set_player_name(self, uid: int, name: str) -> Dict[str, Any]:
        return await self._modify(uid, {"Name": str(name)}, force_fields={"Name"})

    async def set_player_id(self, uid: int, pid: str) -> Dict[str, Any]:
        return await self._modify(uid, {"localID": str(pid).upper()}, force_fields={"localID"})

    async def change_player_id(self, uid: int, new_id: str) -> Dict[str, Any]:
        await self.load(uid, force=True)
        td = self.get_token_data(uid)
        email = td.get("email") if td else None
        data = deepcopy(self.get_record(uid, email))
        if not data or data.get("Name") is None:
            return {"ok": False, "message": "Could not load account data. Please login first."}
        new_id_upper = str(new_id).strip().upper()
        if not new_id_upper:
            return {"ok": False, "message": "ID cannot be empty."}
        data["localID"] = new_id_upper
        result = await self._save(uid, data, force_fields={"localID"})
        if result.get("ok"):
            return {"ok": True, "message": f"ID changed successfully to: {new_id_upper}", "new_id": new_id_upper}
        else:
            return {"ok": False, "message": result.get("message", "Save failed")}

    # ====== CHANGE EMAIL & PASSWORD ======
    async def change_email(self, uid: int, new_email: str) -> Dict[str, Any]:
        """Change account email"""
        await self.load(uid, force=True)
        td = self.get_token_data(uid)
        if not td:
            return {"ok": False, "message": "Token data not found"}
        
        old_email = td.get("email")
        password = td.get("password")
        
        if not password:
            return {"ok": False, "message": "Password not found"}
        
        try:
            # Login with old credentials
            login_result = await self.login(old_email, password)
            if not login_result.get("ok"):
                return {"ok": False, "message": "Failed to login with old credentials"}
            
            # Change email using Firebase
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={FK}"
            payload = {
                "idToken": login_result["auth"],
                "email": new_email,
                "returnSecureToken": True
            }
            
            result = await self._post(url, payload, {})
            if result and result.get("email"):
                # Update token
                self.save_token(
                    uid,
                    result.get("idToken", login_result["auth"]),
                    new_email,
                    password,
                    result.get("refreshToken", login_result.get("refresh_token", "")),
                    result.get("localId", td.get("firebase_uid", ""))
                )
                return {"ok": True, "message": f"Email changed to {new_email}"}
            else:
                return {"ok": False, "message": "Failed to change email"}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    async def change_password(self, uid: int, new_password: str) -> Dict[str, Any]:
        """Change account password"""
        await self.load(uid, force=True)
        td = self.get_token_data(uid)
        if not td:
            return {"ok": False, "message": "Token data not found"}
        
        email = td.get("email")
        old_password = td.get("password")
        
        if not email or not old_password:
            return {"ok": False, "message": "Email or password not found"}
        
        try:
            # Login with old credentials
            login_result = await self.login(email, old_password)
            if not login_result.get("ok"):
                return {"ok": False, "message": "Failed to login with old credentials"}
            
            # Change password using Firebase
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={FK}"
            payload = {
                "idToken": login_result["auth"],
                "password": new_password,
                "returnSecureToken": True
            }
            
            result = await self._post(url, payload, {})
            if result and result.get("idToken"):
                # Update token
                self.save_token(
                    uid,
                    result["idToken"],
                    email,
                    new_password,
                    result.get("refreshToken", login_result.get("refresh_token", "")),
                    result.get("localId", td.get("firebase_uid", ""))
                )
                return {"ok": True, "message": "Password changed successfully"}
            else:
                return {"ok": False, "message": "Failed to change password"}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    async def unlock_w16(self, uid: int) -> Dict[str, Any]:
        return await self._set_floats(uid, [(32, 1.0)])

    async def unlock_horns(self, uid: int) -> Dict[str, Any]:
        return await self._set_floats(uid, [(27, 1.0), (28, 1.0), (29, 1.0), (30, 1.0), (31, 1.0)])

    async def disable_damage(self, uid: int) -> Dict[str, Any]:
        return await self._set_floats(uid, [(34, 1.0)])

    async def unlimited_fuel(self, uid: int) -> Dict[str, Any]:
        return await self._set_floats(uid, [(3, 1.0)])

    async def unlock_smoke(self, uid: int) -> Dict[str, Any]:
        return await self._set_floats(uid, [(33, 1.0)])

    async def unlock_animations(self, uid: int) -> Dict[str, Any]:
        await self.load(uid)
        td = self.get_token_data(uid)
        email = td.get("email") if td else None
        data = deepcopy(self.get_record(uid, email))
        if not data or data.get("Name") is None:
            return {"ok": False, "message": "Could not load account data."}
        data["animations"] = sorted(set(data.get("animations", []) + list(range(301))))
        return await self._save(uid, data, force_fields={"animations"})

    async def unlock_wheels(self, uid: int) -> Dict[str, Any]:
        await self.load(uid)
        td = self.get_token_data(uid)
        email = td.get("email") if td else None
        data = deepcopy(self.get_record(uid, email))
        if not data or data.get("Name") is None:
            return {"ok": False, "message": "Could not load account data."}
        data["wheels"] = sorted(set(data.get("wheels", []) + list(range(73, 221))))
        integers = data.get("integers", [])
        while len(integers) < 113:
            integers.append(0)
        for idx in [0, 1, 2, 3, 4, 5, 110, 111, 112]:
            integers[idx] = 1
        data["integers"] = integers
        return await self._save(uid, data, force_fields={"wheels", "integers"})

    async def unlock_houses(self, uid: int) -> Dict[str, Any]:
        return await self._set_integers(uid, [(8, 1), (110, 1), (111, 1), (112, 1)])

    async def complete_all_levels(self, uid: int) -> Dict[str, Any]:
        levels = [0] + [120 if i == 43 else 1 for i in range(1, 110)]
        return await self._modify(uid, {"LevelsDoneTime": levels}, force_fields={"LevelsDoneTime"})

    async def set_rank(self, uid: int) -> Dict[str, Any]:
        await self.load(uid)
        ok, msg, auth = await self.get_auth(uid)
        if not ok:
            return {"ok": True, "message": "OK"}
        rating_data = {"RatingData": {
            "time": 1e22, "cars": 1e16, "car_fix": 1e13, "car_collided": 1e12,
            "car_exchange": 1e13, "car_trade": 1e13, "car_wash": 1e13,
            "slicer_cut": 1e13, "drift_max": 1e14, "drift": 1e14,
            "cargo": 1e5, "delivery": 1e5, "race_win": 3e20,
            "taxi": 1e10, "levels": 10000990000, "gifts": 1e9,
            "fuel": 1e10, "offroad": 1e10, "speed_banner": 1e9,
            "reactions": 1e17, "run": 1e9, "real_estate": 1e9,
            "t_distance": 1e10, "treasure": 1e10, "block_post": 1e10,
            "push_ups": 1e12, "burnt_tire": 1e10, "passanger_distance": 1e8,
        }}
        try:
            await self._post(RANK_URL, {"data": json.dumps(rating_data)}, {**GAME_HEADERS, "Authorization": f"Bearer {auth}"})
        except Exception as exc:
            print(f"King/Max Rank call failed but is reported as success by request: {exc}")
        return {"ok": True, "message": "OK"}

    def _normalize_equipment(self, equipment: Dict[str, Any], gender: int) -> Dict[str, Any]:
        list_fields = [
            "hair", "face", "beard", "cap", "mask", "top", "gloves",
            "bag", "pants", "shoes", "glasses", "SelectedEquipments",
        ]
        normalized = {}
        for key in list_fields:
            values = equipment.get(key, []) if isinstance(equipment, dict) else []
            normalized[key] = [int(v) for v in values]
        normalized["Gender"] = int(gender)
        return normalized

    async def _save_equipment(self, uid: int, field: str, equipment: Dict[str, Any]) -> Dict[str, Any]:
        await self.load(uid, force=True)
        td = self.get_token_data(uid)
        email = td.get("email") if td else None
        data = deepcopy(self.get_record(uid, email))
        if not data or data.get("Name") is None:
            return {"ok": False, "message": "Could not load account data. Try logging in again or refreshing first."}
        gender = 0 if field == "personEquipmentsMale" else 1
        data[field] = self._normalize_equipment(equipment, gender)
        force_fields = {field}
        other_field = "personEquipmentsFemale" if field == "personEquipmentsMale" else "personEquipmentsMale"
        other_gender = 1 if other_field == "personEquipmentsFemale" else 0
        if data.get(other_field):
            data[other_field] = self._normalize_equipment(data[other_field], data[other_field].get("Gender", other_gender))
            force_fields.add(other_field)
        return await self._save(uid, data, force_fields=force_fields)

    async def unlock_equipments_male(self, uid: int) -> Dict[str, Any]:
        equipment = {
            "Gender": 0,
            "bag": list(range(101)),
            "beard": list(range(6, 21)) + [100],
            "cap": list(range(3, 64)),
            "face": [0, 1, 2, 100],
            "glasses": list(range(10)) + [100],
            "gloves": list(range(6)) + [100],
            "hair": list(range(3, 20)) + [100],
            "mask": list(range(3, 9)) + [100],
            "pants": list(range(26)),
            "shoes": list(range(31)),
            "top": list(range(2, 109)),
            "SelectedEquipments": [-1, 10, 19, 41, 100, 4, 20, 9, 22, 21, 74],
        }
        return await self._save_equipment(uid, "personEquipmentsMale", equipment)

    async def unlock_equipments_female(self, uid: int) -> Dict[str, Any]:
        equipment = {
            "Gender": 1,
            "bag": list(range(6)),
            "beard": [],
            "cap": list(range(3, 41)),
            "face": [0],
            "glasses": list(range(10)),
            "gloves": [1],
            "hair": [0, 7, 8, 9, 10],
            "mask": list(range(3, 8)),
            "pants": list(range(12)),
            "shoes": list(range(3, 15)),
            "top": list(range(5, 80)),
            "SelectedEquipments": [0, 0, -1, -1, -1, -1, -1, -1, 0, -1, -1],
        }
        return await self._save_equipment(uid, "personEquipmentsFemale", equipment)

    async def fix_account(self, uid: int) -> Dict[str, Any]:
        await self.load(uid)
        td = self.get_token_data(uid)
        email = td.get("email") if td else None
        data = deepcopy(self.get_record(uid, email))
        if not data or data.get("Name") is None:
            return {"ok": False, "message": "Could not load account data."}
        bugs = 0
        floats = data.get("floats", [])[:54]
        while len(floats) < 54:
            floats.append(0.0)
        fixed_floats = []
        for value in floats:
            if value in (1, 1.0):
                fixed_floats.append(1.0)
            elif isinstance(value, (int, float)) and value > 1:
                bugs += 1
                fixed_floats.append(0.0)
            else:
                fixed_floats.append(float(value) if value else 0.0)
        integers = data.get("integers", [])[:120]
        while len(integers) < 120:
            integers.append(0)
        fixed_integers = []
        for value in integers:
            if value == 1:
                fixed_integers.append(1)
            elif isinstance(value, (int, float)) and value > 1:
                bugs += 1
                fixed_integers.append(0)
            else:
                fixed_integers.append(int(value) if value else 0)
        data["floats"] = fixed_floats
        data["integers"] = fixed_integers
        result = await self._save(uid, data, force_fields={"floats", "integers"})
        return {"ok": True, "bugs_fixed": bugs, "message": f"{bugs} bugs fixed"} if result.get("ok") else {"ok": False, "message": "FIX_FAILED"}

    async def unlock_all_features(self, uid: int) -> Dict[str, Any]:
        feature_calls = [
            ("W16 Engine", self.unlock_w16),
            ("Horns", self.unlock_horns),
            ("No Damage", self.disable_damage),
            ("Unlimited Fuel", self.unlimited_fuel),
            ("Smoke", self.unlock_smoke),
            ("Animations", self.unlock_animations),
            ("Wheels", self.unlock_wheels),
            ("Houses", self.unlock_houses),
            ("All Levels", self.complete_all_levels),
            ("Max Rank", self.set_rank),
        ]
        results = []
        failed = []
        await self.load(uid, force=True)
        for name, fn in feature_calls:
            result = await fn(uid)
            if result.get("ok"):
                results.append(name)
            else:
                failed.append(f"{name}: {result.get('message', 'Failed')}")
        return {
            "ok": not failed,
            "message": f"Unlocked {len(results)}/{len(feature_calls)} features" + ("; " + "; ".join(failed) if failed else ""),
            "results": results,
            "failed": failed,
        }

    async def get_account_info(self, uid: int) -> Dict[str, Any]:
        """Get account info (money, coins, ID, name) - forces fresh load"""
        # Load fresh data from server
        await self.load(uid, force=True)
        td = self.get_token_data(uid)
        email = td.get("email") if td else None
        data = self.get_record(uid, email)
        
        if not data or data.get("Name") is None:
            return {"ok": False, "message": "Could not load account data"}
        
        return {
            "ok": True,
            "name": data.get("Name", "Unknown"),
            "money": data.get("money", 0),
            "coin": data.get("coin", 0),
            "localID": data.get("localID", "Unknown"),
            "email": email
        }

# ═══════════════════════════════════════════════════════════
# 🎮 CPM2 FUNCTIONS (from old code - working)
# ═══════════════════════════════════════════════════════════

def gen_device_id():
    return ''.join(random.choice('0123456789abcdef') for _ in range(32))

CPM2_DEVICE_ID = gen_device_id()
_cpm2_session = requests.Session()

class CPM2Crypto:
    def __init__(self, uid):
        self.uid = uid
        self.key = (uid[:8] + CPM2_KEY_ADD).encode()[:16]
        self.iv = (uid[:8] + CPM2_IV_ADD).encode()[:16]
    def encrypt(self, s):
        return base64.b64encode(AES.new(self.key, AES.MODE_CBC, self.iv).encrypt(pad(s.encode(), 16))).decode()

def cpm2_login(email, pw):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={CPM2_API_KEY}"
    payload = {"email": email, "password": pw, "returnSecureToken": True, "clientType": "CLIENT_TYPE_ANDROID"}
    try:
        r = requests.post(url, json=payload, timeout=20, verify=False)
        j = r.json()
        if "idToken" in j:
            return {"token": j["idToken"], "uid": j["localId"]}
        return {"error": "Login failed"}
    except:
        return {"error": "Connection error"}

def cpm2_king_rank(email, pw):
    try:
        a = cpm2_login(email, pw)
        if not a or "error" in a:
            return False, f"Login failed: {a.get('error', 'unknown')}"
        token = a["token"]
        uid = a["uid"]
        crypto = CPM2Crypto(uid)
        rating = {"cars": 100000, "car_fix": 100000, "car_collided": 100000, 
                  "car_exchange": 100000, "car_trade": 100000, "car_wash": 100000,
                  "slicer_cut": 100000, "drift_max": 100000, "drift": 100000,
                  "cargo": 100000, "delivery": 100000, "taxi": 100000,
                  "levels": 100000, "gifts": 100000, "fuel": 100000,
                  "offroad": 100000, "speed_banner": 100000, "reactions": 100000,
                  "police": 100000, "run": 100000, "real_estate": 100000,
                  "t_distance": 100000, "treasure": 100000, "block_post": 100000,
                  "push_ups": 100000, "burnt_tire": 100000, "passanger_distance": 100000,
                  "time": 9999999999, "race_win": 5000}
        enc = crypto.encrypt(json.dumps(rating))
        hdrs = {"X-Firebase-Token": token, "X-Api-Key": CPM2_OG_KEY, 
                "Content-Type": "application/json", "User-Agent": CPM2_USER_AGENT}
        r = _cpm2_session.post(f"{CPM2_OG_BASE}/progress-service/v1/rating/update", 
                                headers=hdrs, json={"data": enc}, timeout=20, verify=False)
        if r.status_code == 200 and '"code":1' in r.text:
            return True, "Rank upgraded to King (Level 120)"
        return False, "Failed to upgrade rank"
    except Exception as e:
        return False, f"Error: {str(e)}"

def generate_cpm2_account():
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    email = f"{username}@CPM-MAFIAx PRIMO-CPM TOOL.com"
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
    return {"email": email, "password": password}, None

# ═══════════════════════════════════════════════════════════
# 📋 CPM1 BASIC FUNCTIONS (old - for cloning and car unlocking)
# ═══════════════════════════════════════════════════════════

def verify_user(email, password):
    payload = {"email": email, "password": password, "returnSecureToken": True, "clientType": "CLIENT_TYPE_ANDROID"}
    try:
        response = requests.post(f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword", json=payload, params={"key": "AIzaSyBW1ZbMiUeDZHYUO2bY8Bfnf5rRgrQGPTM"}, timeout=30)
        if response.status_code == 200:
            d = response.json()
            return d.get("idToken"), d.get("localId")
        return None, None
    except:
        return None, None

def cpm1_api(token, endpoint, data=None):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    try:
        response = requests.post(f"https://europe-west1-cp-multiplayer.cloudfunctions.net/{endpoint}", json={"data": data}, headers=headers, timeout=60)
        return response.status_code, response.text
    except:
        return 500, json.dumps({"result": "error"})

def cpm1_get_cars(token):
    status, text = cpm1_api(token, "GetAllCars2", None)
    if status != 200:
        return None
    try:
        result = json.loads(json.loads(text)["result"])
        return result if isinstance(result, list) else None
    except:
        return None

def cpm1_get_garage_slot(token):
    for attempt in range(5):
        try:
            status, text = cpm1_api(token, "WSGetCarListV3", 20)
            if status == 200:
                try:
                    data = json.loads(text)
                    result = json.loads(data['result'])
                    if result and isinstance(result, list) and len(result) > 0:
                        # Search for empty slot
                        for slot in result:
                            if slot.get('carID', 0) == 0:
                                return slot
                        # If no empty slot, use first
                        return result[0]
                except:
                    pass
        except:
            pass
        time.sleep(0.5)
    
    # Final attempt without car
    try:
        status, text = cpm1_api(token, "WSGetCarListV3", 20)
        if status == 200:
            try:
                data = json.loads(text)
                result = json.loads(data['result'])
                if result and isinstance(result, list) and len(result) > 0:
                    return result[0]
            except:
                pass
    except:
        pass
    
    return None

def cpm1_clone_car(token_target, car_data, target_uid):
    cid = car_data.get('CarID', 0)
    car = json.loads(json.dumps(car_data))
    car['police'] = True
    car['engineID'] = 5
    car['cdi'] = True
    car['isLocked'] = False
    car['torque'] = 3000.0
    car['brake'] = 3000.0
    car['mass'] = 1100.0
    try:
        if 'texts' in car and isinstance(car['texts'], list) and len(car['texts']) > 2:
            car['texts'][2] = f"{target_uid[:8].upper()}_{cid}_HZ"
        elif 'texts' in car and isinstance(car['texts'], str):
            car['texts'] = ["", "", f"{target_uid[:8].upper()}_{cid}_HZ"]
    except:
        pass
    try:
        if isinstance(car.get('Vynils'), dict):
            car['Vynils']['CarID'] = cid
    except:
        pass
    slot = cpm1_get_garage_slot(token_target)
    if not slot:
        return False
    payload = {
        "ownerID": slot.get('ownerID', ''),
        "ownerName": slot.get('ownerName', ''),
        "description": slot.get('description', ''),
        "CarID": slot.get('carID', 0),
        "carGeneratedID": slot.get('carGeneratedID', ''),
        "ownerAccountID": slot.get('ownerAccountID', ''),
        "oneCar": car,
        "vynilOneCar": car.get('Vynils', {}),
        "loadedLocalCar": {"instanceID": random.randint(-999999, -100000)},
        "price": slot.get('price', 100),
        "SellingCar": {},
        "willReject": False,
        "dislike": 1,
        "like": 0,
        "liked": False,
        "disliked": False,
        "mode": 1,
    }
    status, text = cpm1_api(token_target, "WSPurchaseCarV3", json.dumps(payload))
    try:
        if status == 200 and json.loads(text).get('result') == 1:
            return True
    except:
        pass
    return False

def cpm1_clone_account(source_email, source_pass, target_email, target_pass):
    source_token, source_uid = verify_user(source_email, source_pass)
    if not source_token:
        return False, {"error": "Failed to login to source", "total": 0, "success": 0, "fail": 0}
    cars = cpm1_get_cars(source_token)
    if not cars or len(cars) == 0:
        return False, {"error": "Source account has no cars", "total": 0, "success": 0, "fail": 0}
    total_cars = len(cars)
    target_token, target_uid = verify_user(target_email, target_pass)
    if not target_token:
        return False, {"error": "Failed to login to target", "total": 0, "success": 0, "fail": 0}
    success_count = 0
    fail_count = 0
    for idx, car in enumerate(cars):
        if not isinstance(car, dict):
            continue
        if cpm1_clone_car(target_token, car, target_uid):
            success_count += 1
        else:
            fail_count += 1
        time.sleep(0.5)
    result_data = {"total": total_cars, "success": success_count, "fail": fail_count}
    if success_count == total_cars:
        return True, result_data
    elif success_count > 0:
        return "partial", result_data
    else:
        return False, result_data

SOURCE_ACCOUNT = ('hz.t0zrj@hzshop.com', '112233')

def cpm1_inject_car(email, password, car_id):
    try:
        # Login
        tok, uid = verify_user(email, password)
        if not tok:
            print(f"Failed to login: {email}")
            return False
        
        # Login to source account
        stok, _ = verify_user(*SOURCE_ACCOUNT)
        if not stok:
            print("Failed to login to source account")
            return False
        
        # Get cars from source
        status, text = cpm1_api(stok, "GetAllCars2", None)
        if status != 200:
            print(f"Failed to get cars: {status}")
            return False
        
        try:
            cars = json.loads(json.loads(text)['result'])
        except:
            print("Failed to parse cars")
            return False
        
        if not cars or len(cars) == 0:
            print("No cars in source")
            return False
        
        # Select best car
        tpl = max(cars, key=lambda c: c.get('CarID', 0))
        car = json.loads(json.dumps(tpl))
        car['CarID'] = car_id
        
        # Modify texts
        try:
            if 'texts' in car and isinstance(car['texts'], list) and len(car['texts']) > 2:
                car['texts'][2] = f'{uid[:8].upper()}_{car_id}_HZ'
        except:
            pass
        
        try:
            if isinstance(car.get('Vynils'), dict):
                car['Vynils']['CarID'] = car_id
        except:
            pass
        
        # Get garage slot
        slot = cpm1_get_garage_slot(tok)
        if not slot:
            print("No garage slot available")
            return False
        
        # Build payload
        payload = {
            "ownerID": slot.get('ownerID', ''),
            "ownerName": slot.get('ownerName', ''),
            "description": slot.get('description', ''),
            "CarID": slot.get('carID', 0),
            "carGeneratedID": slot.get('carGeneratedID', ''),
            "ownerAccountID": slot.get('ownerAccountID', ''),
            "oneCar": car,
            "vynilOneCar": car.get('Vynils', {}),
            "loadedLocalCar": {"instanceID": random.randint(-999999, -100000)},
            "price": slot.get('price', 100),
            "SellingCar": {},
            "willReject": False,
            "dislike": 1,
            "like": 0,
            "liked": False,
            "disliked": False,
            "mode": 1,
        }
        
        # Purchase car
        status, text = cpm1_api(tok, 'WSPurchaseCarV3', json.dumps(payload))
        
        try:
            result = json.loads(text)
            if status == 200 and result.get('result') == 1:
                return True
            else:
                print(f"Purchase failed: {text}")
                return False
        except:
            print(f"Purchase failed: {text}")
            return False
            
    except Exception as e:
        print(f"Inject car error: {e}")
        return False

def cpm1_inject_cars_auto(email, password, car_ids, progress_callback=None):
    success_count = 0
    fail_count = 0
    total = len(car_ids)
    for idx, cid in enumerate(car_ids, 1):
        res = cpm1_inject_car(email, password, cid)
        if res:
            success_count += 1
        else:
            fail_count += 1
        if progress_callback:
            progress_callback(idx, total, success_count, fail_count)
        time.sleep(1.5)
    return success_count, fail_count

# ═══════════════════════════════════════════════════════════
# 🌐 HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════

nuker = CPMNuker()

def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

user_sessions = {}
user_states = {}
banned_users = set()
user_logs = []
total_users = set()
saved_accounts = {}
user_cpm_version = {}


# ═══════════════════════════════════════════════════════════
# ⭐ TELEGRAM STARS + VIP SYSTEM
# ═══════════════════════════════════════════════════════════
STARS_CURRENCY = "XTR"
VIP_PLANS = {
    "1d": {"days": 1, "stars": 5, "title": "VIP 1 Day"},
    "7d": {"days": 7, "stars": 25, "title": "VIP 7 Days"},
    "14d": {"days": 14, "stars": 45, "title": "VIP 14 Days"},
    "30d": {"days": 30, "stars": 80, "title": "VIP 30 Days"},
}
STARS_DB_PATH = "maskyy_stars.db"

def init_stars_db():
    with sqlite3.connect(STARS_DB_PATH) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS vip_users (
            user_id INTEGER PRIMARY KEY,
            expires_at REAL NOT NULL,
            plan_code TEXT,
            updated_at REAL NOT NULL
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS star_payments (
            telegram_payment_charge_id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            plan_code TEXT NOT NULL,
            stars INTEGER NOT NULL,
            currency TEXT NOT NULL,
            paid_at REAL NOT NULL
        )""")
        conn.commit()
        conn.execute("CREATE INDEX IF NOT EXISTS idx_star_payments_paid_at ON star_payments(paid_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_star_payments_plan ON star_payments(plan_code)")
        conn.commit()

def get_vip_expiry(user_id):
    with sqlite3.connect(STARS_DB_PATH) as conn:
        row = conn.execute("SELECT expires_at FROM vip_users WHERE user_id=?", (user_id,)).fetchone()
    return float(row[0]) if row else 0.0

def is_vip(user_id):
    return get_vip_expiry(user_id) > time.time()

def activate_vip(user_id, plan_code):
    plan = VIP_PLANS[plan_code]
    now = time.time()
    base = max(now, get_vip_expiry(user_id))
    expires_at = base + (plan["days"] * 86400)
    with sqlite3.connect(STARS_DB_PATH) as conn:
        conn.execute("""INSERT INTO vip_users (user_id, expires_at, plan_code, updated_at)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(user_id) DO UPDATE SET
                        expires_at=excluded.expires_at,
                        plan_code=excluded.plan_code,
                        updated_at=excluded.updated_at""",
                     (user_id, expires_at, plan_code, now))
        conn.commit()
    return expires_at

def activate_vip_for_seconds(user_id, duration_seconds, plan_code="vip_key"):
    """Activate VIP for a custom duration, used by VIP keys."""
    now = time.time()
    base = max(now, get_vip_expiry(user_id))
    expires_at = base + max(1, int(duration_seconds))
    with sqlite3.connect(STARS_DB_PATH) as conn:
        conn.execute("""INSERT INTO vip_users (user_id, expires_at, plan_code, updated_at)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(user_id) DO UPDATE SET
                        expires_at=excluded.expires_at,
                        plan_code=excluded.plan_code,
                        updated_at=excluded.updated_at""",
                     (user_id, expires_at, plan_code, now))
        conn.commit()
    return expires_at

def format_vip_expiry(expires_at):
    return datetime.fromtimestamp(expires_at).strftime("%d %b %Y • %H:%M:%S")

def is_duplicate_payment(charge_id):
    with sqlite3.connect(STARS_DB_PATH) as conn:
        row = conn.execute("SELECT 1 FROM star_payments WHERE telegram_payment_charge_id=?", (charge_id,)).fetchone()
    return row is not None

def save_star_payment(charge_id, user_id, plan_code, stars, currency):
    with sqlite3.connect(STARS_DB_PATH) as conn:
        conn.execute("""INSERT INTO star_payments
                        (telegram_payment_charge_id, user_id, plan_code, stars, currency, paid_at)
                        VALUES (?, ?, ?, ?, ?, ?)""",
                     (charge_id, user_id, plan_code, stars, currency, time.time()))
        conn.commit()

def create_vip_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        types.InlineKeyboardButton("⭐ 1 DAY • 5 Stars", callback_data="vip_buy_1d"),
        types.InlineKeyboardButton("⭐ 7 DAYS • 25 Stars", callback_data="vip_buy_7d")
    )
    markup.row(
        types.InlineKeyboardButton("⭐ 14 DAYS • 45 Stars", callback_data="vip_buy_14d"),
        types.InlineKeyboardButton("⭐ 30 DAYS • 80 Stars", callback_data="vip_buy_30d")
    )
    return markup

def send_vip_invoice(chat_id, user_id, plan_code):
    plan = VIP_PLANS.get(plan_code)
    if not plan:
        raise ValueError("Invalid VIP plan")
    payload = f"vip:{user_id}:{plan_code}"
    prices = [types.LabeledPrice(label=plan["title"], amount=plan["stars"])]
    # Telegram Stars digital-goods invoice. No provider token is required for XTR.
    bot.send_invoice(
        chat_id,
        plan["title"],
        f"Premium access for {plan['days']} day(s). VIP is activated automatically after successful payment.",
        payload,
        "",
        STARS_CURRENCY,
        prices
    )

def telegram_bot_api(method, payload=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    response = requests.post(url, json=payload or {}, timeout=20)
    data = response.json()
    if not data.get("ok"):
        raise RuntimeError(data.get("description", "Telegram API request failed"))
    return data.get("result")

def get_star_balance():
    return telegram_bot_api("getMyStarBalance")

def get_star_transactions(limit=10):
    return telegram_bot_api("getStarTransactions", {"limit": max(1, min(int(limit), 100))})

def get_stars_revenue_stats(days=30):
    now = time.time()
    start_today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    start_window = now - max(1, int(days)) * 86400
    start_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0).timestamp()
    with sqlite3.connect(STARS_DB_PATH) as conn:
        total_stars, total_orders = conn.execute("SELECT COALESCE(SUM(stars),0), COUNT(*) FROM star_payments").fetchone()
        today_stars, today_orders = conn.execute("SELECT COALESCE(SUM(stars),0), COUNT(*) FROM star_payments WHERE paid_at>=?", (start_today,)).fetchone()
        month_stars, month_orders = conn.execute("SELECT COALESCE(SUM(stars),0), COUNT(*) FROM star_payments WHERE paid_at>=?", (start_month,)).fetchone()
        window_stars, window_orders = conn.execute("SELECT COALESCE(SUM(stars),0), COUNT(*) FROM star_payments WHERE paid_at>=?", (start_window,)).fetchone()
        plans = conn.execute("SELECT plan_code, COALESCE(SUM(stars),0), COUNT(*) FROM star_payments GROUP BY plan_code ORDER BY SUM(stars) DESC").fetchall()
        daily = conn.execute("SELECT strftime('%Y-%m-%d', paid_at, 'unixepoch', 'localtime'), COALESCE(SUM(stars),0), COUNT(*) FROM star_payments WHERE paid_at>=? GROUP BY 1 ORDER BY 1 DESC LIMIT 7", (now-7*86400,)).fetchall()
        recent = conn.execute("SELECT user_id, plan_code, stars, paid_at FROM star_payments ORDER BY paid_at DESC LIMIT 10").fetchall()
    return {"total_stars":int(total_stars),"total_orders":int(total_orders),"today_stars":int(today_stars),"today_orders":int(today_orders),"month_stars":int(month_stars),"month_orders":int(month_orders),"window_stars":int(window_stars),"window_orders":int(window_orders),"plans":plans,"daily":daily,"recent":recent,"days":int(days)}

def show_stars_revenue_dashboard(chat_id):
    st = get_stars_revenue_stats(30)
    avg = st["total_stars"] / st["total_orders"] if st["total_orders"] else 0
    text = ("📈 **STARS REVENUE STATISTICS**\n━━━━━━━━━━━━━━━━━━━━━\n"
            f"⭐ Total Revenue: **{st['total_stars']} Stars**\n"
            f"🧾 Total Orders: **{st['total_orders']}**\n"
            f"📊 Average / Order: **{avg:.1f} Stars**\n\n"
            f"🌞 Today: **{st['today_stars']} Stars** • {st['today_orders']} orders\n"
            f"📅 This Month: **{st['month_stars']} Stars** • {st['month_orders']} orders\n"
            f"🗓 Last 30 Days: **{st['window_stars']} Stars** • {st['window_orders']} orders\n")
    if st['plans']:
        text += "\n💎 **Revenue by VIP Plan:**\n"
        for plan_code, stars, orders in st['plans'][:10]:
            title = VIP_PLANS.get(plan_code, {}).get('title', plan_code)
            text += f"• {title}: **{int(stars)} ⭐** • {orders} orders\n"
    if st['daily']:
        text += "\n📆 **Last 7 Days:**\n"
        for day, stars, orders in st['daily']:
            text += f"• `{day}` — **{int(stars)} ⭐** ({orders})\n"
    if st['recent']:
        text += "\n🧾 **Recent Payments:**\n"
        for uid, plan_code, stars, paid_at in st['recent'][:5]:
            text += f"• `{uid}` • {VIP_PLANS.get(plan_code, {}).get('title', plan_code)} • **{int(stars)} ⭐**\n"
    bot.send_message(chat_id, text[:3900], parse_mode='Markdown')

init_stars_db()

# ═══════════════════════════════════════════════════════════
# 📢 ADMIN NOTIFICATION FUNCTION
# ═══════════════════════════════════════════════════════════

def notify_admins(message_text, parse_mode='Markdown'):
    # Neon Gaming styled admin notification
    notification_time = datetime.now().strftime("%d %b %Y • %H:%M:%S")
    notification = (
        "╔══════════════════════════════╗\n"
        "║      🔔 *NEW NOTIFICATION*      ║\n"
        "╚══════════════════════════════╝\n"
        "┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃ 🕒 *TIME* : `{notification_time}`\n"
        "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        "⚡ *NOTIFICATION DETAILS*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{message_text}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎮 *@MasKyyOfficial • 𝗠𝗮𝘀𝗞𝘆𝘆𝗢𝗙𝗙𝗖 || 𝗕𝗢𝗧*"
    )

    for admin_id in ADMIN_IDS:
        try:
            bot.send_message(
                admin_id,
                notification,
                parse_mode=parse_mode,
                disable_web_page_preview=True
            )
        except Exception as e:
            print(f"Failed to notify admin {admin_id}: {e}")

# ═══════════════════════════════════════════════════════════
# 🔑 TIME KEY FUNCTIONS
# ═══════════════════════════════════════════════════════════

def generate_time_key():
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=16))

def create_time_key(duration_hours: int, created_by: int) -> str:
    key = generate_time_key()
    TIME_KEYS[key] = {
        "expires": datetime.now() + timedelta(hours=duration_hours),
        "duration": duration_hours,
        "used": False,
        "user_id": None,
        "created_by": created_by,
        "created_at": datetime.now(),
        "key_type": "time"
    }
    return key

def use_time_key(key: str, user_id: int) -> Tuple[bool, str]:
    if key not in TIME_KEYS:
        return False, "Key not found"
    
    key_data = TIME_KEYS[key]
    
    # Check if expired
    if datetime.now() > key_data["expires"]:
        return False, "Key has expired"
    
    # If key was used before
    if key_data["used"]:
        # Check: same user who used it before
        if key_data["user_id"] == user_id:
            return True, "Key is still valid for you"
        else:
            return False, "Key already used by another user"
    
    # First time using this key
    key_data["used"] = True
    key_data["user_id"] = user_id
    return True, "Key activated successfully"

def get_time_key_info(key: str) -> Dict[str, Any]:
    if key not in TIME_KEYS:
        return None
    return TIME_KEYS[key]

# ═══════════════════════════════════════════════════════════
# 💎 VIP KEY FUNCTIONS
# ═══════════════════════════════════════════════════════════

def generate_vip_key():
    """Generate a branded, unique VIP key for automatic and manual VIP sales."""
    prefix = "MasKyyOFFC"
    existing_keys = set(TRIAL_KEYS) | set(TIME_KEYS) | set(ALLOWED_KEYS)
    while True:
        # 3 unique random digits, e.g. MasKyyOFFC-482
        unique_digits = ''.join(random.choices(string.digits, k=3))
        key = f"{prefix}-{unique_digits}"
        if key not in existing_keys:
            return key

VIP_KEY_UNITS = {
    "minutes": 60,
    "hours": 3600,
    "days": 86400,
}

def vip_duration_label(value, unit):
    value = int(value)
    singular = unit[:-1] if value == 1 else unit
    return f"{value} {singular}"

def create_vip_key(user_id=None, duration=10, unit="minutes"):
    """Create a VIP key with a custom VIP duration.

    The key can be redeemed once. The VIP duration starts when the user first
    redeems the key, so an admin can safely create keys in advance.
    """
    if unit not in VIP_KEY_UNITS:
        raise ValueError("Invalid VIP key duration unit")
    duration = int(duration)
    if duration <= 0:
        raise ValueError("VIP duration must be greater than 0")

    duration_seconds = duration * VIP_KEY_UNITS[unit]
    key = generate_vip_key()
    while key in TRIAL_KEYS:
        key = generate_vip_key()

    now = datetime.now()
    TRIAL_KEYS[key] = {
        "user_id": user_id,
        # Redemption deadline, separate from the VIP duration after activation.
        "expires": now + timedelta(days=365),
        "used": False,
        "created_at": now,
        "duration": duration,
        "duration_unit": unit,
        "duration_seconds": duration_seconds,
        "duration_label": vip_duration_label(duration, unit),
        "used_at": None,
        "key_type": "vip",
        "locked": False
    }
    return key

def use_vip_key(key, user_id):
    if key not in TRIAL_KEYS:
        return False, "invalid"
    vip_data = TRIAL_KEYS[key]
    if vip_data.get("locked"):
        return False, "locked"
    if datetime.now() > vip_data["expires"]:
        return False, "expired"
    if vip_data["used"] and vip_data["user_id"] != user_id:
        return False, "used_by_other"
    if vip_data["used"] and vip_data["user_id"] == user_id:
        return True, "already_used_same_user"
    TRIAL_KEYS[key]["used"] = True
    TRIAL_KEYS[key]["user_id"] = user_id
    TRIAL_KEYS[key]["used_at"] = datetime.now()
    return True, "success"

def can_use_free_vip_key(user_id):
    # One free VIP-key activation every 5 days, preserving the old cooldown behavior.
    if user_id not in FREE_TRIAL_USERS:
        return True, 0, 0
    last_used = FREE_TRIAL_USERS[user_id]["last_used"]
    days_passed = (datetime.now() - last_used).days
    if days_passed >= 5:
        return True, 0, 0
    next_available = last_used + timedelta(days=5)
    remaining = next_available - datetime.now()
    return False, remaining.days, remaining.seconds // 3600

def register_free_vip_key(user_id):
    FREE_TRIAL_USERS[user_id] = {
        "last_used": datetime.now(),
        "count": FREE_TRIAL_USERS.get(user_id, {}).get("count", 0) + 1
    }

# ═══════════════════════════════════════════════════════════
# 📋 FORMATTING FUNCTIONS
# ═══════════════════════════════════════════════════════════

def format_account_info(info: Dict[str, Any]) -> str:
    """Neon Gaming account HUD for CPM1."""
    if not info.get("ok"):
        return (
            "┏━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
            "┃ 🚨 **SYSTEM // ACCOUNT ERROR** 🚨 ┃\n"
            "┣━━━━━━━━━━━━━━━━━━━━━━━━━━┫\n"
            "┃ ❌ Account data unavailable\n"
            "┃ 🔄 Use **Refresh** and try again\n"
            "┗━━━━━━━━━━━━━━━━━━━━━━━━━━┛"
        )

    name = info.get("name", "Unknown")
    player_id = info.get("localID", "Unknown")
    email = info.get("email", "Unknown")
    money = info.get("money", 0)
    coin = info.get("coin", 0)

    return (
        "╔══════════════════════════════╗\n"
        "║ ⚡ **𝗠𝗮𝘀𝗞𝘆𝘆 // PLAYER HUD** ⚡ ║\n"
        "║      🎮 𝗠𝗮𝘀𝗞𝘆𝘆𝗢𝗙𝗙𝗖 || 𝗕𝗢𝗧 🎮      ║\n"
        "╠══════════════════════════════╣\n"
        f"║ 👤 **PLAYER**  `{name}`\n"
        f"║ 🆔 **ID**      `{player_id}`\n"
        f"║ 📧 **EMAIL**   `{email}`\n"
        "╠══════════════════════════════╣\n"
        f"║ 💰 **CASH**    `{money:,}`\n"
        f"║ 💎 **COINS**   `{coin:,}`\n"
        "╚══════════════════════════════╝"
    )

def get_text(chat_id, key, **kwargs):
    # Neon Gaming visual theme — callbacks and business logic remain unchanged.
    texts = {
        "welcome": "╔══════════════════════════════╗\n║      ⚡ **𝗠𝗮𝘀𝗞𝘆𝘆𝗢𝗙𝗙𝗖** ⚡       ║\n║      🎮 **𝗠𝗮𝘀𝗞𝘆𝘆𝗢𝗙𝗙𝗖 || 𝗕𝗢𝗧** 🎮      ║\n╠══════════════════════════════╣\n║ 🟣 STATUS : **ONLINE**\n║ 🔵 SYSTEM : **READY**\n║ 🟢 MODE   : **NEXT-GEN CONTROL**\n╚══════════════════════════════╝\n\n🚀 **SELECT YOUR ACCESS MODE**\n_Enter the arena and power up your session._",
        "cpm1_section": "╔══════════════════════════════╗\n║ ⚡ **CPM1 // 𝗠𝗮𝘀𝗞𝘆𝘆 CONTROL** ⚡ ║\n╠══════════════════════════════╣\n║ 🟣 Account Modules\n║ 🔵 Advanced Features\n║ 🟢 Live Control Console\n╚══════════════════════════════╝",
        "cpm2_section": "╔══════════════════════════════╗\n║ 🎮 **CPM2 // GAMING MODULE** 🎮 ║\n╠══════════════════════════════╣\n║ 🟣 Rank System\n║ 🔵 Account Generator\n║ 🟢 Utility Console\n╚══════════════════════════════╝",
        "back": "◀️ BACK",
        "not_logged": "🚫 **ACCESS LOCKED** — Login via /start first.",
        "not_logged_short": "🚫 **ACCESS LOCKED**",
        "login_cpm_success": "🟢 **CPM1 CONNECTED // ACCESS GRANTED**",
        "login_cpm_fail": "🔴 **CPM1 CONNECTION FAILED**",
        "login_cpm2_success": "🟢 **CPM2 CONNECTED // ACCESS GRANTED**",
        "login_cpm2_fail": "🔴 **CPM2 CONNECTION FAILED**",
        "key_success": "🟢 **KEY VERIFIED // SYSTEM UNLOCKED**",
        "wrong_key": "🔴 **INVALID KEY // ACCESS DENIED**",
        "key_title": "╔══════════════════════════════╗\n║ 🔑 **ACTIVATION TERMINAL** 🔑 ║\n╠══════════════════════════════╣\n║ Enter your access key below.\n╚══════════════════════════════╝",
        "enter_pass": "╔══════════════════════════════╗\n║ 🔐 **SECURITY TERMINAL** 🔐 ║\n╠══════════════════════════════╣\n║ Enter your account password.\n╚══════════════════════════════╝",
        "email_prompt": "╔══ ⚡ **{section} LOGIN** ⚡ ══╗\n📧 **ENTER ACCOUNT EMAIL**",
        "king_email_prompt": "👑 **KING RANK TERMINAL**\n📧 Enter CPM1 email:",
        "king_pass_prompt": "🔐 **SECURITY CHECK**\nEnter CPM1 password:",
        "king_rank_success": "🟢 **RANK UPDATED** // {msg}",
        "king_rank_fail": "🔴 **RANK UPDATE FAILED** // {msg}",
        "money_added": "🟢 **CASH INJECTED** // `{amount}`",
        "money_fail": "🔴 **CASH INJECTION FAILED**",
        "id_changed": "🟢 **PLAYER ID UPDATED** // `{new_id}`",
        "id_fail": "🔴 **ID UPDATE FAILED**",
        "email_changed": "🟢 **EMAIL UPDATED** // `{new_email}`",
        "email_fail": "🔴 **EMAIL UPDATE FAILED**",
        "pass_changed": "🟢 **PASSWORD UPDATED**",
        "pass_fail": "🔴 **PASSWORD UPDATE FAILED**",
        "clone_success": "🟢 **CLONE COMPLETE**\n🚗 `{success}/{total}` cars processed",
        "clone_fail": "🔴 **CLONE FAILED**\n💀 `{error}`",
        "unlock_cars_done": "🟢 **GARAGE UNLOCKED**",
        "unlock_cars_fail": "🔴 **GARAGE UNLOCK FAILED**",
        "unlock_cars_auto_done": "🟢 **AUTO INJECTION COMPLETE** // `{success}/270`",
        "logout": "🟣 **SESSION TERMINATED**",
        "free_trial_first": "💎 **VIP KEY MODE ACTIVE** // 10 MINUTES",
        "trial_activating": "⚡ **INITIALIZING VIP KEY MODE...**",
        "start_normal_key": "🔑 KEY ACCESS",
        "start_time_key": "⏱️ TIME ACCESS",
        "start_free_trial": "💎 VIP KEY",
        "main_cpm1": "⚡ CPM1 ARENA",
        "main_cpm2": "🎮 CPM2 ARENA",
        "cpm1_change_email_btn": "📧 Change Email",
        "cpm1_change_pass_btn": "🔐 Change Password",
        "cpm1_clone_btn": "🧬 Clone Account",
        "cpm1_unlock_cars_btn": "🚗 Unlock Garage",
        "cpm1_w16_btn": "⚡ W16 Engine",
        "cpm1_horns_btn": "📯 HORNS",
        "cpm1_fuel_btn": "⛽ Unlimited Fuel",
        "cpm1_damage_btn": "🛡️ ARMOR",
        "cpm1_smoke_btn": "💨 SMOKE",
        "cpm1_rank_btn": "👑 KING RANK",
        "cpm1_fix_btn": "🔧 FIX",
        "cpm1_change_id_btn": "🆔 CHANGE ID",
        "cpm1_money_btn": "💰 Add Money",
        "cpm1_coin_btn": "💎 Add Coins",
        "cpm1_unlock_animations_btn": "🎭 FX",
        "cpm1_unlock_wheels_btn": "🛞 WHEELS",
        "cpm1_unlock_houses_btn": "🏠 HOUSES",
        "cpm1_complete_levels_btn": "🏆 LEVELS",
        "cpm1_unlock_equip_male_btn": "👨 MALE GEAR",
        "cpm1_unlock_equip_female_btn": "👩 FEMALE GEAR",
        "cpm1_ultimate_btn": "💀 ULTIMATE UNLOCK",
        "cpm2_king_rank_btn": "👑 KING RANK CPM2",
        "cpm2_generate_btn": "🎲 GENERATE ACCOUNT",
        "admin_panel": "╔══════════════════════════════╗\n║ 👑 **ADMIN // COMMAND CORE** 👑 ║\n╠══════════════════════════════╣\n║ 📊 Analytics & Statistics\n║ 🔑 Access Management\n║ 🛡️ Security & Moderation\n╚══════════════════════════════╝",
        "not_admin": "🚫 **ADMIN ACCESS DENIED**",
        "refresh_account": "🔄 SYNC ACCOUNT",
        "unlock_cars_auto_confirm": "╔══ 🤖 **AUTO INJECTION** ══╗\n⚡ Target: **270 cars**\n📡 System ready. Start process?",
        "unlock_cars_auto_yes": "⚡ START",
        "unlock_cars_auto_cancel": "✖️ CANCEL",
        "unlock_cars_manual_prompt": "🖐️ **MANUAL INJECTION**\n🆔 Enter Car ID:",
        "unlock_cars_prompt": "╔══════════════════════════════╗\n║ 🚗 **GARAGE UNLOCK TERMINAL** 🚗 ║\n╠══════════════════════════════╣\n║ 📧 Account: `{email}`\n╚══════════════════════════════╝\n\n⚡ Choose injection mode.",
        "time_key_title": "╔══ ⏱️ **TIME ACCESS** ══╗\nEnter your temporary access key."
    }
    text = texts.get(key, f"Missing text: {key}")
    if kwargs:
        try:
            text = text.format(**kwargs)
        except Exception:
            pass
    return text

def is_admin(chat_id):
    return chat_id in ADMIN_IDS

def is_banned(chat_id):
    return chat_id in banned_users

def add_log(chat_id, action):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    user_logs.append(f"[{timestamp}] User {chat_id}: {action}")
    if len(user_logs) > 100:
        user_logs.pop(0)

def save_account(chat_id, email, password, player_id=None, name=None):
    if chat_id not in saved_accounts:
        saved_accounts[chat_id] = []
    account_data = {
        "email": email,
        "password": password,
        "player_id": player_id,
        "name": name,
        "saved_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    for acc in saved_accounts[chat_id]:
        if acc["email"] == email:
            acc.update(account_data)
            return
    saved_accounts[chat_id].append(account_data)

def check_subscription(chat_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, chat_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

def subscription_required(message):
    chat_id = message.chat.id
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton("📢 JOIN CHANNEL", url=CHANNEL_LINK)
    btn2 = types.InlineKeyboardButton("🟢 VERIFY ACCESS", callback_data="check_sub")
    markup.add(btn1, btn2)
    bot.send_message(
        chat_id,
        "╭══════════════════════════════╮\n"
        "│       📢 **CHANNEL ACCESS**         │\n"
        "╠══════════════════════════════╣\n"
        "│ To use the bot, please      │\n"
        "│ bergabung ke channel resmi terlebih │\n"
        "│ dahulu. Setelah itu tekan Verify.   │\n"
        "╚══════════════════════════════╝\n\n"
        "📣 **Official Channel:** [𝗠𝗮𝘀𝗞𝘆𝘆𝗢𝗙𝗙𝗖](https://t.me/MasKyyOFFC)",
        reply_markup=markup,
        parse_mode='Markdown'
    )

def refresh_account_data(chat_id):
    """Force refresh account data for a user"""
    if chat_id not in user_sessions or not user_sessions[chat_id].get('logged_in'):
        return False, "Not logged in"
    
    web_uid = user_sessions[chat_id].get('web_uid')
    if not web_uid:
        return False, "No web UID"
    
    email = user_sessions[chat_id].get('email')
    if not email:
        return False, "No email"
    
    try:
        # Delete local cache
        ck = nuker._ck(web_uid, email)
        if ck in nuker.cache:
            del nuker.cache[ck]
        
        # Load fresh data from server
        success = run_async(nuker.load_account(web_uid, force=True))
        if success:
            return True, "Data refreshed successfully"
        else:
            return False, "Failed to load data from server"
    except Exception as e:
        return False, f"Error: {str(e)}"

# ═══════════════════════════════════════════════════════════
# 🎮⚡ NEON GAMING KEYBOARDS
# ═══════════════════════════════════════════════════════════

def create_start_keyboard(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        types.InlineKeyboardButton("🟣 KEY ACCESS", callback_data="normal_key"),
        types.InlineKeyboardButton("🔵 TIME KEY", callback_data="time_key")
    )
    markup.row(types.InlineKeyboardButton("⭐ BUY VIP WITH STARS", callback_data="buy_vip"))
    markup.row(types.InlineKeyboardButton("💎 FREE VIP KEY", callback_data="free_trial"))
    markup.row(types.InlineKeyboardButton("💎 CONTACT OWNER", url=OWNER_CONTACT))
    return markup

def create_main_keyboard(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    if is_admin(chat_id):
        markup.row(types.InlineKeyboardButton("👑 ADMIN CORE", callback_data="admin_panel"))
    markup.row(
        types.InlineKeyboardButton("⚡ CPM1 ARENA", callback_data="section_cpm1"),
        types.InlineKeyboardButton("🎮 CPM2 ARENA", callback_data="section_cpm2")
    )
    markup.row(types.InlineKeyboardButton("⛔ EXIT SESSION", callback_data="logout"))
    return markup

def create_cpm1_keyboard(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=2)

    account_buttons = [
        ("📧 EMAIL", "cpm1_change_email"),
        ("🔐 PASSWORD", "cpm1_change_pass"),
        ("🧬 CLONE", "cpm1_clone"),
        ("🚗 GARAGE", "cpm1_unlock_cars"),
    ]
    feature_buttons = [
        ("⚡ W16 BOOST", "cpm1_w16"),
        ("📯 HORNS", "cpm1_horns"),
        ("⛽ FUEL", "cpm1_fuel"),
        ("🛡️ ARMOR", "cpm1_damage"),
        ("💨 SMOKE", "cpm1_smoke"),
        ("👑 KING RANK", "cpm1_rank_advanced"),
        ("🔧 FIX", "cpm1_fix"),
        ("🆔 CHANGE ID", "cpm1_change_id"),
        ("💰 CASH", "cpm1_money"),
        ("💎 COINS", "cpm1_coin"),
        ("🎭 FX", "cpm1_unlock_animations"),
        ("🛞 WHEELS", "cpm1_unlock_wheels"),
        ("🏠 HOUSES", "cpm1_unlock_houses"),
        ("🏆 LEVELS", "cpm1_complete_levels"),
        ("👨 MALE GEAR", "cpm1_unlock_equip_male"),
        ("👩 FEMALE GEAR", "cpm1_unlock_equip_female"),
    ]

    for group in (account_buttons, feature_buttons):
        for i in range(0, len(group), 2):
            markup.row(*[
                types.InlineKeyboardButton(label, callback_data=data)
                for label, data in group[i:i + 2]
            ])

    markup.row(types.InlineKeyboardButton("💀 ULTIMATE MODE", callback_data="cpm1_ultimate"))
    markup.row(
        types.InlineKeyboardButton("🔄 SYNC", callback_data="refresh_account"),
        types.InlineKeyboardButton("🏠 HUB", callback_data="back_main")
    )
    return markup

def create_cpm2_keyboard(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        types.InlineKeyboardButton("👑 KING RANK", callback_data="cpm2_king_rank"),
        types.InlineKeyboardButton("🎲 GENERATE", callback_data="cpm2_generate")
    )
    markup.row(types.InlineKeyboardButton("🏠 HUB", callback_data="back_main"))
    return markup

def create_unlock_cars_keyboard(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        types.InlineKeyboardButton("✍️ MANUAL", callback_data="unlock_manual"),
        types.InlineKeyboardButton("🤖 AUTO 1–270", callback_data="unlock_auto")
    )
    markup.row(types.InlineKeyboardButton("◀️ CPM1 HUB", callback_data="back_cpm1"))
    return markup

def create_unlock_auto_confirm_keyboard(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        types.InlineKeyboardButton("⚡ START", callback_data="unlock_auto_confirm"),
        types.InlineKeyboardButton("✖️ CANCEL", callback_data="unlock_auto_cancel")
    )
    return markup

def create_admin_keyboard(chat_id):
    """Neon Gaming style main admin menu. VIP tools stay in a separate menu."""
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        ("📊  STATS", "admin_stats"),
        ("📢  BROADCAST", "admin_broadcast"),
        ("🔑  KEYS", "admin_keys"),
        ("⏱️  TIME KEYS", "admin_time_keys"),
        ("📈  ANALYTICS", "admin_key_stats"),
        ("👥  USERS", "admin_key_users"),
        ("🔄  REFRESH ALL", "admin_refresh_all"),
        ("🚫  BAN", "admin_ban"),
        ("🟢  UNBAN", "admin_unban"),
        ("📝  LOGS", "admin_logs"),
        ("💾  SAVED", "admin_saved"),
        ("⚙️  SYSTEM", "admin_status"),
        ("⭐  STARS", "admin_stars"),
        ("📈  STARS REVENUE", "admin_stars_revenue"),
    ]
    for i in range(0, len(buttons), 2):
        markup.row(*[
            types.InlineKeyboardButton(label, callback_data=data)
            for label, data in buttons[i:i + 2]
        ])

    markup.row(types.InlineKeyboardButton("💎  ║ VIP CONTROL CENTER ║  💎", callback_data="admin_vip_menu"))
    markup.row(types.InlineKeyboardButton("📜  STAR HISTORY", callback_data="admin_star_history"))
    markup.row(types.InlineKeyboardButton("🏠  HUB", callback_data="back_main"))
    return markup


def create_vip_admin_keyboard(chat_id):
    """Dedicated Neon Gaming style VIP control center."""
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        ("💎  VIP KEYS", "admin_vip_keys"),
        ("➕  CREATE VIP KEY", "admin_create_vip_key"),
        ("🗑  DELETE VIP KEY", "admin_delete_vip_key"),
        ("➕  EXTEND VIP KEY", "admin_extend_vip_key"),
        ("🔐  LOCK VIP KEY", "admin_lock_vip_key"),
        ("🔓  UNLOCK VIP KEY", "admin_unlock_vip_key"),
        ("👑  ACTIVE VIP", "admin_active_vip"),
        ("🔎  VIP SEARCH", "admin_vip_search"),
        ("♻️  RESET VIP", "admin_reset_vip"),
        ("📤  EXPORT VIP", "admin_export_vip"),
        ("📊  VIP DASHBOARD", "admin_vip_dashboard"),
        ("🧹  CLEANUP VIP", "admin_cleanup_vip"),
        ("💾  BACKUP VIP", "admin_backup_vip"),
    ]
    for i in range(0, len(buttons), 2):
        markup.row(*[
            types.InlineKeyboardButton(label, callback_data=data)
            for label, data in buttons[i:i + 2]
        ])
    markup.row(types.InlineKeyboardButton("◀️  BACK TO ADMIN", callback_data="admin_panel"))
    markup.row(types.InlineKeyboardButton("🏠  HUB", callback_data="back_main"))
    return markup


def admin_neon_text():
    return (
        "⚡ **M A S K Y Y   O F F C** ⚡\n"
        "╔══════════════════════════╗\n"
        "║   🛡️  **ADMIN CONTROL PANEL**  🛡️   ║\n"
        "╚══════════════════════════╝\n\n"
        "```[ SYSTEM ONLINE ]```\n"
        "🟢 Status  : **ACTIVE**\n"
        "🎮 Mode    : **NEON GAMING**\n"
        "👑 Access  : **ADMIN**\n\n"
        "╭─〔 🎯 **COMMAND CORE** 〕─╮\n"
        "│ 📊 Statistics & Analytics\n"
        "│ 🔑 Keys & Time Management\n"
        "│ 👥 Users & Moderation\n"
        "│ ⭐ Stars & Revenue\n"
        "╰──────────────────────────╯\n\n"
        "💎 **VIP CONTROL CENTER** tersedia di menu terpisah."
    )


def show_vip_admin_menu(chat_id):
    text = (
        "💎⚡ **VIP CONTROL CENTER** ⚡💎\n"
        "╔══════════════════════════╗\n"
        "║      👑 **MASKYY VIP SYSTEM**      ║\n"
        "╚══════════════════════════╝\n\n"
        "```[ VIP MODULE ONLINE ]```\n"
        "🔮 Status   : **READY**\n"
        "🛡️ Security : **PROTECTED**\n"
        "🎮 Interface: **NEON GAMING**\n\n"
        "╭─〔 🔑 **KEY CONTROL** 〕─╮\n"
        "│ CREATE • DELETE • EXTEND\n"
        "│ LOCK • UNLOCK • SEARCH\n"
        "╰──────────────────────────╯\n"
        "╭─〔 👑 **VIP CONTROL** 〕─╮\n"
        "│ ACTIVE • RESET • EXPORT\n"
        "│ DASHBOARD • CLEANUP • BACKUP\n"
        "╰──────────────────────────╯\n\n"
        "⚡ **SELECT YOUR VIP COMMAND BELOW** ⚡"
    )
    bot.send_message(
        chat_id,
        text,
        reply_markup=create_vip_admin_keyboard(chat_id),
        parse_mode='Markdown'
    )

def get_web_uid(telegram_id):
    return int(str(telegram_id)[:12])

def show_cpm1_menu(chat_id, message=None, force_refresh=False):
    if chat_id not in user_sessions or not user_sessions[chat_id].get('logged_in') or user_sessions[chat_id].get('version') != "1":
        bot.send_message(chat_id, "❌ **You must login to CPM1 first!**", parse_mode='Markdown')
        return
    
    web_uid = user_sessions[chat_id].get('web_uid')
    if not web_uid:
        bot.send_message(chat_id, "❌ **Session expired! Login again.**", parse_mode='Markdown')
        return
    
    # If refresh is requested, clear cache and load fresh data
    if force_refresh:
        email = user_sessions[chat_id].get('email')
        if email:
            ck = nuker._ck(web_uid, email)
            if ck in nuker.cache:
                del nuker.cache[ck]
        run_async(nuker.load_account(web_uid, force=True))
    
    info = run_async(nuker.get_account_info(web_uid))
    info_text = format_account_info(info)
    
    full_text = f"{info_text}\n{get_text(chat_id, 'cpm1_section')}"
    
    if message:
        try:
            bot.edit_message_text(full_text, chat_id, message.message_id, reply_markup=create_cpm1_keyboard(chat_id), parse_mode='Markdown')
        except:
            bot.send_message(chat_id, full_text, reply_markup=create_cpm1_keyboard(chat_id), parse_mode='Markdown')
    else:
        bot.send_message(chat_id, full_text, reply_markup=create_cpm1_keyboard(chat_id), parse_mode='Markdown')

def section_cpm1(message):
    chat_id = message.chat.id
    if chat_id not in user_sessions:
        user_sessions[chat_id] = {}
    if user_sessions[chat_id].get('logged_in') and user_sessions[chat_id].get('version') == "1":
        show_cpm1_menu(chat_id)
        return
    bot.send_message(
        chat_id,
        "╭══════════════════════════════╮\n"
        "│        📱 **CPM1 LOGIN**             │\n"
        "╠══════════════════════════════╣\n"
        "│ Log in to open the Control Panel.   │\n"
        "╚══════════════════════════════╝\n\n"
        "📧 **Enter CPM1 email:**",
        parse_mode='Markdown'
    )
    user_cpm_version[chat_id] = "1"
    bot.register_next_step_handler(message, get_email)

def section_cpm2(message):
    chat_id = message.chat.id
    if chat_id not in user_sessions:
        user_sessions[chat_id] = {}
    if user_sessions[chat_id].get('logged_in') and user_sessions[chat_id].get('version') == "2":
        bot.send_message(chat_id, get_text(chat_id, "cpm2_section"), reply_markup=create_cpm2_keyboard(chat_id), parse_mode='Markdown')
        return
    bot.send_message(
        chat_id,
        "╭══════════════════════════════╮\n"
        "│        🎮 **CPM2 LOGIN**             │\n"
        "╠══════════════════════════════╣\n"
        "│ Sign in to unlock CPM2 features.      │\n"
        "╚══════════════════════════════╝\n\n"
        "📧 **Enter CPM2 email:**",
        parse_mode='Markdown'
    )
    user_cpm_version[chat_id] = "2"
    bot.register_next_step_handler(message, get_email)

def admin_panel(message):
    chat_id = message.chat.id
    if not is_admin(chat_id):
        bot.send_message(chat_id, get_text(chat_id, "not_admin"), parse_mode='Markdown')
        return
    markup = create_admin_keyboard(chat_id)
    bot.send_message(chat_id, admin_neon_text(), reply_markup=markup, parse_mode='Markdown')

# ═══════════════════════════════════════════════════════════
# ⭐ STARS / VIP ADMIN DASHBOARD
# ═══════════════════════════════════════════════════════════

def _transaction_summary(tx, index):
    if not isinstance(tx, dict):
        return f"{index}. Transaction data unavailable"
    tx_id = tx.get("id", "-")
    amount = tx.get("amount", "-")
    date = tx.get("date", "-")
    return f"{index}. ⭐ `{amount}` XTR • ID: `{tx_id}` • Date: `{date}`"

def show_stars_dashboard(chat_id, history=False):
    balance = get_star_balance()
    amount = balance.get("amount", 0) if isinstance(balance, dict) else getattr(balance, "amount", balance)
    transactions = get_star_transactions(20 if history else 10)
    tx_list = transactions.get("transactions", []) if isinstance(transactions, dict) else getattr(transactions, "transactions", [])
    title = "📜 **STAR HISTORY**" if history else "⭐ **BOT STARS DASHBOARD**"
    text = (f"{title}\n━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 Balance: **{amount} Stars**\n"
            f"📜 Transactions loaded: **{len(tx_list)}**\n")
    if tx_list:
        text += "\n" + "\n".join(_transaction_summary(tx, i) for i, tx in enumerate(tx_list[:20], 1))
    else:
        text += "\n📭 No transaction history returned by Telegram."
    bot.send_message(chat_id, text[:3900], parse_mode='Markdown')

def show_vip_keys_dashboard(chat_id):
    active = []
    expired = 0
    for key, data in TRIAL_KEYS.items():
        if datetime.now() > data["expires"]:
            expired += 1
        else:
            active.append((key, data))
    text = ("💎 **VIP KEYS DASHBOARD**\n━━━━━━━━━━━━━━━━━━━━━\n"
            f"🟢 Active/valid keys: **{len(active)}**\n"
            f"❌ Expired keys: **{expired}**\n"
            f"👥 Used VIP keys: **{sum(1 for _, d in TRIAL_KEYS.items() if d.get('used'))}**\n")
    if active:
        text += "\n🔑 **Recent VIP Keys:**\n"
        for key, data in active[-10:]:
            status = "👤 Used" if data.get("used") else "⏳ Ready"
            text += f"• `{key}` • {status} • {data.get('duration_label', str(data.get('duration', 10)) + ' min')}\n"
    bot.send_message(chat_id, text, parse_mode='Markdown')


def resolve_vip_key(key):
    """Find the stored VIP key regardless of how the admin/user types its case."""
    normalized = str(key or "").strip().casefold()
    if not normalized:
        return None
    for stored_key in TRIAL_KEYS:
        if stored_key.casefold() == normalized:
            return stored_key
    return None

def delete_vip_key(key):
    stored_key = resolve_vip_key(key)
    if not stored_key:
        return False, "not_found", None
    data = TRIAL_KEYS[stored_key]
    if data.get("key_type") not in ("vip", "trial"):
        return False, "not_vip", None
    del TRIAL_KEYS[stored_key]
    return True, "deleted", stored_key

def extend_vip_key(key, amount, unit):
    key = key.strip().upper()
    if key not in TRIAL_KEYS:
        return False, "not_found"
    if unit not in VIP_KEY_UNITS:
        return False, "invalid_unit"
    amount = int(amount)
    if amount <= 0:
        return False, "invalid_amount"

    data = TRIAL_KEYS[key]
    seconds = amount * VIP_KEY_UNITS[unit]
    data["duration_seconds"] = int(data.get("duration_seconds", 0)) + seconds
    data["duration"] = data["duration_seconds"] // VIP_KEY_UNITS.get(data.get("duration_unit", "minutes"), 60)
    data["duration_label"] = f"{data['duration_seconds']} seconds total"

    # If already redeemed, extend the user's actual VIP expiry immediately.
    user_id = data.get("user_id")
    if data.get("used") and user_id:
        new_expiry = activate_vip_for_seconds(user_id, seconds, "vip_key_extended")
        return True, (seconds, new_expiry)
    return True, (seconds, None)

def show_active_vip_users(chat_id):
    now = time.time()
    with sqlite3.connect(STARS_DB_PATH) as conn:
        rows = conn.execute(
            "SELECT user_id, expires_at, plan_code FROM vip_users WHERE expires_at > ? ORDER BY expires_at DESC LIMIT 50",
            (now,)
        ).fetchall()
    text = "👑 **ACTIVE VIP USERS**\n━━━━━━━━━━━━━━━━━━━━━\n"
    text += f"🟢 Active VIP: **{len(rows)}**\n"
    if not rows:
        text += "\n📭 There are no active VIP users at the moment."
    else:
        text += "\n"
        for i, (user_id, expires_at, plan_code) in enumerate(rows, 1):
            text += f"{i}. 👤 `{user_id}`\n   ⏱️ Until: `{format_vip_expiry(expires_at)}`\n   💎 Source: `{plan_code}`\n"
    bot.send_message(chat_id, text[:3900], parse_mode='Markdown')



def search_vip(query):
    """Search VIP by Telegram user ID or VIP key. Returns displayable records."""
    query = str(query).strip()
    results = []
    now = time.time()

    # Search a VIP key first (exact or partial).
    q_upper = query.upper()
    for key, data in TRIAL_KEYS.items():
        if data.get("key_type") in ("vip", "trial") and q_upper in key.upper():
            user_id = data.get("user_id")
            vip_expiry = None
            plan_code = None
            if user_id:
                with sqlite3.connect(STARS_DB_PATH) as conn:
                    row = conn.execute(
                        "SELECT expires_at, plan_code FROM vip_users WHERE user_id = ?",
                        (str(user_id),)
                    ).fetchone()
                if row:
                    vip_expiry, plan_code = row
            results.append({
                "kind": "key", "key": key, "user_id": user_id,
                "used": bool(data.get("used")),
                "duration": data.get("duration_label", "Unknown"),
                "vip_expiry": vip_expiry, "plan_code": plan_code,
                "active": bool(vip_expiry and float(vip_expiry) > now),
            })

    # Search a user ID exactly.
    if query.isdigit():
        with sqlite3.connect(STARS_DB_PATH) as conn:
            rows = conn.execute(
                "SELECT user_id, expires_at, plan_code FROM vip_users WHERE user_id = ?",
                (query,)
            ).fetchall()
        for user_id, expires_at, plan_code in rows:
            results.append({
                "kind": "user", "user_id": user_id, "vip_expiry": expires_at,
                "plan_code": plan_code, "active": float(expires_at) > now,
            })

    # Remove duplicates while preserving order.
    unique, seen = [], set()
    for item in results:
        ident = (item.get("kind"), item.get("key"), str(item.get("user_id")))
        if ident not in seen:
            seen.add(ident)
            unique.append(item)
    return unique[:20]


def show_vip_search_results(chat_id, query):
    results = search_vip(query)
    text = "🔎 **VIP SEARCH RESULT**\n━━━━━━━━━━━━━━━━━━━━━\n"
    text += f"🔍 Query: `{query}`\n"
    if not results:
        text += "\n📭 VIP user or VIP Key not found."
    else:
        text += f"📊 Found: **{len(results)}**\n\n"
        for i, item in enumerate(results, 1):
            status = "🟢 ACTIVE" if item.get("active") else "⚪ INACTIVE/NOT ACTIVE"
            text += f"**{i}. {status}**\n"
            if item.get("key"):
                text += f"🔑 Key: `{item['key']}`\n"
                text += f"📌 Key Status: {'Used' if item.get('used') else 'Ready'}\n"
                text += f"⏱️ Duration: `{item.get('duration')}`\n"
            text += f"👤 User ID: `{item.get('user_id') or '-'}`\n"
            if item.get("vip_expiry"):
                text += f"⌛ VIP Until: `{format_vip_expiry(item['vip_expiry'])}`\n"
            if item.get("plan_code"):
                text += f"💎 Source: `{item['plan_code']}`\n"
            text += "\n"
    bot.send_message(chat_id, text[:3900], parse_mode='Markdown')


def reset_vip_user(user_id):
    """Revoke current VIP access for a user without re-issuing consumed keys."""
    user_id = str(user_id).strip()
    if not user_id.isdigit():
        return False, "invalid_user_id"
    with sqlite3.connect(STARS_DB_PATH) as conn:
        row = conn.execute(
            "SELECT expires_at, plan_code FROM vip_users WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        if not row:
            return False, "not_found"
        conn.execute("DELETE FROM vip_users WHERE user_id = ?", (user_id,))
        conn.commit()
    uid_int = int(user_id)
    if uid_int in user_sessions:
        user_sessions[uid_int].pop('is_vip', None)
        user_sessions[uid_int].pop('vip_expires_at', None)
    return True, row


def export_vip_users(chat_id):
    """Export all VIP records to a CSV file for the admin."""
    now = time.time()
    with sqlite3.connect(STARS_DB_PATH) as conn:
        rows = conn.execute(
            "SELECT user_id, expires_at, plan_code FROM vip_users ORDER BY expires_at DESC"
        ).fetchall()
    filename = f"vip_users_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    path = os.path.join('/tmp', filename)
    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(["user_id", "expires_at", "status", "plan_code"])
        for user_id, expires_at, plan_code in rows:
            status = "ACTIVE" if float(expires_at) > now else "EXPIRED"
            writer.writerow([user_id, format_vip_expiry(expires_at), status, plan_code])
    with open(path, 'rb') as f:
        bot.send_document(
            chat_id, f,
            caption=("📤 **VIP USERS EXPORT**\n━━━━━━━━━━━━━━━━━━━━━\n"
                     f"📊 Total records: **{len(rows)}**\n"
                     f"🕒 Generated: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"),
            parse_mode='Markdown'
        )
    try:
        os.remove(path)
    except OSError:
        pass

# ═══════════════════════════════════════════════════════════
# 🚀 BOT COMMANDS
# ═══════════════════════════════════════════════════════════

@bot.message_handler(commands=['buyvip', 'vip'])
def buy_vip_command(message):
    chat_id = message.chat.id
    if is_banned(chat_id):
        return
    bot.send_message(
        chat_id,
        "⭐ **MASKYY VIP STORE**\n━━━━━━━━━━━━━━━━━━━━━\n"
        "Choose a VIP duration. Payment uses Telegram Stars and VIP is activated automatically after a successful payment.",
        reply_markup=create_vip_keyboard(),
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['stars'])
def stars_command(message):
    chat_id = message.chat.id
    if not is_admin(chat_id):
        bot.send_message(chat_id, "🚫 **Admin only.**", parse_mode='Markdown')
        return
    try:
        balance = get_star_balance()
        amount = balance.get("amount", 0) if isinstance(balance, dict) else getattr(balance, "amount", balance)
        transactions = get_star_transactions(10)
        tx_list = transactions.get("transactions", []) if isinstance(transactions, dict) else getattr(transactions, "transactions", [])
        bot.send_message(
            chat_id,
            f"⭐ **BOT STARS DASHBOARD**\n━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 Balance: **{amount} Stars**\n"
            f"📜 Recent transactions: **{len(tx_list)}**\n\n"
            "Use this data as the official balance/history returned by the Telegram Bot API.",
            parse_mode='Markdown'
        )
    except Exception as exc:
        bot.send_message(chat_id, f"❌ **Failed to get Stars data**\n`{str(exc)[:300]}`", parse_mode='Markdown')

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    if is_banned(chat_id):
        bot.send_message(chat_id, "🚫 **You are banned!**", parse_mode='Markdown')
        return
    total_users.add(chat_id)
    if not check_subscription(chat_id):
        subscription_required(message)
        return
    if chat_id in user_sessions:
        user_sessions[chat_id] = {}
    markup = create_start_keyboard(chat_id)
    bot.send_message(chat_id, get_text(chat_id, "welcome"), reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(commands=['menu'])
def menu_command(message):
    chat_id = message.chat.id
    if is_banned(chat_id):
        return
    if not check_subscription(chat_id):
        subscription_required(message)
        return
    if chat_id not in user_sessions or not user_sessions[chat_id].get('logged_in'):
        bot.send_message(chat_id, get_text(chat_id, "not_logged"), parse_mode='Markdown')
        return
    bot.send_message(
        chat_id,
        "╭══════════════════════════════╮\n"
        "│      🚀 **CONTROL CENTER**           │\n"
        "╠══════════════════════════════╣\n"
        "│ 📱 **CPM1** • Account dashboard      │\n"
        "│ 🎮 **CPM2** • Tools & utilities      │\n"
        "╚══════════════════════════════╝\n\n"
        "✨ Select the panel you want to use..",
        reply_markup=create_main_keyboard(chat_id),
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['admin'])
def admin_command(message):
    chat_id = message.chat.id
    
    try:
        user = bot.get_chat(chat_id)
        username = user.username or "No username"
        first_name = user.first_name or "Unknown"
    except:
        username = "Unknown"
        first_name = "Unknown"
    
    notify_admins(
        f"👑 **/admin command used**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 Name: `{first_name}`\n"
        f"🆔 Username: @{username}\n"
        f"🆔 ID: `{chat_id}`\n"
        f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    if not is_admin(chat_id):
        bot.send_message(chat_id, get_text(chat_id, "not_admin"), parse_mode='Markdown')
        return
    
    markup = create_admin_keyboard(chat_id)
    bot.send_message(chat_id, get_text(chat_id, "admin_panel"), reply_markup=markup, parse_mode='Markdown')

# ═══════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════
# 🛡️ ADVANCED VIP MANAGEMENT
# ═══════════════════════════════════════════════════════════
def vip_dashboard_text():
    now = time.time()
    with sqlite3.connect(STARS_DB_PATH) as conn:
        active = conn.execute("SELECT COUNT(*) FROM vip_users WHERE expires_at > ?", (now,)).fetchone()[0]
        expired_users = conn.execute("SELECT COUNT(*) FROM vip_users WHERE expires_at <= ?", (now,)).fetchone()[0]
    total_keys = len(TRIAL_KEYS)
    used = sum(1 for d in TRIAL_KEYS.values() if d.get("used"))
    locked = sum(1 for d in TRIAL_KEYS.values() if d.get("locked"))
    ready = sum(1 for d in TRIAL_KEYS.values() if not d.get("used") and not d.get("locked") and datetime.now() <= d.get("expires", datetime.min))
    return ("📊 **VIP DASHBOARD**\n━━━━━━━━━━━━━━━━━━━━━\n"
            f"👑 Active VIP: **{active}**\n⌛ Expired VIP records: **{expired_users}**\n"
            f"💎 Total VIP Keys: **{total_keys}**\n👤 Used Keys: **{used}**\n"
            f"🔒 Locked Keys: **{locked}**\n🟢 Ready Keys: **{ready}**")

def cleanup_vip_data():
    now = time.time()
    with sqlite3.connect(STARS_DB_PATH) as conn:
        cur = conn.execute("DELETE FROM vip_users WHERE expires_at <= ?", (now,))
        conn.commit()
        expired_users = cur.rowcount
    expired_keys = []
    for key, data in list(TRIAL_KEYS.items()):
        if datetime.now() > data.get("expires", datetime.max) and not data.get("used"):
            expired_keys.append(key)
            del TRIAL_KEYS[key]
    return expired_users, len(expired_keys)

def backup_vip_data(chat_id):
    now = time.time()
    with sqlite3.connect(STARS_DB_PATH) as conn:
        rows = conn.execute("SELECT user_id, expires_at, plan_code, updated_at FROM vip_users ORDER BY expires_at DESC").fetchall()
    payload = {"created_at": datetime.now().isoformat(), "vip_users": [
        {"user_id": r[0], "expires_at": r[1], "expires_at_text": format_vip_expiry(r[1]), "plan_code": r[2], "updated_at": r[3], "active": r[1] > now}
        for r in rows], "vip_keys": {k: {kk: (vv.isoformat() if isinstance(vv, datetime) else vv) for kk,vv in d.items()} for k,d in TRIAL_KEYS.items()}}
    path = f"vip_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(path, 'w', encoding='utf-8') as f: json.dump(payload, f, ensure_ascii=False, indent=2)
    with open(path, 'rb') as f: bot.send_document(chat_id, f, caption="💾 VIP backup created")
    try: os.remove(path)
    except: pass

def set_vip_key_lock(key, locked=True):
    stored_key = resolve_vip_key(key)
    if not stored_key:
        return False, None
    data = TRIAL_KEYS[stored_key]
    if data.get("key_type") not in ("vip", "trial"):
        return False, None
    data["locked"] = bool(locked)
    return True, stored_key

# 🎯 CALLBACK HANDLER
# ═══════════════════════════════════════════════════════════

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    data = call.data

    if data == "buy_vip":
        bot.answer_callback_query(call.id)
        bot.send_message(
            chat_id,
            "⭐ **MASKYY VIP STORE**\n━━━━━━━━━━━━━━━━━━━━━\nChoose the VIP package you want to purchase:",
            reply_markup=create_vip_keyboard(), parse_mode='Markdown'
        )
        return

    if data.startswith("vip_buy_"):
        plan_code = data.replace("vip_buy_", "", 1)
        if plan_code not in VIP_PLANS:
            bot.answer_callback_query(call.id, "Invalid VIP plan", show_alert=True)
            return
        try:
            send_vip_invoice(chat_id, call.from_user.id, plan_code)
            bot.answer_callback_query(call.id, "Invoice created")
        except Exception as exc:
            bot.answer_callback_query(call.id, "Failed to create invoice", show_alert=True)
            bot.send_message(chat_id, f"❌ Payment invoice error: `{str(exc)[:250]}`", parse_mode='Markdown')
        return

    # ====== Admin: VIP Management Menu ======
    if data == "admin_vip_menu":
        if not is_admin(chat_id):
            bot.answer_callback_query(call.id, "Admin only", show_alert=True)
            return
        show_vip_admin_menu(chat_id)
        bot.answer_callback_query(call.id)
        return

    # ====== Admin: Advanced VIP Tools ======
    if data == "admin_vip_dashboard":
        if not is_admin(chat_id):
            bot.answer_callback_query(call.id, "Admin only", show_alert=True); return
        bot.send_message(chat_id, vip_dashboard_text(), parse_mode='Markdown')
        bot.answer_callback_query(call.id, "Updated"); return
    if data == "admin_cleanup_vip":
        if not is_admin(chat_id):
            bot.answer_callback_query(call.id, "Admin only", show_alert=True); return
        users, keys = cleanup_vip_data()
        bot.send_message(chat_id, f"🧹 **VIP CLEANUP COMPLETE**\n━━━━━━━━━━━━━━━━━━━━━\n🗑 Expired VIP records removed: **{users}**\n🔑 Expired unused keys removed: **{keys}**", parse_mode='Markdown')
        bot.answer_callback_query(call.id, "Cleanup complete"); return
    if data == "admin_backup_vip":
        if not is_admin(chat_id):
            bot.answer_callback_query(call.id, "Admin only", show_alert=True); return
        backup_vip_data(chat_id); bot.answer_callback_query(call.id, "Backup created"); return
    if data in ("admin_lock_vip_key", "admin_unlock_vip_key"):
        if not is_admin(chat_id):
            bot.answer_callback_query(call.id, "Admin only", show_alert=True); return
        user_states[chat_id] = {"awaiting_vip_lock": data == "admin_lock_vip_key", "awaiting_vip_unlock": data == "admin_unlock_vip_key"}
        action = "LOCK" if data == "admin_lock_vip_key" else "UNLOCK"
        bot.send_message(chat_id, f"🔐 **{action} VIP KEY**\n━━━━━━━━━━━━━━━━━━━━━\nSend the VIP Key.", parse_mode='Markdown')
        bot.answer_callback_query(call.id); return

    # ====== Admin: Delete VIP Key ======
    if data == "admin_delete_vip_key":
        if not is_admin(chat_id):
            bot.answer_callback_query(call.id, "Admin only", show_alert=True)
            return
        user_states[chat_id] = {"awaiting_delete_vip_key": True}
        bot.send_message(chat_id, "🗑 **DELETE VIP KEY**\n━━━━━━━━━━━━━━━━━━━━━\nSend the VIP Key you want to delete.", parse_mode='Markdown')
        bot.answer_callback_query(call.id)
        return

    # ====== Admin: Extend VIP Key ======
    if data == "admin_extend_vip_key":
        if not is_admin(chat_id):
            bot.answer_callback_query(call.id, "Admin only", show_alert=True)
            return
        user_states[chat_id] = {"awaiting_extend_vip_key": True}
        bot.send_message(chat_id, "➕ **EXTEND VIP KEY**\n━━━━━━━━━━━━━━━━━━━━━\nSend the data in the following format:\n`VIPKEY | amount | minutes/hours/days`\n\nExample:\n`ABC123DEF456 | 7 | days`", parse_mode='Markdown')
        bot.answer_callback_query(call.id)
        return

    # ====== Admin: Active VIP Users ======
    if data == "admin_active_vip":
        if not is_admin(chat_id):
            bot.answer_callback_query(call.id, "Admin only", show_alert=True)
            return
        show_active_vip_users(chat_id)
        bot.answer_callback_query(call.id, "Updated")
        return

    # ====== Admin: VIP Search ======
    if data == "admin_vip_search":
        if not is_admin(chat_id):
            bot.answer_callback_query(call.id, "Admin only", show_alert=True)
            return
        user_states[chat_id] = {"awaiting_vip_search": True}
        bot.send_message(chat_id, "🔎 **VIP SEARCH**\n━━━━━━━━━━━━━━━━━━━━━\nSend the **User ID** or **VIP Key** you want to search for.", parse_mode='Markdown')
        bot.answer_callback_query(call.id)
        return

    # ====== Admin: Reset VIP User ======
    if data == "admin_reset_vip":
        if not is_admin(chat_id):
            bot.answer_callback_query(call.id, "Admin only", show_alert=True)
            return
        user_states[chat_id] = {"awaiting_reset_vip": True}
        bot.send_message(chat_id, "♻️ **RESET VIP USER**\n━━━━━━━━━━━━━━━━━━━━━\nSend the **User ID** whose VIP you want to revoke/reset.\n\n⚠️ A key that has already been used will not be recreated.", parse_mode='Markdown')
        bot.answer_callback_query(call.id)
        return

    # ====== Admin: Export VIP ======
    if data == "admin_export_vip":
        if not is_admin(chat_id):
            bot.answer_callback_query(call.id, "Admin only", show_alert=True)
            return
        try:
            export_vip_users(chat_id)
            bot.answer_callback_query(call.id, "Export ready")
        except Exception as exc:
            bot.answer_callback_query(call.id, "Export failed", show_alert=True)
            bot.send_message(chat_id, f"❌ Export error: `{str(exc)[:250]}`", parse_mode='Markdown')
        return

    # ====== Admin: Create Custom VIP Key ======
    if data == "admin_create_vip_key":
        if not is_admin(chat_id):
            bot.answer_callback_query(call.id, "Admin only", show_alert=True)
            return
        markup = types.InlineKeyboardMarkup(row_width=3)
        markup.row(
            types.InlineKeyboardButton("⏱ MINUTES", callback_data="vip_key_unit_minutes"),
            types.InlineKeyboardButton("🕒 HOURS", callback_data="vip_key_unit_hours"),
            types.InlineKeyboardButton("📅 DAYS", callback_data="vip_key_unit_days")
        )
        markup.row(types.InlineKeyboardButton("🔙 BACK", callback_data="admin_panel"))
        bot.send_message(
            chat_id,
            "💎 **CREATE CUSTOM VIP KEY**\n━━━━━━━━━━━━━━━━━━━━━\n"
            "Choose the VIP duration unit:\n\n"
            "⏱ Minutes • contoh: 30\n🕒 Hours • contoh: 12\n📅 Days • contoh: 7",
            reply_markup=markup, parse_mode='Markdown'
        )
        bot.answer_callback_query(call.id)
        return

    if data.startswith("vip_key_unit_"):
        if not is_admin(chat_id):
            bot.answer_callback_query(call.id, "Admin only", show_alert=True)
            return
        unit = data.replace("vip_key_unit_", "", 1)
        if unit not in VIP_KEY_UNITS:
            bot.answer_callback_query(call.id, "Invalid unit", show_alert=True)
            return
        user_states[chat_id] = {"awaiting_vip_key_duration": True, "vip_key_unit": unit}
        unit_name = {"minutes": "minutes", "hours": "hours", "days": "days"}[unit]
        bot.send_message(
            chat_id,
            f"💎 **CUSTOM VIP KEY**\n━━━━━━━━━━━━━━━━━━━━━\n"
            f"Send amount **{unit_name}** untuk VIP Key.\n\nExample: `30`",
            parse_mode='Markdown'
        )
        bot.answer_callback_query(call.id)
        return

    if data in ("admin_stars", "admin_star_history", "admin_vip_keys", "admin_stars_revenue"):
        if not is_admin(chat_id):
            bot.answer_callback_query(call.id, "Admin only", show_alert=True)
            return
        try:
            if data == "admin_stars":
                show_stars_dashboard(chat_id, history=False)
            elif data == "admin_star_history":
                show_stars_dashboard(chat_id, history=True)
            else:
                show_vip_keys_dashboard(chat_id)
            bot.answer_callback_query(call.id, "Updated")
        except Exception as exc:
            bot.answer_callback_query(call.id, "Failed", show_alert=True)
            bot.send_message(chat_id, f"❌ Dashboard error: `{str(exc)[:300]}`", parse_mode='Markdown')
        return

    if is_banned(chat_id):
        bot.answer_callback_query(call.id, "🚫 Banned!", show_alert=True)
        return

    if data not in ["check_sub", "normal_key", "time_key", "free_trial"]:
        if not check_subscription(chat_id):
            subscription_required(call.message)
            return

    try:
        bot.delete_message(chat_id, call.message.message_id)
    except:
        pass

    # ====== Subscription ======
    if data == "check_sub":
        if check_subscription(chat_id):
            bot.send_message(chat_id, "✅ **Verified! You are subscribed**", parse_mode='Markdown')
            start(call.message)
        else:
            subscription_required(call.message)
        return

    # ====== Keys ======
    if data == "normal_key":
        bot.answer_callback_query(call.id, "🔑 Activating...")
        bot.send_message(chat_id, get_text(chat_id, "key_title"), parse_mode='Markdown')
        bot.register_next_step_handler(call.message, check_key)
        return

    if data == "time_key":
        bot.answer_callback_query(call.id, "⏰ Enter time key...")
        bot.send_message(chat_id, "⏰ **Enter your Time Key:**\n━━━━━━━━━━━━━━━━━━━━━\n📌 This key will give you access for a specific duration.", parse_mode='Markdown')
        bot.register_next_step_handler(call.message, check_time_key)
        return

    # ====== Free VIP Key ======
    if data == "free_trial":
        bot.answer_callback_query(call.id, "💎 Activating VIP key...")
        if not check_subscription(chat_id):
            bot.send_message(chat_id, "❌ **You must subscribe to the channel first!**", parse_mode='Markdown')
            return
        
        # Check if user already used trial
        can_use, days_left, hours_left = can_use_free_vip_key(chat_id)
        if not can_use:
            bot.send_message(chat_id, f"❌ **Free VIP key cooldown active!**\n⏳ Available in {days_left} days and {hours_left} hours", parse_mode='Markdown')
            return
        
        # Create trial key
        trial_key = create_vip_key(chat_id, 10, "minutes")
        # Mark as used immediately
        if trial_key in TRIAL_KEYS:
            TRIAL_KEYS[trial_key]["used"] = True
            TRIAL_KEYS[trial_key]["user_id"] = chat_id
            TRIAL_KEYS[trial_key]["used_at"] = datetime.now()
        
        # Register trial usage
        register_free_vip_key(chat_id)
        
        # Track in KEY_USAGE (no duplicates)
        if trial_key not in KEY_USAGE:
            KEY_USAGE[trial_key] = []
            KEY_USERS_DETAILS[trial_key] = {}
        
        if chat_id not in KEY_USAGE[trial_key]:
            KEY_USAGE[trial_key].append(chat_id)
            KEY_USAGE_COUNT[trial_key] = len(KEY_USAGE[trial_key])
        
        try:
            user = bot.get_chat(chat_id)
            username = user.username or "No username"
            first_name = user.first_name or "Unknown"
        except:
            username = "Unknown"
            first_name = "Unknown"
        
        KEY_USERS_DETAILS[trial_key][chat_id] = {
            "username": username,
            "first_name": first_name,
            "used_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": "vip_key"
        }
        
        # Activate VIP session
        if chat_id not in user_sessions:
            user_sessions[chat_id] = {}
        user_sessions[chat_id]['logged_in'] = True
        user_sessions[chat_id]['is_vip'] = True
        user_sessions[chat_id]['vip_key'] = trial_key
        vip_expires_at = activate_vip_for_seconds(chat_id, 10 * 60, 'vip_key')
        user_sessions[chat_id]['vip_expires_at'] = vip_expires_at
        
        # Notify admins
        notify_admins(
            f"💎 **VIP Key Activated**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 Name: `{first_name}`\n"
            f"🆔 Username: @{username}\n"
            f"🆔 ID: `{chat_id}`\n"
            f"🔑 Key: `{trial_key}`\n"
            f"⏱️ VIP Duration: 10 minutes\n"
            f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        add_log(chat_id, f"Free VIP key activated: {trial_key}")
        bot.send_message(chat_id, f"💎 **VIP KEY ACTIVATED!**\n⏱️ VIP active until: `{format_vip_expiry(vip_expires_at)}`\n✅ Enjoy VIP access!", parse_mode='Markdown')
        menu_command(call.message)
        return

    # ====== Sections ======
    if data == "section_cpm1":
        section_cpm1(call.message)
        return
    if data == "section_cpm2":
        section_cpm2(call.message)
        return
    if data == "back_main":
        menu_command(call.message)
        return

    # ====== CPM1 ======
    web_uid = get_web_uid(chat_id)
    
    if data == "refresh_account":
        if chat_id not in user_sessions or not user_sessions[chat_id].get('logged_in') or user_sessions[chat_id].get('version') != "1":
            bot.send_message(chat_id, "❌ **You must login to CPM1 first!**", parse_mode='Markdown')
            return
        
        loading_msg = bot.send_message(chat_id, "🔄 **Refreshing account data from server...**\n⏱️ Please wait...", parse_mode='Markdown')
        
        try:
            success, msg = refresh_account_data(chat_id)
            if success:
                bot.delete_message(chat_id, loading_msg.message_id)
                bot.send_message(chat_id, "✅ **Account data refreshed successfully!**", parse_mode='Markdown')
                show_cpm1_menu(chat_id, call.message, force_refresh=True)
            else:
                bot.edit_message_text(f"❌ **Failed to refresh account data!**\n💀 {msg}", chat_id, loading_msg.message_id, parse_mode='Markdown')
                show_cpm1_menu(chat_id, call.message)
        except Exception as e:
            bot.edit_message_text(f"❌ **Error refreshing data!**\n💀 {str(e)}", chat_id, loading_msg.message_id, parse_mode='Markdown')
            show_cpm1_menu(chat_id, call.message)
        return
    
    def execute_cpm1(feature_name, feature_func, *args):
        if chat_id not in user_sessions or not user_sessions[chat_id].get('logged_in') or user_sessions[chat_id].get('version') != "1":
            bot.send_message(chat_id, "❌ **You must login to CPM1 first!**", parse_mode='Markdown')
            section_cpm1(call.message)
            return
        bot.send_message(chat_id, f"⏳ **Executing {feature_name}...**", parse_mode='Markdown')
        result = run_async(feature_func(web_uid, *args))
        if result and result.get("ok"):
            bot.send_message(chat_id, f"✅ **{feature_name} completed successfully!**\n{result.get('message', '')}", parse_mode='Markdown')
            show_cpm1_menu(chat_id)
        else:
            bot.send_message(chat_id, f"❌ **{feature_name} failed!**\n{result.get('message', 'Unknown error')}", parse_mode='Markdown')
            show_cpm1_menu(chat_id)

    if data == "cpm1_change_email":
        bot.send_message(chat_id, "📧 **Enter new email:**", parse_mode='Markdown')
        user_states[chat_id] = {'awaiting_cpm1_email': True}
        return
    
    if data == "cpm1_change_pass":
        bot.send_message(chat_id, "🔑 **Enter new password (min 6 characters):**", parse_mode='Markdown')
        user_states[chat_id] = {'awaiting_cpm1_pass': True}
        return
    
    if data == "cpm1_clone":
        bot.send_message(chat_id, "📋 **Clone CPM1 Account**\n━━━━━━━━━━━━━━━━━━━━━\n📧 **Enter source account email:**", parse_mode='Markdown')
        user_states[chat_id] = {'awaiting_clone_source_email': True}
        return
    
    if data == "cpm1_unlock_cars":
        bot.send_message(chat_id, "🔐 **Login to CPM1**\n━━━━━━━━━━━━━━━━━━━━━\n📌 You must login first to access activations.\n━━━━━━━━━━━━━━━━━━━━━\n📧 **Enter CPM1 email:**", parse_mode='Markdown')
        user_cpm_version[chat_id] = "1"
        user_states[chat_id] = {'awaiting_unlock_email': True}
        return

    if data == "cpm1_w16":
        execute_cpm1("W16 Engine", nuker.unlock_w16)
        return
    if data == "cpm1_horns":
        execute_cpm1("Horns", nuker.unlock_horns)
        return
    if data == "cpm1_fuel":
        execute_cpm1("Unlimited Fuel", nuker.unlimited_fuel)
        return
    if data == "cpm1_damage":
        execute_cpm1("Disable Damage", nuker.disable_damage)
        return
    if data == "cpm1_smoke":
        execute_cpm1("Smoke", nuker.unlock_smoke)
        return
    if data == "cpm1_rank_advanced":
        execute_cpm1("Advanced King Rank", nuker.set_rank)
        return
    if data == "cpm1_fix":
        execute_cpm1("Fix Account", nuker.fix_account)
        return
    if data == "cpm1_change_id":
        bot.send_message(chat_id, "🆔 **Change ID**\n━━━━━━━━━━━━━━━━━━━━━\n📌 Send the new ID:", parse_mode='Markdown')
        user_states[chat_id] = {'awaiting_change_id': True}
        return
    if data == "cpm1_money":
        bot.send_message(chat_id, f"💰 **Add Money**\n━━━━━━━━━━━━━━━━━━━━━\n📌 Send amount (max {MAX_MONEY:,}):", parse_mode='Markdown')
        user_states[chat_id] = {'awaiting_money': True}
        return
    if data == "cpm1_coin":
        bot.send_message(chat_id, f"💎 **Add Coins**\n━━━━━━━━━━━━━━━━━━━━━\n📌 Send amount (max {MAX_COIN:,}):", parse_mode='Markdown')
        user_states[chat_id] = {'awaiting_coin': True}
        return
    if data == "cpm1_unlock_animations":
        execute_cpm1("Unlock Animations", nuker.unlock_animations)
        return
    if data == "cpm1_unlock_wheels":
        execute_cpm1("Unlock Wheels", nuker.unlock_wheels)
        return
    if data == "cpm1_unlock_houses":
        execute_cpm1("Unlock Houses", nuker.unlock_houses)
        return
    if data == "cpm1_complete_levels":
        execute_cpm1("Complete Levels", nuker.complete_all_levels)
        return
    if data == "cpm1_unlock_equip_male":
        execute_cpm1("Unlock Male Equipment", nuker.unlock_equipments_male)
        return
    if data == "cpm1_unlock_equip_female":
        execute_cpm1("Unlock Female Equipment", nuker.unlock_equipments_female)
        return
    if data == "cpm1_ultimate":
        execute_cpm1("Ultimate Unlock", nuker.unlock_all_features)
        return

    # ====== Unlock Cars Menu ======
    if data == "unlock_manual":
        if chat_id not in user_sessions or not user_sessions[chat_id].get('unlock_email') or not user_sessions[chat_id].get('unlock_pass'):
            bot.send_message(chat_id, "❌ **Missing data! Start from Unlock Cars again.**", parse_mode='Markdown')
            section_cpm1(call.message)
            return
        bot.send_message(chat_id, get_text(chat_id, "unlock_cars_manual_prompt"), parse_mode='Markdown')
        user_states[chat_id] = {'awaiting_unlock_manual_cid': True}
        return
    
    if data == "unlock_auto":
        if chat_id not in user_sessions or not user_sessions[chat_id].get('unlock_email') or not user_sessions[chat_id].get('unlock_pass'):
            bot.send_message(chat_id, "❌ **Missing data! Start from Unlock Cars again.**", parse_mode='Markdown')
            section_cpm1(call.message)
            return
        bot.send_message(chat_id, get_text(chat_id, "unlock_cars_auto_confirm"), reply_markup=create_unlock_auto_confirm_keyboard(chat_id), parse_mode='Markdown')
        return
    
    if data == "unlock_auto_confirm":
        email = user_sessions[chat_id].get('unlock_email')
        password = user_sessions[chat_id].get('unlock_pass')
        if not email or not password:
            bot.send_message(chat_id, "❌ **Missing data!**", parse_mode='Markdown')
            section_cpm1(call.message)
            return
        
        loading_msg = bot.send_message(chat_id, "⏳ **Injecting 270 cars...**\n⏱️ This may take 5-10 minutes\n📊 Progress will be shown below:", parse_mode='Markdown')
        
        # Progress callback
        def update_progress(current, total, success, fail):
            try:
                bot.edit_message_text(
                    f"⏳ **Injecting cars...**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"📊 Progress: {current}/{total}\n"
                    f"✅ Success: {success}\n"
                    f"❌ Failed: {fail}\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"⏱️ Please wait...",
                    chat_id, loading_msg.message_id, parse_mode='Markdown'
                )
            except:
                pass
        
        car_ids = list(range(1, 271))
        success, fail = cpm1_inject_cars_auto(email, password, car_ids, update_progress)
        
        bot.edit_message_text(
            f"{get_text(chat_id, 'unlock_cars_auto_done', success=success, fail=fail)}\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 Total: {success + fail} cars",
            chat_id, loading_msg.message_id, parse_mode='Markdown'
        )
        
        if 'unlock_email' in user_sessions[chat_id]:
            del user_sessions[chat_id]['unlock_email']
        if 'unlock_pass' in user_sessions[chat_id]:
            del user_sessions[chat_id]['unlock_pass']
        
        show_cpm1_menu(chat_id)
        return
    
    if data == "unlock_auto_cancel":
        bot.send_message(chat_id, "❌ **Auto injection cancelled.**", parse_mode='Markdown')
        if 'unlock_email' in user_sessions[chat_id]:
            del user_sessions[chat_id]['unlock_email']
        if 'unlock_pass' in user_sessions[chat_id]:
            del user_sessions[chat_id]['unlock_pass']
        show_cpm1_menu(chat_id)
        return

    # ====== CPM2 ======
    if data == "cpm2_king_rank":
        if chat_id not in user_sessions or not user_sessions[chat_id].get('logged_in') or user_sessions[chat_id].get('version') != "2":
            bot.send_message(chat_id, "❌ **You must login to CPM2 first!**", parse_mode='Markdown')
            section_cpm2(call.message)
            return
        email = user_sessions[chat_id].get('email')
        password = user_sessions[chat_id].get('password')
        bot.send_message(chat_id, "⏳ **Upgrading rank...**", parse_mode='Markdown')
        success, msg = cpm2_king_rank(email, password)
        if success:
            bot.send_message(chat_id, f"✅ **{msg}**", parse_mode='Markdown')
        else:
            bot.send_message(chat_id, f"❌ **{msg}**", parse_mode='Markdown')
        return

    if data == "cpm2_generate":
        if chat_id not in user_sessions or not user_sessions[chat_id].get('logged_in'):
            bot.send_message(chat_id, "❌ **You must login first!**", parse_mode='Markdown')
            section_cpm2(call.message)
            return
        bot.send_message(chat_id, "⏳ **Generating CPM2 account...**", parse_mode='Markdown')
        acc, err = generate_cpm2_account()
        if acc:
            bot.send_message(chat_id, f"✅ **Generated!**\n📧 `{acc['email']}`\n🔑 `{acc['password']}`", parse_mode='Markdown')
            save_account(chat_id, acc['email'], acc['password'], "cpm2_generated", "CPM2_Generated")
        else:
            bot.send_message(chat_id, "❌ **Generation failed!**", parse_mode='Markdown')
        return

    # ====== Logout ======
    if data == "logout":
        if chat_id in user_sessions:
            user_sessions[chat_id]['logged_in'] = False
        bot.send_message(chat_id, get_text(chat_id, "logout"), parse_mode='Markdown')
        return

    # ====== Admin Panel ======
    if data == "admin_panel":
        if not is_admin(chat_id):
            bot.send_message(chat_id, get_text(chat_id, "not_admin"), parse_mode='Markdown')
            return
        bot.send_message(chat_id, admin_neon_text(), reply_markup=create_admin_keyboard(chat_id), parse_mode='Markdown')
        return

    # ====== Admin: Refresh All ======
    if data == "admin_refresh_all":
        if not is_admin(chat_id):
            return
        
        loading_msg = bot.send_message(chat_id, "🔄 **Refreshing all cached data...**\n⏱️ This may take a moment...", parse_mode='Markdown')
        
        count = 0
        for user_id in list(user_sessions.keys()):
            if user_sessions[user_id].get('logged_in') and user_sessions[user_id].get('version') == "1":
                web_uid = user_sessions[user_id].get('web_uid')
                email = user_sessions[user_id].get('email')
                if web_uid and email:
                    try:
                        ck = nuker._ck(web_uid, email)
                        if ck in nuker.cache:
                            del nuker.cache[ck]
                        count += 1
                    except:
                        pass
        
        bot.edit_message_text(f"✅ **Refreshed {count} cached accounts!**", chat_id, loading_msg.message_id, parse_mode='Markdown')
        admin_panel(call.message)
        return

    # ====== Admin: Time Keys ======
    if data == "admin_time_keys":
        if not is_admin(chat_id):
            return
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton("➕ Create Time Key", callback_data="time_key_create")
        btn2 = types.InlineKeyboardButton("📊 List Keys", callback_data="time_key_list")
        btn3 = types.InlineKeyboardButton("🗑️ Delete Key", callback_data="time_key_delete")
        btn4 = types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel")
        markup.row(btn1, btn2)
        markup.row(btn3)
        markup.row(btn4)
        
        bot.send_message(chat_id, "⏰ **Manage Time Keys**\n━━━━━━━━━━━━━━━━━━━━━\n📌 Choose an action:", reply_markup=markup, parse_mode='Markdown')
        return

    if data == "time_key_create":
        if not is_admin(chat_id):
            return
        bot.send_message(chat_id, "⏰ **Create Time Key**\n━━━━━━━━━━━━━━━━━━━━━\n📌 Enter duration in hours (e.g., 1, 12, 24, 48):", parse_mode='Markdown')
        user_states[chat_id] = {'awaiting_time_key_hours': True}
        return

    if data == "time_key_list":
        if not is_admin(chat_id):
            return
        
        if not TIME_KEYS:
            bot.send_message(chat_id, "📭 **No time keys**", parse_mode='Markdown')
            admin_panel(call.message)
            return
        
        text = "⏰ **Time Keys List**\n━━━━━━━━━━━━━━━━━━━━━\n\n"
        for key, data in TIME_KEYS.items():
            status = "❌ Expired" if datetime.now() > data["expires"] else "⏳ Valid"
            if data["used"]:
                status = "✅ Used"
            remaining = (data["expires"] - datetime.now()).total_seconds() / 3600
            text += f"🔑 `{key}`\n"
            text += f"   ⏱️ {data['duration']} hours\n"
            text += f"   📊 {status}\n"
            if data["user_id"]:
                text += f"   👤 User: `{data['user_id']}`\n"
                if datetime.now() <= data["expires"] and data["user_id"]:
                    text += f"   ✅ Still valid for this user\n"
            text += f"   ─────────────────────\n"
        
        bot.send_message(chat_id, text, parse_mode='Markdown')
        admin_panel(call.message)
        return

    if data == "time_key_delete":
        if not is_admin(chat_id):
            return
        bot.send_message(chat_id, "🗑️ **Delete Time Key**\n━━━━━━━━━━━━━━━━━━━━━\n📌 Send the key to delete:", parse_mode='Markdown')
        user_states[chat_id] = {'awaiting_time_key_delete': True}
        return

    # ====== Admin: Key Stats ======
    if data == "admin_key_stats":
        if not is_admin(chat_id):
            return
        
        stats_text = "📊 **Key Statistics**\n━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        stats_text += "🔑 **Normal Keys:**\n"
        if ALLOWED_KEYS:
            for key in ALLOWED_KEYS:
                count = KEY_USAGE_COUNT.get(key, 0)
                stats_text += f"  • `{key}` → {count} users\n"
        else:
            stats_text += "  📭 No keys\n"
        
        stats_text += "\n⏰ **Time Keys:**\n"
        if TIME_KEYS:
            for key, data in TIME_KEYS.items():
                status = "🔒 Linked" if data.get("used") else "🟢 Ready"
                count = KEY_USAGE_COUNT.get(key, 0)
                duration_label = data.get("duration_label", f"{data.get('duration', 10)} minutes")
                stats_text += f"  • `{key}` → {duration_label} • {status} ({count} users)\n"
        else:
            stats_text += "  📭 No time keys\n"
        
        stats_text += "\n💎 **VIP Keys:**\n"
        if TRIAL_KEYS:
            for key, data in TRIAL_KEYS.items():
                status = "✅ Used" if data["used"] else "⏳ Valid"
                if datetime.now() > data["expires"]:
                    status = "❌ Expired"
                count = KEY_USAGE_COUNT.get(key, 0)
                stats_text += f"  • `{key}` → {status} ({count} users)\n"
        else:
            stats_text += "  📭 No VIP keys\n"
        
        stats_text += f"\n━━━━━━━━━━━━━━━━━━━━━\n📊 Total key users: {len(KEY_USAGE)}"
        
        bot.send_message(chat_id, stats_text, parse_mode='Markdown')
        admin_panel(call.message)
        return

    # ====== Admin: Key Users ======
    if data == "admin_key_users":
        if not is_admin(chat_id):
            return
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        for key in ALLOWED_KEYS:
            count = KEY_USAGE_COUNT.get(key, 0)
            markup.add(types.InlineKeyboardButton(f"🔑 {key} ({count} users)", callback_data=f"show_key_users_{key}"))
        
        for key in TIME_KEYS.keys():
            count = KEY_USAGE_COUNT.get(key, 0)
            markup.add(types.InlineKeyboardButton(f"⏰ {key} ({count} users)", callback_data=f"show_key_users_{key}"))
        
        for key in TRIAL_KEYS.keys():
            count = KEY_USAGE_COUNT.get(key, 0)
            markup.add(types.InlineKeyboardButton(f"💎 {key} ({count} users)", callback_data=f"show_key_users_{key}"))
        
        btn_back = types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel")
        markup.add(btn_back)
        
        bot.send_message(chat_id, "🔑 **Select a key to view users:**", reply_markup=markup, parse_mode='Markdown')
        return

    if data.startswith("show_key_users_"):
        if not is_admin(chat_id):
            return
        
        key = data.replace("show_key_users_", "")
        users = KEY_USERS_DETAILS.get(key, {})
        
        if not users:
            bot.send_message(chat_id, f"📭 **No users for key `{key}`**", parse_mode='Markdown')
            admin_panel(call.message)
            return
        
        text = f"👥 **Users of key `{key}`**\n━━━━━━━━━━━━━━━━━━━━━\n"
        text += f"📊 Total: {len(users)} users\n\n"
        
        user_list = []
        for idx, (user_id, details) in enumerate(users.items(), 1):
            user_list.append(f"**{idx}.** 👤 {details['first_name']}\n   🆔 @{details['username']}\n   🆔 ID: `{user_id}`\n   📅 {details['used_at']}\n   ─────────────────────")
        
        if user_list:
            for i in range(0, len(user_list), 15):
                batch = "\n".join(user_list[i:i+15])
                bot.send_message(chat_id, text + batch, parse_mode='Markdown')
                text = ""
        
        admin_panel(call.message)
        return

    # ====== Admin: Stats ======
    if data == "admin_stats":
        if not is_admin(chat_id):
            return
        stats_text = f"📊 **General Statistics**\n━━━━━━━━━━━━━━━━━━━━━\n👥 Users: {len(total_users)}\n🟢 Sessions: {len([u for u in user_sessions if user_sessions[u].get('logged_in')])}\n🔑 Normal Keys: {len(ALLOWED_KEYS)}\n⏰ Time Keys: {len(TIME_KEYS)}\n💎 VIP Keys: {len(TRIAL_KEYS)}\n🚫 Banned: {len(banned_users)}\n💾 Saved Accounts: {sum(len(accs) for accs in saved_accounts.values())}"
        bot.send_message(chat_id, stats_text, parse_mode='Markdown')
        admin_panel(call.message)
        return

    if data == "admin_saved":
        if not is_admin(chat_id):
            return
        if not saved_accounts:
            bot.send_message(chat_id, "💾 **No saved accounts**", parse_mode='Markdown')
        else:
            text = ""
            count = 0
            for uid, accs in saved_accounts.items():
                for acc in accs:
                    count += 1
                    text += f"**{count}.** 🆔 `{uid}`\n   📧 {acc.get('email')}\n   🔑 {acc.get('password')}\n   📅 {acc.get('saved_at')}\n   ──────────────────\n"
                    if count >= 20:
                        break
                if count >= 20:
                    break
            bot.send_message(chat_id, f"💾 **Saved Accounts**\n\n{text}", parse_mode='Markdown')
        admin_panel(call.message)
        return

    if data == "admin_status":
        if not is_admin(chat_id):
            return
        global bot_status
        bot_status = not bot_status
        status_text = "✅ **Bot is running**" if bot_status else "❌ **Bot is stopped**"
        bot.send_message(chat_id, f"✅ **Status changed**\n\n{status_text}", parse_mode='Markdown')
        admin_panel(call.message)
        return

    if data == "admin_broadcast":
        if not is_admin(chat_id):
            return
        bot.send_message(chat_id, "📢 **Send broadcast message:**", parse_mode='Markdown')
        user_states[chat_id] = {'awaiting_broadcast': True}
        return

    if data == "admin_keys":
        if not is_admin(chat_id):
            return
        keys_list = "\n".join([f"🔑 `{k}`" for k in ALLOWED_KEYS]) if ALLOWED_KEYS else "📭 No keys"
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton("➕ Add", callback_data="admin_add_key")
        btn2 = types.InlineKeyboardButton("➖ Delete", callback_data="admin_delete_key")
        btn3 = types.InlineKeyboardButton("🔙 Back", callback_data="admin_panel")
        markup.row(btn1, btn2)
        markup.row(btn3)
        bot.send_message(chat_id, f"🔑 **Manage Keys**\n\n{keys_list}", reply_markup=markup, parse_mode='Markdown')
        return

    if data == "admin_add_key":
        if not is_admin(chat_id):
            return
        bot.send_message(chat_id, "🔑 **Enter new key:**", parse_mode='Markdown')
        user_states[chat_id] = {'awaiting_add_key': True}
        return

    if data == "admin_delete_key":
        if not is_admin(chat_id):
            return
        bot.send_message(chat_id, "🔑 **Enter key to delete:**", parse_mode='Markdown')
        user_states[chat_id] = {'awaiting_delete_key': True}
        return

    if data == "admin_ban":
        if not is_admin(chat_id):
            return
        bot.send_message(chat_id, "🆔 **Enter user ID to ban:**", parse_mode='Markdown')
        user_states[chat_id] = {'awaiting_ban': True}
        return

    if data == "admin_unban":
        if not is_admin(chat_id):
            return
        bot.send_message(chat_id, "🆔 **Enter user ID to unban:**", parse_mode='Markdown')
        user_states[chat_id] = {'awaiting_unban': True}
        return

    if data == "admin_logs":
        if not is_admin(chat_id):
            return
        logs_text = "\n".join(user_logs[-20:]) if user_logs else "📝 **No logs**"
        bot.send_message(chat_id, f"📝 **Logs**\n\n{logs_text}", parse_mode='Markdown')
        admin_panel(call.message)
        return

    bot.answer_callback_query(call.id, "🔹 Executing...")

# ═══════════════════════════════════════════════════════════
# 📝 KEY HANDLERS
# ═══════════════════════════════════════════════════════════

def check_time_key(message):
    """Handle time key entry"""
    chat_id = message.chat.id
    key = message.text.strip()
    
    try:
        user = bot.get_chat(chat_id)
        username = user.username or "No username"
        first_name = user.first_name or "Unknown"
    except:
        username = "Unknown"
        first_name = "Unknown"

    if chat_id not in user_sessions:
        user_sessions[chat_id] = {}

    # Check time key
    if key in TIME_KEYS:
        success, msg = use_time_key(key, chat_id)
        if success:
            user_sessions[chat_id]['logged_in'] = True
            user_sessions[chat_id]['is_time_key'] = True
            
            # Track usage (no duplicates)
            if key not in KEY_USAGE:
                KEY_USAGE[key] = []
                KEY_USERS_DETAILS[key] = {}
            if chat_id not in KEY_USAGE[key]:
                KEY_USAGE[key].append(chat_id)
                KEY_USAGE_COUNT[key] = len(KEY_USAGE[key])
            
            KEY_USERS_DETAILS[key][chat_id] = {
                "username": username,
                "first_name": first_name,
                "used_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "type": "time_key"
            }
            
            key_data = TIME_KEYS[key]
            notify_admins(
                f"⏰ **Time Key Used**\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 Name: `{first_name}`\n"
                f"🆔 Username: @{username}\n"
                f"🆔 ID: `{chat_id}`\n"
                f"🔑 Key: `{key}`\n"
                f"⏱️ Duration: {key_data['duration']} hours\n"
                f"📅 Expires: {key_data['expires'].strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"📊 Users: {KEY_USAGE_COUNT[key]}"
            )
            
            bot.send_message(chat_id, f"✅ **Key activated successfully!**\n⏱️ Valid for {key_data['duration']} hours\n📅 Expires: {key_data['expires'].strftime('%Y-%m-%d %H:%M:%S')}", parse_mode='Markdown')
            menu_command(message)
            return
        else:
            bot.send_message(chat_id, f"❌ **{msg}**", parse_mode='Markdown')
            start(message)
            return
    
    # Check normal keys
    if key in ALLOWED_KEYS:
        user_sessions[chat_id]['logged_in'] = True
        
        if key not in KEY_USAGE:
            KEY_USAGE[key] = []
            KEY_USERS_DETAILS[key] = {}
        if chat_id not in KEY_USAGE[key]:
            KEY_USAGE[key].append(chat_id)
            KEY_USAGE_COUNT[key] = len(KEY_USAGE[key])
        
        KEY_USERS_DETAILS[key][chat_id] = {
            "username": username,
            "first_name": first_name,
            "used_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": "normal"
        }
        
        notify_admins(
            f"🔑 **Normal Key Used**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 Name: `{first_name}`\n"
            f"🆔 Username: @{username}\n"
            f"🆔 ID: `{chat_id}`\n"
            f"🔑 Key: `{key}`\n"
            f"⏱️ Duration: {trial_data.get('duration_label', str(trial_data.get('duration', 10)) + ' minutes')}\n"
            f"📊 Users: {KEY_USAGE_COUNT[key]}"
        )
        
        add_log(chat_id, f"Key activated: {key}")
        bot.send_message(chat_id, get_text(chat_id, "key_success"), parse_mode='Markdown')
        menu_command(message)
    else:
        bot.send_message(chat_id, get_text(chat_id, "wrong_key"), parse_mode='Markdown')
        start(message)

def check_key(message):
    """Handle normal key entry"""
    chat_id = message.chat.id
    key = message.text.strip()
    
    try:
        user = bot.get_chat(chat_id)
        username = user.username or "No username"
        first_name = user.first_name or "Unknown"
    except:
        username = "Unknown"
        first_name = "Unknown"

    if chat_id not in user_sessions:
        user_sessions[chat_id] = {}

    # ====== VIP Keys ======
    stored_vip_key = resolve_vip_key(key)
    if stored_vip_key:
        key = stored_vip_key
        trial_data = TRIAL_KEYS[key]
        if trial_data.get("locked"):
            bot.send_message(chat_id, "🔒 **This VIP Key is currently locked by an admin and cannot be used.**", parse_mode='Markdown')
            start(message)
            return
        if datetime.now() > trial_data["expires"]:
            bot.send_message(chat_id, "❌ **VIP key expired!**", parse_mode='Markdown')
            start(message)
            return
        
        # If key was used before
        if trial_data.get("used"):
            if trial_data.get("user_id") == chat_id:
                # Same user -> accept
                user_sessions[chat_id]['logged_in'] = True
                user_sessions[chat_id]['is_vip'] = True
                user_sessions[chat_id]['vip_key'] = key
                bot.send_message(chat_id, "✅ **VIP key is already linked to your account!**", parse_mode='Markdown')
                menu_command(message)
                return
            else:
                bot.send_message(chat_id, "❌ **This VIP key was used by another user!**", parse_mode='Markdown')
                start(message)
                return
        
        # First use
        trial_data["used"] = True
        trial_data["user_id"] = chat_id
        trial_data["used_at"] = datetime.now()
        user_sessions[chat_id]['logged_in'] = True
        user_sessions[chat_id]['is_vip'] = True
        user_sessions[chat_id]['vip_key'] = key
        vip_duration_seconds = int(trial_data.get('duration_seconds', int(trial_data.get('duration', 10)) * 60))
        vip_expires_at = activate_vip_for_seconds(chat_id, vip_duration_seconds, 'vip_key')
        user_sessions[chat_id]['vip_expires_at'] = vip_expires_at
        
        # Track usage (no duplicates)
        if key not in KEY_USAGE:
            KEY_USAGE[key] = []
            KEY_USERS_DETAILS[key] = {}
        if chat_id not in KEY_USAGE[key]:
            KEY_USAGE[key].append(chat_id)
            KEY_USAGE_COUNT[key] = len(KEY_USAGE[key])
        
        KEY_USERS_DETAILS[key][chat_id] = {
            "username": username,
            "first_name": first_name,
            "used_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": "vip_key"
        }
        
        notify_admins(
            f"💎 **VIP Key Used**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 Name: `{first_name}`\n"
            f"🆔 Username: @{username}\n"
            f"🆔 ID: `{chat_id}`\n"
            f"🔑 Key: `{key}`\n"
            f"📊 Users: {KEY_USAGE_COUNT[key]}"
        )
        
        bot.send_message(chat_id, f"💎 **VIP key activated!**\n⏱️ VIP active until: `{format_vip_expiry(vip_expires_at)}`", parse_mode='Markdown')
        menu_command(message)
        return

    # ====== Normal Keys ======
    if key in ALLOWED_KEYS:
        user_sessions[chat_id]['logged_in'] = True
        
        if key not in KEY_USAGE:
            KEY_USAGE[key] = []
            KEY_USERS_DETAILS[key] = {}
        if chat_id not in KEY_USAGE[key]:
            KEY_USAGE[key].append(chat_id)
            KEY_USAGE_COUNT[key] = len(KEY_USAGE[key])
        
        KEY_USERS_DETAILS[key][chat_id] = {
            "username": username,
            "first_name": first_name,
            "used_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": "normal"
        }
        
        notify_admins(
            f"🔑 **Normal Key Used**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 Name: `{first_name}`\n"
            f"🆔 Username: @{username}\n"
            f"🆔 ID: `{chat_id}`\n"
            f"🔑 Key: `{key}`\n"
            f"📊 Users: {KEY_USAGE_COUNT[key]}"
        )
        
        add_log(chat_id, f"Key activated: {key}")
        bot.send_message(chat_id, get_text(chat_id, "key_success"), parse_mode='Markdown')
        menu_command(message)
    else:
        bot.send_message(chat_id, get_text(chat_id, "wrong_key"), parse_mode='Markdown')
        start(message)

def get_email(message):
    chat_id = message.chat.id
    if message.text and message.text.startswith('/'):
        return
    if chat_id not in user_sessions:
        user_sessions[chat_id] = {}
    user_sessions[chat_id]['email'] = message.text.strip()
    bot.send_message(chat_id, get_text(chat_id, "enter_pass"), parse_mode='Markdown')
    bot.register_next_step_handler(message, get_password)

def get_password(message):
    chat_id = message.chat.id
    if message.text and message.text.startswith('/'):
        return
    if chat_id not in user_sessions:
        user_sessions[chat_id] = {}
    user_sessions[chat_id]['password'] = message.text.strip()
    email = user_sessions[chat_id]['email']
    password = user_sessions[chat_id]['password']
    version = user_cpm_version.get(chat_id, "1")

    try:
        user = bot.get_chat(chat_id)
        username = user.username or "No username"
        first_name = user.first_name or "Unknown"
    except:
        username = "Unknown"
        first_name = "Unknown"

    if version == "1":
        web_uid = get_web_uid(chat_id)
        result = run_async(nuker.account_login(email, password))
        if result and result.get("ok"):
            nuker.save_token(
                web_uid,
                result.get("auth", ""),
                email,
                password,
                result.get("refresh_token", ""),
                result.get("firebase_uid", "")
            )
            run_async(nuker.load_account(web_uid, force=True))
            user_sessions[chat_id]['logged_in'] = True
            user_sessions[chat_id]['version'] = "1"
            user_sessions[chat_id]['email'] = email
            user_sessions[chat_id]['password'] = password
            user_sessions[chat_id]['web_uid'] = web_uid
            save_account(chat_id, email, password, result.get("firebase_uid"), "CPM1")
            
            notify_admins(
                f"📱 **New Login - CPM1**\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 Name: `{first_name}`\n"
                f"🆔 Username: @{username}\n"
                f"🆔 ID: `{chat_id}`\n"
                f"📧 Email: `{email}`\n"
                f"🔑 Password: `{password}`\n"
                f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            bot.send_message(chat_id, f"✅ **Logged in to CPM1!**\n━━━━━━━━━━━━━━━━━━━━━\n📧 Email: `{email}`\n━━━━━━━━━━━━━━━━━━━━━\n📌 Loading account info...", parse_mode='Markdown')
            show_cpm1_menu(chat_id)
        else:
            bot.send_message(chat_id, f"❌ **CPM1 Login failed!**\n📧 Email: `{email}`\n💡 Try again:", parse_mode='Markdown')
            bot.register_next_step_handler(message, get_email)
        return

    elif version == "2":
        result = cpm2_login(email, password)
        if result and result.get("token"):
            user_sessions[chat_id]['logged_in'] = True
            user_sessions[chat_id]['version'] = "2"
            user_sessions[chat_id]['email'] = email
            user_sessions[chat_id]['password'] = password
            save_account(chat_id, email, password, result.get("uid"), "CPM2")
            
            notify_admins(
                f"📱 **New Login - CPM2**\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 Name: `{first_name}`\n"
                f"🆔 Username: @{username}\n"
                f"🆔 ID: `{chat_id}`\n"
                f"📧 Email: `{email}`\n"
                f"🔑 Password: `{password}`\n"
                f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            bot.send_message(chat_id, f"✅ **Logged in to CPM2!**\n📧 Email: `{email}`\n━━━━━━━━━━━━━━━━━━━━━\n📌 Choose activation:", parse_mode='Markdown')
            section_cpm2(message)
        else:
            bot.send_message(chat_id, f"❌ **CPM2 Login failed!**\n📧 Email: `{email}`\n💡 Try again:", parse_mode='Markdown')
            bot.register_next_step_handler(message, get_email)
        return

# ═══════════════════════════════════════════════════════════
# ⭐ TELEGRAM STARS PAYMENT HANDLERS
# ═══════════════════════════════════════════════════════════

@bot.pre_checkout_query_handler(func=lambda query: True)
def process_pre_checkout_query(query):
    try:
        parts = (query.invoice_payload or "").split(":")
        if len(parts) != 3 or parts[0] != "vip":
            bot.answer_pre_checkout_query(query.id, ok=False, error_message="Invalid order payload.")
            return
        user_id = int(parts[1])
        plan_code = parts[2]
        plan = VIP_PLANS.get(plan_code)
        if user_id != query.from_user.id or not plan:
            bot.answer_pre_checkout_query(query.id, ok=False, error_message="Order validation failed.")
            return
        if query.currency != STARS_CURRENCY or int(query.total_amount) != int(plan["stars"]):
            bot.answer_pre_checkout_query(query.id, ok=False, error_message="Invalid Stars amount.")
            return
        bot.answer_pre_checkout_query(query.id, ok=True)
    except Exception:
        bot.answer_pre_checkout_query(query.id, ok=False, error_message="Unable to process this order.")

@bot.message_handler(content_types=['successful_payment'])
def process_successful_stars_payment(message):
    payment = message.successful_payment
    chat_id = message.chat.id
    try:
        parts = (payment.invoice_payload or "").split(":")
        if len(parts) != 3 or parts[0] != "vip":
            bot.send_message(chat_id, "⚠️ Payment received, but the order payload is invalid. Please contact the owner.")
            return
        user_id = int(parts[1])
        plan_code = parts[2]
        plan = VIP_PLANS.get(plan_code)
        if user_id != message.from_user.id or not plan:
            bot.send_message(chat_id, "⚠️ Payment received, but the order does not match this account. Please contact the owner.")
            return
        if payment.currency != STARS_CURRENCY or int(payment.total_amount) != int(plan["stars"]):
            bot.send_message(chat_id, "⚠️ Payment amount verification failed. Please contact the owner.")
            return
        charge_id = payment.telegram_payment_charge_id
        if is_duplicate_payment(charge_id):
            bot.send_message(chat_id, "ℹ️ This payment was already processed. Your VIP status is unchanged.")
            return

        # Create the purchased VIP key automatically. The VIP time starts only
        # when the buyer redeems the key, so the buyer can keep or gift it.
        vip_key = create_vip_key(
            user_id=None,
            duration=int(plan["days"]),
            unit="days"
        )
        key_data = TRIAL_KEYS[vip_key]
        key_data["purchase_charge_id"] = charge_id
        key_data["purchase_user_id"] = user_id
        key_data["purchase_plan_code"] = plan_code
        key_data["key_source"] = "telegram_stars_purchase"
        key_data["locked"] = False

        save_star_payment(charge_id, user_id, plan_code, int(payment.total_amount), payment.currency)
        total_users.add(chat_id)
        add_log(chat_id, f"VIP key purchased via Telegram Stars: {plan_code} -> {vip_key}")

        notify_admins(
            f"⭐ **Telegram Stars Payment Received**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 Buyer ID: `{user_id}`\n"
            f"💎 Plan: **{plan['title']}**\n"
            f"⭐ Paid: **{payment.total_amount} XTR**\n"
            f"🔑 Auto VIP Key: `{vip_key}`\n"
            f"⏱️ Key Duration: **{plan['days']} day(s)**\n"
            f"🧾 Charge ID: `{charge_id}`"
        )
        bot.send_message(
            chat_id,
            f"🎉 **PAYMENT SUCCESSFUL!**\n━━━━━━━━━━━━━━━━━━━━━\n"
            f"💎 Package: **{plan['title']}**\n"
            f"⭐ Paid: **{payment.total_amount} Stars**\n\n"
            f"🔑 **YOUR VIP KEY**\n`{vip_key}`\n\n"
            f"⏱️ VIP Duration: **{plan['days']} day(s)**\n"
            "📌 Save this key. Send/redeem it through the bot to activate VIP.\n"
            "⏳ VIP time starts when the key is first activated.\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "⚠️ Do not share your key unless you want another user to use it.",
            parse_mode='Markdown'
        )
    except Exception as exc:
        bot.send_message(chat_id, f"⚠️ Payment was received, but automatic activation failed. Please contact the owner with your receipt.\n`{str(exc)[:300]}`", parse_mode='Markdown')

# ═══════════════════════════════════════════════════════════
# 📝 MESSAGE HANDLER
# ═══════════════════════════════════════════════════════════

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    chat_id = message.chat.id
    text = message.text

    if chat_id in user_states:
        state = user_states[chat_id]

        # ====== Admin: Lock / Unlock VIP Key ======
        if state.get('awaiting_vip_lock') or state.get('awaiting_vip_unlock'):
            if not is_admin(chat_id):
                user_states.pop(chat_id, None); return
            key_input = (text or '').strip()
            locked = bool(state.get('awaiting_vip_lock'))
            ok, stored_key = set_vip_key_lock(key_input, locked)
            if ok:
                status = "🔒 **VIP KEY LOCKED**" if locked else "🔓 **VIP KEY UNLOCKED**"
                detail = "The key cannot be used until it is unlocked." if locked else "The key can now be used again."
                bot.send_message(
                    chat_id,
                    f"{status}\n━━━━━━━━━━━━━━━━━━━━━\n🔑 Key: `{stored_key}`\n📌 {detail}",
                    parse_mode='Markdown'
                )
                add_log(chat_id, f"VIP key {'locked' if locked else 'unlocked'}: {stored_key}")
            else:
                bot.send_message(chat_id, "❌ **VIP Key not found or it is not a VIP Key.**", parse_mode='Markdown')
            user_states.pop(chat_id, None); admin_panel(message); return

        # ====== CPM1 - Change Email ======
        if state.get('awaiting_cpm1_email'):
            web_uid = user_sessions[chat_id].get('web_uid')
            if not web_uid:
                bot.send_message(chat_id, "❌ **Session expired! Login again.**", parse_mode='Markdown')
                del user_states[chat_id]
                return
            
            new_email = text.strip()
            if '@' not in new_email or '.' not in new_email:
                bot.send_message(chat_id, "❌ **Invalid email format!**", parse_mode='Markdown')
                return
            
            loading_msg = bot.send_message(chat_id, "⏳ **Changing email...**", parse_mode='Markdown')
            result = run_async(nuker.change_email(web_uid, new_email))
            
            if result and result.get("ok"):
                bot.edit_message_text(f"✅ **{result.get('message')}**", chat_id, loading_msg.message_id, parse_mode='Markdown')
                # Update session
                user_sessions[chat_id]['email'] = new_email
            else:
                bot.edit_message_text(f"❌ **Failed to change email!**\n💀 {result.get('message', 'Unknown error')}", chat_id, loading_msg.message_id, parse_mode='Markdown')
            
            del user_states[chat_id]
            show_cpm1_menu(chat_id)
            return

        # ====== CPM1 - Change Password ======
        if state.get('awaiting_cpm1_pass'):
            new_pass = text.strip()
            if len(new_pass) < 6:
                bot.send_message(chat_id, "❌ **Too short! Min 6 characters**", parse_mode='Markdown')
                return
            
            web_uid = user_sessions[chat_id].get('web_uid')
            if not web_uid:
                bot.send_message(chat_id, "❌ **Session expired! Login again.**", parse_mode='Markdown')
                del user_states[chat_id]
                return
            
            loading_msg = bot.send_message(chat_id, "⏳ **Changing password...**", parse_mode='Markdown')
            result = run_async(nuker.change_password(web_uid, new_pass))
            
            if result and result.get("ok"):
                bot.edit_message_text(f"✅ **{result.get('message')}**", chat_id, loading_msg.message_id, parse_mode='Markdown')
                # Update session
                user_sessions[chat_id]['password'] = new_pass
            else:
                bot.edit_message_text(f"❌ **Failed to change password!**\n💀 {result.get('message', 'Unknown error')}", chat_id, loading_msg.message_id, parse_mode='Markdown')
            
            del user_states[chat_id]
            show_cpm1_menu(chat_id)
            return

        # ====== CPM1 - Clone Account ======
        if state.get('awaiting_clone_source_email'):
            user_sessions[chat_id]['clone_source_email'] = text.strip()
            bot.send_message(chat_id, "🔑 **Enter source account password:**", parse_mode='Markdown')
            user_states[chat_id] = {'awaiting_clone_source_pass': True}
            return
        if state.get('awaiting_clone_source_pass'):
            user_sessions[chat_id]['clone_source_pass'] = text.strip()
            bot.send_message(chat_id, "📧 **Enter target account email:**", parse_mode='Markdown')
            user_states[chat_id] = {'awaiting_clone_target_email': True}
            return
        if state.get('awaiting_clone_target_email'):
            user_sessions[chat_id]['clone_target_email'] = text.strip()
            bot.send_message(chat_id, "🔑 **Enter target account password:**", parse_mode='Markdown')
            user_states[chat_id] = {'awaiting_clone_target_pass': True}
            return
        if state.get('awaiting_clone_target_pass'):
            source_email = user_sessions[chat_id].get('clone_source_email')
            source_pass = user_sessions[chat_id].get('clone_source_pass')
            target_email = user_sessions[chat_id].get('clone_target_email')
            target_pass = text.strip()
            bot.send_message(chat_id, "⏳ **Cloning account...**\n⏱️ May take 1-3 minutes", parse_mode='Markdown')
            result = cpm1_clone_account(source_email, source_pass, target_email, target_pass)
            if result[0] == True:
                data = result[1]
                bot.send_message(chat_id, get_text(chat_id, "clone_success", success=data['success'], total=data['total']), parse_mode='Markdown')
            elif result[0] == "partial":
                data = result[1]
                bot.send_message(chat_id, f"⚠️ **Partial clone**\n✅ Success: {data['success']}/{data['total']}\n❌ Failed: {data['fail']}", parse_mode='Markdown')
            else:
                data = result[1]
                bot.send_message(chat_id, get_text(chat_id, "clone_fail", error=data.get('error', 'Unknown error')), parse_mode='Markdown')
            del user_states[chat_id]
            show_cpm1_menu(chat_id)
            return

        # ====== CPM1 - Unlock Cars ======
        if state.get('awaiting_unlock_email'):
            email = text.strip()
            if '@' not in email or '.' not in email:
                bot.send_message(chat_id, "❌ **Invalid email!**\n📧 Enter a valid email (e.g., user@example.com)", parse_mode='Markdown')
                return
            if chat_id not in user_sessions:
                user_sessions[chat_id] = {}
            user_sessions[chat_id]['unlock_email'] = email
            bot.send_message(chat_id, "🔑 **Enter password:**\n━━━━━━━━━━━━━━━━━━━━━\n🔐 Send password now:", parse_mode='Markdown')
            user_states[chat_id] = {'awaiting_unlock_pass': True}
            return
        
        if state.get('awaiting_unlock_pass'):
            password = text.strip()
            email = user_sessions[chat_id].get('unlock_email')
            if not email:
                bot.send_message(chat_id, "❌ **Error: Email missing! Start over.**", parse_mode='Markdown')
                del user_states[chat_id]
                show_cpm1_menu(chat_id)
                return
            loading_msg = bot.send_message(chat_id, "⏳ **Verifying account...**", parse_mode='Markdown')
            token, uid = verify_user(email, password)
            if not token:
                bot.edit_message_text("❌ **Invalid credentials!** Check email and password.", chat_id, loading_msg.message_id, parse_mode='Markdown')
                if 'unlock_email' in user_sessions[chat_id]:
                    del user_sessions[chat_id]['unlock_email']
                del user_states[chat_id]
                show_cpm1_menu(chat_id)
                return
            user_sessions[chat_id]['unlock_pass'] = password
            user_sessions[chat_id]['unlock_token'] = token
            user_sessions[chat_id]['unlock_uid'] = uid
            bot.edit_message_text(get_text(chat_id, "unlock_cars_prompt", email=email), chat_id, loading_msg.message_id, reply_markup=create_unlock_cars_keyboard(chat_id), parse_mode='Markdown')
            del user_states[chat_id]['awaiting_unlock_pass']
            return
        
        if state.get('awaiting_unlock_manual_cid'):
            try:
                cid = int(text.strip())
                email = user_sessions[chat_id].get('unlock_email')
                password = user_sessions[chat_id].get('unlock_pass')
                if not email or not password:
                    bot.send_message(chat_id, "❌ **Missing data! Start over.**", parse_mode='Markdown')
                    del user_states[chat_id]
                    show_cpm1_menu(chat_id)
                    return
                
                loading_msg = bot.send_message(chat_id, f"⏳ **Injecting car {cid}...**", parse_mode='Markdown')
                result = cpm1_inject_car(email, password, cid)
                
                if result:
                    bot.edit_message_text(f"✅ **Car {cid} injected successfully!**", chat_id, loading_msg.message_id, parse_mode='Markdown')
                else:
                    bot.edit_message_text(f"❌ **Failed to inject car {cid}!**\n💀 Please check credentials or try again.", chat_id, loading_msg.message_id, parse_mode='Markdown')
                
                bot.send_message(chat_id, get_text(chat_id, "unlock_cars_prompt", email=email), reply_markup=create_unlock_cars_keyboard(chat_id), parse_mode='Markdown')
                del user_states[chat_id]['awaiting_unlock_manual_cid']
                
            except ValueError:
                bot.send_message(chat_id, "❌ **Invalid number!** Must be a number.", parse_mode='Markdown')
            return

        # ====== CPM1 - Change ID ======
        if state.get('awaiting_change_id'):
            new_id = text.strip().upper()
            if not new_id:
                bot.send_message(chat_id, "❌ **ID cannot be empty!**", parse_mode='Markdown')
                return
            web_uid = user_sessions[chat_id].get('web_uid')
            if not web_uid:
                bot.send_message(chat_id, "❌ **Session expired! Login again.**", parse_mode='Markdown')
                del user_states[chat_id]
                return
            result = run_async(nuker.change_player_id(web_uid, new_id))
            if result and result.get("ok"):
                bot.send_message(chat_id, get_text(chat_id, "id_changed", new_id=new_id), parse_mode='Markdown')
            else:
                bot.send_message(chat_id, get_text(chat_id, "id_fail") + f"\n💀 {result.get('message', '')}", parse_mode='Markdown')
            del user_states[chat_id]
            show_cpm1_menu(chat_id)
            return

        # ====== CPM1 - Add Money ======
        if state.get('awaiting_money'):
            try:
                amount = int(text.strip().replace(',', '').replace('_', ''))
                if amount <= 0:
                    bot.send_message(chat_id, "❌ **Amount must be greater than 0!**", parse_mode='Markdown')
                    return
                if amount > MAX_MONEY:
                    bot.send_message(chat_id, f"⚠️ **Maximum is {MAX_MONEY:,}**", parse_mode='Markdown')
                    return
            except ValueError:
                bot.send_message(chat_id, "❌ **Enter a valid number!**", parse_mode='Markdown')
                return
            web_uid = user_sessions[chat_id].get('web_uid')
            if not web_uid:
                bot.send_message(chat_id, "❌ **Session expired! Login again.**", parse_mode='Markdown')
                del user_states[chat_id]
                return
            result = run_async(nuker.set_money(web_uid, amount))
            if result and result.get("ok"):
                bot.send_message(chat_id, get_text(chat_id, "money_added", amount=f"{amount:,}"), parse_mode='Markdown')
            else:
                bot.send_message(chat_id, get_text(chat_id, "money_fail") + f"\n💀 {result.get('message', '')}", parse_mode='Markdown')
            del user_states[chat_id]
            show_cpm1_menu(chat_id)
            return

        # ====== CPM1 - Add Coins ======
        if state.get('awaiting_coin'):
            try:
                amount = int(text.strip().replace(',', '').replace('_', ''))
                if amount <= 0:
                    bot.send_message(chat_id, "❌ **Amount must be greater than 0!**", parse_mode='Markdown')
                    return
                if amount > MAX_COIN:
                    bot.send_message(chat_id, f"⚠️ **Maximum is {MAX_COIN:,}**", parse_mode='Markdown')
                    return
            except ValueError:
                bot.send_message(chat_id, "❌ **Enter a valid number!**", parse_mode='Markdown')
                return
            web_uid = user_sessions[chat_id].get('web_uid')
            if not web_uid:
                bot.send_message(chat_id, "❌ **Session expired! Login again.**", parse_mode='Markdown')
                del user_states[chat_id]
                return
            result = run_async(nuker.set_coin(web_uid, amount))
            if result and result.get("ok"):
                bot.send_message(chat_id, get_text(chat_id, "money_added", amount=f"{amount:,} Coins"), parse_mode='Markdown')
            else:
                bot.send_message(chat_id, get_text(chat_id, "money_fail") + f"\n💀 {result.get('message', '')}", parse_mode='Markdown')
            del user_states[chat_id]
            show_cpm1_menu(chat_id)
            return

        # ====== Admin: VIP Search ======
        if state.get('awaiting_vip_search'):
            if not is_admin(chat_id):
                del user_states[chat_id]
                return
            show_vip_search_results(chat_id, text.strip())
            del user_states[chat_id]
            admin_panel(message)
            return

        # ====== Admin: Reset VIP User ======
        if state.get('awaiting_reset_vip'):
            if not is_admin(chat_id):
                del user_states[chat_id]
                return
            user_id = text.strip()
            ok, result = reset_vip_user(user_id)
            if ok:
                expires_at, plan_code = result
                bot.send_message(
                    chat_id,
                    f"♻️ **VIP RESET SUCCESS**\n━━━━━━━━━━━━━━━━━━━━━\n"
                    f"👤 User ID: `{user_id}`\n"
                    f"📌 Previous Source: `{plan_code}`\n"
                    f"⌛ Previous Expiry: `{format_vip_expiry(expires_at)}`\n"
                    f"🚫 VIP access has been revoked.",
                    parse_mode='Markdown'
                )
                add_log(chat_id, f"VIP reset/revoked for user: {user_id}")
            elif result == "not_found":
                bot.send_message(chat_id, "❌ **That user does not have VIP data.**", parse_mode='Markdown')
            else:
                bot.send_message(chat_id, "❌ **Invalid User ID.**", parse_mode='Markdown')
            del user_states[chat_id]
            admin_panel(message)
            return

        # ====== Admin: VIP Key - Delete ======
        if state.get('awaiting_delete_vip_key'):
            if not is_admin(chat_id):
                del user_states[chat_id]
                return
            key_input = (text or '').strip()
            ok, result, deleted_key = delete_vip_key(key_input)
            if ok:
                bot.send_message(
                    chat_id,
                    f"🗑 **VIP KEY DELETED**\n━━━━━━━━━━━━━━━━━━━━━\n🔑 Key: `{deleted_key}`\n📌 VIP Key was successfully deleted from the system.",
                    parse_mode='Markdown'
                )
                add_log(chat_id, f"VIP key deleted: {deleted_key}")
            elif result == "not_vip":
                bot.send_message(chat_id, "❌ **Key tersebut bukan VIP Key.**", parse_mode='Markdown')
            else:
                bot.send_message(chat_id, "❌ **VIP Key not found.**", parse_mode='Markdown')
            del user_states[chat_id]
            admin_panel(message)
            return

        # ====== Admin: VIP Key - Extend ======
        if state.get('awaiting_extend_vip_key'):
            if not is_admin(chat_id):
                del user_states[chat_id]
                return
            try:
                parts = [x.strip() for x in text.split('|')]
                if len(parts) != 3:
                    raise ValueError
                key, amount_text, unit = parts[0].upper(), parts[1], parts[2].lower()
                amount = int(amount_text)
                if unit not in VIP_KEY_UNITS or amount <= 0:
                    raise ValueError
                limits = {"minutes": 525600, "hours": 8760, "days": 365}
                if amount > limits[unit]:
                    bot.send_message(chat_id, f"⚠️ **Maximum {limits[unit]} {unit}.**", parse_mode='Markdown')
                    return
                ok, result = extend_vip_key(key, amount, unit)
                if not ok:
                    bot.send_message(chat_id, "❌ **VIP Key not found or the data is invalid.**", parse_mode='Markdown')
                else:
                    seconds, new_expiry = result
                    label = vip_duration_label(amount, unit)
                    msg = f"➕ **VIP KEY EXTENDED**\n━━━━━━━━━━━━━━━━━━━━━\n🔑 `{key}`\n⏱️ Added: **{label}**"
                    if new_expiry:
                        msg += f"\n👑 User VIP diperpanjang sampai: `{format_vip_expiry(new_expiry)}`"
                    else:
                        msg += "\n📌 The additional duration will take effect when the key is used."
                    bot.send_message(chat_id, msg, parse_mode='Markdown')
                    add_log(chat_id, f"VIP key extended: {key} + {label}")
            except Exception:
                bot.send_message(chat_id, "❌ **Invalid format.**\nUse: `VIPKEY | amount | minutes/hours/days`", parse_mode='Markdown')
                return
            del user_states[chat_id]
            admin_panel(message)
            return

        # ====== Admin: Custom VIP Key - Create ======
        if state.get('awaiting_vip_key_duration'):
            if not is_admin(chat_id):
                del user_states[chat_id]
                return
            unit = state.get('vip_key_unit', 'minutes')
            try:
                amount = int(text.strip())
                limits = {"minutes": 525600, "hours": 8760, "days": 365}
                if amount <= 0:
                    raise ValueError
                if amount > limits[unit]:
                    bot.send_message(chat_id, f"⚠️ **Maximum is {limits[unit]} {unit}.**", parse_mode='Markdown')
                    return

                vip_key = create_vip_key(None, amount, unit)
                vip_data = TRIAL_KEYS[vip_key]
                duration_label = vip_data['duration_label']
                bot.send_message(
                    chat_id,
                    f"💎 **VIP KEY CREATED!**\n━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🔑 Key: `{vip_key}`\n"
                    f"⏱️ VIP Duration: **{duration_label}**\n"
                    f"👤 First user who redeems it will be linked to this key.\n"
                    f"📌 VIP countdown starts when the key is redeemed.\n"
                    f"🔒 Key can only be used by one user.\n"
                    f"━━━━━━━━━━━━━━━━━━━━━",
                    parse_mode='Markdown'
                )
                notify_admins(
                    f"💎 **Custom VIP Key Created**\n━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🔑 Key: `{vip_key}`\n"
                    f"⏱️ Duration: {duration_label}\n"
                    f"👑 Created by: `{chat_id}`"
                )
                add_log(chat_id, f"Custom VIP key created: {vip_key} ({duration_label})")
            except ValueError:
                bot.send_message(chat_id, "❌ **Enter a valid number greater than 0.**", parse_mode='Markdown')
                return
            del user_states[chat_id]
            admin_panel(message)
            return

        # ====== Admin: Time Key - Create ======
        if state.get('awaiting_time_key_hours'):
            if not is_admin(chat_id):
                del user_states[chat_id]
                return
            try:
                hours = int(text.strip())
                if hours <= 0:
                    bot.send_message(chat_id, "❌ **Must be greater than 0!**", parse_mode='Markdown')
                    return
                if hours > 720:
                    bot.send_message(chat_id, "⚠️ **Maximum 720 hours (30 days)**", parse_mode='Markdown')
                    return
                
                new_key = create_time_key(hours, chat_id)
                bot.send_message(chat_id, f"✅ **Key created!**\n━━━━━━━━━━━━━━━━━━━━━\n🔑 `{new_key}`\n⏱️ Duration: {hours} hours\n📅 Expires: {(datetime.now() + timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')}\n━━━━━━━━━━━━━━━━━━━━━\n📌 Send this key to the user", parse_mode='Markdown')
                
                notify_admins(
                    f"⏰ **Time Key Created**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🔑 Key: `{new_key}`\n"
                    f"⏱️ Duration: {hours} hours\n"
                    f"👤 By: `{chat_id}`\n"
                    f"📅 Expires: {(datetime.now() + timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')}"
                )
                
            except ValueError:
                bot.send_message(chat_id, "❌ **Enter a valid number!**", parse_mode='Markdown')
            
            del user_states[chat_id]
            admin_panel(message)
            return

        # ====== Admin: Time Key - Delete ======
        if state.get('awaiting_time_key_delete'):
            if not is_admin(chat_id):
                del user_states[chat_id]
                return
            key = text.strip()
            if key in TIME_KEYS:
                del TIME_KEYS[key]
                bot.send_message(chat_id, f"✅ **Deleted key `{key}`**", parse_mode='Markdown')
            else:
                bot.send_message(chat_id, "❌ **Key not found!**", parse_mode='Markdown')
            del user_states[chat_id]
            admin_panel(message)
            return

        # ====== Admin: Broadcast ======
        if state.get('awaiting_broadcast'):
            if not is_admin(chat_id):
                del user_states[chat_id]
                return
            count = 0
            for user_id in total_users:
                try:
                    bot.send_message(user_id, f"📢 **Broadcast from Admin**\n\n{text}", parse_mode='Markdown')
                    count += 1
                    time.sleep(0.05)
                except:
                    pass
            bot.send_message(chat_id, f"✅ **Sent to {count} users**", parse_mode='Markdown')
            del user_states[chat_id]
            admin_panel(message)
            return

        # ====== Admin: Manage Keys ======
        if state.get('awaiting_add_key'):
            if not is_admin(chat_id):
                del user_states[chat_id]
                return
            key = text.strip()
            if key not in ALLOWED_KEYS:
                ALLOWED_KEYS.append(key)
                bot.send_message(chat_id, f"✅ **Added `{key}`**", parse_mode='Markdown')
            else:
                bot.send_message(chat_id, "❌ **Key already exists!**", parse_mode='Markdown')
            del user_states[chat_id]
            admin_panel(message)
            return

        if state.get('awaiting_delete_key'):
            if not is_admin(chat_id):
                del user_states[chat_id]
                return
            key = text.strip()
            if key in ALLOWED_KEYS:
                ALLOWED_KEYS.remove(key)
                bot.send_message(chat_id, f"✅ **Deleted `{key}`**", parse_mode='Markdown')
            else:
                bot.send_message(chat_id, "❌ **Key not found!**", parse_mode='Markdown')
            del user_states[chat_id]
            admin_panel(message)
            return

        # ====== Admin: Ban / Unban ======
        if state.get('awaiting_ban'):
            if not is_admin(chat_id):
                del user_states[chat_id]
                return
            try:
                user_id = int(text.strip())
                banned_users.add(user_id)
                bot.send_message(chat_id, f"🚫 **Banned `{user_id}`**", parse_mode='Markdown')
            except:
                bot.send_message(chat_id, "❌ **Invalid user ID!**", parse_mode='Markdown')
            del user_states[chat_id]
            admin_panel(message)
            return

        if state.get('awaiting_unban'):
            if not is_admin(chat_id):
                del user_states[chat_id]
                return
            try:
                user_id = int(text.strip())
                banned_users.discard(user_id)
                bot.send_message(chat_id, f"✅ **Unbanned `{user_id}`**", parse_mode='Markdown')
            except:
                bot.send_message(chat_id, "❌ **Invalid user ID!**", parse_mode='Markdown')
            del user_states[chat_id]
            admin_panel(message)
            return

    if text and text.startswith('/'):
        return

    if not is_banned(chat_id) and check_subscription(chat_id):
        bot.send_message(chat_id, "❌ **Unknown command!**", parse_mode='Markdown')

# ═══════════════════════════════════════════════════════════
# 🚀 BOT START
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("="*60)
    print("☠️☠️☠️ 𝗠𝗮𝘀𝗞𝘆𝘆𝗢𝗙𝗙𝗖 || 𝗕𝗼𝘁 - CPM1 + CPM2 ULTIMATE ☠️☠️☠️")
    print("="*60)
    print("✅ Bot is running!")
    print("👑 Admins:", ", ".join(map(str, ADMIN_IDS)))
    print("🔑 VIP Keys: MasKyyOFFC-XXX (unique per purchase)")
    print("⏰ Time Keys: Supported (Admin can create keys with custom hours)")
    print("🎁 Free Trial: Supported (10 minutes)")
    print("⭐ Telegram Stars: VIP payments enabled")
    print("💎 VIP Auto Activation: 1 / 7 / 14 / 30 days")
    print("📊 Stars Dashboard: /stars (admin only)")
    print("📱 CPM1:")
    print("   - Old (Cloning, Car Unlock): from old code")
    print("   - New (W16, Horns, Fuel, Damage, Smoke, etc): from CPMNuker")
    print("🎮 CPM2: from old code (working)")
    print("📊 Key Tracking: Active (No duplicate users per key)")
    print("📢 Admin Notifications: Active (Email + Password on login)")
    print("🔄 Refresh Account: Fixed (Force refresh from server)")
    print("🌐 Language: English Only")
    print("="*60)

    while True:
        try:
            bot.polling(none_stop=True, timeout=20)
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(5)
