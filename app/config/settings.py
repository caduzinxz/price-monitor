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
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_TO = os.getenv("EMAIL_TO", "")

# --- Armazenamento -----------------------------------------------------------
DATA_DIR = BASE_DIR / "data"
EXCEL_PATH = DATA_DIR / "price_history.xlsx"
