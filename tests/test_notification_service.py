"""Testes do NotificationService.

Usa canais falsos (dublês) em vez de e-mail/Telegram reais: o que esta sendo
testado e a logica de "enviar por todos e sobreviver a falhas", nao a API de
cada servico.
"""

import unittest

from app.services.notification_service import NotificationError, NotificationService


class CanalFalso:
    """Registra as chamadas recebidas, para o teste inspecionar depois."""

    def __init__(self):
        self.chamadas = []

    def send_price_alert(self, **kwargs):
        self.chamadas.append(kwargs)


class CanalQueFalha:
    def send_price_alert(self, **kwargs):
        raise NotificationError("canal indisponivel")


class TestNotificationService(unittest.TestCase):
    def test_envia_por_todos_os_canais(self):
        canal_a, canal_b = CanalFalso(), CanalFalso()
        NotificationService([canal_a, canal_b]).send_price_alert(product_name="X")

        self.assertEqual(len(canal_a.chamadas), 1)
        self.assertEqual(len(canal_b.chamadas), 1)

    def test_repassa_os_dados_do_alerta(self):
        canal = CanalFalso()
        NotificationService([canal]).send_price_alert(product_name="X", current_price=99.9)

        self.assertEqual(canal.chamadas[0]["product_name"], "X")
        self.assertEqual(canal.chamadas[0]["current_price"], 99.9)

    def test_falha_de_um_canal_nao_impede_os_outros(self):
        canal_bom = CanalFalso()
        servico = NotificationService([CanalQueFalha(), canal_bom])

        with self.assertLogs("app.services.notification_service", level="ERROR"):
            servico.send_price_alert(product_name="X")

        self.assertEqual(len(canal_bom.chamadas), 1)

    def test_lista_vazia_apenas_avisa(self):
        with self.assertLogs("app.services.notification_service", level="WARNING"):
            NotificationService([]).send_price_alert(product_name="X")


if __name__ == "__main__":
    unittest.main()
