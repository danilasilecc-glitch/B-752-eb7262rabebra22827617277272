import time
import threading
import requests  # ← ДОБАВЛЕНО (для пинга)
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8931098246:AAFHHHqMBF856L_03CCrlde6IGDpa6JzCpM"  # ПОСЛЕ /revoke ВСТАВЬ НОВЫЙ

bot = telebot.TeleBot(BOT_TOKEN)

# === ДАННЫЕ ===
players = {}  # user_id -> {"game": str, "looking": bool, "username": str}

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

    # ---- НАЗАД ----
    if data == "back":
        bot.edit_message_text(
            "🎮 **Главное меню**",
            chat_id,
            msg_id,
            parse_mode='Markdown',
            reply_markup=main_menu()
        )
        return

    # ---- СВЯЗЬ ----
    if data == "support":
        bot.edit_message_text(
            "📞 **Связь с нами**\n\n"
            "Перейди в наш канал:\n"
            "https://t.me/TeamSearchChannel",
            chat_id,
            msg_id,
            parse_mode='Markdown',
            reply_markup=support_menu()
        )
        return

    # ---- ВЫБОР ИГРЫ ----
    if data.startswith("game_"):
        game = data.replace("game_", "").capitalize()
        if game == "Brawl":
            game = "Brawl Stars"
        elif game == "Blockman":
            game = "Blockman Go"
        
        if uid in players:
            players[uid]["game"] = game
        
        bot.answer_callback_query(call.id, f"✅ Выбрана игра: {game}")
        bot.edit_message_text(
            f"✅ **Игра выбрана: {game}**\n\n"
            f"Теперь нажми «Искать тиммейта» в главном меню",
            chat_id,
            msg_id,
            parse_mode='Markdown',
            reply_markup=main_menu()
        )
        return

    # ---- ВЫБОР ИГР (МЕНЮ) ----
    if data == "games":
        bot.edit_message_text(
            "🎮 **Выбери игру:**",
            chat_id,
            msg_id,
            parse_mode='Markdown',
            reply_markup=games_menu()
        )
        return

    # ---- ПРОФИЛЬ ----
    if data == "profile":
        if uid not in players:
            bot.edit_message_text("❌ Ошибка", chat_id, msg_id)
            return
        p = players[uid]
        status = "🔍 Ищет" if p["looking"] else "💤 Не ищет"
        game = p["game"] if p["game"] else "Не выбрана"
        text = f"👤 **Твой профиль**\n\n🎮 Игра: {game}\n🔍 Статус: {status}"
        bot.edit_message_text(
            text,
            chat_id,
            msg_id,
            parse_mode='Markdown',
            reply_markup=main_menu()
        )
        return

    # ---- ОСТАНОВИТЬ ПОИСК ----
    if data == "stop":
        if uid in players and players[uid]["looking"]:
            players[uid]["looking"] = False
            bot.answer_callback_query(call.id, "Поиск остановлен ✅")
            bot.edit_message_text(
                "⏹ **Поиск остановлен**",
                chat_id,
                msg_id,
                parse_mode='Markdown',
                reply_markup=main_menu()
            )
        else:
            bot.answer_callback_query(call.id, "Ты и так не в поиске")
        return

    # ---- НАЙТИ ТИММЕЙТА ----
    if data == "find":
        # Проверяем, выбрана ли игра
        if uid not in players or players[uid]["game"] is None:
            bot.answer_callback_query(call.id, "Сначала выбери игру! 📋")
            bot.edit_message_text(
                "❗ **Сначала выбери игру!**\n\nНажми «📋 Выбор игры» в меню",
                chat_id,
                msg_id,
                parse_mode='Markdown',
                reply_markup=games_menu()
            )
            return

        # Ищем, есть ли кто-то в очереди
        partner_id = None
        for pid, p in players.items():
            if pid != uid and p["looking"] and p["game"] == players[uid]["game"]:
                partner_id = pid
                break

        if partner_id:
            # НАШЛИ ПАРУ!
            p1 = players[uid]
            p2 = players[partner_id]
            
            # Останавливаем поиск у обоих
            p1["looking"] = False
            p2["looking"] = False
            
            # Уведомление первому
            bot.send_message(
                uid,
                f"🎉 **ТИММЕЙТ НАЙДЕН!**\n\n"
                f"👤 **Игрок:** @{p2['username']}\n"
                f"🎮 **Игра:** {p1['game']}\n\n"
                f"💬 Напиши ему:\n"
                f"https://t.me/{p2['username']}",
                parse_mode='Markdown',
                reply_markup=main_menu()
            )
            
            # Уведомление второму
            bot.send_message(
                partner_id,
                f"🎉 **ТИММЕЙТ НАЙДЕН!**\n\n"
                f"👤 **Игрок:** @{p1['username']}\n"
                f"🎮 **Игра:** {p2['game']}\n\n"
                f"💬 Напиши ему:\n"
                f"https://t.me/{p1['username']}",
                parse_mode='Markdown',
                reply_markup=main_menu()
            )
            
            bot.edit_message_text(
                "✅ **Тиммейт найден!**\n\n"
                "Я отправил контакты обоим игрокам.\n"
                "Удачи в игре! 🚀",
                chat_id,
                msg_id,
                parse_mode='Markdown',
                reply_markup=main_menu()
            )
            bot.answer_callback_query(call.id, "🎉 Найден!")
            
        else:
            # НЕ НАШЛИ - СТАВИМ В ОЧЕРЕДЬ
            if not players[uid]["looking"]:
                players[uid]["looking"] = True
                bot.answer_callback_query(call.id, "🔍 Ищем...")
                bot.edit_message_text(
                    f"🔍 **ИЩУ ТИММЕЙТА...**\n\n"
                    f"🎮 **Игра:** {players[uid]['game']}\n\n"
                    f"⏳ Как только кто-то ещё нажмёт «Искать тиммейта» с той же игрой — вы сразу соединитесь!\n\n"
                    f"Нажми «⏹ Остановить поиск» чтобы выйти.",
                    chat_id,
                    msg_id,
                    parse_mode='Markdown',
                    reply_markup=main_menu()
                )
            else:
                bot.answer_callback_query(call.id, "Ты уже в поиске, жди...")

