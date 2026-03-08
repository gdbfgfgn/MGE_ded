import telebot
import random
import os
import requests
import json
from io import BytesIO
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import time


TOKEN = '7574969352:AAFsKrm9dO0nfIszpCzUIBkKmJW7d5-uZIg'


bot = telebot.TeleBot(TOKEN)


BOT_NAME = "MGE_Dedus"


RARITY_FOLDERS = {
    'obichnie': 'mge_dedus_images/obichnie',
    'redkie': 'mge_dedus_images/redkie',
    'pashalki': 'mge_dedus_images/pashalki',
    'kolabnie': 'mge_dedus_images/kolabnie',
    'spoylemie': 'mge_dedus_images/spoylemie'
}


RARITY_CHANCES = {
    'obichnie': 47,
    'redkie': 20,
    'pashalki': 25,
    'kolabnie': 5,
    'spoylemie': 3
}


for folder in RARITY_FOLDERS.values():
    if not os.path.exists(folder):
        os.makedirs(folder)


INVENTORY_FILE = 'user_inventory.json'


def load_inventory():
    if os.path.exists(INVENTORY_FILE):
        try:
            with open(INVENTORY_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    data = json.loads(content)

                    if data and isinstance(data, dict):

                        first_user = next(iter(data.values()))
                        if isinstance(first_user, dict):
                            first_card = next(iter(first_user.values()))

                            if isinstance(first_card, int):
                                print("⚠️ Обнаружен старый формат инвентаря. Создаем новый...")
                                return {}
                return data
        except (json.JSONDecodeError, StopIteration) as e:
            print(f"⚠️ Ошибка загрузки инвентаря: {e}. Создаем новый файл...")

            if os.path.exists(INVENTORY_FILE):
                os.rename(INVENTORY_FILE, INVENTORY_FILE + '.backup')
            return {}
    return {}


def save_inventory(inventory):
    with open(INVENTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(inventory, f, ensure_ascii=False, indent=2)


user_inventory = load_inventory()


last_images = {}


RARITY_EMOJI = {
    'obichnie': '🟢',
    'redkie': '🔵',
    'pashalki': '🟣',
    'kolabnie': '🟡',
    'spoylemie': '🔴'
}


RARITY_NAMES = {
    'obichnie': 'Обычная',
    'redkie': 'Редкая',
    'pashalki': 'Пасхалка',
    'kolabnie': 'Колабная',
    'spoylemie': 'Спойлерная'
}

def get_random_image_with_rarity():
    """Получает случайное изображение с учетом редкости"""
    

    chosen_rarity = random.choices(
        list(RARITY_CHANCES.keys()),
        weights=list(RARITY_CHANCES.values())
    )[0]
    

    folder_path = RARITY_FOLDERS[chosen_rarity]
    

    local_images = []
    if os.path.exists(folder_path):
        local_images = [f for f in os.listdir(folder_path) 
                       if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    

    if not local_images:
        return None, 'empty', chosen_rarity, None
    

    filename = random.choice(local_images)
    image_path = os.path.join(folder_path, filename)
    return image_path, 'local', chosen_rarity, filename

def add_to_inventory(user_id, rarity, filename):
    """Добавляет карточку в инвентарь пользователя"""
    global user_inventory
    user_id_str = str(user_id)
    if user_id_str not in user_inventory:
        user_inventory[user_id_str] = {}
    
    for card_id, card_data in user_inventory[user_id_str].items():
        if card_data["filename"] == filename and card_data["rarity"] == rarity:
            return None
    
    card_id = f"{rarity}_{filename}_{int(time.time())}_{random.randint(1000, 9999)}"
    

    user_inventory[user_id_str][card_id] = {
        "rarity": rarity,
        "filename": filename,
        "name": os.path.splitext(filename)[0],  
        "received_time": time.time()
    }
    
    save_inventory(user_inventory)
    return card_id

def get_inventory_text(user_id):
    """Возвращает текст инвентаря пользователя"""
    user_id_str = str(user_id)
    if user_id_str not in user_inventory:
        return "У тебя пока нет карточек. Напиши 'дедус' чтобы получить первую!"
    
    inventory = user_inventory[user_id_str]
    if not inventory:
        return "У тебя пока нет карточек. Напиши 'дедус' чтобы получить первую!"
    

    rarity_groups = {}
    for card_id, card_data in inventory.items():
        rarity = card_data["rarity"]
        if rarity not in rarity_groups:
            rarity_groups[rarity] = []
        rarity_groups[rarity].append(card_data)
    
    text = f"📦 ИНВЕНТАРЬ {BOT_NAME}\n"
    text += "═══════════════════\n\n"
    
    total = len(inventory)
    
    for rarity in ['spoylemie', 'kolabnie', 'pashalki', 'redkie', 'obichnie']:
        if rarity in rarity_groups:
            emoji = RARITY_EMOJI.get(rarity, '🎴')
            name = RARITY_NAMES.get(rarity, rarity)
            count = len(rarity_groups[rarity])
            text += f"{emoji} {name}: {count}\n"
            

            for i, card in enumerate(rarity_groups[rarity][:5]):
                card_name = card["name"][:15] + "..." if len(card["name"]) > 15 else card["name"]
                text += f"  • {card_name}\n"
            
            if count > 5:
                text += f"  ... и еще {count - 5}\n"
            text += "\n"
    
    text += f"═══════════════════\n"
    text += f"🎴 Всего карточек: {total}\n"
    text += f"\n👉 Напиши '{BOT_NAME} карточка [название]' чтобы посмотреть"
    
    return text

def get_card_by_name(user_id, card_name):
    """Ищет карточку по названию"""
    user_id_str = str(user_id)
    if user_id_str not in user_inventory:
        return None
    
    for card_id, card_data in user_inventory[user_id_str].items():
        if card_name.lower() in card_data["name"].lower():
            return card_data
    
    return None

@bot.message_handler(func=lambda message: True)
def handle_message(message):

    if message.chat.type not in ['group', 'supergroup']:
        return
    

    text = message.text or ''
    

    bot_mentions = [BOT_NAME, BOT_NAME.lower(), 'дедус', 'MGE', 'mge']
    

    for mention in bot_mentions:
        if mention in text and 'карточка' in text.lower():
            parts = text.lower().split('карточка')
            if len(parts) > 1 and parts[1].strip():
                card_search = parts[1].strip()
                card_data = get_card_by_name(message.from_user.id, card_search)
                
                if card_data:
                    folder_path = RARITY_FOLDERS[card_data["rarity"]]
                    image_path = os.path.join(folder_path, card_data["filename"])
                    
                    try:
                        with open(image_path, 'rb') as img:
                            bot.send_photo(
                                message.chat.id,
                                img,
                                caption=f"🎴 Карточка '{card_data['name']}'\n{RARITY_EMOJI.get(card_data['rarity'], '🎴')} Редкость: {RARITY_NAMES.get(card_data['rarity'], card_data['rarity'])}"
                            )
                    except:
                        bot.reply_to(message, "😕 Не могу найти файл карточки")
                else:
                    bot.reply_to(message, f"😕 Нет карточки с названием '{card_search}'")
                return
            break
    

    is_inventory_request = False
    for mention in bot_mentions:
        if mention in text and ('инвентарь' in text.lower() or 'коллекция' in text.lower()):
            is_inventory_request = True
            break
    
    if is_inventory_request:
        inventory_text = get_inventory_text(message.from_user.id)
        bot.reply_to(message, inventory_text)
        return
    

    should_respond = False
    for mention in bot_mentions:
        if mention in text and 'инвентарь' not in text.lower() and 'карточка' not in text.lower():
            should_respond = True
            break
    
    if should_respond:
 
        bot.send_chat_action(message.chat.id, 'upload_photo')
        

        image_data, source, rarity, filename = get_random_image_with_rarity()
        
        if image_data and filename:
            try:

                card_id = add_to_inventory(message.from_user.id, rarity, filename)
                
                if card_id is None:
                    bot.reply_to(message, "😕 Эта карточка у тебя уже есть! Дедус попробует найти другую...")
                    return
                

                keyboard = InlineKeyboardMarkup()
                keyboard.row(
                    InlineKeyboardButton("🔄 Ещё", callback_data="more"),
                    InlineKeyboardButton("👍 Нравится", callback_data="like"),
                    InlineKeyboardButton("👴 Дедус одобряет", callback_data="dedus_approve")
                )
                

                emoji = RARITY_EMOJI.get(rarity, '🎴')
                rarity_name = RARITY_NAMES.get(rarity, rarity)
                card_name = os.path.splitext(filename)[0][:20]
                

                captions = [
                    f"👴 {BOT_NAME} нашел для тебя карточку!\n{emoji} {rarity_name}\n📇 {card_name}",
                    f"🎨 Держи, внучок, карточку от {BOT_NAME}!\n{emoji} {rarity_name}\n📇 {card_name}",
                    f"📸 {BOT_NAME} поделился карточкой:\n{emoji} {rarity_name}\n📇 {card_name}",
                    f"🌟 По просьбе @{message.from_user.username or 'пользователя'}\n{emoji} {rarity_name}\n📇 {card_name}",
                    f"👴 Дедус говорит: 'Смотри, что нашел!'\n{emoji} {rarity_name}\n📇 {card_name}"
                ]
                

                if source == 'local':
                    with open(image_data, 'rb') as img:
                        sent_msg = bot.send_photo(
                            message.chat.id,
                            img,
                            caption=random.choice(captions),
                            reply_to_message_id=message.message_id,
                            reply_markup=keyboard
                        )
                

                chat_id = message.chat.id
                if chat_id not in last_images:
                    last_images[chat_id] = []
                
                last_images[chat_id].append({
                    'message_id': sent_msg.message_id,
                    'time': time.time(),
                    'rarity': rarity
                })
                

                if len(last_images[chat_id]) > 5:
                    last_images[chat_id].pop(0)
                    
            except Exception as e:
                bot.reply_to(message, f"😕 Ошибка у дедуса: {str(e)}")
        else:
            bot.reply_to(message, "карточка появилась у тебя в очке(честно)")

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == "more":

        try:
            bot.edit_message_reply_markup(
                call.message.chat.id,
                call.message.message_id,
                reply_markup=None
            )
        except:
            pass
        

        image_data, source, rarity, filename = get_random_image_with_rarity()
        
        if image_data and filename:

            card_id = add_to_inventory(call.from_user.id, rarity, filename)
            
            if card_id is None:
                bot.send_message(call.message.chat.id, "😕 Эта карточка у тебя уже есть! Дедус попробует найти другую...")
                return
            
            if source == 'local':
                with open(image_data, 'rb') as img:
                    bot.send_photo(
                        call.message.chat.id,
                        img,
                        caption="🔄 Ещё одна карточка от MGE_Dedus!"
                    )
        else:
            bot.send_message(call.message.chat.id, "карточка появилась у тебя в очке(честно)")
    
    elif call.data == "like":
        bot.answer_callback_query(call.id, "❤️ Дедус рад, что тебе нравится!", show_alert=False)
    
    elif call.data == "dedus_approve":
        bot.answer_callback_query(call.id, "👴 Дедус одобряет эту карточку!", show_alert=False)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = f"""
 **Привет! Я {BOT_NAME}!**

Я даю вам карточки.

**Как использовать:**
• Напишите `{BOT_NAME}` или просто "дедус" в чате - я пришлю карточку
• Напишите `{BOT_NAME} инвентарь` - покажу твои карточки
• Напишите `{BOT_NAME} карточка [название]` - покажу конкретную карточку

**Команды:**
/help - показать эту справку
/status - показать статистику
/inventory - показать инвентарь

 Дедус всегда рад помочь!
    """
    
    if message.chat.type in ['group', 'supergroup']:
        bot.reply_to(message, welcome_text)
    else:
        bot.send_message(message.chat.id, welcome_text)

@bot.message_handler(commands=['status'])
def send_status(message):
    if message.chat.type in ['group', 'supergroup']:

        stats_text = "📊 СТАТИСТИКА\n══════════\n\n"
        total_count = 0
        
        for rarity, folder in RARITY_FOLDERS.items():
            if os.path.exists(folder):
                count = len([f for f in os.listdir(folder) 
                           if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))])
                total_count += count
                emoji = RARITY_EMOJI.get(rarity, '📁')
                name = RARITY_NAMES.get(rarity, rarity)
                stats_text += f"{emoji} {name}: {count} ({RARITY_CHANCES[rarity]}%)\n"
        

        group_images = len(last_images.get(message.chat.id, []))
        
  
        total_users = len(user_inventory)
        total_cards_collected = sum(len(cards) for cards in user_inventory.values())
        
        stats_text += f"\n══════════\n"
        stats_text += f"📦 Всего карточек в базе: {total_count}\n"
        stats_text += f"💬 В этой группе отправлено: {group_images}\n"
        stats_text += f"👥 Всего коллекционеров: {total_users}\n"
        stats_text += f"🎴 Всего собрано карточек: {total_cards_collected}\n"
        stats_text += f"\n⚡ Дедус работает!"
        
        bot.reply_to(message, stats_text)

@bot.message_handler(commands=['inventory'])
def show_inventory(message):
    """Показывает инвентарь пользователя"""
    inventory_text = get_inventory_text(message.from_user.id)
    bot.reply_to(message, inventory_text)

@bot.message_handler(commands=['add_image'])
def add_image(message):
    """Команда для добавления изображений (только для админов)"""
    

    if message.chat.type not in ['group', 'supergroup']:
        bot.reply_to(message, "Эта команда работает только в группах!")
        return
    

    if not message.reply_to_message or not message.reply_to_message.photo:
        bot.reply_to(message, 
                    f"{BOT_NAME} говорит: отправь фото с подписью /add_image в ответ на него")
        return
    
    try:

        file_id = message.reply_to_message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        

        filename = f"dedus_{int(time.time())}.png"
        filepath = os.path.join(RARITY_FOLDERS['obichnie'], filename)
        
        with open(filepath, 'wb') as new_file:
            new_file.write(downloaded_file)
        
        bot.reply_to(message, f"✅ Спасибо! Дедус сохранил карточку в обычные как {filename}")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка при сохранении: {str(e)}")


@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_member(message):
    for member in message.new_chat_members:
        if member.id == bot.get_me().id:

            bot.send_message(
                message.chat.id,
                f"Всем привет! Я {BOT_NAME}\n"
                f"Напишите '{BOT_NAME}' в чате, и я пришлю карточку!"
            )
        else:

            welcome_msgs = [
                f"{BOT_NAME} приветствует нового внучка {member.first_name}!",
                f"🌟 О, {member.first_name} пришел! Дедус рад!",
                f"🎉 {BOT_NAME}: 'Добро пожаловать, {member.first_name}!'"
            ]
            bot.send_message(message.chat.id, random.choice(welcome_msgs))


if __name__ == '__main__':
    print(f"🚀 Бот {BOT_NAME} запущен и готов к работе!")
    print("📁 Структура папок с редкостями:")
    for rarity, folder in RARITY_FOLDERS.items():
        print(f"   {RARITY_EMOJI.get(rarity, '📁')} {rarity}: {RARITY_CHANCES[rarity]}% -> {folder}")
    print(f"📦 Загружено инвентарей: {len(user_inventory)}")
    print("👴 Дедус проснулся и ждет сообщений...")
    print(f"✅ Токен установлен: {TOKEN[:10]}...")
    

    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            print("🔄 Перезапуск через 5 секунд...")
            time.sleep(5)
