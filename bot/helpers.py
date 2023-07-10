import os
import ffmpeg
import math
from datetime import datetime
from dateutil.relativedelta import relativedelta
from langcodes import *
from pydub import AudioSegment
from telegram.ext import (
    ContextTypes,
)

supported_languages = ["af", "ar", "hy", "az", "be", "bs", "bg", "ca", "zh", "hr", "cs", "da", "nl", "en", "et", "fi", "fr", "gl", "de", "el", "he", "hi", "hu", "is", "id", "it", "ja", "kn", "kk", "ko", "lv", "lt", "mk", "ms", "mr", "mi", "ne", "no", "fa", "pl", "pt", "ro", "ru", "sr", "sk", "sl", "es", "sw", "sv", "tl", "ta", "th", "tr", "uk", "ur", "vi", "cy"]

async def download_media(update: object, context: ContextTypes.DEFAULT_TYPE) -> []:
    if hasattr(update.message, "voice") and update.message.voice != None:
        file_id = update.message.voice.file_id
        file_extension = get_file_extension(update.message.voice.mime_type)
        file_name = "voice message"
    elif hasattr(update.message, "audio") and update.message.audio != None:
        file_id = update.message.audio.file_id
        file_extension = get_file_extension(update.message.audio.mime_type)
        file_name = update.message.audio.file_name
    elif hasattr(update.message, "video") and update.message.video != None:
        file_id = update.message.video.file_id
        file_extension = get_file_extension(update.message.video.mime_type)
        file_name = update.message.video.file_name
    else:
        return None
    new_file = await context.bot.get_file(file_id)
    f = await new_file.download_to_drive(file_id + file_extension)
    return [f, file_name]

def convert_and_speedup_audio(audio_file: object, speed: float) -> object:
    file_split = audio_file.name.split('.')
    file_name = file_split[0]
    #file_extension = file_split[1]
    (
        ffmpeg
        .input(audio_file.name)
        .filter("atempo", speed)
        .output(file_name + ".mp3")
        .global_args("-c:a", "libmp3lame")
        .global_args("-q:a", "0")
        .global_args("-loglevel", "error")
        .global_args("-nostats")
        .run()
    )
    os.remove(audio_file)
    return file_name + ".mp3";

def get_file_extension(mime_type: str) -> str:
    return "." + mime_type.split('/')[1]

def get_final_file_size(f: object) -> int:
    file_size_bytes = os.fstat(f.fileno()).st_size
    return math.ceil(file_size_bytes / (1024 * 1024))

def get_command_argument(command: str, text: str) -> str:
    if len(text) > (len(command) + 1):
        return text.split(command)[1]
    else:
        return ""

def validate_entered_language(entered_lang: str) -> str:
    if entered_lang == "auto" or len(entered_lang) == 0:
        return "auto"
    elif len(entered_lang) > 3:
        try:
            lang = Language.find(entered_lang)
        except:
            return "auto"
    else:
        try:
            lang = Language.get(standardize_tag(entered_lang))
        except:
            return "auto"

    if lang.is_valid():
        return closest_supported_match(lang, supported_languages)

def validate_entered_speed(entered_speed: str) -> float:
    if len(entered_speed) == 0:
        return 1.0
    else:
        try:
            speed = float(entered_speed)
        except:
            return 1.0
        if speed >= 0.8 and speed <= 1.8:
            return speed
    return 1.0

def get_first_last_day_of_this_month() -> object:
    date = datetime.now()
    first_day = date + relativedelta(day=1)
    last_day = date + relativedelta(day=31)
    return {
        "today": date.strftime("%Y-%m-%d"),
        "first_day": first_day.strftime("%Y-%m-%d"),
        "last_day": last_day.strftime("%Y-%m-%d")
    }