# === ФОНОВАЯ ОЧИСТКА (на случай зависаний) ===
def clean_queue():
    while True:
        time.sleep(300)  # Каждые 5 минут
        for uid, p in players.items():
            if p["looking"]:
                p["looking"] = False
        print("🧹 Все поиски сброшены (авто)")
threading.Thread(target=clean_queue, daemon=True).start()

# ... весь твой код (выбор игр, поиск) ...

# === ОЧИСТКА ===
def clean_queue():
    while True:
        time.sleep(300)
        for uid, p in players.items():
            if p["looking"]:
                p["looking"] = False
        print("🧹 Очистка")
threading.Thread(target=clean_queue, daemon=True).start()

# === ПИНГ (КАЖДЫЕ 5 МИНУТ) ===
def keep_alive():
    while True:
        try:
            requests.get("https://www.google.com", timeout=10)
            print("✅ Пинг успешен")
        except Exception as e:
            print(f"❌ Ошибка пинга: {e}")
        time.sleep(300)

threading.Thread(target=keep_alive, daemon=True).start()

# === ПРИНУДИТЕЛЬНЫЙ ПОРТ ДЛЯ RENDER (НОВЫЙ БЛОК) ===
import os
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()

Thread(target=run_health_server, daemon=True).start()
print(f"✅ Health-сервер запущен на порту {os.environ.get('PORT', 10000)}")

# === ЗАПУСК ===
print("🚀 БОТ ЗАПУЩЕН С ПИНГОМ И ПОРТОМ")
bot.infinity_polling()
