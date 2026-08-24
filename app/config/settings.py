"""Configuracoes centralizadas do projeto.

Todo modulo que precisar de uma configuracao (URL do produto, credenciais de
e-mail, regras de alerta etc.) deve importar deste arquivo, em vez de ler
os.environ diretamente ou ter valores espalhados pelo codigo.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

# --- Produtos monitorados ----------------------------------------------------
# A lista de produtos fica num JSON (e nao no .env) porque o .env so representa
# valores simples. Ver app/config/products.py.
PRODUCTS_FILE = BASE_DIR / "products.json"

# --- Regras de monitoramento -------------------------------------------------
MIN_PRICE_DROP_PERCENT = float(os.getenv("MIN_PRICE_DROP_PERCENT", "10"))
CHECK_INTERVAL_HOURS = float(os.getenv("CHECK_INTERVAL_HOURS", "1"))

# Alerta quando o preco atinge o menor valor ja registrado, mesmo que a queda
# desde a ultima verificacao seja menor que MIN_PRICE_DROP_PERCENT.
ALERT_ON_HISTORIC_LOW = os.getenv("ALERT_ON_HISTORIC_LOW", "true").strip().lower() not in (
    "false",
    "0",
    "no",
)

# Pausa entre um produto e outro, para nao disparar varias requisicoes seguidas
# ao mesmo site (boa pratica de scraping).
DELAY_BETWEEN_PRODUCTS_SECONDS = float(os.getenv("DELAY_BETWEEN_PRODUCTS_SECONDS", "5"))

# --- E-mail (SMTP) -----------------------------------------------------------
# Interruptor para desligar os alertas sem perder as credenciais configuradas.
# Aceita "false", "0" ou "no" (em qualquer caixa) para desativar.
ALERTS_ENABLED = os.getenv("ALERTS_ENABLED", "true").strip().lower() not in (
    "false",
    "0",
    "no",
)

EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
# .strip() protege contra espacos acidentais no copiar/colar. A App Password do
# Gmail e exibida em blocos ("abcd efgh ijkl mnop") e funciona com ou sem eles,
# mas um espaco sobrando no inicio/fim causaria uma falha de login confusa.
EMAIL_USER = os.getenv("EMAIL_USER", "").strip()
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "").strip()
EMAIL_TO = os.getenv("EMAIL_TO", "").strip()

# O canal so e ativado se estiver totalmente configurado -- assim nao e preciso
# um interruptor separado por canal.
EMAIL_CONFIGURED = bool(EMAIL_USER and EMAIL_PASSWORD and EMAIL_TO)

# --- Telegram -----------------------------------------------------------------
# O token da uma o controle total do bot: trate como senha (nunca versione).
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
TELEGRAM_CONFIGURED = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)

# --- Armazenamento (Excel, mantido como referencia/alternativa) -------------
DATA_DIR = BASE_DIR / "data"
EXCEL_PATH = DATA_DIR / "price_history.xlsx"

# --- Armazenamento (Supabase) -------------------------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_PUBLISHABLE_KEY = os.getenv("SUPABASE_PUBLISHABLE_KEY", "")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY", "")
