"""Modo de demonstracao: mostra o projeto inteiro funcionando em ~20 segundos,
sem exigir nenhuma conta, credencial ou configuracao.

Motivacao: no uso normal os alertas dependem de o preco realmente cair, o que
pode levar dias. Quem esta avaliando o projeto precisa ver o recurso principal
funcionando agora. A demo usa um banco SQLite separado e descartavel e roda em
duas partes:

1. um produto REAL, buscado com Playwright, provando que o scraping funciona;
2. um produto SIMULADO, com historico semeado e uma queda forcada, provando o
   calculo de variacao, a deteccao de menor preco historico e o alerta.

Os dois usam exatamente o mesmo check_product() que roda em producao -- nada
aqui e uma reimplementacao "de mentira" do fluxo.
"""

import logging
from datetime import datetime, timedelta

from app.config import settings
from app.config.products import Product, ProductConfigError, load_products
from app.main import build_notification_channels, check_product, setup_logging
from app.scraper.price_scraper import PriceScraper, PriceScraperError
from app.services.notification_service import NotificationService
from app.services.price_service import PriceService
from app.storage.errors import StorageError
from app.storage.sqlite_storage import SQLiteStorage
from app.utils.helpers import format_price_brl

logger = logging.getLogger(__name__)

DEMO_DB_NAME = "demo.db"

SIMULATED_PRODUCT = Product(
    name="Notebook Gamer (simulado)",
    url="https://exemplo.com/notebook-gamer",
    price_selector="span.preco",
)
SEEDED_PRICES = (3500.00, 3400.00, 3299.00)
DROPPED_PRICE = 2799.00


class FixedPriceScraper(PriceScraper):
    """Devolve um preco definido por nos, no lugar de acessar um site.

    Usado so no produto simulado: o restante do fluxo (comparacao, gravacao,
    decisao de alerta, envio) e o codigo real, sem desvio.
    """

    def __init__(self, price: float):
        super().__init__()
        self.price = price

    def fetch_price(self, url: str, price_selector: str) -> float:
        return self.price


def run_demo() -> None:
    setup_logging()

    logger.info("=" * 64)
    logger.info("  MODO DEMONSTRACAO")
    logger.info("  Banco temporario, sem credenciais, sem contas externas.")
    logger.info("=" * 64)

    demo_db = settings.DATA_DIR / DEMO_DB_NAME
    if demo_db.exists():
        demo_db.unlink()  # comeca sempre do zero

    try:
        storage = SQLiteStorage(demo_db)
    except StorageError as exc:
        logger.error("Nao foi possivel preparar a demonstracao: %s", exc)
        return

    price_service = PriceService(min_drop_percent=settings.MIN_PRICE_DROP_PERCENT)
    notifier = NotificationService(build_notification_channels())

    # A demo foi pedida explicitamente, entao o interruptor global de alertas
    # nao deve escondê-la. Restaurado no final para nao afetar o resto.
    alerts_were_enabled = settings.ALERTS_ENABLED
    settings.ALERTS_ENABLED = True
    try:
        _step_real_scrape(storage, price_service, notifier)
        _step_seed_history(storage)
        _step_simulate_drop(storage, price_service, notifier)
    finally:
        settings.ALERTS_ENABLED = alerts_were_enabled

    logger.info("")
    logger.info("Demonstracao concluida. Banco temporario: %s", demo_db)
    logger.info("Para monitorar de verdade: python run.py")


def _step_real_scrape(storage, price_service, notifier) -> None:
    """Parte 1: busca um preco real na internet, com Playwright."""
    logger.info("")
    logger.info("[1/3] Buscando um preco REAL com o Playwright...")

    try:
        products = load_products(settings.PRODUCTS_FILE)
    except ProductConfigError as exc:
        logger.warning("Nao foi possivel ler os produtos (%s). Pulando esta etapa.", exc)
        return

    try:
        check_product(products[0], PriceScraper(), storage, price_service, notifier)
    except PriceScraperError as exc:
        logger.warning("Site indisponivel (%s). A simulacao a seguir nao depende dele.", exc)
    except StorageError as exc:
        logger.error("Falha no armazenamento: %s", exc)


def _step_seed_history(storage) -> None:
    """Parte 2: cria um historico passado para haver o que comparar."""
    logger.info("")
    logger.info("[2/3] Semeando o historico de '%s'...", SIMULATED_PRODUCT.name)

    total = len(SEEDED_PRICES)
    for position, price in enumerate(SEEDED_PRICES, start=1):
        recorded_at = datetime.now() - timedelta(hours=total - position + 1)
        storage.append_record(
            product_name=SIMULATED_PRODUCT.name,
            url=SIMULATED_PRODUCT.url,
            price=price,
            variation_percent=None,
            recorded_at=recorded_at,
        )
        logger.info("      %s -> %s", recorded_at.strftime("%H:%M"), format_price_brl(price))


def _step_simulate_drop(storage, price_service, notifier) -> None:
    """Parte 3: forca uma queda e deixa o codigo real decidir o alerta."""
    drop = (SEEDED_PRICES[-1] - DROPPED_PRICE) / SEEDED_PRICES[-1] * 100

    logger.info("")
    logger.info(
        "[3/3] Nova verificacao encontra %s (queda de %.2f%% e menor valor ja visto)...",
        format_price_brl(DROPPED_PRICE),
        drop,
    )
    logger.info("")

    try:
        check_product(
            SIMULATED_PRODUCT,
            FixedPriceScraper(DROPPED_PRICE),
            storage,
            price_service,
            notifier,
        )
    except (PriceScraperError, StorageError) as exc:
        logger.error("Falha na simulacao: %s", exc)
