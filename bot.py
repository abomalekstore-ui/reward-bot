import telebot, json, os, time, threading, requests
from flask import Flask

# ========= إعدادات =========
TOKEN = "8376936171:AAFxfdp4S4RtyCI9f-ZDUi7vMQTXEuPQUs4"   BotFather
REWARD_POINTS = 10             # عدد النقاط المطلوبة للمكافأة
KEEPALIVE_URL = os.environ.get("KEEPALIVE_URL", None)  # رابط الخدمة على Koyeb أو Render
PING_EVERY_SEC = 180           # كل كام ثانية نعمل self-ping

bot = telebot.TeleBot(TOKEN)

# ========= بيانات المستخدمين =========
if os.path.exists("users.json"):
    with open("users.json", "r", encoding="utf-8") as f:
        users = json.load(f)
else:
    users = {}

def save_data():
    with open("users.json", "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

# ========= منطق البوت =========
@bot.message_handler(commands=['start'])
def start(message):
    args = message.text.split()
    uid = str(message.chat.id)

    if uid not in users:
        users[uid] = {"points": 0, "referrals": [], "name": message.from_user.first_name, "rewarded": False}

        # لو دخل من رابط إحالة فيه كلمة "مكافأة"
        if len(args) > 1 and args[1].startswith("مكافأة"):
            ref_id = args[1].replace("مكافأة", "")
            if ref_id in users and uid != ref_id:
                users[ref_id]["points"] += 1
                users[ref_id]["referrals"].append(uid)
                bot.send_message(ref_id, f"🎉 شخص جديد دخل من رابطك!\n🔹 مجموعك الآن: {users[ref_id]['points']} نقطة")

                # مكافأة تلقائية لو وصل الحد
                if users[ref_id]["points"] >= REWARD_POINTS and not users[ref_id]["rewarded"]:
                    bot.send_message(ref_id, f"🎁 مبروك! وصلت {REWARD_POINTS} نقاط!\nانضم لقناتنا 👉 https://t.me/AkhbarLast")
                    users[ref_id]["rewarded"] = True

    save_data()

    invite_link = f"https://t.me/{bot.get_me().username}?start=مكافأة{uid}"
    bot.send_message(
        message.chat.id,
        f"👋 أهلاً بك في <b>بوت المكافآت</b> 🎁\n\n"
        f"🎯 نقاطك: <b>{users[uid]['points']}</b>\n\n"
        f"🔗 رابط دعوتك:\n<code>{invite_link}</code>\n\n"
        f"📢 كل شخص يدخل من رابطك = نقطة 🏅\n"
        f"🏆 استخدم /الترتيب لعرض أفضل 10",
        parse_mode="HTML"
    )

@bot.message_handler(commands=['نقاطي'])
def my_points(message):
    uid = str(message.chat.id)
    if uid in users:
        bot.send_message(uid, f"🎯 نقاطك الحالية: {users[uid]['points']}")
    else:
        bot.send_message(uid, "⚠️ اكتب /start أولاً.")

@bot.message_handler(commands=['مكافأة'])
def reward(message):
    uid = str(message.chat.id)
    if uid not in users:
        bot.send_message(uid, "⚠️ اكتب /start أولاً.")
        return
    if users[uid]["points"] >= REWARD_POINTS:
        bot.send_message(uid, "🎁 مبروك! وصلت للمكافأة!\nانضم لقناتنا 👉 https://t.me/AkhbarLast")
        users[uid]["rewarded"] = True
        save_data()
    else:
        remaining = REWARD_POINTS - users[uid]["points"]
        bot.send_message(uid, f"😅 لسه ناقص {remaining} نقطة.")

@bot.message_handler(commands=['الترتيب'])
def ranking(message):
    if not users:
        bot.send_message(message.chat.id, "لا يوجد مستخدمون بعد 😅")
        return
    top = sorted(users.items(), key=lambda x: x[1]["points"], reverse=True)[:10]
    text = "🏆 <b>أعلى 10 مستخدمين:</b>\n\n"
    for i, (_, data) in enumerate(top, start=1):
        text += f"{i}. {data.get('name','مستخدم')} — {data['points']} نقطة\n"
    bot.send_message(message.chat.id, text, parse_mode="HTML")

# ========= Flask + Keepalive =========
app = Flask(__name__)

@app.route("/")
def index():
    return "OK - Bot is alive"

def keepalive_loop():
    if not KEEPALIVE_URL:
        return
    while True:
        try:
            requests.get(KEEPALIVE_URL, timeout=10)
            print("✅ Self-ping sent")
        except Exception as e:
            print(f"⚠️ keepalive error: {e}")
        time.sleep(PING_EVERY_SEC)

def polling_loop():
    while True:
        try:
            print("🤖 polling…")
            bot.polling(non_stop=True, timeout=60)
        except Exception as e:
            print(f"⚠️ polling error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=polling_loop, daemon=True).start()
    threading.Thread(target=keepalive_loop, daemon=True).start()
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 running on port {port}")
    app.run(host="0.0.0.0", port=port)
# ================== Flask Server to Keep Alive ==================
app = Flask(__name__)

@app.route('/')
def index():
    return "<h2>✅ Reward Bot is running successfully!</h2>"

def keepalive_loop():
    url = os.environ.get("KEEPALIVE_URL")
    if not url:
        return
    while True:
        try:
            requests.get(url)
            print("🔁 Ping sent to keep server awake.")
        except Exception as e:
            print(f"⚠️ Error pinging server: {e}")
        time.sleep(240)  # كل 4 دقائق

# ================== تشغيل البوت والسيرفر ==================
def polling_loop():
    while True:
        try:
            bot.polling(non_stop=True)
        except Exception as e:
            print(f"⚠️ خطأ في التشغيل: {e}")
            time.sleep(5)

if __name__ == '__main__':
    threading.Thread(target=polling_loop).start()
    threading.Thread(target=keepalive_loop).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
