import time
import threading
import requests
import telebot
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from threading import Thread  # ← ВАЖНО: ДОБАВЛЕН ПРАВИЛЬНЫЙ ИМПОРТ

BOT_TOKEN = "8931098246:AAFmaI36_-djNpBzvGTGl7eqNY_sopup8s0"  # ЗАМЕНИ

bot = telebot.TeleBot(BOT_TOKEN)

# === ДАННЫЕ ===
players = {}
start_sent = {}

# === КЛАВИАТУРЫ ===

def main_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🎮 Искать тиммейта", callback_data="find"),
        InlineKeyboardButton("📋 Выбор игры", callback_data="games")
    )
    kb.add(
        InlineKeyboardButton("👤 Мой профиль", callback_data="profile"),
        InlineKeyboardButton("📞 Связь", callback_data="support")
    )
    kb.add(InlineKeyboardButton("⏹ Остановить поиск", callback_data="stop"))
    return kb

def games_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("⛏️ Minecraft", callback_data="game_minecraft"),
        InlineKeyboardButton("🔫 Brawl Stars", callback_data="game_brawl"),
        InlineKeyboardButton("🧱 Roblox", callback_data="game_roblox"),
        InlineKeyboardButton("🎮 Blockman Go", callback_data="game_blockman")
    )
    kb.add(InlineKeyboardButton("🔙 Назад", callback_data="back"))
    return kb

def support_menu():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("📢 Перейти в канал", url="https://t.me/TeamSearchChannel"))
    kb.add(InlineKeyboardButton("🔙 Назад", callback_data="back"))
    return kb

# === КОМАНДЫ ===

@bot.message_handler(commands=['start'])
def start(msg):
    uid = msg.from_user.id
    username = msg.from_user.username or f"User{uid}"
    
    current_time = time.time()
    if uid in start_sent and current_time - start_sent[uid] < 10:
        return
    start_sent[uid] = current_time
    
    if uid not in players:
        players[uid] = {"game": None, "looking": False, "username": username}
    
    bot.send_message(
        uid,
        f"🎮 **Добро пожаловать в TeamFinder!**\n\n"
        f"Привет, {username}!\n\n"
        f"1️⃣ Сначала выбери игру\n"
        f"2️⃣ Нажми «Искать тиммейта»\n"
        f"3️⃣ Жди, пока кто-то ещё нажмёт\n\n"
        f"📢 Связь: @TeamSearchChannel",
        parse_mode='Markdown',
        reply_markup=main_menu()
    )

# === ОБРАБОТКА НАЖАТИЙ ===

