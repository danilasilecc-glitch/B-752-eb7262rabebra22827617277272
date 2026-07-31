import os
import random
import time
from datetime import datetime
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

BOT_TOKEN = "8931098246:AAHXCV0LS4QCSvHRdfI9qaQCDbfRrpdr43k"  # ЗАМЕНИ НА СВОЙ

bot = telebot.TeleBot(BOT_TOKEN)

# === ХРАНИЛИЩЕ ДАННЫХ ===
# games[user_id] = {"game": str, "looking": bool, "username": str, "time": int}
players = {}
pending_requests = {}  # user_id -> [list of requester_ids]

# === ГЛАВНОЕ МЕНЮ (КРАСИВОЕ) ===
def main_menu_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    btn_find = InlineKeyboardButton("🎮 Искать тиммейта", callback_data="find_teammate")
    btn_games = InlineKeyboardButton("📋 Выбор игры", callback_data="choose_game")
    btn_profile = InlineKeyboardButton("👤 Мой профиль", callback_data="my_profile")
    btn_support = InlineKeyboardButton("📞 Связь", callback_data="support")
    btn_stop = InlineKeyboardButton("⏹ Остановить поиск", callback_data="stop_search")
    keyboard.row(btn_find, btn_games)
    keyboard.row(btn_profile, btn_support)
    keyboard.row(btn_stop)
    return keyboard

# === ВЫБОР ИГРЫ (С ЭМОДЗИ) ===
def games_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("⛏️ Minecraft", callback_data="game_minecraft"),
        InlineKeyboardButton("🔫 Brawl Stars", callback_data="game_brawl"),
        InlineKeyboardButton("🧱 Roblox", callback_data="game_roblox"),
        InlineKeyboardButton("🎮 Blockman Go", callback_data="game_blockman")
    )
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="back_main"))
    return keyboard

# === КЛАВИАТУРА ДЛЯ ВЫБОРА РЕЖИМА ===
def mode_keyboard(game):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🎯 Быстрый поиск", callback_data=f"quick_{game}"),
        InlineKeyboardButton("⚡ Соревновательный", callback_data=f"comp_{game}"),
        InlineKeyboardButton("🎉 Для веселья", callback_data=f"fun_{game}")
    )
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="choose_game"))
    return keyboard

# === ПОДТВЕРЖДЕНИЕ ПОИСКА ===
def confirm_keyboard(game, mode):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Начать поиск", callback_data=f"start_search_{game}_{mode}"),
        InlineKeyboardButton("❌ Отмена", callback_data="back_main")
    )
    return keyboard

# === КНОПКА "СВЯЗЬ" (ВСЕГДА РАБОТАЕТ) ===
def support_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("📢 Перейти в канал", url="https://t.me/TeamSearchChannel"),
        InlineKeyboardButton("🔙 Назад", callback_data="back_main")
    )
    return keyboard

# === ПРОФИЛЬ ===
def profile_text(user_id):
    if user_id not in players:
        return "❌ Ты не зарегистрирован! Напиши /start"
    data = players[user_id]
    status = "🔍 Ищет тиммейта" if data["looking"] else "💤 Не ищет"
    game = data["game"] if data["game"] else "Не выбрана"
    return f"""👤 **Твой профиль**
━━━━━━━━━━━━━━
🎮 **Игра:** {game}
🔍 **Статус:** {status}
⏱ **В поиске:** {data["time"]} сек
👥 **Всего игроков:** {len(players)}

💡 Найди тиммейта через главное меню!"""

# === ОБРАБОТЧИКИ КОМАНД ===

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username or "Без имени"
    
    # Регистрируем игрока
    if user_id not in players:
        players[user_id] = {
            "game": None,
            "looking": False,
            "username": username,
            "time": 0,
            "mode": None
        }
    
    # Приветствие
    welcome_text = f"""🎮 **Добро пожаловать в TeamFinder!**

Привет, {username}! 

Здесь ты найдёшь тиммейтов для:
⛏️ Minecraft | 🔫 Brawl Stars | 🧱 Roblox | 🎮 Blockman Go

🔥 **Как это работает:**
1. Выбери игру
2. Нажми "Искать тиммейта"
3. Жди, пока бот найдёт тебе пару

📢 Есть вопросы? Нажми "Связь"

**Удачи в поиске!** 🚀"""

    bot.send_message(
        user_id,
        welcome_text,
        parse_mode='Markdown',
        reply_markup=main_menu_keyboard()
    )

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(
        message.from_user.id,
        "📖 **Помощь по TeamFinder**\n\n"
        "/start - Главное меню\n"
        "🎮 Искать тиммейта - начать поиск\n"
        "📋 Выбор игры - сменить игру\n"
        "👤 Мой профиль - посмотреть статус\n"
        "📞 Связь - перейти в наш канал\n"
        "⏹ Остановить поиск - выйти из поиска",
        parse_mode='Markdown',
        reply_markup=main_menu_keyboard()
    )

