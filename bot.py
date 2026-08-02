import time
import threading
import requests
import telebot
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from threading import Thread

BOT_TOKEN = "8931098246:AAFm5RQYU_662sEKDt95cKWzVyxpZd9xI3c"
bot = telebot.TeleBot(BOT_TOKEN)

# === ДАННЫЕ ===
players = {}
start_sent = {}

# === ЖАНРЫ И ИГРЫ ===
GAMES_BY_GENRE = {
    "Шутер": ["CS2", "Valorant", "Call of Duty", "Apex Legends", "Fortnite", "PUBG", "Overwatch 2", "Rainbow Six Siege", "Escape from Tarkov", "Destiny 2", "Battlefield 2042", "Team Fortress 2", "Splitgate", "Titanfall 2", "The Finals", "Borderlands 3"],
    "Выживание": ["Minecraft", "Rust", "DayZ", "The Forest", "Sons of the Forest", "Ark", "Conan Exiles", "Scum", "Project Zomboid", "Don't Starve Together", "Terraria", "Valheim", "Grounded", "Raft", "Subnautica", "7 Days to Die"],
    "RPG": ["World of Warcraft", "Final Fantasy XIV", "Guild Wars 2", "Elder Scrolls Online", "Black Desert", "Lost Ark", "Albion Online", "New World", "Diablo III", "Diablo IV", "Path of Exile", "Monster Hunter: World", "Baldur's Gate 3", "Divinity 2"],
    "MOBA": ["Dota 2", "League of Legends", "Mobile Legends", "Smite", "Heroes of the Storm", "Pokemon Unite", "Arena of Valor", "Wild Rift"],
    "Гонки": ["Forza Horizon 5", "Need for Speed", "F1 2024", "Assetto Corsa", "Gran Turismo 7", "Rocket League", "The Crew 2", "DiRT Rally 2.0", "Trackmania"],
    "Песочница": ["Factorio", "Satisfactory", "Cities: Skylines", "Transport Fever 2", "Anno 1800", "Stellaris", "Civilization VI", "Age of Empires IV", "RimWorld", "Oxygen Not Included"],
    "Battle Royale": ["PUBG Mobile", "Garena Free Fire", "Call of Duty Mobile", "Fortnite", "Apex Legends Mobile", "Battle Royale (другие)"],
    "Хоррор": ["Phasmophobia", "Lethal Company", "Dead by Daylight", "Outlast Trials", "The Past Within", "Barotrauma", "Among Us"],
    "Инди / Кооп": ["Stardew Valley", "Core Keeper", "It Takes Two", "A Way Out", "Portal 2", "Human Fall Flat", "Gang Beasts", "Overcooked 2", "PlateUp!"],
    "Мобильные": ["Brawl Stars", "Blockman Go", "Roblox", "Clash of Clans", "Clash Royale", "Hay Day", "Boom Beach", "Pokémon GO", "Whiteout Survival", "State of Survival", "Standoff 2", "Critical Ops"]
}

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

def genre_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    for genre in GAMES_BY_GENRE.keys():
        kb.add(InlineKeyboardButton(genre, callback_data=f"genre_{genre}"))
    kb.add(InlineKeyboardButton("🔙 Назад", callback_data="back"))
    return kb

