import logging
import json
import os
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler,
    JobQueue
)

# ==============================
# TOKENNI SHU YERGA YOZING ⬇️
# ==============================
BOT_TOKEN = "8814110130:AAGYxmBuJE6pgaFNvTH36ZJjISsiKXPADL4"
# ==============================

DATA_FILE = "users_data.json"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

(ASK_NAME, MAIN_MENU,
 ADD_TASK_NAME, ADD_TASK_AMOUNT, ADD_TASK_DATE,
 ADD_RENT_NAME, ADD_RENT_AMOUNT, ADD_RENT_DAY,
 CHECK_SAVINGS) = range(9)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user(user_id):
    return load_data().get(str(user_id), None)

def save_user(user_id, user_info):
    data = load_data()
    data[str(user_id)] = user_info
    save_data(data)

def next_id(user):
    all_ids = [t.get("id",0) for t in user.get("tasks",[])] + \
              [r.get("id",0) for r in user.get("rents",[])]
    return max(all_ids, default=0) + 1

def main_keyboard():
    keyboard = [
        [KeyboardButton("💰 Yangi vazifa"), KeyboardButton("🏠 Ijara qo'shish")],
        [KeyboardButton("📋 Vazifalarim"), KeyboardButton("🏠 Ijaralarim")],
        [KeyboardButton("✅ To'lov qildim"), KeyboardButton("💵 Pulni yangilash")],
        [KeyboardButton("🗑 O'chirish"), KeyboardButton("ℹ️ Yordam")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    if user and user.get("name"):
        await update.message.reply_text(
            f"💚 *Assalomu aleykum, {user['name']}!*\n\n💰 Moliyaviy yordamchingiz tayyor!",
            parse_mode="Markdown", reply_markup=main_keyboard()
        )
        return MAIN_MENU
    else:
        await update.message.reply_text(
            "💚 *Assalomu aleykum!*\n\nMen sizning moliyaviy yordamchingizman! 💰\n\nIsmingizni yozing:",
            parse_mode="Markdown"
        )
        return ASK_NAME

async def save_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    name = update.message.text.strip()
    save_user(user_id, {"name": name, "tasks": [], "rents": []})
    await update.message.reply_text(
        f"✅ *Xush kelibsiz, {name}!* 😊\n\n"
        f"💰 Bir martalik vazifalar\n"
        f"🏠 Oylik ijara to'lovlari\n"
        f"⏰ Avtomatik eslatmalar",
        parse_mode="Markdown", reply_markup=main_keyboard()
    )
    return MAIN_MENU

# ===== BIR MARTALIK VAZIFA =====
async def add_task_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💰 *Vazifa nomi:*\n_(Masalan: Kassaga pul berish)_", parse_mode="Markdown")
    return ADD_TASK_NAME

async def add_task_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_task_name"] = update.message.text.strip()
    await update.message.reply_text("💵 *Qancha pul kerak?*\n_(Masalan: 8000)_", parse_mode="Markdown")
    return ADD_TASK_AMOUNT

async def add_task_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().replace("$","").replace(",","").replace(" ","")
    try:
        context.user_data["new_task_amount"] = float(text)
        await update.message.reply_text("📅 *Qaysi sanaga?*\n_(Masalan: 25.12.2024)_", parse_mode="Markdown")
        return ADD_TASK_DATE
    except:
        await update.message.reply_text("❌ Faqat raqam yozing. Masalan: 8000")
        return ADD_TASK_AMOUNT

async def add_task_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    date_text = update.message.text.strip()
    due_date = None
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            due_date = datetime.strptime(date_text, fmt)
            break
        except:
            pass
    if not due_date:
        await update.message.reply_text("❌ Sana noto'g'ri. Masalan: *25.12.2024*", parse_mode="Markdown")
        return ADD_TASK_DATE

    user = get_user(user_id)
    task = {
        "id": next_id(user),
        "name": context.user_data["new_task_name"],
        "amount": context.user_data["new_task_amount"],
        "due_date": due_date.strftime("%Y-%m-%d"),
        "saved": 0, "completed": False, "type": "once"
    }
    user["tasks"].append(task)
    save_user(user_id, user)
    days_left = (due_date - datetime.now()).days
    await update.message.reply_text(
        f"✅ *Saqlandi!*\n\n📌 *{task['name']}*\n"
        f"💰 *{task['amount']:,.0f}$* | 📅 {due_date.strftime('%d.%m.%Y')}\n"
        f"⏳ {days_left} kun qoldi\n\n🔔 4 kun qolganda eslataman!",
        parse_mode="Markdown", reply_markup=main_keyboard()
    )
    return MAIN_MENU

# ===== OYLIK IJARA =====
async def add_rent_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏠 *Ijara nomi:*\n_(Masalan: Sklad ijarasi)_", parse_mode="Markdown")
    return ADD_RENT_NAME

async def add_rent_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["rent_name"] = update.message.text.strip()
    await update.message.reply_text("💵 *Har oylik to'lov miqdori?*\n_(Masalan: 500)_", parse_mode="Markdown")
    return ADD_RENT_AMOUNT

async def add_rent_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().replace("$","").replace(",","").replace(" ","")
    try:
        context.user_data["rent_amount"] = float(text)
        await update.message.reply_text("📅 *Har oyning nechanchi sanasida to'lanadi?*\n_(Masalan: 10)_", parse_mode="Markdown")
        return ADD_RENT_DAY
    except:
        await update.message.reply_text("❌ Faqat raqam yozing. Masalan: 500")
        return ADD_RENT_AMOUNT

async def add_rent_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        day = int(update.message.text.strip())
        if day < 1 or day > 28:
            raise ValueError
    except:
        await update.message.reply_text("❌ 1 dan 28 gacha raqam yozing.")
        return ADD_RENT_DAY

    now = datetime.now()
    if now.day <= day:
        next_due = now.replace(day=day)
    else:
        if now.month == 12:
            next_due = now.replace(year=now.year+1, month=1, day=day)
        else:
            next_due = now.replace(month=now.month+1, day=day)

    user = get_user(user_id)
    rent = {
        "id": next_id(user),
        "name": context.user_data["rent_name"],
        "amount": context.user_data["rent_amount"],
        "day_of_month": day,
        "next_due": next_due.strftime("%Y-%m-%d"),
        "active": True, "type": "monthly"
    }
    user["rents"].append(rent)
    save_user(user_id, user)
    days_left = (next_due - now).days
    await update.message.reply_text(
        f"✅ *Ijara saqlandi!*\n\n🏠 *{rent['name']}*\n"
        f"💰 *{rent['amount']:,.0f}$* / oy\n"
        f"📅 Har oyning *{day}-sanasi*\n"
        f"⏳ Keyingi to'lovga: *{days_left} kun* ({next_due.strftime('%d.%m.%Y')})\n\n"
        f"🔔 7 kun va 3 kun oldin eslataman!",
        parse_mode="Markdown", reply_markup=main_keyboard()
    )
    return MAIN_MENU

# ===== RO'YXATLAR =====
async def show_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    tasks = [t for t in user.get("tasks",[]) if not t.get("completed")]
    if not tasks:
        await update.message.reply_text(f"📋 *{user['name']}, bir martalik vazifalar yo'q!*", parse_mode="Markdown", reply_markup=main_keyboard())
        return MAIN_MENU
    msg = f"📋 *{user['name']}, vazifalar:*\n\n"
    for t in tasks:
        due = datetime.strptime(t["due_date"], "%Y-%m-%d")
        days_left = (due - datetime.now()).days
        rem = t["amount"] - t.get("saved",0)
        st = "🔴 O'tgan!" if days_left < 0 else (f"🟡 {days_left} kun!" if days_left<=3 else f"🟢 {days_left} kun")
        msg += f"💼 *{t['name']}*\n   💰 {t['amount']:,.0f}$ | ✅ {t.get('saved',0):,.0f}$ | ❗ {rem:,.0f}$ qoldi\n   📅 {due.strftime('%d.%m.%Y')} — {st}\n\n"
    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=main_keyboard())
    return MAIN_MENU

async def show_rents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    rents = [r for r in user.get("rents",[]) if r.get("active")]
    if not rents:
        await update.message.reply_text(f"🏠 *{user['name']}, oylik to'lovlar yo'q!*", parse_mode="Markdown", reply_markup=main_keyboard())
        return MAIN_MENU
    msg = f"🏠 *{user['name']}, oylik to'lovlar:*\n\n"
    for r in rents:
        nd = datetime.strptime(r["next_due"], "%Y-%m-%d")
        days_left = (nd - datetime.now()).days
        st = "🔴 Kechikdi!" if days_left<0 else (f"🟡 {days_left} kun!" if days_left<=7 else f"🟢 {days_left} kun")
        msg += f"🏠 *{r['name']}*\n   💰 {r['amount']:,.0f}$ / oy | 📅 Har oyning {r['day_of_month']}-sanasi\n   ⏳ {nd.strftime('%d.%m.%Y')} — {st}\n\n"
    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=main_keyboard())
    return MAIN_MENU

