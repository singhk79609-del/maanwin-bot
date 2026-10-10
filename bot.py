import time
import threading
import json
import os
import requests
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from PIL import Image, ImageDraw, ImageFont

# ---------------- CONFIGURATION ----------------
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"  # Yahan apna Bot Token daalein

# Aapke exact sticker file IDs
WIN_STICKER_ID = "CAACAgUAAxkBAAESBUxqyjYIPEDt5ahD21hMcG4aX3gSQQACNxIAAnYF2FSRemp6wVeLrD0E"
LOSS_STICKER_ID = "CAACAgUAAxkBAAESBVBqyjZPkGxu_944MSW82L6CRAABIFMAAh8SAAJBAZhW1wckyA5w-N09BA"
JACKPOT_STICKER_ID = "CAACAgUAAxkBAAESBU5qyjYSFQVYUL7i519ZKT8K0ki_jQACbhcAAh2MgFdeqKpTfjvIGD0E"

bot = telebot.TeleBot(TOKEN)

is_running = False
last_checked_issue = None
active_prediction = None
total_wins = 1198
current_streak = 1

# User states aur saved channels ke liye file management
CHANNELS_FILE = "channels.json"
user_states = {}

def load_channels():
    if os.path.exists(CHANNELS_FILE):
        try:
            with open(CHANNELS_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return []

def save_channels(channels):
    with open(CHANNELS_FILE, "w") as f:
        json.dump(channels, f)

saved_channels = load_channels()

# ---------------- MINI KEYBOARD (Multi-Channel Style)[span_1](start_span)[span_1](end_span) ----------------
def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = KeyboardButton("▶ Start Prediction")
    btn2 = KeyboardButton("⏹ Stop Prediction")
    btn3 = KeyboardButton("➕ Add Channel")
    btn4 = KeyboardButton("📋 My Channels")
    keyboard.add(btn1, btn2, btn3, btn4)
    return keyboard

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        "🤖 **MAAN WIN PREDICTION BOT CONNECTED**\nUse the buttons below to manage channels and control predictions.",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda message: message.text == "▶ Start Prediction")
def start_prediction_command(message):
    global is_running
    if not saved_channels:
        bot.send_message(message.chat.id, "⚠️ Pehle **➕ Add Channel** par click karke apna channel add karein!", reply_markup=get_main_keyboard())
        return
    if not is_running:
        is_running = True
        bot.send_message(message.chat.id, "✅ **Prediction Started Successfully for all connected channels!**", reply_markup=get_main_keyboard(), parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "⚠️ Prediction is already running!", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda message: message.text == "⏹ Stop Prediction")
def stop_prediction_command(message):
    global is_running
    is_running = False
    bot.send_message(message.chat.id, "🛑 **Stopped receiving predictions.**\nTap Start Prediction anytime to resume.", reply_markup=get_main_keyboard(), parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "➕ Add Channel")
def add_channel_prompt(message):
    user_states[message.chat.id] = "waiting_for_channel"
    bot.send_message(message.chat.id, "📢 Apne Telegram Channel ka username bhejiye (Jaise: `@mychannel`):\n\n*(Note: Bot ko apne channel par Admin zaroor banayein)*", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda message: message.text == "📋 My Channels")
def list_channels(message):
    if not saved_channels:
        bot.send_message(message.chat.id, "📂 Koi bhi channel abhi add nahi kiya gaya hai.", reply_markup=get_main_keyboard())
    else:
        ch_list = "\n".join([f"• {ch}" for ch in saved_channels])
        bot.send_message(message.chat.id, f"📋 **Connected Channels:**\n{ch_list}", reply_markup=get_main_keyboard(), parse_mode="Markdown")

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "waiting_for_channel")
def save_new_channel(message):
    global saved_channels
    channel_username = message.text.strip()
    
    if not channel_username.startswith("@"):
        bot.send_message(message.chat.id, "❌ Galat format! Kripya `@channelname` ke roop mein bhejiye.", reply_markup=get_main_keyboard())
        return
        
    if channel_username not in saved_channels:
        saved_channels.append(channel_username)
        save_channels(saved_channels)
        bot.send_message(message.chat.id, f"✅ Channel **{channel_username}** successfully add ho gaya hai!", reply_markup=get_main_keyboard(), parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "⚠️ Yeh channel pehle se added hai!", reply_markup=get_main_keyboard())
        
    user_states[message.chat.id] = None


# ---------------- DYNAMIC IMAGE GENERATOR ----------------
def generate_prediction_image(period, trend, number_str, wins, streak):
    img_width, img_height = 800, 900
    image = Image.new("RGB", (img_width, img_height), color=(10, 5, 15))
    draw = ImageDraw.Draw(image)
    
    try:
        font_large = ImageFont.truetype("arial.ttf", 45)
        font_med = ImageFont.truetype("arial.ttf", 30)
    except:
        font_large = font_med = ImageFont.load_default()

    draw.rectangle([40, 40, 760, 140], fill=(30, 10, 25), outline=(255, 100, 150), width=3)
    draw.text((70, 60), "WinGo 1 Min AI PREDICTION BOT", fill=(255, 255, 255), font=font_large)
    
    draw.rectangle([40, 160, 380, 240], fill=(20, 40, 25), outline=(0, 255, 100), width=2)
    draw.text((60, 185), f"🏆 WIN  {wins}", fill=(0, 255, 100), font=font_med)
    
    draw.rectangle([420, 160, 760, 240], fill=(40, 30, 10), outline=(255, 165, 0), width=2)
    draw.text((440, 185), f"🔥 STREAK  {streak}", fill=(255, 165, 0), font=font_med)

    draw.rectangle([40, 280, 760, 500], fill=(50, 15, 25), outline=(255, 50, 100), width=4)
    draw.text((220, 330), f"{trend}", fill=(255, 50, 100), font=font_large)
    draw.text((240, 410), f"PERIOD: {period}", fill=(255, 255, 255), font=font_med)

    draw.rectangle([40, 540, 760, 680], fill=(20, 20, 35), outline=(100, 150, 255), width=3)
    draw.text((70, 580), f"TARGET NUMBER: {number_str}", fill=(255, 255, 255), font=font_med)

    file_path = "dynamic_prediction.png"
    image.save(file_path)
    return file_path


