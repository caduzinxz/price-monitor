"""Testes do backend SQLite.

Usam um arquivo temporario, entao rodam de verdade contra o sqlite3 (nao ha
dublê aqui) sem sujar nada e sem depender de rede.
"""

import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from app.storage.sqlite_storage import SQLiteStorage


class TestSQLiteStorage(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.storage = SQLiteStorage(Path(self.temp_dir) / "test.db")

    def test_banco_novo_nao_tem_historico(self):
        self.assertIsNone(self.storage.get_last_price("Produto A"))
        self.assertIsNone(self.storage.get_min_price("Produto A"))

    def test_grava_e_le_o_ultimo_preco(self):
        self.storage.append_record("Produto A", "https://a.com", 99.90, None)
        self.assertEqual(self.storage.get_last_price("Produto A"), 99.90)

    def test_ultimo_preco_e_o_mais_recente(self):
        for price in (100.0, 90.0, 95.0):
            self.storage.append_record("Produto A", "https://a.com", price, None)
        self.assertEqual(self.storage.get_last_price("Produto A"), 95.0)

    def test_menor_preco_considera_todo_o_historico(self):
        for price in (100.0, 90.0, 95.0):
            self.storage.append_record("Produto A", "https://a.com", price, None)
        self.assertEqual(self.storage.get_min_price("Produto A"), 90.0)

    def test_produtos_tem_historicos_separados(self):
        self.storage.append_record("Produto A", "https://a.com", 100.0, None)
        self.storage.append_record("Produto B", "https://b.com", 50.0, None)

        self.assertEqual(self.storage.get_last_price("Produto A"), 100.0)
        self.assertEqual(self.storage.get_last_price("Produto B"), 50.0)
        self.assertEqual(self.storage.get_min_price("Produto A"), 100.0)

    def test_historico_sobrevive_a_reabertura_do_banco(self):
        db_path = Path(self.temp_dir) / "persistente.db"
        SQLiteStorage(db_path).append_record("Produto A", "https://a.com", 77.7, None)

        # Uma instancia nova, como acontece ao reiniciar o programa.
        self.assertEqual(SQLiteStorage(db_path).get_last_price("Produto A"), 77.7)

    def test_aceita_data_personalizada(self):
        ontem = datetime.now() - timedelta(days=1)
        self.storage.append_record("Produto A", "https://a.com", 10.0, None, recorded_at=ontem)
        self.assertEqual(self.storage.get_last_price("Produto A"), 10.0)

    def test_grava_variacao_nula_sem_erro(self):
        self.storage.append_record("Produto A", "https://a.com", 10.0, None)
        self.storage.append_record("Produto A", "https://a.com", 9.0, 10.0)
        self.assertEqual(self.storage.get_last_price("Produto A"), 9.0)


if __name__ == "__main__":
    unittest.main()