# === ОБРАБОТЧИКИ CALLBACK ===

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    data = call.data
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    # === ГЛАВНЫЕ КНОПКИ ===
    if data == "find_teammate":
        if user_id not in players or players[user_id]["game"] is None:
            bot.answer_callback_query(call.id, "Сначала выбери игру в меню!")
            bot.edit_message_text(
                "❗ **Сначала выбери игру!**\nНажми '📋 Выбор игры' в меню.",
                chat_id,
                message_id,
                parse_mode='Markdown',
                reply_markup=games_keyboard()
            )
            return
        game = players[user_id]["game"]
        bot.edit_message_text(
            f"🎯 **Выбери режим для {game}**",
            chat_id,
            message_id,
            parse_mode='Markdown',
            reply_markup=mode_keyboard(game)
        )
    
    elif data == "choose_game":
        bot.edit_message_text(
            "🎮 **Выбери игру**",
            chat_id,
            message_id,
            parse_mode='Markdown',
            reply_markup=games_keyboard()
        )
    
    elif data == "my_profile":
        bot.edit_message_text(
            profile_text(user_id),
            chat_id,
            message_id,
            parse_mode='Markdown',
            reply_markup=main_menu_keyboard()
        )
    
    elif data == "support":
        bot.edit_message_text(
            "📞 **Связь с поддержкой**\n\n"
            "Перейди в наш канал для связи с админами:\n"
            "🔗 https://t.me/TeamSearchChannel\n\n"
            "Также там публикуются новости и обновления!",
            chat_id,
            message_id,
            parse_mode='Markdown',
            reply_markup=support_keyboard()
        )
    
    elif data == "stop_search":
        if user_id in players and players[user_id]["looking"]:
            players[user_id]["looking"] = False
            players[user_id]["time"] = 0
            bot.answer_callback_query(call.id, "Поиск остановлен ✅")
            bot.edit_message_text(
                "⏹ **Поиск остановлен**\n\nТы больше не ищешь тиммейта.",
                chat_id,
                message_id,
                parse_mode='Markdown',
                reply_markup=main_menu_keyboard()
            )
        else:
            bot.answer_callback_query(call.id, "Ты и так не в поиске")
            bot.edit_message_text(
                "ℹ️ **Ты не в поиске**\nНажми 'Искать тиммейта' чтобы начать",
                chat_id,
                message_id,
                parse_mode='Markdown',
                reply_markup=main_menu_keyboard()
            )
    
    elif data == "back_main":
        bot.edit_message_text(
            "🎮 **Главное меню**\n\nВыбери действие:",
            chat_id,
            message_id,
            parse_mode='Markdown',
            reply_markup=main_menu_keyboard()
        )

    # === ВЫБОР ИГРЫ ===
    elif data.startswith("game_"):
        game_name = data.replace("game_", "").capitalize()
        if game_name == "Brawl":
            game_name = "Brawl Stars"
        elif game_name == "Blockman":
            game_name = "Blockman Go"
        elif game_name == "Roblox":
            game_name = "Roblox"
        elif game_name == "Minecraft":
            game_name = "Minecraft"
        
        if user_id in players:
            players[user_id]["game"] = game_name
        
        bot.answer_callback_query(call.id, f"Выбрана игра: {game_name} ✅")
        bot.edit_message_text(
            f"🎮 **Игра выбрана: {game_name}**\n\n"
            f"Теперь нажми 'Искать тиммейта' в главном меню",
            chat_id,
            message_id,
            parse_mode='Markdown',
            reply_markup=main_menu_keyboard()
        )

    # === ВЫБОР РЕЖИМА ===
    elif data.startswith("quick_") or data.startswith("comp_") or data.startswith("fun_"):
        parts = data.split("_")
        mode = parts[0]
        game = parts[1] if len(parts) > 1 else "игре"
        
        mode_names = {
            "quick": "🎯 Быстрый поиск",
            "comp": "⚡ Соревновательный",
            "fun": "🎉 Для веселья"
        }
        mode_name = mode_names.get(mode, "Режим")
        
        # Сохраняем режим
        if user_id in players:
            players[user_id]["mode"] = mode
        
        bot.edit_message_text(
            f"🔥 **Ты выбрал: {mode_name}**\n"
            f"🎮 Игра: {game}\n\n"
            "Начать поиск?",
            chat_id,
            message_id,
            parse_mode='Markdown',
            reply_markup=confirm_keyboard(game, mode)
        )

    # === СТАРТ ПОИСКА ===
    elif data.startswith("start_search_"):
        parts = data.replace("start_search_", "").split("_")
        game = parts[0]
        mode = parts[1] if len(parts) > 1 else "quick"
        
        # Проверяем, есть ли уже другие игроки в поиске
        found = False
        for pid, pdata in players.items():
            if pid != user_id and pdata["looking"] and pdata["game"] == game and pdata["mode"] == mode:
                # НАШЛИ ПАРУ!
                found = True
                partner_id = pid
                partner_name = pdata["username"]
                
                # Останавливаем поиск у обоих
                players[pid]["looking"] = False
                players[pid]["time"] = 0
                players[user_id]["looking"] = False
                players[user_id]["time"] = 0
                
                # Уведомляем обоих
                bot.send_message(
                    user_id,
                    f"🎉 **ТИММЕЙТ НАЙДЕН!**\n\n"
                    f"👤 **Игрок:** @{partner_name}\n"
                    f"🎮 **Игра:** {game}\n"
                    f"🔥 **Режим:** {mode_names.get(mode, mode)}\n\n"
                    f"💬 Напиши ему прямо сейчас!\n"
                    f"🔗 https://t.me/{partner_name}",
                    parse_mode='Markdown',
                    reply_markup=main_menu_keyboard()
                )
                
                bot.send_message(
                    pid,
                    f"🎉 **ТИММЕЙТ НАЙДЕН!**\n\n"
                    f"👤 **Игрок:** @{players[user_id]['username']}\n"
                    f"🎮 **Игра:** {game}\n"
                    f"🔥 **Режим:** {mode_names.get(mode, mode)}\n\n"
                    f"💬 Напиши ему прямо сейчас!\n"
                    f"🔗 https://t.me/{players[user_id]['username']}",
                    parse_mode='Markdown',
                    reply_markup=main_menu_keyboard()
                )
                
                bot.answer_callback_query(call.id, "Найден тиммейт! 🎉")
                bot.edit_message_text(
                    "✅ **Тиммейт найден!**\n\n"
                    "Я отправил вам обоим контакты.\n"
                    "Удачи в игре! 🚀",
                    chat_id,
                    message_id,
                    parse_mode='Markdown',
                    reply_markup=main_menu_keyboard()
                )
                break
        
        if not found:
            # Если не нашли - ставим в поиск
            if user_id in players:
                players[user_id]["looking"] = True
                players[user_id]["time"] = int(time.time())
            
            bot.answer_callback_query(call.id, "🔍 Ищем тиммейта...")
            bot.edit_message_text(
                f"🔍 **ИЩУ ТИММЕЙТА...**\n\n"
                f"🎮 Игра: {game}\n"
                f"🔥 Режим: {mode_names.get(mode, mode)}\n\n"
                f"⏳ Подожди, скоро кто-то найдётся!\n"
                f"Нажми '⏹ Остановить поиск' чтобы выйти",
                chat_id,
                message_id,
                parse_mode='Markdown',
                reply_markup=main_menu_keyboard()
            )
            
            # Запускаем таймер для автоматической остановки через 5 минут
            import threading
            def auto_stop(user_id):
                time.sleep(300)  # 5 минут
                if user_id in players and players[user_id]["looking"]:
                    players[user_id]["looking"] = False
                    players[user_id]["time"] = 0
                    bot.send_message(
                        user_id,
                        "⏰ **Поиск остановлен**\nВремя истекло. Попробуй снова!",
                        reply_markup=main_menu_keyboard()
                    )
            threading.Thread(target=auto_stop, args=(user_id,), daemon=True).start()

# === ОБНОВЛЕНИЕ ПРОФИЛЕЙ (ФОН) ===
import threading
def update_profiles():
    while True:
        time.sleep(60)
        for uid in list(players.keys()):
            if players[uid]["looking"]:
                players[uid]["time"] += 60
threading.Thread(target=update_profiles, daemon=True).start()

# === ЗАПУСК ===
print("🚀 TEAMFINDER БОТ ЗАПУЩЕН!")
print("🔥 Игры: Minecraft, Brawl Stars, Roblox, Blockman Go")
print("📢 Канал: @TeamSearchChannel")
bot.infinity_polling()