# ===== TO'LOV QILDIM =====
async def task_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    tasks = [t for t in user.get("tasks",[]) if not t.get("completed")]
    rents = [r for r in user.get("rents",[]) if r.get("active")]
    all_items = tasks + rents
    if not all_items:
        await update.message.reply_text(f"✅ *{user['name']}, faol vazifalar yo'q!*", parse_mode="Markdown", reply_markup=main_keyboard())
        return MAIN_MENU
    if len(all_items) == 1:
        await complete_item(update, user, user_id, all_items[0])
        return MAIN_MENU
    msg = f"✅ *Qaysi to'lov bajarildi?*\n\n"
    for i, item in enumerate(all_items, 1):
        icon = "🏠" if item.get("type")=="monthly" else "💼"
        msg += f"{i}. {icon} {item['name']} — {item['amount']:,.0f}$\n"
    msg += "\nRaqamini yozing:"
    context.user_data["action"] = "complete"
    context.user_data["action_items"] = [item["id"] for item in all_items]
    await update.message.reply_text(msg, parse_mode="Markdown")
    return MAIN_MENU

async def complete_item(update, user, user_id, item):
    name = user["name"]
    if item.get("type") == "monthly":
        now = datetime.now()
        day = item["day_of_month"]
        if now.month == 12:
            next_due = now.replace(year=now.year+1, month=1, day=day)
        else:
            next_due = now.replace(month=now.month+1, day=day)
        for r in user["rents"]:
            if r["id"] == item["id"]:
                r["next_due"] = next_due.strftime("%Y-%m-%d")
        save_user(user_id, user)
        await update.message.reply_text(
            f"✅ *Zo'r, {name}!*\n\n🏠 *{item['name']}* — *{item['amount']:,.0f}$* to'landi!\n📅 Keyingi: *{next_due.strftime('%d.%m.%Y')}*",
            parse_mode="Markdown", reply_markup=main_keyboard()
        )
    else:
        for t in user["tasks"]:
            if t["id"] == item["id"]:
                t["completed"] = True
        save_user(user_id, user)
        await update.message.reply_text(
            f"🎉 *Zo'r, {name}!*\n\n✅ *{item['name']}* bajarildi!",
            parse_mode="Markdown", reply_markup=main_keyboard()
        )

