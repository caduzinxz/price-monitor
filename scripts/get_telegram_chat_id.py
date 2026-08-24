"""Descobre o seu TELEGRAM_CHAT_ID.

Uso:
    1. Crie um bot com o @BotFather no Telegram e copie o token.
    2. Coloque o token em TELEGRAM_BOT_TOKEN no .env.
    3. Abra uma conversa com o SEU bot e mande qualquer mensagem (ex.: "oi").
       Isso e obrigatorio: o Telegram so entrega mensagens de um bot para quem
       ja falou com ele, entao o bot nao consegue te achar sozinho.
    4. Rode: python -m scripts.get_telegram_chat_id
"""

import json
import logging
import urllib.error
import urllib.request

from app.config import settings

API_BASE = "https://api.telegram.org"


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s", datefmt="%H:%M:%S")
    logger = logging.getLogger(__name__)

    if not settings.TELEGRAM_BOT_TOKEN:
        logger.error("Preencha TELEGRAM_BOT_TOKEN no .env antes de rodar este script.")
        return

    endpoint = f"{API_BASE}/bot{settings.TELEGRAM_BOT_TOKEN}/getUpdates"

    try:
        with urllib.request.urlopen(endpoint, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        # Nao imprimimos a URL porque ela contem o token do bot.
        logger.error("A API do Telegram respondeu HTTP %s. O token esta correto?", exc.code)
        return
    except urllib.error.URLError as exc:
        logger.error("Nao foi possivel alcancar a API do Telegram: %s", exc.reason)
        return

    updates = data.get("result", [])
    if not updates:
        logger.error(
            "Nenhuma mensagem encontrada. Abra o Telegram, procure o seu bot, "
            "mande qualquer mensagem para ele e rode este script de novo."
        )
        return

    found_chats = {}
    for update in updates:
        message = update.get("message") or update.get("edited_message") or {}
        chat = message.get("chat") or {}
        if "id" in chat:
            chat_name = chat.get("first_name") or chat.get("title") or "sem nome"
            found_chats[chat["id"]] = chat_name

    for chat_id, chat_name in found_chats.items():
        logger.info("Encontrado: %s -> TELEGRAM_CHAT_ID=%s", chat_name, chat_id)

    logger.info("Copie o valor acima para TELEGRAM_CHAT_ID no seu .env.")


if __name__ == "__main__":
    main()
