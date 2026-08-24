"""Testes de resiliencia do ciclo de monitoramento.

Garantem que uma falha isolada (site fora do ar, banco indisponivel) nao
derruba o programa inteiro nem impede a verificacao dos demais produtos.
"""

import logging
import unittest

from app.config import settings
from app.config.products import Product
from app.main import run_check_cycle
from app.scraper.price_scraper import PriceScraperError
from app.services.notification_service import NotificationService
from app.services.price_service import PriceService
from app.storage.supabase_storage import StorageError


class FakeScraper:
    def __init__(self, price=100.0, error=None):
        self.price = price
        self.error = error
        self.calls = 0

    def fetch_price(self, url, price_selector):
        self.calls += 1
        if self.error:
            raise self.error
        return self.price


class FakeStorage:
    def __init__(self, error=None):
        self.error = error
        self.records = []

    def get_last_price(self, product_name):
        if self.error:
            raise self.error
        return 110.0

    def get_min_price(self, product_name):
        if self.error:
            raise self.error
        return 105.0

    def append_record(self, **kwargs):
        if self.error:
            raise self.error
        self.records.append(kwargs)


def make_products(quantity=2):
    return [
        Product(name=f"Produto {n}", url=f"https://exemplo.com/{n}", price_selector=".preco")
        for n in range(1, quantity + 1)
    ]


class TestCicloResiliente(unittest.TestCase):
    def setUp(self):
        self.price_service = PriceService(min_drop_percent=10)
        self.notifier = NotificationService([])
        logging.disable(logging.CRITICAL)

        # Sem isso, cada teste dormiria a pausa real entre produtos. Teste que
        # espera de verdade deixa a suite lenta sem testar nada a mais.
        self.delay_original = settings.DELAY_BETWEEN_PRODUCTS_SECONDS
        settings.DELAY_BETWEEN_PRODUCTS_SECONDS = 0

    def tearDown(self):
        logging.disable(logging.NOTSET)
        settings.DELAY_BETWEEN_PRODUCTS_SECONDS = self.delay_original

    def run_cycle(self, scraper, storage, products=None):
        run_check_cycle(
            products or make_products(),
            scraper,
            storage,
            self.price_service,
            self.notifier,
        )

    def test_falha_do_banco_nao_derruba_o_ciclo(self):
        # Este era o bug: um erro do Supabase subia sem ser tratado e matava o
        # processo inteiro, parando o monitoramento ate alguem reiniciar na mao.
        storage = FakeStorage(error=StorageError("banco indisponivel"))
        scraper = FakeScraper()

        self.run_cycle(scraper, storage)  # nao deve levantar excecao

        self.assertEqual(scraper.calls, 2, "os dois produtos deveriam ter sido tentados")

    def test_falha_do_scraper_nao_derruba_o_ciclo(self):
        scraper = FakeScraper(error=PriceScraperError("site fora do ar"))
        storage = FakeStorage()

        self.run_cycle(scraper, storage)

        self.assertEqual(scraper.calls, 2)

    def test_produto_com_erro_nao_impede_os_seguintes(self):
        """So o primeiro produto falha; o segundo deve ser gravado normalmente."""

        class ScraperQueFalhaUmaVez(FakeScraper):
            def fetch_price(self, url, price_selector):
                self.calls += 1
                if self.calls == 1:
                    raise PriceScraperError("falha temporaria")
                return 100.0

        storage = FakeStorage()
        self.run_cycle(ScraperQueFalhaUmaVez(), storage)

        self.assertEqual(len(storage.records), 1)
        self.assertEqual(storage.records[0]["product_name"], "Produto 2")

    def test_ciclo_normal_grava_todos_os_produtos(self):
        storage = FakeStorage()
        self.run_cycle(FakeScraper(), storage)

        self.assertEqual(len(storage.records), 2)


if __name__ == "__main__":
    unittest.main()
