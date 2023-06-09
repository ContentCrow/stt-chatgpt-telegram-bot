# GPT-4 Telegram Bot modified

GPT-4 Telegram Bot is a simple and easy-to-use conversational AI-assistant running on GPT-4 language models. It provides the capability to interact with the bot through voice inputs by performing audio recognition on Telegram.

## Features
* Responds to user inputs in text format using [OpenAI GPT-4 Language Models](https://beta.openai.com/docs/models/gpt-4).
* Reset mechanism for clearing the conversation history.
* Speech-To-Text with OpenAI Whisper ASR (multi-language support).

## Requirements
* Python 3.x installed
* Install necessary Python packages using the requirements.txt file.
  ```
  pip install -r requirements.txt
  ```
* Install FFmpeg
The command-line tool [`ffmpeg`](https://ffmpeg.org/) needs to be installed on your system, which is available from most package managers:

```bash
# on Ubuntu or Debian
sudo apt update && sudo apt install ffmpeg

# on Arch Linux
sudo pacman -S ffmpeg

# on MacOS using Homebrew (https://brew.sh/)
brew install ffmpeg

# on Windows using Chocolatey (https://chocolatey.org/)
choco install ffmpeg

# on Windows using Scoop (https://scoop.sh/)
scoop install ffmpeg
```

## Environment Variables
* `TELEGRAM_BOT_KEY`: Your Telegram Bot Token which can be obtained from [BotFather](https://core.telegram.org/bots#6-botfather).
* `OPENAI_API_KEY`: Your OpenAI API Key, which can be found on the [OpenAI Dashboard](https://beta.openai.com/signup).

## Usage
1. Set your environment variables (linux):

   ```bash
   export TELEGRAM_BOT_KEY=your_telegram_token
   export OPENAI_API_KEY=your_openai_token
   ```
   And for Windows:
   ```bash
   setx TELEGRAM_BOT_KEY “your_telegram_token”
   setx OPENAI_API_KEY “your_openai_token”
   ```


2. Run the script:
   ```bash
   python gpt_telegram_bot.py
   ```

3. Open the Telegram app and interact with the bot using text messages or voice inputs.
