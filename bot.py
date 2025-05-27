import os
import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Хранилище в памяти (в проде лучше использовать базу данных)
user_data = {}

# Главное меню
MAIN_MENU = [["🏋️‍♂️ Тренировка", "🧘‍♀️ Растяжка"], ["📊 Измерения", "📈 Отчёты"]]

# Состояния
(
    SELECT_TRAINING_FOLDER, CREATE_TRAINING_FOLDER,
    SELECT_EXERCISE, CREATE_EXERCISE,
    RECORD_WEIGHT, RECORD_MEASUREMENTS,
    SELECT_MEASUREMENT_TYPE,
) = range(7)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id

    if chat_id not in user_data:
        user_data[chat_id] = {
            "folders": {},
            "measurements": [],
            "stretching": [],
        }
        await update.message.reply_text(
            f"Привет, {user.first_name}! Добро пожаловать в фитнес-бот 💪",
            reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True),
        )
    else:
        await update.message.reply_text(
            "С возвращением! Выберите действие:",
            reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True),
        )

# --- ТРЕНИРОВКА ---
async def training_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    folders = user_data[chat_id]["folders"]

    if not folders:
        await update.message.reply_text("У вас нет папок для упражнений. Введите название новой папки:")
        return CREATE_TRAINING_FOLDER

    folder_list = "\n".join(f"- {name}" for name in folders)
    await update.message.reply_text(f"Выберите папку или введите новое имя:\n{folder_list}")
    return CREATE_TRAINING_FOLDER

async def create_training_folder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    folder_name = update.message.text.strip()
    folders = user_data[chat_id]["folders"]

    if folder_name not in folders:
        folders[folder_name] = {}
        await update.message.reply_text(f"Создана папка: {folder_name}")

    exercises = folders[folder_name]
    if not exercises:
        await update.message.reply_text("Папка пуста. Введите название первого упражнения:")
        context.user_data["current_folder"] = folder_name
        return CREATE_EXERCISE

    return SELECT_EXERCISE

async def create_exercise(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    folder = context.user_data["current_folder"]
    exercise = update.message.text.strip()

    user_data[chat_id]["folders"][folder][exercise] = {
        "sets": 0,
        "reps": 0,
        "records": []
    }

    await update.message.reply_text(f"Упражнение '{exercise}' добавлено. Сколько повторений и подходов? (Напр: 10x3)")
    context.user_data["current_exercise"] = exercise
    return RECORD_WEIGHT

async def record_sets_reps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    input_text = update.message.text.strip().lower()
    folder = context.user_data["current_folder"]
    exercise = context.user_data["current_exercise"]

    try:
        reps, sets = map(int, input_text.split("x"))
        user_data[chat_id]["folders"][folder][exercise]["reps"] = reps
        user_data[chat_id]["folders"][folder][exercise]["sets"] = sets
        await update.message.reply_text("Сколько кг вы поднимали? Можете указать по подходам (напр: 50,50,52)")
        return RECORD_WEIGHT
    except:
        await update.message.reply_text("Неверный формат. Пример: 10x3")
        return RECORD_WEIGHT

async def record_weights(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    weights = update.message.text.strip().split(",")
    folder = context.user_data["current_folder"]
    exercise = context.user_data["current_exercise"]
    now = datetime.datetime.now().strftime("%Y-%m-%d")

    user_data[chat_id]["folders"][folder][exercise]["records"].append({
        "date": now,
        "weights": weights
    })

    await update.message.reply_text("Успешно записано! Возвращаемся в главное меню.")
    return ConversationHandler.END

# --- РАСТЯЖКА ---
async def stretching_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    stretching = user_data[chat_id]["stretching"]

    await update.message.reply_text("Введите название упражнения на растяжку:")
    return CREATE_EXERCISE

# --- ИЗМЕРЕНИЯ ---
async def measurement_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите вес, обхват груди, талии, бёдер через пробел (напр: 80 100 90 100)")
    return RECORD_MEASUREMENTS

async def record_measurements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    now = datetime.datetime.now().strftime("%Y-%m-%d")
    try:
        weight, chest, waist, hips = map(float, update.message.text.strip().split())
        user_data[chat_id]["measurements"].append({
            "date": now,
            "weight": weight,
            "chest": chest,
            "waist": waist,
            "hips": hips,
        })
        await update.message.reply_text("Измерения сохранены!")
    except:
        await update.message.reply_text("Неверный формат. Пример: 80 100 90 100")
    return ConversationHandler.END

# --- ОТЧЁТЫ ---
async def reports_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Пока отчёты доступны только в виде графиков по весам. (Функция в разработке)")
    return ConversationHandler.END

# --- ОТМЕНА ---
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Действие отменено.")
    return ConversationHandler.END

# --- ЗАПУСК ---
if __name__ == '__main__':
    token = os.getenv("7598042604:AAFGcoTCYnTtnNyXI3Kt_-KFaPsMzokAEqY")
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("Тренировка"), training_menu)],
        states={
            CREATE_TRAINING_FOLDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_training_folder)],
            CREATE_EXERCISE: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_exercise)],
            RECORD_WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, record_sets_reps)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    ))

    app.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("Растяжка"), stretching_menu)],
        states={CREATE_EXERCISE: [MessageHandler(filters.TEXT & ~filters.COMMAND, cancel)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    ))

    app.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("Измерения"), measurement_menu)],
        states={RECORD_MEASUREMENTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, record_measurements)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    ))

    app.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("Отчёты"), reports_menu)],
        states={},
        fallbacks=[CommandHandler("cancel", cancel)],
    ))

    app.run_polling()