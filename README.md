# STT GPT-3.5 Telegram Bot

SST GPT-3.5 Telegram Bot is a simple and easy-to-use conversational AI-assistant and Speech-To-Text converter running on GPT-3.5 language models. It provides the capability to interact with the bot through text inputs as well as transcribe audio messages to text.

## Features
* Responds to user inputs in text format using [OpenAI GPT-3.5 Language Models](https://platform.openai.com/docs/models/gpt-3-5).
* Reset mechanism for clearing the ChatGPT conversation history.
* Multi-language Speech-To-Text with [OpenAI Whisper](https://platform.openai.com/docs/models/whisper).
* The speech transcription language and the audio speed can be configured directly via the bot.
* Access restriction with environment password and black-/whitelisting of user_ids.

## Docker (Windows)
To run this bot directly with docker, simple run the following commands: (The TELEGRAM_BOT_WL_ID environment variable is optional.)
```bash
docker build -t contentcrow/stt-chatgpt-telegram-bot https://github.com/ContentCrow/stt-chatgpt-telegram-bot.git

docker run --name your_bot_name --restart unless-stopped -e TELEGRAM_BOT_KEY=your_telegram_token -e OPENAI_API_KEY=your_openai_token -e TELEGRAM_BOT_PW=your_bot_pw -e TELEGRAM_BOT_WL_ID=telegram_user_id contentcrow/stt-chatgpt-telegram-bot

```

## Requirements
* Python 3.x installed
* Install necessary Python packages using the requirements.txt file.
  ```bash
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
* `TELEGRAM_BOT_KEY`: Your Telegram Bot Token which can be obtained from [BotFather](https://core.telegram.org/bots#6-botfather). (mandatory)
* `OPENAI_API_KEY`: Your OpenAI API Key, which can be found on the [OpenAI Dashboard](https://beta.openai.com/signup). (mandatory)
* `TELEGRAM_BOT_PW`: An access password of your choice for the Telegram Bot. (mandatory)
* `TELEGRAM_BOT_WL_ID`: Telegram User ID which will be whitelisted by default. (optional)

## Usage
1. Set your environment variables:

   For Linux:
   ```bash
   export TELEGRAM_BOT_KEY=your_telegram_token
   export OPENAI_API_KEY=your_openai_token
   export TELEGRAM_BOT_PW=your_bot_pw
   export TELEGRAM_BOT_WL_ID=telegram_user_id
   ```
   For Windows:
   ```bash
   setx TELEGRAM_BOT_KEY “your_telegram_token”
   setx OPENAI_API_KEY “your_openai_token”
   setx TELEGRAM_BOT_PW “your_bot_pw”
   setx TELEGRAM_BOT_WL_ID “telegram_user_id”
   ```

2. Run the script:
   ```bash
   python gpt_telegram_bot.py
   ```

3. Open the Telegram app and interact with the bot using text messages, voice inputs or the following commands.
   ```bash
   /password your_bot_pw # Gain access to the bot
   /language en # Set the speech language used for the transcription (e.g. en, de, fr, es, it...)
   /speed 1.2 # Set the audio speed used for transcription (0.8x-1.8x)
   /add_cost 0.15 # Manually add cost to this months usage cost (in USD)
   /info # Display important info (monthly usage cost, language, speed)
   /reset # Reset the ChatGPT context history
   ```
