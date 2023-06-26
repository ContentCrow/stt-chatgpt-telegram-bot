import os
import ffmpeg
from datetime import datetime
from dateutil.relativedelta import relativedelta
from langcodes import *
from pydub import AudioSegment
from telegram.ext import (
    ContextTypes,
)

supported_languages = ["af", "ar", "hy", "az", "be", "bs", "bg", "ca", "zh", "hr", "cs", "da", "nl", "en", "et", "fi", "fr", "gl", "de", "el", "he", "hi", "hu", "is", "id", "it", "ja", "kn", "kk", "ko", "lv", "lt", "mk", "ms", "mr", "mi", "ne", "no", "fa", "pl", "pt", "ro", "ru", "sr", "sk", "sl", "es", "sw", "sv", "tl", "ta", "th", "tr", "uk", "ur", "vi", "cy"]

async def download_audio(update: object, context: ContextTypes.DEFAULT_TYPE) -> object:
    file_id = update.message.voice.file_id
    new_file = await context.bot.get_file(file_id)
    await new_file.download_to_drive(file_id + ".oga")
    return file_id

def convert_audio_to_wav(audio_file: str) -> object:
    with open(audio_file + ".oga", "rb") as f:
        voice = AudioSegment.from_ogg(f)
    voice_wav = voice.export(audio_file + ".wav", format="wav")
    voice_wav.close()
    os.remove(audio_file + ".wav")
    os.remove(audio_file + ".oga")
    return voice_wav

def convert_and_speedup_audio(audio_file: str, speed: float) -> str:
    (
        ffmpeg
        .input(audio_file + ".oga")
        .filter("atempo", speed)
        .output(audio_file + ".mp3")
        .global_args("-c:a", "libmp3lame")
        .global_args("-q:a", "0")
        .global_args("-loglevel", "error")
        .global_args("-nostats")
        .run()
    )
    os.remove(audio_file + ".oga")
    return audio_file + ".mp3";

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