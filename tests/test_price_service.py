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


class TestMenorPrecoHistorico(unittest.TestCase):
    def setUp(self):
        self.service = PriceService(min_drop_percent=10)

    def test_detecta_novo_recorde(self):
        resultado = self.service.evaluate(
            current_price=900, previous_price=950, historic_min_price=920
        )
        self.assertTrue(resultado.is_historic_low)

    def test_preco_acima_do_recorde_nao_e_recorde(self):
        resultado = self.service.evaluate(
            current_price=930, previous_price=950, historic_min_price=920
        )
        self.assertFalse(resultado.is_historic_low)

    def test_preco_igual_ao_recorde_nao_conta_como_novo_recorde(self):
        # Evita alertar de hora em hora enquanto o preco fica parado no minimo.
        resultado = self.service.evaluate(
            current_price=920, previous_price=950, historic_min_price=920
        )
        self.assertFalse(resultado.is_historic_low)

    def test_primeira_verificacao_nao_e_recorde(self):
        resultado = self.service.evaluate(
            current_price=1000, previous_price=None, historic_min_price=None
        )
        self.assertFalse(resultado.is_historic_low)

    def test_recorde_alerta_mesmo_com_queda_pequena(self):
        # Queda de apenas 2%, abaixo do limite de 10%, mas e o menor preco ja visto.
        resultado = self.service.evaluate(
            current_price=931, previous_price=950, historic_min_price=940
        )
        self.assertTrue(resultado.is_historic_low)
        self.assertTrue(resultado.should_alert)
        self.assertLess(resultado.variation_percent, 10)

    def test_recorde_nao_alerta_quando_desativado(self):
        service = PriceService(min_drop_percent=10, alert_on_historic_low=False)
        resultado = service.evaluate(
            current_price=931, previous_price=950, historic_min_price=940
        )
        self.assertTrue(resultado.is_historic_low)
        self.assertFalse(resultado.should_alert)

    def test_queda_grande_ainda_alerta_sem_ser_recorde(self):
        resultado = self.service.evaluate(
            current_price=850, previous_price=1000, historic_min_price=800
        )
        self.assertFalse(resultado.is_historic_low)
        self.assertTrue(resultado.should_alert)

    def test_preco_que_sobe_nunca_e_recorde(self):
        resultado = self.service.evaluate(
            current_price=1100, previous_price=1000, historic_min_price=900
        )
        self.assertFalse(resultado.is_historic_low)
        self.assertFalse(resultado.should_alert)


if __name__ == "__main__":
    unittest.main()