# ===== PUL YANGILASH =====
async def update_savings_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    tasks = [t for t in user.get("tasks",[]) if not t.get("completed")]
    if not tasks:
        await update.message.reply_text(f"❌ *Yangilanadigan vazifalar yo'q!*", parse_mode="Markdown", reply_markup=main_keyboard())
        return MAIN_MENU
    if len(tasks) == 1:
        context.user_data["update_task_id"] = tasks[0]["id"]
        rem = tasks[0]["amount"] - tasks[0].get("saved",0)
        await update.message.reply_text(
            f"💵 *{tasks[0]['name']}* uchun qancha yig'dingiz?\n"
            f"📊 {tasks[0].get('saved',0):,.0f}$ / {tasks[0]['amount']:,.0f}$ | ❗ {rem:,.0f}$ qoldi\n\nSummani yozing:",
            parse_mode="Markdown"
        )
        return CHECK_SAVINGS
    msg = "💵 *Qaysi vazifani yangilaysiz?*\n\n"
    for i, t in enumerate(tasks, 1):
        msg += f"{i}. {t['name']} — {t['amount']:,.0f}$\n"
    msg += "\nRaqamini yozing:"
    context.user_data["action"] = "update_savings"
    context.user_data["action_items"] = [t["id"] for t in tasks]
    await update.message.reply_text(msg, parse_mode="Markdown")
    return MAIN_MENU

async def update_savings_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip().replace("$","").replace(",","").replace(" ","")
    try:
        saved = float(text)
    except:
        await update.message.reply_text("❌ Faqat raqam yozing.")
        return CHECK_SAVINGS
    user = get_user(user_id)
    task_id = context.user_data.get("update_task_id")
    for task in user["tasks"]:
        if task["id"] == task_id:
            task["saved"] = saved
            remaining = task["amount"] - saved
            due = datetime.strptime(task["due_date"], "%Y-%m-%d")
            days_left = (due - datetime.now()).days
            save_user(user_id, user)
            if remaining <= 0:
                msg = f"🎉 *{user['name']}, pul to'liq yig'ildi!*\n\n✅ *{task['name']}* — *{task['amount']:,.0f}$* TAYYOR!"
            elif days_left > 0:
                msg = (f"💰 *Yangilandi, {user['name']}!*\n\n📌 *{task['name']}*\n"
                       f"✅ Yig'ilgan: *{saved:,.0f}$*\n❗ Qoldi: *{remaining:,.0f}$*\n"
                       f"📅 {days_left} kun | 💡 Har kuni ~*{remaining/days_left:,.0f}$* yig'ing!")
            else:
                msg = f"⚠️ *{user['name']}, muddati o'tdi!*\n\n❗ Hali *{remaining:,.0f}$* yig'ilmagan!\n🔴 Tezroq yig'ing!"
            break
    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=main_keyboard())
    return MAIN_MENU

