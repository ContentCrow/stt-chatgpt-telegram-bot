import openai
import os
import sys
import logging
import usersettings
import httpx
import traceback
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    filters,
    CommandHandler,
    TypeHandler,
    ApplicationHandlerStop,
)
from telegram.error import TelegramError
from helpers import download_media, convert_and_speedup_audio, validate_entered_language, validate_entered_speed, get_command_argument, get_first_last_day_of_this_month, get_final_file_size

# enable/disable full traceback logging for the logfile
LOG_TRACEBACK = False
# Init logger: Save log to file with level DEBUG and print out log to console with level CRITICAL (reason: suppress annoying _updater.py ERROR messages)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.CRITICAL) # handler with log level for console
logging.basicConfig(
    format="[%(asctime)s] %(levelname)s [%(filename)s.%(funcName)s:%(lineno)d] %(message)s", 
    datefmt="%a, %d %b %Y %H:%M:%S",
    level=logging.ERROR, # log level for log file
    handlers= [
        logging.FileHandler("sttchatgpttelegrambot.log"),
        handler
    ]
)
logger = logging.getLogger("SST-CHATGPT-TELEGRAM-BOT")

# Limit the log level of imported modules to ERROR
for log_name, log_obj in logging.Logger.manager.loggerDict.items():
    #logger.critical(log_obj)
    if log_name != 'SST-CHATGPT-TELEGRAM-BOT' and isinstance(log_obj, logging.Logger):
        log_obj.setLevel(logging.ERROR)

WHISPER_API_FILE_SIZE_LIMIT = 25
MAX_COUNT = 5

telegram_token = os.environ["TELEGRAM_BOT_KEY"]
telegram_bot_password = os.environ["TELEGRAM_BOT_PW"]
openai.api_key = os.environ["OPENAI_API_KEY"]

messages_list = []
_user_id = None

# Init the local settings file
settings = usersettings.Settings("contentcrow.sttchatgpttelegrambot")
settings.add_setting("language", str, default="auto")
settings.add_setting("speed", float, default=1.0)
settings.add_setting("whitelisted_ids", list, [])
settings.add_setting("blacklisted_ids", list, [])
settings.load_settings()

def append_history(content, role) -> []:
    messages_list.append({"role": role, "content": content})
    return messages_list


def clear_history() -> []:
    messages_list.clear()
    return messages_list


def get_openai_usage_cost() -> float:
    dates = get_first_last_day_of_this_month()
    r = openai.api_requestor.APIRequestor()
    resp = r.request("GET", f"/dashboard/billing/usage?end_date={dates['last_day']}&start_date={dates['first_day']}")
    resp_object = resp[0]
    return resp_object.data["total_usage"]

def log_traceback() -> None:
    if LOG_TRACEBACK:
        traceback_str = traceback.format_exc()
        logger.error(traceback_str)

async def process_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
    logger.critical(f"User: {_user_id}. Proccessed text message with ChatGPT.")


async def process_audio_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    transcript = await get_audio_transcription(update, context)
    append_history(transcript, "user")

    response = generate_gpt_response()

    append_history(response, "assistant")
    await context.bot.send_message(chat_id=update.effective_chat.id, text=response)
    logger.critical(f"User: {_user_id}. Proccessed audio message with ChatGPT.")


async def process_audio_message_no_gpt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    thinking = await context.bot.send_message(
        chat_id=update.effective_chat.id, text="🤔💬"
    )

    transcript_arr = await get_audio_transcription(update, context)

    await context.bot.deleteMessage(
        message_id=thinking.message_id, chat_id=update.message.chat_id
    )
    # aborted or not
    if transcript_arr[2]:
        chat_message = f"Transcription aborted! The converted audio file size ({transcript_arr[0]}MB) exceeds the Whisper API size limit of {WHISPER_API_FILE_SIZE_LIMIT}MB. Please split your input file accordingly."
        logger_message = f"User: {_user_id}. Transcription for '{transcript_arr[1]}' via Whisper API aborted. The converted file size ({transcript_arr[0]}MB) exceeds {WHISPER_API_FILE_SIZE_LIMIT}MB."
    else:
        chat_message = transcript_arr[0]
        logger_message = f"User: {_user_id}. Transcription for '{transcript_arr[1]}' via Whisper API finished."

    await context.bot.send_message(chat_id=update.effective_chat.id, text=chat_message)
    logger.critical(logger_message)


