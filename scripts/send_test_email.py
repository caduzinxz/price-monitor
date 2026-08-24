"""Envia um e-mail de alerta ficticio para validar a configuracao de SMTP.

Uso (com o ambiente virtual ativado):

    python -m scripts.send_test_email

Serve para testar as credenciais do .env sem precisar esperar uma queda de
preco real acontecer. Os valores de produto/preco abaixo sao inventados --
o que esta sendo testado e a conexao com o servidor de e-mail.
"""

import logging

from app.config import settings
from app.services.email_service import EmailService, EmailServiceError


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s", datefmt="%H:%M:%S")
    logger = logging.getLogger(__name__)

    faltando = [
        nome
        for nome, valor in (
            ("EMAIL_USER", settings.EMAIL_USER),
            ("EMAIL_PASSWORD", settings.EMAIL_PASSWORD),
            ("EMAIL_TO", settings.EMAIL_TO),
        )
        if not valor or valor.startswith(("seu_", "sua_", "email_destino"))
    ]
    if faltando:
        logger.error(
            "Preencha no .env, com valores reais, a(s) variavel(is): %s", ", ".join(faltando)
        )
        return

    logger.info("Enviando e-mail de teste de %s para %s...", settings.EMAIL_USER, settings.EMAIL_TO)

    email_service = EmailService(
        host=settings.EMAIL_HOST,
        port=settings.EMAIL_PORT,
        user=settings.EMAIL_USER,
        password=settings.EMAIL_PASSWORD,
        to_address=settings.EMAIL_TO,
    )

    try:
        email_service.send_price_alert(
            product_name="[TESTE] Produto ficticio",
            previous_price=1000.00,
            current_price=850.00,
            variation_percent=15.0,
            url="https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
        )
    except EmailServiceError as exc:
        logger.error("Falhou: %s", exc)
        return

    logger.info("Enviado. Confira a caixa de entrada de %s (veja tambem o spam).", settings.EMAIL_TO)


if __name__ == "__main__":
    main()
