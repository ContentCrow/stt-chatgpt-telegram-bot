import openai
import os
import logging
import usersettings

from helpers import download_audio, convert_audio_to_wav, convert_and_speedup_audio, validate_entered_language, validate_entered_speed, get_command_argument, get_first_last_day_of_this_month
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    filters,
    CommandHandler,
    TypeHandler,
    ApplicationHandlerStop
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

MAX_COUNT = 5
telegram_token = os.environ["TELEGRAM_BOT_KEY"]
telegram_bot_password = os.environ["TELEGRAM_BOT_PW"]
openai.api_key = os.environ["OPENAI_API_KEY"]

messages_list = []

settings = usersettings.Settings("contentcrow.sttchatgpttelegrambot")
settings.add_setting("language", str, default="auto")
settings.add_setting("speed", float, default=1.0)
settings.add_setting("whitelisted_ids", list, [])
settings.add_setting("blacklisted_ids", list, [])
settings.load_settings()

def append_history(content, role):
    messages_list.append({"role": role, "content": content})
    return messages_list


def clear_history():
    messages_list.clear()
    return messages_list


def get_openai_usage_cost():
    dates = get_first_last_day_of_this_month()
    r = openai.api_requestor.APIRequestor()
    resp = r.request("GET", f"/dashboard/billing/usage?end_date={dates['last_day']}&start_date={dates['first_day']}")
    resp_object = resp[0]
    return resp_object.data["total_usage"]


async def process_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    thinking = await context.bot.send_message(
        chat_id=update.effective_chat.id, text="🤔💬"
    )
    append_history(update.message.text, "user")

    response = generate_gpt_response()

    append_history(response, "assistant")
    await context.bot.deleteMessage(
        message_id=thinking.message_id, chat_id=update.message.chat_id
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=response)
    logging.info("Proccessed text message with ChatGPT.")


async def process_audio_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    transcript = await get_audio_transcription(update, context)
    append_history(transcript, "user")

    response = generate_gpt_response()

    append_history(response, "assistant")
    await context.bot.send_message(chat_id=update.effective_chat.id, text=response)
    logging.info("Proccessed audio message with ChatGPT.")


async def process_audio_message_no_gpt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    thinking = await context.bot.send_message(
        chat_id=update.effective_chat.id, text="🤔💬"
    )

    transcript = await get_audio_transcription(update, context)

    await context.bot.deleteMessage(
        message_id=thinking.message_id, chat_id=update.message.chat_id
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=transcript)
    logging.info("Transcription with Whisper finished.")


def generate_gpt_response():
    completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages_list)
    return completion.choices[0].message["content"]


async def get_audio_transcription(update, context):
    new_file = await download_audio(update, context)
    file_name = convert_and_speedup_audio(new_file, settings.speed)
    with open(file_name, "rb") as f:
        if settings.language == "auto":
            transcript = openai.Audio.transcribe(
                file = f,
                model = "whisper-1",
                #response_format="text", # verbose_json, srt, vtt, text
            )
        else:
            transcript = openai.Audio.transcribe(
                file = f,
                model = "whisper-1",
                #response_format="text",
                language=settings.language
            )
    os.remove(file_name)
    return transcript["text"]


async def reset_history(update, context):
    clear_history()
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Messages history cleared."
    )
    logging.info(f"User cleared the message history.")
    return messages_list


async def set_language(update, context):
    if hasattr(update, "message") and hasattr(update.message, "text"):
        entered_language = get_command_argument("/language ", update.message.text)
    elif hasattr(update, "edited_message"):
        entered_language = get_command_argument("/language ", update.edited_message.text)
    else:
        entered_language = "auto"

    settings.language = validate_entered_language(entered_language)
    settings.save_settings()

    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=f"Speech language set to '{settings.language}'."
    )
    logging.info(f"User set speech language to '{settings.language}'.")


async def set_speed(update, context):
    if hasattr(update, "message") and hasattr(update.message, "text"):
        entered_speed = get_command_argument("/speed ", update.message.text)
    elif hasattr(update, "edited_message"):
        entered_speed = get_command_argument("/speed ", update.edited_message.text)
    else:
        entered_speed = 1.0

    settings.speed = validate_entered_speed(entered_speed)
    settings.save_settings()

    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=f"Audio speed set to '{settings.speed}x'."
    )
    logging.info(f"User set audio speed to '{settings.speed}x'.")


async def show_info(update, context):
    cost = round(get_openai_usage_cost() / 100.0, 2)
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=f"Total usage cost this month: {cost}$\nSpeech language: {settings.language}\nAudio speed: {settings.speed}x"
    )
    logging.info(f"User displayed infos: language={settings.language}, speed={settings.speed}x, usage_cost={cost}$")


async def chat_guard(update, context):
    count = context.user_data.get("usageCount", 0)
    if hasattr(update, "message") and hasattr(update.message, "from_user"):
        user_id = update.message.from_user.id
        user_firstname = update.message.from_user.first_name
        text = update.message.text
    else:
        user_id = update.edited_message.from_user.id
        user_firstname = update.edited_message.from_user.first_name
        text = update.edited_message.text
    #print(user_id, text, '/password ' in text, count)
    
    if user_id in settings.blacklisted_ids:
        raise ApplicationHandlerStop
    elif user_id in settings.whitelisted_ids:
        pass
    elif count < MAX_COUNT and "/password " in text and get_command_argument("/password ", text) == telegram_bot_password:
        settings.whitelisted_ids.append(user_id)
        settings.save_settings()
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=f"Welcome {user_firstname}! Your user_id {user_id} has been whitelisted."
        )
        await context.bot.deleteMessage(
            message_id=update.message.message_id, chat_id=update.message.chat_id
        )
        logging.info(f"Chat-Guard: User with user_id {user_id} was successfully whitelisted!")
    elif count < MAX_COUNT:
        context.user_data["usageCount"] = count + 1
        attempt = MAX_COUNT - count
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=f"This is a private bot. Please enter the correct password! You have {attempt} attempt{'s' if attempt > 1 else ''} left."
        )
        raise ApplicationHandlerStop
    elif count == MAX_COUNT:
        context.user_data["usageCount"] = count + 1
        settings.blacklisted_ids.append(user_id)
        settings.save_settings()
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=f"🛑 You have been permanently blocked by this bot. 🛑"
        )
        logging.info(f"Chat-Guard: User with user_id {user_id} was blacklisted!")
        raise ApplicationHandlerStop
    else:
        raise ApplicationHandlerStop


if __name__ == "__main__":
    application = ApplicationBuilder().token(telegram_token).build()

    type_handler = TypeHandler(Update, chat_guard)
    application.add_handler(type_handler, -1)

    text_handler = MessageHandler(
        filters.TEXT & (~filters.COMMAND), process_text_message
    )
    application.add_handler(text_handler)

    application.add_handler(CommandHandler("reset", reset_history))
    application.add_handler(CommandHandler("language", set_language))
    application.add_handler(CommandHandler("speed", set_speed))
    application.add_handler(CommandHandler("info", show_info))

    audio_handler = MessageHandler(filters.VOICE, process_audio_message_no_gpt)
    application.add_handler(audio_handler)

    application.run_polling()
