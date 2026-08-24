"""Testes da logica de negocio (price_service) e da conversao de preco (helpers).

Nao dependem de rede, navegador ou arquivos -- por isso rodam rapido e nao
precisam de Playwright instalado.
"""

import unittest

from app.services.price_service import PriceService
from app.utils.helpers import parse_price


class TestParsePrice(unittest.TestCase):
    def test_preco_com_simbolo_e_separadores_br(self):
        self.assertEqual(parse_price("R$ 1.299,90"), 1299.90)

    def test_preco_sem_simbolo_de_moeda(self):
        self.assertEqual(parse_price("850"), 850.0)

    def test_preco_com_espacos_extras(self):
        self.assertEqual(parse_price("  R$   999,90  "), 999.90)

    def test_preco_com_ponto_decimal(self):
        self.assertEqual(parse_price("51.77"), 51.77)

    def test_preco_invalido_levanta_erro(self):
        with self.assertRaises(ValueError):
            parse_price("indisponivel")


class TestPriceService(unittest.TestCase):
    def setUp(self):
        self.service = PriceService(min_drop_percent=10)

    def test_calcula_queda_de_preco(self):
        variacao = self.service.calculate_variation_percent(previous_price=1000, current_price=850)
        self.assertAlmostEqual(variacao, 15.0)

    def test_calcula_aumento_de_preco_como_variacao_negativa(self):
        variacao = self.service.calculate_variation_percent(previous_price=1000, current_price=1100)
        self.assertAlmostEqual(variacao, -10.0)

    def test_alerta_quando_queda_atinge_o_minimo(self):
        resultado = self.service.evaluate(current_price=890, previous_price=1000)
        self.assertTrue(resultado.should_alert)

    def test_nao_alerta_quando_queda_e_menor_que_o_minimo(self):
        resultado = self.service.evaluate(current_price=950, previous_price=1000)
        self.assertFalse(resultado.should_alert)

    def test_nao_alerta_quando_preco_sobe(self):
        resultado = self.service.evaluate(current_price=1100, previous_price=1000)
        self.assertFalse(resultado.should_alert)

    def test_nao_alerta_sem_historico_anterior(self):
        resultado = self.service.evaluate(current_price=1000, previous_price=None)
        self.assertFalse(resultado.should_alert)
        self.assertIsNone(resultado.variation_percent)


if __name__ == "__main__":
    unittest.main()
