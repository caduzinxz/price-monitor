"""Carrega a lista de produtos monitorados a partir de um arquivo JSON.

Por que um JSON e nao o .env: o .env so aceita pares "chave=valor" simples,
entao cadastrar varios produtos exigiria gambiarras (PRODUCT_URL_2, _3...).
JSON representa listas naturalmente. De quebra, isso separa o que e segredo
(fica no .env) do que e apenas configuracao (fica aqui, e pode ir para o Git).
"""

import json
from dataclasses import dataclass
from pathlib import Path

REQUIRED_FIELDS = ("name", "url", "price_selector")


class ProductConfigError(Exception):
    """Arquivo de produtos ausente, mal formatado ou com campos faltando."""


@dataclass
class Product:
    """Um produto monitorado.

    Usar uma dataclass em vez de um dicionario solto deixa claro quais campos
    existem e permite acessar como produto.name em vez de produto["name"],
    alem de gerar um erro imediato se um campo obrigatorio faltar.
    """

    name: str
    url: str
    price_selector: str


def load_products(file_path: Path) -> list[Product]:
    """Le o arquivo JSON e devolve a lista de produtos ja validada.

    Validar aqui (e nao no meio do monitoramento) faz o programa falhar cedo,
    com uma mensagem clara, em vez de quebrar so daqui a uma hora ao tentar
    acessar um campo inexistente.
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise ProductConfigError(
            f"Arquivo de produtos nao encontrado: {file_path}. "
            "Copie products.example.json para products.json."
        )

    try:
        dados = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ProductConfigError(f"JSON invalido em {file_path.name}: {exc}") from exc

    if not isinstance(dados, list):
        raise ProductConfigError(
            f"{file_path.name} deve conter uma lista de produtos (comecando com '[')."
        )
    if not dados:
        raise ProductConfigError(f"{file_path.name} nao tem nenhum produto cadastrado.")

    produtos = []
    for indice, item in enumerate(dados, start=1):
        if not isinstance(item, dict):
            raise ProductConfigError(f"O produto #{indice} deveria ser um objeto JSON.")

        faltando = [campo for campo in REQUIRED_FIELDS if not str(item.get(campo, "")).strip()]
        if faltando:
            raise ProductConfigError(
                f"O produto #{indice} esta sem o(s) campo(s): {', '.join(faltando)}."
            )

        produtos.append(
            Product(
                name=item["name"].strip(),
                url=item["url"].strip(),
                price_selector=item["price_selector"].strip(),
            )
        )

    nomes = [produto.name for produto in produtos]
    duplicados = {nome for nome in nomes if nomes.count(nome) > 1}
    if duplicados:
        # Nomes duplicados quebrariam o historico: o Supabase guarda os precos
        # por nome de produto, entao dois produtos com o mesmo nome misturariam
        # seus historicos e gerariam variacoes sem sentido.
        raise ProductConfigError(
            f"Ha produtos com nomes repetidos: {', '.join(sorted(duplicados))}. "
            "Cada produto precisa de um nome unico."
        )

    return produtos
