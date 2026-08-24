"""Responsavel por abrir o navegador via Playwright, acessar a pagina do
produto e extrair o preco. Nenhuma regra de negocio (comparacao, alerta etc.)
vive aqui -- so a extracao do dado bruto.
"""

import logging

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from app.utils.helpers import parse_price

logger = logging.getLogger(__name__)


class PriceScraperError(Exception):
    """Erro ao tentar obter o preco de um produto."""


class PriceScraper:
    """Extrai o preco de um produto a partir da sua URL.

    A URL e o seletor CSS do preco sao recebidos por parametro (nao ficam
    fixos na classe), entao o mesmo scraper serve para qualquer site: para
    trocar de e-commerce basta passar outra URL e outro seletor.
    """

    def __init__(self, headless: bool = True, timeout_ms: int = 30_000):
        self.headless = headless
        self.timeout_ms = timeout_ms

    def fetch_price(self, url: str, price_selector: str) -> float:
        raw_text = self._extract_raw_price(url, price_selector)
        try:
            return parse_price(raw_text)
        except ValueError as exc:
            raise PriceScraperError(str(exc)) from exc

    def _extract_raw_price(self, url: str, price_selector: str) -> str:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=self.headless)
            try:
                page = browser.new_page()

                try:
                    logger.debug("Acessando %s", url)
                    page.goto(url, timeout=self.timeout_ms, wait_until="domcontentloaded")
                except PlaywrightTimeoutError as exc:
                    raise PriceScraperError(f"Timeout ao acessar a pagina: {url}") from exc
                except PlaywrightError as exc:
                    raise PriceScraperError(f"Pagina indisponivel ({url}): {exc}") from exc

                try:
                    page.wait_for_selector(price_selector, timeout=self.timeout_ms)
                except PlaywrightTimeoutError as exc:
                    raise PriceScraperError(
                        f"Elemento de preco nao encontrado (seletor={price_selector!r}). "
                        "O site pode ter mudado a estrutura ou bloqueado o acesso."
                    ) from exc

                return page.locator(price_selector).first.inner_text()
            finally:
                browser.close()