def generate_gpt_response() -> str:
    completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages_list)
    return completion.choices[0].message["content"]


async def get_audio_transcription(update: object, context: ContextTypes.DEFAULT_TYPE) -> []:
    file_arr = await download_media(update, context)
    downloaded_file = file_arr[0]
    converted_file_name = convert_and_speedup_audio(downloaded_file, settings.speed)
    has_error = False
    with open(converted_file_name, "rb") as f:
        file_size = get_final_file_size(f)
        if file_size > WHISPER_API_FILE_SIZE_LIMIT:
            has_error = True
            transcript = file_size
        else:
            if settings.language == "auto":
                transcript_obj = openai.Audio.transcribe(
                    file = f,
                    model = "whisper-1",
                    #response_format="text", # verbose_json, srt, vtt, text
                )
            else:
                transcript_obj = openai.Audio.transcribe(
                    file = f,
                    model = "whisper-1",
                    #response_format="text",
                    language=settings.language
                )
            transcript = transcript_obj["text"]
    os.remove(converted_file_name)
    return [transcript, file_arr[1], has_error]


async def reset_history(update: object, context: ContextTypes.DEFAULT_TYPE) -> []:
    clear_history()
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Messages history cleared."
    )
    logger.critical(f"User ({_user_id}) cleared the message history.")
    return messages_list


async def set_language(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
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
    logger.critical(f"User ({_user_id}) set speech language to '{settings.language}'.")


async def set_speed(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
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
    logger.critical(f"User ({_user_id}) set audio speed to '{settings.speed}x'.")


async def show_info(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    cost = round(get_openai_usage_cost() / 100.0, 2)
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=f"Total usage cost this month: {cost}$\nSpeech language: {settings.language}\nAudio speed: {settings.speed}x"
    )
    logger.critical(f"User ({_user_id}) displayed infos: language={settings.language}, speed={settings.speed}x, usage_cost={cost}$")


async def chat_guard(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    count = context.user_data.get("usageCount", 0)
    if hasattr(update, "message") and hasattr(update.message, "from_user"):
        user_id = update.message.from_user.id
        user_firstname = update.message.from_user.first_name
        text = update.message.text
    else:
        user_id = update.edited_message.from_user.id
        user_firstname = update.edited_message.from_user.first_name
        text = update.edited_message.text
    #print(user_id, text, '/password ' in text, count, update.effective_chat.id)

    global _user_id
    _user_id = user_id

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
        logger.critical(f"Chat-Guard: User ({user_id}) was successfully whitelisted!")
    elif count < MAX_COUNT:
        context.user_data["usageCount"] = count + 1
        attempt = MAX_COUNT - count
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=f"This is a private bot. Please enter the correct password! You have {attempt} attempt{'s' if attempt > 1 else ''} left."
        )
        logger.critical(f"Chat-Guard: User ({user_id}) tried to access the bot without being whitelisted.")
        raise ApplicationHandlerStop
    elif count == MAX_COUNT:
        context.user_data["usageCount"] = count + 1
        settings.blacklisted_ids.append(user_id)
        settings.save_settings()
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=f"🛑 You have been permanently blocked by this bot. 🛑"
        )
        logger.critical(f"Chat-Guard: User ({user_id}) was blacklisted!")
        raise ApplicationHandlerStop
    else:
        raise ApplicationHandlerStop


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        raise context.error
    except httpx.HTTPError as e:
        # Handle httpx-specific errors
        logger.critical(f"HTTPx Error: {str(e)}")
        log_traceback()
    except TelegramError as e:
        e_string = str(e)
        # Handle generic Telegram errors
        # do not log these errors, as the _updater.py will log them anyways
        if ("httpx.LocalProtocolError" in e_string or "httpx.RemoteProtocolError" in e_string or "httpx.WriteError" in e_string or "httpx.ReadError" in e_string or "httpx.ConnectError" in e_string):
            pass
        else:
            logger.critical(f"Telegram Error: {e_string}")
        log_traceback()
    except Exception as e:
        # Handle other unexpected errors
        logger.error(f"Unexpected Error: {str(e)}")
        log_traceback()

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

    audio_handler = MessageHandler(filters.VOICE | filters.AUDIO | filters.VIDEO, process_audio_message_no_gpt)
    application.add_handler(audio_handler)

    application.add_error_handler(error_handler)

    logger.critical("The bot has been (re)started.")
    application.run_polling()
