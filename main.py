import os
import random
import sqlite3
import asyncio
from datetime import datetime, timezone

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
OWNER_ID = int(os.getenv("OWNER_ID", "0") or 0)
DB_PATH = os.getenv("DB_PATH", "giveaway.db")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN belum diisi.")
if not OWNER_ID:
    raise RuntimeError("OWNER_ID belum diisi.")

db_lock = asyncio.Lock()


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS giveaways (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            message_id INTEGER,
            reward TEXT NOT NULL,
            winners_count INTEGER NOT NULL,
            end_time INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            created_by INTEGER NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS participants (
            giveaway_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            username TEXT,
            full_name TEXT,
            joined_at INTEGER NOT NULL,
            PRIMARY KEY (giveaway_id, user_id)
        )
    """)
    conn.commit()
    conn.close()


def now_ts():
    return int(datetime.now(timezone.utc).timestamp())


def format_time(seconds):
    seconds = max(0, int(seconds))
    d, rem = divmod(seconds, 86400)
    h, rem = divmod(rem, 3600)
    m, s = divmod(rem, 60)
    if d:
        return f"{d}d {h}h {m}m"
    if h:
        return f"{h}h {m}m {s}s"
    return f"{m}m {s}s"


def get_giveaway(gid):
    conn = db()
    row = conn.execute("SELECT * FROM giveaways WHERE id=?", (gid,)).fetchone()
    conn.close()
    return row


def participant_count(gid):
    conn = db()
    n = conn.execute(
        "SELECT COUNT(*) FROM participants WHERE giveaway_id=?", (gid,)
    ).fetchone()[0]
    conn.close()
    return n


def is_participant(gid, user_id):
    conn = db()
    row = conn.execute(
        "SELECT 1 FROM participants WHERE giveaway_id=? AND user_id=?",
        (gid, user_id),
    ).fetchone()
    conn.close()
    return row is not None


def giveaway_text(row):
    remaining = format_time(row["end_time"] - now_ts())
    joined = participant_count(row["id"])
    return (
        "🎁 <b>MEGA DROP ACTIVE</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"◇ <b>Reward:</b> {escape_html(row['reward'])}\n"
        f"◇ <b>Winners:</b> {row['winners_count']}\n\n"
        f"👥 <b>Joined:</b> {joined}\n"
        f"⏳ <b>{remaining} remaining!</b>\n"
        "━━━━━━━━━━━━━━━━━━"
    )


def escape_html(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def giveaway_keyboard(gid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◇ Secure Position ◇", callback_data=f"join:{gid}")]
    ])


async def owner_only(update: Update):
    user = update.effective_user
    if not user or user.id != OWNER_ID:
        if update.message:
            await update.message.reply_text("⛔ Perintah ini khusus Owner.")
        return False
    return True


async def giveaway_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await owner_only(update):
        return

    if update.effective_chat.type == "private":
        await update.message.reply_text(
            "Gunakan /giveaway di grup/channel tempat giveaway ingin dibuat."
        )
        return

    # Format:
    # /giveaway 10 30m | Premium 30 Hari
    raw = " ".join(context.args)
    if "|" not in raw:
        await update.message.reply_text(
            "Format:\n"
            "/giveaway JUMLAH_PEMENANG DURASI | HADIAH\n\n"
            "Contoh:\n"
            "/giveaway 20 30m | Premium 30 Hari\n"
            "/giveaway 3 1h | 1000 Coins"
        )
        return

    left, reward = raw.split("|", 1)
    parts = left.strip().split()
    reward = reward.strip()

    if len(parts) != 2 or not reward:
        await update.message.reply_text("Format tidak valid.")
        return

    try:
        winners = int(parts[0])
        duration = parse_duration(parts[1])
    except ValueError:
        await update.message.reply_text(
            "Jumlah pemenang harus angka dan durasi seperti 30m, 1h, 2d."
        )
        return

    if winners < 1 or winners > 1000:
        await update.message.reply_text("Jumlah pemenang harus 1-1000.")
        return
    if duration < 10 or duration > 30 * 86400:
        await update.message.reply_text("Durasi harus 10 detik sampai 30 hari.")
        return

    end_time = now_ts() + duration
    conn = db()
    cur = conn.execute(
        """INSERT INTO giveaways
        (chat_id, reward, winners_count, end_time, status, created_by)
        VALUES (?, ?, ?, ?, 'active', ?)""",
        (update.effective_chat.id, reward, winners, end_time, OWNER_ID),
    )
    gid = cur.lastrowid
    conn.commit()
    conn.close()

    msg = await update.message.reply_text(
        giveaway_text(get_giveaway(gid)),
        parse_mode=ParseMode.HTML,
        reply_markup=giveaway_keyboard(gid),
    )

    conn = db()
    conn.execute(
        "UPDATE giveaways SET message_id=? WHERE id=?",
        (msg.message_id, gid),
    )
    conn.commit()
    conn.close()

    asyncio.create_task(giveaway_worker(context.application, gid))


def parse_duration(value):
    value = value.lower().strip()
    if len(value) < 2:
        raise ValueError

    number = int(value[:-1])
    unit = value[-1]

    multipliers = {
        "s": 1,
        "m": 60,
        "h": 3600,
        "d": 86400,
    }
    if unit not in multipliers:
        raise ValueError
    return number * multipliers[unit]


async def join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        gid = int(query.data.split(":")[1])
    except Exception:
        return

    row = get_giveaway(gid)
    if not row or row["status"] != "active":
        await query.answer("❌ Giveaway sudah berakhir.", show_alert=True)
        return

    if row["end_time"] <= now_ts():
        await finish_giveaway(context.application, gid)
        await query.answer("❌ Giveaway sudah berakhir.", show_alert=True)
        return

    user = query.from_user

    async with db_lock:
        conn = db()
        try:
            conn.execute(
                """INSERT INTO participants
                (giveaway_id, user_id, username, full_name, joined_at)
                VALUES (?, ?, ?, ?, ?)""",
                (
                    gid,
                    user.id,
                    user.username or "",
                    user.full_name or "",
                    now_ts(),
                ),
            )
            conn.commit()
            already = False
        except sqlite3.IntegrityError:
            already = True
        finally:
            conn.close()

    if already:
        await query.answer("⚠️ Kamu sudah ikut giveaway!", show_alert=True)
    else:
        await query.answer("✅ Posisi berhasil diamankan! Good luck 🍀", show_alert=True)

    await refresh_giveaway_message(context.application, gid)


async def refresh_giveaway_message(application, gid):
    row = get_giveaway(gid)
    if not row or row["status"] != "active" or not row["message_id"]:
        return

    try:
        await application.bot.edit_message_text(
            chat_id=row["chat_id"],
            message_id=row["message_id"],
            text=giveaway_text(row),
            parse_mode=ParseMode.HTML,
            reply_markup=giveaway_keyboard(gid),
        )
    except Exception:
        pass


async def giveaway_worker(application, gid):
    # Background task survives normally while the bot process is running.
    # Database state allows the bot to recover active giveaways after restart.
    while True:
        row = get_giveaway(gid)
        if not row or row["status"] != "active":
            return

        remaining = row["end_time"] - now_ts()
        if remaining <= 0:
            await finish_giveaway(application, gid)
            return

        await refresh_giveaway_message(application, gid)
        await asyncio.sleep(min(10, max(1, remaining)))


async def recover_active_giveaways(application):
    conn = db()
    rows = conn.execute(
        "SELECT id FROM giveaways WHERE status='active'"
    ).fetchall()
    conn.close()

    for row in rows:
        gid = row["id"]
        if get_giveaway(gid)["end_time"] <= now_ts():
            await finish_giveaway(application, gid)
        else:
            asyncio.create_task(giveaway_worker(application, gid))


async def finish_giveaway(application, gid):
    row = get_giveaway(gid)
    if not row or row["status"] != "active":
        return

    conn = db()
    users = conn.execute(
        "SELECT * FROM participants WHERE giveaway_id=?",
        (gid,),
    ).fetchall()

    winners = random.sample(users, min(row["winners_count"], len(users)))
    conn.execute(
        "UPDATE giveaways SET status='finished' WHERE id=?", (gid,)
    )
    conn.commit()
    conn.close()

    if winners:
        winner_lines = []
        for w in winners:
            if w["username"]:
                winner_lines.append(f"• @{escape_html(w['username'])}")
            else:
                winner_lines.append(
                    f"• <a href='tg://user?id={w['user_id']}'>{escape_html(w['full_name'])}</a>"
                )
        winners_text = "\n".join(winner_lines)
    else:
        winners_text = "Tidak ada peserta."

    final_text = (
        "🏆 <b>GIVEAWAY ENDED</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"🎁 <b>Reward:</b> {escape_html(row['reward'])}\n"
        f"👥 <b>Participants:</b> {len(users)}\n\n"
        "🥇 <b>WINNERS</b>\n"
        f"{winners_text}\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Terima kasih sudah ikut! ❤️"
    )

    try:
        await application.bot.edit_message_text(
            chat_id=row["chat_id"],
            message_id=row["message_id"],
            text=final_text,
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        pass

    if winners:
        for w in winners:
            try:
                await application.bot.send_message(
                    chat_id=w["user_id"],
                    text=(
                        "🎉 <b>CONGRATULATIONS!</b>\n\n"
                        f"Kamu memenangkan: <b>{escape_html(row['reward'])}</b>\n\n"
                        "Silakan hubungi Owner untuk klaim hadiah."
                    ),
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                # User may have blocked the bot / not started it.
                pass


async def end_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await owner_only(update):
        return

    if not context.args:
        await update.message.reply_text("Gunakan: /end ID")
        return

    try:
        gid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("ID harus angka.")
        return

    row = get_giveaway(gid)
    if not row or row["status"] != "active":
        await update.message.reply_text("Giveaway tidak ditemukan atau sudah selesai.")
        return

    await finish_giveaway(context.application, gid)
    await update.message.reply_text(f"✅ Giveaway #{gid} telah diakhiri.")


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await owner_only(update):
        return

    if not context.args:
        await update.message.reply_text("Gunakan: /cancel ID")
        return

    try:
        gid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("ID harus angka.")
        return

    row = get_giveaway(gid)
    if not row or row["status"] != "active":
        await update.message.reply_text("Giveaway tidak ditemukan atau sudah selesai.")
        return

    conn = db()
    conn.execute(
        "UPDATE giveaways SET status='cancelled' WHERE id=?", (gid,)
    )
    conn.commit()
    conn.close()

    try:
        await context.bot.edit_message_text(
            chat_id=row["chat_id"],
            message_id=row["message_id"],
            text="❌ <b>GIVEAWAY CANCELLED</b>\n\nGiveaway dibatalkan oleh Owner.",
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        pass

    await update.message.reply_text(f"✅ Giveaway #{gid} dibatalkan.")


async def participants_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await owner_only(update):
        return

    if not context.args:
        await update.message.reply_text("Gunakan: /participants ID")
        return

    try:
        gid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("ID harus angka.")
        return

    row = get_giveaway(gid)
    if not row:
        await update.message.reply_text("Giveaway tidak ditemukan.")
        return

    conn = db()
    users = conn.execute(
        "SELECT * FROM participants WHERE giveaway_id=? ORDER BY joined_at ASC",
        (gid,),
    ).fetchall()
    conn.close()

    lines = [f"👥 Participants Giveaway #{gid}: {len(users)}"]
    for i, u in enumerate(users[:100], 1):
        name = f"@{u['username']}" if u["username"] else u["full_name"]
        lines.append(f"{i}. {name}")

    if len(users) > 100:
        lines.append(f"\n... dan {len(users)-100} peserta lainnya.")

    await update.message.reply_text("\n".join(lines))


async def active_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await owner_only(update):
        return

    conn = db()
    rows = conn.execute(
        "SELECT * FROM giveaways WHERE status='active' ORDER BY end_time ASC"
    ).fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("Tidak ada giveaway aktif.")
        return

    lines = ["🎁 <b>ACTIVE GIVEAWAYS</b>"]
    for r in rows:
        lines.append(
            f"#{r['id']} — {escape_html(r['reward'])} — "
            f"{format_time(r['end_time'] - now_ts())} — "
            f"{participant_count(r['id'])} peserta"
        )

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.HTML,
    )


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎁 <b>Giveaway Bot</b>\n\n"
        "Bot giveaway otomatis untuk grup Telegram.\n\n"
        "Tekan tombol giveaway untuk mengamankan posisi.",
        parse_mode=ParseMode.HTML,
    )


async def post_init(application):
    init_db()
    await recover_active_giveaways(application)


def main():
    init_db()

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("giveaway", giveaway_command))
    app.add_handler(CommandHandler("end", end_command))
    app.add_handler(CommandHandler("cancel", cancel_command))
    app.add_handler(CommandHandler("participants", participants_command))
    app.add_handler(CommandHandler("active", active_command))
    app.add_handler(CallbackQueryHandler(join_callback, pattern=r"^join:\d+$"))

    print("Giveaway bot started.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
