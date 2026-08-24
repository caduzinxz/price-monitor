"""Envia o alerta por todos os canais configurados (e-mail, Telegram, ...).

Por que essa camada existe: sem ela, o main.py teria um bloco try/except para
cada canal, e adicionar um novo canal exigiria mexer no main.py de novo. Aqui,
o main.py so monta a lista de canais e manda enviar -- quem cuida de "tentar
todos, mesmo que um falhe" e esta classe.

Isso e polimorfismo na pratica: NotificationService nao sabe se o canal e
e-mail ou Telegram. Basta que o objeto tenha um metodo send_price_alert com a
mesma assinatura.
"""

import logging

logger = logging.getLogger(__name__)


class NotificationError(Exception):
    """Falha ao enviar uma notificacao.

    Cada canal define sua propria excecao herdando desta, o que permite ao
    NotificationService capturar as falhas de qualquer canal com um unico
    except, sem conhecer os detalhes de SMTP ou da API do Telegram.
    """


class NotificationService:
    def __init__(self, channels: list):
        self.channels = channels

    def send_price_alert(self, **kwargs) -> None:
        """Envia por todos os canais. A falha de um nao impede os demais.

        Se o Telegram estiver fora do ar, o e-mail ainda deve sair -- perder
        as duas notificacoes por causa de um canal quebrado seria pior.
        """
        if not self.channels:
            logger.warning("Nenhum canal de notificacao configurado; alerta nao enviado.")
            return

        for channel in self.channels:
            nome_do_canal = type(channel).__name__
            try:
                channel.send_price_alert(**kwargs)
            except NotificationError as exc:
                logger.error("Falha ao notificar via %s: %s", nome_do_canal, exc)