# ===== O'CHIRISH =====
async def delete_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    tasks = [t for t in user.get("tasks",[]) if not t.get("completed")]
    rents = [r for r in user.get("rents",[]) if r.get("active")]
    all_items = tasks + rents
    if not all_items:
        await update.message.reply_text(f"❌ *O'chirish uchun hech narsa yo'q!*", parse_mode="Markdown", reply_markup=main_keyboard())
        return MAIN_MENU
    msg = f"🗑 *Qaysi yozuvni o'chirasiz?*\n\n"
    for i, item in enumerate(all_items, 1):
        icon = "🏠" if item.get("type")=="monthly" else "💼"
        msg += f"{i}. {icon} {item['name']} — {item['amount']:,.0f}$\n"
    msg += "\nRaqamini yozing yoki *bekor* deb yozing."
    context.user_data["action"] = "delete"
    context.user_data["action_items"] = [item["id"] for item in all_items]
    await update.message.reply_text(msg, parse_mode="Markdown")
    return MAIN_MENU

# ===== RAQAM KIRITILGANDA =====
async def handle_number_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    text = update.message.text.strip()
    action = context.user_data.get("action")
    if not action:
        return MAIN_MENU
    if text.lower() == "bekor":
        context.user_data.pop("action", None)
        await update.message.reply_text("❌ Bekor qilindi.", reply_markup=main_keyboard())
        return MAIN_MENU
    try:
        idx = int(text) - 1
        item_ids = context.user_data.get("action_items", [])
        if idx < 0 or idx >= len(item_ids):
            await update.message.reply_text("❌ Noto'g'ri raqam.")
            return MAIN_MENU
        target_id = item_ids[idx]
        target = None
        is_rent = False
        for t in user.get("tasks",[]):
            if t["id"] == target_id:
                target = t; break
        for r in user.get("rents",[]):
            if r["id"] == target_id:
                target = r; is_rent = True; break
        if not target:
            await update.message.reply_text("❌ Topilmadi.")
            return MAIN_MENU
        if action == "delete":
            if is_rent:
                user["rents"] = [r for r in user["rents"] if r["id"] != target_id]
            else:
                user["tasks"] = [t for t in user["tasks"] if t["id"] != target_id]
            save_user(user_id, user)
            await update.message.reply_text(f"🗑 *{target['name']}* o'chirildi!", parse_mode="Markdown", reply_markup=main_keyboard())
        elif action == "complete":
            await complete_item(update, user, user_id, target)
        elif action == "update_savings":
            context.user_data["update_task_id"] = target_id
            rem = target["amount"] - target.get("saved",0)
            await update.message.reply_text(
                f"💵 *{target['name']}* uchun qancha yig'dingiz?\n❗ Qoldi: {rem:,.0f}$\n\nSummani yozing:",
                parse_mode="Markdown"
            )
            context.user_data.pop("action", None)
            return CHECK_SAVINGS
        context.user_data.pop("action", None)
    except:
        await update.message.reply_text("❌ Faqat raqam yozing.")
    return MAIN_MENU

# ===== YORDAM =====
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    name = user["name"] if user else "Do'stim"
    await update.message.reply_text(
        f"ℹ️ *Yordam, {name}!*\n\n"
        f"💰 *Yangi vazifa* — bir martalik to'lovlar\n"
        f"🏠 *Ijara qo'shish* — oylik takrorlanuvchi to'lovlar\n"
        f"📋 *Vazifalarim* — bir martalik ro'yxat\n"
        f"🏠 *Ijaralarim* — oylik to'lovlar ro'yxati\n"
        f"✅ *To'lov qildim* — bajarildi deb belgilash\n"
        f"💵 *Pulni yangilash* — yig'ilgan summani yangilash\n"
        f"🗑 *O'chirish* — yozuvni o'chirish\n\n"
        f"*Eslatmalar:*\n"
        f"🔔 Vazifa: muddatga 4 kun qolganda\n"
        f"🏠 Ijara: 7 kun va 3 kun oldin",
        parse_mode="Markdown", reply_markup=main_keyboard()
    )
    return MAIN_MENU

