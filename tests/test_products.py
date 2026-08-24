"""Testes do carregador de produtos (app/config/products.py).

Usa arquivos temporarios para nao depender do products.json real do projeto.
"""

import json
import tempfile
import unittest
from pathlib import Path

from app.config.products import ProductConfigError, load_products


class TestLoadProducts(unittest.TestCase):
    def escrever_json(self, conteudo) -> Path:
        """Cria um arquivo JSON temporario e devolve o caminho."""
        pasta = tempfile.mkdtemp()
        caminho = Path(pasta) / "products.json"
        if isinstance(conteudo, str):
            caminho.write_text(conteudo, encoding="utf-8")
        else:
            caminho.write_text(json.dumps(conteudo), encoding="utf-8")
        return caminho

    def test_carrega_lista_de_produtos(self):
        caminho = self.escrever_json(
            [
                {"name": "Produto A", "url": "https://a.com", "price_selector": ".preco"},
                {"name": "Produto B", "url": "https://b.com", "price_selector": "#valor"},
            ]
        )
        produtos = load_products(caminho)
        self.assertEqual(len(produtos), 2)
        self.assertEqual(produtos[0].name, "Produto A")
        self.assertEqual(produtos[1].price_selector, "#valor")

    def test_remove_espacos_em_volta_dos_valores(self):
        caminho = self.escrever_json(
            [{"name": "  Produto A  ", "url": " https://a.com ", "price_selector": " .preco "}]
        )
        produto = load_products(caminho)[0]
        self.assertEqual(produto.name, "Produto A")
        self.assertEqual(produto.url, "https://a.com")

    def test_erro_quando_arquivo_nao_existe(self):
        with self.assertRaises(ProductConfigError):
            load_products(Path("caminho/que/nao/existe.json"))

    def test_erro_quando_json_e_invalido(self):
        caminho = self.escrever_json("{isso nao e json valido")
        with self.assertRaises(ProductConfigError):
            load_products(caminho)

    def test_erro_quando_lista_esta_vazia(self):
        caminho = self.escrever_json([])
        with self.assertRaises(ProductConfigError):
            load_products(caminho)

    def test_erro_quando_falta_campo_obrigatorio(self):
        caminho = self.escrever_json([{"name": "Produto A", "url": "https://a.com"}])
        with self.assertRaises(ProductConfigError) as contexto:
            load_products(caminho)
        self.assertIn("price_selector", str(contexto.exception))

    def test_erro_quando_campo_esta_vazio(self):
        caminho = self.escrever_json(
            [{"name": "Produto A", "url": "", "price_selector": ".preco"}]
        )
        with self.assertRaises(ProductConfigError) as contexto:
            load_products(caminho)
        self.assertIn("url", str(contexto.exception))

    def test_erro_quando_ha_nomes_duplicados(self):
        caminho = self.escrever_json(
            [
                {"name": "Produto A", "url": "https://a.com", "price_selector": ".preco"},
                {"name": "Produto A", "url": "https://b.com", "price_selector": ".preco"},
            ]
        )
        with self.assertRaises(ProductConfigError) as contexto:
            load_products(caminho)
        self.assertIn("Produto A", str(contexto.exception))


if __name__ == "__main__":
    unittest.main()
