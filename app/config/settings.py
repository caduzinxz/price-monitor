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

# --- Produto monitorado -----------------------------------------------------
PRODUCT_URL = os.getenv(
    "PRODUCT_URL",
    "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
)
PRODUCT_NAME = os.getenv("PRODUCT_NAME", "Produto de exemplo")

# Seletor CSS do elemento que contem o preco na pagina do produto.
# Precisa ser ajustado de acordo com o site monitorado (ver README).
PRICE_SELECTOR = os.getenv("PRICE_SELECTOR", "p.price_color")

# --- Regras de monitoramento -------------------------------------------------
MIN_PRICE_DROP_PERCENT = float(os.getenv("MIN_PRICE_DROP_PERCENT", "10"))
CHECK_INTERVAL_HOURS = float(os.getenv("CHECK_INTERVAL_HOURS", "1"))

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

# --- Armazenamento (Excel, mantido como referencia/alternativa) -------------
DATA_DIR = BASE_DIR / "data"
EXCEL_PATH = DATA_DIR / "price_history.xlsx"

# --- Armazenamento (Supabase) -------------------------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_PUBLISHABLE_KEY = os.getenv("SUPABASE_PUBLISHABLE_KEY", "")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY", "")
