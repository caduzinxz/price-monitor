"""Testes do PriceScraper sem abrir navegador.

A parte que fala com o Playwright (_extract_raw_price) e substituida por um
valor fixo. O que sobra -- converter o texto da pagina em numero e transformar
formato inesperado em PriceScraperError -- e justamente o contrato da classe,
e pode ser testado sem rede nem browser.
"""

import unittest

from app.scraper.price_scraper import PriceScraper, PriceScraperError


class ScraperComTextoFixo(PriceScraper):
    """Devolve um texto pre-definido no lugar de acessar a pagina real."""

    def __init__(self, raw_text):
        super().__init__()
        self.raw_text = raw_text

    def _extract_raw_price(self, url, price_selector):
        return self.raw_text


class TestPriceScraper(unittest.TestCase):
    def fetch(self, raw_text):
        return ScraperComTextoFixo(raw_text).fetch_price("https://exemplo.com", ".preco")

    def test_converte_preco_em_reais(self):
        self.assertEqual(self.fetch("R$ 1.299,90"), 1299.90)

    def test_converte_preco_com_ponto_decimal(self):
        self.assertEqual(self.fetch("51.77"), 51.77)

    def test_ignora_texto_em_volta_do_valor(self):
        self.assertEqual(self.fetch("Por apenas R$ 89,90 a vista"), 89.90)

    def test_texto_sem_numero_vira_erro_do_scraper(self):
        # Importante: o erro sai como PriceScraperError, e nao ValueError, para
        # que o main.py trate falha de scraping de um jeito so.
        with self.assertRaises(PriceScraperError):
            self.fetch("Produto indisponivel")

    def test_texto_vazio_vira_erro_do_scraper(self):
        with self.assertRaises(PriceScraperError):
            self.fetch("")


if __name__ == "__main__":
    unittest.main()
