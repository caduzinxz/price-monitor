"""Funcoes utilitarias puras (sem efeitos colaterais), reaproveitadas por outros modulos."""

import re


def parse_price(raw_price: str) -> float:
    """Converte um preco em texto (ex.: "R$ 1.299,90") para float (1299.90).

    Regras aplicadas:
    - remove simbolos de moeda, letras e espacos, mantendo apenas digitos, '.' e ','.
    - se houver '.' e ',' ao mesmo tempo, o ultimo caractere entre eles e o separador
      decimal; o outro e tratado como separador de milhar e removido.
    - se houver apenas um dos dois, ele e tratado como separador decimal.
    """
    if raw_price is None:
        raise ValueError("Preco vazio: nao foi possivel converter.")

    cleaned = re.sub(r"[^0-9.,]", "", raw_price).strip()
    if not cleaned:
        raise ValueError(f"Preco em formato inesperado: {raw_price!r}")

    has_dot = "." in cleaned
    has_comma = "," in cleaned

    if has_dot and has_comma:
        comma_is_decimal = cleaned.rfind(",") > cleaned.rfind(".")
        if comma_is_decimal:
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif has_comma:
        cleaned = cleaned.replace(",", ".")
    # se so tem ponto (ou nenhum separador), ja esta no formato que float() entende

    try:
        return round(float(cleaned), 2)
    except ValueError as exc:
        raise ValueError(f"Preco em formato inesperado: {raw_price!r}") from exc


def format_price_brl(value: float) -> str:
    """Formata um float como preco em reais: 1299.9 -> 'R$ 1.299,90'."""
    text = f"{value:,.2f}"
    # Troca os separadores para o padrao brasileiro, usando "X" como marcador
    # temporario para nao sobrescrever o que acabou de ser trocado.
    text = text.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {text}"