@bot.callback_query_handler(func=lambda call: True)
def handle(call):
    uid = call.from_user.id
    data = call.data
    chat_id = call.message.chat.id
    msg_id = call.message.message_id

    if data == "back":
        bot.edit_message_text("🎮 **Главное меню**", chat_id, msg_id, parse_mode='Markdown', reply_markup=main_menu())
        return

    if data == "support":
        bot.edit_message_text("📞 **Связь**\n\nhttps://t.me/TeamSearchChannel", chat_id, msg_id, parse_mode='Markdown', reply_markup=support_menu())
        return

    if data.startswith("game_"):
        game = data.replace("game_", "").capitalize()
        if game == "Brawl":
            game = "Brawl Stars"
        elif game == "Blockman":
            game = "Blockman Go"
        if uid in players:
            players[uid]["game"] = game
        bot.answer_callback_query(call.id, f"✅ {game}")
        bot.edit_message_text(f"✅ **Игра: {game}**\n\nТеперь ищи тиммейта", chat_id, msg_id, parse_mode='Markdown', reply_markup=main_menu())
        return

    if data == "games":
        bot.edit_message_text("🎮 **Выбери игру:**", chat_id, msg_id, parse_mode='Markdown', reply_markup=games_menu())
        return

    if data == "profile":
        if uid not in players:
            bot.edit_message_text("❌ Ошибка", chat_id, msg_id)
            return
        p = players[uid]
        status = "🔍 Ищет" if p["looking"] else "💤 Не ищет"
        game = p["game"] if p["game"] else "Не выбрана"
        bot.edit_message_text(f"👤 **Профиль**\n\n🎮 {game}\n🔍 {status}", chat_id, msg_id, parse_mode='Markdown', reply_markup=main_menu())
        return

    if data == "stop":
        if uid in players and players[uid]["looking"]:
            players[uid]["looking"] = False
            bot.answer_callback_query(call.id, "Поиск остановлен ✅")
            bot.edit_message_text("⏹ **Остановлен**", chat_id, msg_id, reply_markup=main_menu())
        else:
            bot.answer_callback_query(call.id, "Ты не в поиске")
        return

    if data == "find":
        if uid not in players or players[uid]["game"] is None:
            bot.answer_callback_query(call.id, "Сначала выбери игру!")
            bot.edit_message_text("❗ **Выбери игру**", chat_id, msg_id, reply_markup=games_menu())
            return

        partner_id = None
        for pid, p in players.items():
            if pid != uid and p["looking"] and p["game"] == players[uid]["game"]:
                partner_id = pid
                break

        if partner_id:
            p1 = players[uid]
            p2 = players[partner_id]
            p1["looking"] = False
            p2["looking"] = False

            bot.send_message(uid, f"🎉 **НАЙДЕН!**\n\n👤 @{p2['username']}\n🎮 {p1['game']}\n\n💬 https://t.me/{p2['username']}", parse_mode='Markdown', reply_markup=main_menu())
            bot.send_message(partner_id, f"🎉 **НАЙДЕН!**\n\n👤 @{p1['username']}\n🎮 {p2['game']}\n\n💬 https://t.me/{p1['username']}", parse_mode='Markdown', reply_markup=main_menu())
            bot.edit_message_text("✅ **Найден!** Контакты отправлены.", chat_id, msg_id, reply_markup=main_menu())
            bot.answer_callback_query(call.id, "🎉 Найден!")
        else:
            if not players[uid]["looking"]:
                players[uid]["looking"] = True
                bot.answer_callback_query(call.id, "🔍 Ищем...")
                bot.edit_message_text(f"🔍 **ИЩУ...**\n\n🎮 {players[uid]['game']}\n\n⏳ Жди...", chat_id, msg_id, parse_mode='Markdown', reply_markup=main_menu())
            else:
                bot.answer_callback_query(call.id, "Ты уже в поиске")

# === ФОНОВАЯ ОЧИСТКА ===
def clean_queue():
    while True:
        time.sleep(300)
        for uid, p in players.items():
            if p["looking"]:
                p["looking"] = False
        print("🧹 Очистка")

threading.Thread(target=clean_queue, daemon=True).start()  # ← ИСПОЛЬЗУЕМ threading.Thread

# === ПИНГ ===
def keep_alive():
    import datetime
    print("🔁 [ПИНГ] Поток запущен и будет работать каждые 5 минут")
    while True:
        try:
            # Пробуем оба адреса для надёжности
            r1 = requests.get("https://www.google.com", timeout=15)
            r2 = requests.get("https://www.cloudflare.com", timeout=15)
            if r1.status_code == 200 or r2.status_code == 200:
                print(f"✅ [ПИНГ] Успешно ({datetime.datetime.now()})")
            else:
                print(f"⚠️ [ПИНГ] Ответ не 200, но мы живы")
        except Exception as e:
            # ЛЮБАЯ ошибка будет поймана и записана
            print(f"❌ [ПИНГ] Ошибка: {type(e).__name__} — {e}")
        # Ждём ровно 5 минут, даже если была ошибка
        time.sleep(300)
threading.Thread(target=keep_alive, daemon=True).start()  # ← ИСПОЛЬЗУЕМ threading.Thread

# === ПОРТ ===
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()

Thread(target=run_health_server, daemon=True).start()  # ← ТЕПЕРЬ Thread РАБОТАЕТ
print(f"✅ Health-сервер запущен на порту {os.environ.get('PORT', 10000)}")

# === ЗАПУСК ===
print("🚀 БОТ ЗАПУЩЕН (ПОЛНАЯ ВЕРСИЯ, ИСПРАВЛЕН ИМПОРТ)")
bot.infinity_polling()