# ===== AVTOMATIK ESLATMALAR =====
async def send_reminders(context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    now = datetime.now()
    for user_id, user in data.items():
        if not user.get("name"):
            continue
        name = user["name"]
        for task in user.get("tasks",[]):
            if task.get("completed"):
                continue
            due = datetime.strptime(task["due_date"], "%Y-%m-%d")
            days_left = (due - now).days
            rem = task["amount"] - task.get("saved",0)
            if days_left <= 4:
                if days_left < 0:
                    msg = f"🔴 *Assalomu aleykum, {name}!*\n\n⚠️ *{task['name']}* muddati {abs(days_left)} kun o'tdi!\n💰 Hali *{rem:,.0f}$* yig'ilmagan!\n😟 Tezroq yig'ing!"
                elif days_left == 0:
                    msg = f"🔔 *Assalomu aleykum, {name}!*\n\n⏰ Bugun *{task['name']}* kuni!\n💰 Qoldi: *{rem:,.0f}$*\n\n💪 Pul tayyor?"
                else:
                    msg = f"⏰ *Assalomu aleykum, {name}!*\n\n📌 *{task['name']}* — *{days_left} kun qoldi!*\n💰 Qoldi: *{rem:,.0f}$*\n\n💪 Pul jamladingizmi?"
                try:
                    await context.bot.send_message(chat_id=int(user_id), text=msg, parse_mode="Markdown")
                except Exception as e:
                    logging.error(f"Xato ({user_id}): {e}")

        for rent in user.get("rents",[]):
            if not rent.get("active"):
                continue
            nd = datetime.strptime(rent["next_due"], "%Y-%m-%d")
            days_left = (nd - now).days
            if days_left in [7,3,1,0] or days_left < 0:
                if days_left < 0:
                    msg = f"🔴 *Assalomu aleykum, {name}!*\n\n⚠️ *{rent['name']}* {abs(days_left)} kun kechikdi!\n💰 *{rent['amount']:,.0f}$* to'lanmagan!"
                elif days_left == 0:
                    msg = f"🔔 *Assalomu aleykum, {name}!*\n\n🏠 Bugun *{rent['name']}* to'lov kuni!\n💰 *{rent['amount']:,.0f}$*\n\nTo'ladingizmi?"
                else:
                    msg = f"🏠 *Assalomu aleykum, {name}!*\n\n📌 *{rent['name']}* — *{days_left} kun qoldi!*\n💰 *{rent['amount']:,.0f}$*\n📅 {nd.strftime('%d.%m.%Y')}\n\n💡 Pulni tayyorlang!"
                try:
                    await context.bot.send_message(chat_id=int(user_id), text=msg, parse_mode="Markdown")
                except Exception as e:
                    logging.error(f"Rent xato ({user_id}): {e}")

# ===== MAIN =====
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NAME:        [MessageHandler(filters.TEXT & ~filters.COMMAND, save_name)],
            MAIN_MENU: [
                MessageHandler(filters.Regex("^💰 Yangi vazifa$"), add_task_start),
                MessageHandler(filters.Regex("^🏠 Ijara qo'shish$"), add_rent_start),
                MessageHandler(filters.Regex("^📋 Vazifalarim$"), show_tasks),
                MessageHandler(filters.Regex("^🏠 Ijaralarim$"), show_rents),
                MessageHandler(filters.Regex("^✅ To'lov qildim$"), task_done),
                MessageHandler(filters.Regex("^💵 Pulni yangilash$"), update_savings_start),
                MessageHandler(filters.Regex("^🗑 O'chirish$"), delete_item),
                MessageHandler(filters.Regex("^ℹ️ Yordam$"), help_command),
                MessageHandler(filters.Regex(r"^\d+$"), handle_number_input),
            ],
            ADD_TASK_NAME:   [MessageHandler(filters.TEXT & ~filters.COMMAND, add_task_name)],
            ADD_TASK_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_task_amount)],
            ADD_TASK_DATE:   [MessageHandler(filters.TEXT & ~filters.COMMAND, add_task_date)],
            ADD_RENT_NAME:   [MessageHandler(filters.TEXT & ~filters.COMMAND, add_rent_name)],
            ADD_RENT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_rent_amount)],
            ADD_RENT_DAY:    [MessageHandler(filters.TEXT & ~filters.COMMAND, add_rent_day)],
            CHECK_SAVINGS:   [MessageHandler(filters.TEXT & ~filters.COMMAND, update_savings_amount)],
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True
    )

    app.add_handler(conv)
    app.job_queue.run_repeating(send_reminders, interval=10800, first=10)

    print("🤖 Bot ishga tushdi!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
