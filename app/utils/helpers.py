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

    limpo = re.sub(r"[^0-9.,]", "", raw_price).strip()
    if not limpo:
        raise ValueError(f"Preco em formato inesperado: {raw_price!r}")

    tem_ponto = "." in limpo
    tem_virgula = "," in limpo

    if tem_ponto and tem_virgula:
        se_decimal_e_virgula = limpo.rfind(",") > limpo.rfind(".")
        if se_decimal_e_virgula:
            limpo = limpo.replace(".", "").replace(",", ".")
        else:
            limpo = limpo.replace(",", "")
    elif tem_virgula:
        limpo = limpo.replace(",", ".")
    # se so tem ponto (ou nenhum separador), ja esta no formato que float() entende

    try:
        return round(float(limpo), 2)
    except ValueError as exc:
        raise ValueError(f"Preco em formato inesperado: {raw_price!r}") from exc


def format_price_brl(valor: float) -> str:
    """Formata um float como preco em reais: 1299.9 -> 'R$ 1.299,90'."""
    texto = f"{valor:,.2f}"
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"