def games_menu_for_genre(genre):
    kb = InlineKeyboardMarkup(row_width=2)
    for game in GAMES_BY_GENRE[genre]:
        kb.add(InlineKeyboardButton(game, callback_data=f"game_{game.lower().replace(' ', '_')}"))
    kb.add(InlineKeyboardButton("🔙 Назад", callback_data="genre_back"))
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

    # ---- НАЗАД ----
    if data == "back":
        bot.edit_message_text("🎮 **Главное меню**", chat_id, msg_id, parse_mode='Markdown', reply_markup=main_menu())
        bot.answer_callback_query(call.id)
        return

    if data == "genre_back":
        bot.edit_message_text("🎮 **Выбери жанр:**", chat_id, msg_id, parse_mode='Markdown', reply_markup=genre_menu())
        bot.answer_callback_query(call.id)
        return

    # ---- СВЯЗЬ ----
    if data == "support":
        bot.edit_message_text("📞 **Связь**\n\nhttps://t.me/TeamSearchChannel", chat_id, msg_id, parse_mode='Markdown', reply_markup=support_menu())
        bot.answer_callback_query(call.id)
        return

    # ---- ВЫБОР ЖАНРА ----
    if data.startswith("genre_"):
        genre = data.replace("genre_", "")
        if genre in GAMES_BY_GENRE:
            bot.edit_message_text(f"🎮 **Жанр: {genre}**\n\nВыбери игру:", chat_id, msg_id, parse_mode='Markdown', reply_markup=games_menu_for_genre(genre))
        else:
            bot.answer_callback_query(call.id, "❌ Ошибка")
        bot.answer_callback_query(call.id)
        return

    # ---- ВЫБОР ИГРЫ ----
    if data.startswith("game_"):
        game = data.replace("game_", "").replace("_", " ").title()
        # Исправляем названия
        if "Brawl Stars" in game:
            game = "Brawl Stars"
        elif "Roblox" in game:
            game = "Roblox"
        elif "Blockman Go" in game:
            game = "Blockman Go"
        elif "Cs2" in game:
            game = "CS2"
        elif "F1 2024" in game:
            game = "F1 2024"
        elif "Gta V" in game:
            game = "GTA V"
        # Сохраняем игру
        if uid in players:
            players[uid]["game"] = game
        bot.answer_callback_query(call.id, f"✅ {game}")
        bot.edit_message_text(f"✅ **Игра: {game}**\n\nТеперь ищи тиммейта", chat_id, msg_id, parse_mode='Markdown', reply_markup=main_menu())
        return

    # ---- ВЫБОР ИГР (МЕНЮ) ----
    if data == "games":
        bot.edit_message_text("🎮 **Выбери жанр:**", chat_id, msg_id, parse_mode='Markdown', reply_markup=genre_menu())
        bot.answer_callback_query(call.id)
        return

    # ---- ПРОФИЛЬ ----
    if data == "profile":
        if uid not in players:
            bot.edit_message_text("❌ Ошибка", chat_id, msg_id)
            bot.answer_callback_query(call.id)
            return
        p = players[uid]
        status = "🔍 Ищет" if p["looking"] else "💤 Не ищет"
        game = p["game"] if p["game"] else "Не выбрана"
        bot.edit_message_text(f"👤 **Профиль**\n\n🎮 {game}\n🔍 {status}", chat_id, msg_id, parse_mode='Markdown', reply_markup=main_menu())
        bot.answer_callback_query(call.id)
        return

    # ---- ОСТАНОВИТЬ ПОИСК ----
    if data == "stop":
        if uid in players and players[uid]["looking"]:
            players[uid]["looking"] = False
            bot.answer_callback_query(call.id, "Поиск остановлен ✅")
            bot.edit_message_text("⏹ **Остановлен**", chat_id, msg_id, reply_markup=main_menu())
        else:
            bot.answer_callback_query(call.id, "Ты не в поиске")
        return

    # ---- НАЙТИ ТИММЕЙТА ----
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
        return

    # ---- ЕСЛИ НИЧЕГО НЕ ПОДОШЛО ----
    bot.answer_callback_query(call.id, "❌ Неизвестная команда")

# === ФОНОВАЯ ОЧИСТКА ===
def clean_queue():
    while True:
        time.sleep(300)
        for uid, p in players.items():
            if p["looking"]:
                p["looking"] = False
        print("🧹 Очистка")
threading.Thread(target=clean_queue, daemon=True).start()

# === ПИНГ ===
def keep_alive():
    import datetime
    print("🔁 [ПИНГ] Поток запущен и будет работать каждые 5 минут")
    while True:
        try:
            r1 = requests.get("https://www.google.com", timeout=15)
            r2 = requests.get("https://www.cloudflare.com", timeout=15)
            if r1.status_code == 200 or r2.status_code == 200:
                print(f"✅ [ПИНГ] Успешно ({datetime.datetime.now()})")
            else:
                print(f"⚠️ [ПИНГ] Ответ не 200, но мы живы")
        except Exception as e:
            print(f"❌ [ПИНГ] Ошибка: {type(e).__name__} — {e}")
        time.sleep(300)
threading.Thread(target=keep_alive, daemon=True).start()

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

Thread(target=run_health_server, daemon=True).start()
print(f"✅ Health-сервер запущен на порту {os.environ.get('PORT', 10000)}")

# === ЗАПУСК ===
print("🚀 БОТ ЗАПУЩЕН (С ЖАНРАМИ И 190+ ИГРАМИ)")
bot.infinity_polling()
