# Hangman Bot

<i> Recreating the classic game of Hangman on Telegram! </i>


## Usage

### Bot Setup

To create a clone of the bot, please run the following commands:

```bash

git clone https://github.com/xbowery/hangman_bot.git

cp .env.example .env

```

Next, obtain your Telegram Bot token from [BotFather](https://t.me/BotFather) by sending the /newbot command to it.

Also, create a MongoDB cluster and obtain the MongoDB URL Connection String.

After obtaining the Telegram Bot token and the connection string, go to your `.env` file and edit the `token` and `mongourl` fields respectively.

### Running the Bot locally

On your command line terminal, run the following command:

```bash

python3 bot.py

```

You should be able to interact with your bot thereafter.

### Running the Bot on Docker

I have provided the `Dockerfile` and `docker-compose.yml` files to allow you to easily run the Bot on Docker.

Please ensure you have Docker Desktop installed before proceeding with the steps below.

To run the Bot on Docker,

```bash

docker compose up -d --build

```