# ---------------- LIVE API & BROADCAST ENGINE ----------------
def fetch_wingo_data():
    try:
        url = f"https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json?t={int(time.time()*1000)}"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if data and 'data' in data and 'list' in data['data']:
                return data['data']['list']
    except Exception:
        pass
    return None

def background_prediction_loop():
    global last_checked_issue, active_prediction, is_running, total_wins, current_streak
    
    while True:
        time.sleep(3)
        if not is_running or not saved_channels:
            continue
            
        history = fetch_wingo_data()
        if not history or len(history) == 0:
            continue
            
        latest_draw = history[0]
        current_period = str(latest_draw['issueNumber'])
        winning_number = int(latest_draw['number'])
        winning_size = "BIG" if winning_number >= 5 else "SMALL"
        
        if active_prediction and active_prediction['period'] == current_period:
            pred_type = active_prediction['prediction']
            pred_num = active_prediction['number']
            
            is_win = False
            is_jackpot = False
            
            if pred_type == winning_size:
                is_win = True
            elif str(winning_number) in str(pred_num):
                is_jackpot = True
            
            short_period = current_period[-4:]
            
            for channel in saved_channels:
                try:
                    if is_jackpot:
                        bot.send_sticker(channel, JACKPOT_STICKER_ID)
                        res_msg = f"✅ JACKPOT !\n================================\nPeriod  =>  #{short_period}\nResult  =>  NUM:{winning_number}  🔵  {winning_size}\n================================"
                        bot.send_message(channel, res_msg)
                    elif is_win:
                        bot.send_sticker(channel, WIN_STICKER_ID)
                        res_msg = f"✅ WIN!\n================================\nPeriod  =>  #{short_period}\nResult  =>  NUM:{winning_number}  🔵  {winning_size}\n================================"
                        bot.send_message(channel, res_msg)
                    else:
                        bot.send_sticker(channel, LOSS_STICKER_ID)
                        res_msg = f"❌ LOSS\n================================\nPeriod  =>  #{short_period}\nResult  =>  NUM:{winning_number}  🔵  {winning_size}\n================================"
                        bot.send_message(channel, res_msg)
                except:
                    pass
                    
            if is_jackpot or is_win:
                total_wins += 1
                current_streak += 1
            else:
                current_streak = 0
                
            active_prediction = None

        if last_checked_issue != current_period:
            last_checked_issue = current_period
            next_period_num = str(int(current_period) + 1)
            short_next_period = next_period_num[-4:]
            
            nums = [int(x['number']) for x in history[:10]]
            big_count = sum(1 for n in nums if n >= 5)
            trend = "GREEN" if big_count >= 5 else "RED"
            size_trend = "SMALL" if big_count >= 5 else "BIG"
            pred_number_str = "4 / 0" if size_trend == "SMALL" else "6 / 7"
            
            prediction_text = (
                f"═══════════════════════════\n"
                f"     🎯 POWERED BY MAAN WIN\n"
                f"═══════════════════════════\n"
                f"           🎰 𝗪𝗜𝗡𝗚𝗢 𝟭 𝗠𝗜𝗡𝗨𝗧𝗘🎰\n\n"
                f"🗿 𝗣𝗘𝗥𝗜𝗢𝗗: {short_next_period}\n"
                f"🎲 𝗣𝗥𝗘𝗗𝗜𝗖𝗧𝗜𝗢𝗡: {trend}\n"
                f"🎯 𝗡𝗨𝗠𝗕𝗘𝗥: {pred_number_str}\n\n"
                f"⚠  𝟳 𝗟𝗘𝗩𝗘𝗟 𝗠𝗘𝗡𝗧𝗘𝗡 𝗔𝗟𝗟 𝗧𝗜𝗠𝗘  ⚠️ \n\n"
                f"═══════════════════════════\n"
                f" ☠️ 𝗣𝗢𝗪𝗘𝗥 𝗢𝗙 : @maanwin123_bot\n"
                f"═══════════════════════════"
            )
            
            active_prediction = {
                'period': next_period_num,
                'prediction': size_trend,
                'number': pred_number_str
            }
            
            img_path = generate_prediction_image(short_next_period, trend, pred_number_str, total_wins, current_streak)
            
            for channel in saved_channels:
                try:
                    with open(img_path, 'rb') as photo:
                        bot.send_photo(channel, photo, caption=prediction_text)
                except Exception:
                    try:
                        bot.send_message(channel, prediction_text)
                    except:
                        pass

threading.Thread(target=background_prediction_loop, daemon=True).start()

if __name__ == "__main__":
    print("Multi-channel bot is running successfully...")
    bot.infinity_polling()
