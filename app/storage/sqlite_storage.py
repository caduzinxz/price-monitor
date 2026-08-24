"""Armazena o historico de precos num arquivo SQLite local.

E o backend padrao do projeto porque nao exige nenhuma conta, servidor ou
configuracao: o sqlite3 vem na biblioteca padrao do Python e o banco e um
unico arquivo criado automaticamente. Assim, `python run.py` funciona logo
apos clonar o repositorio.

Expõe exatamente os mesmos metodos do SupabaseStorage, entao trocar de um para
o outro nao exige mudanca nenhuma em quem usa.
"""

import sqlite3
from datetime import datetime
from pathlib import Path

from app.storage.errors import StorageError

TABLE_NAME = "price_history"

CREATE_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_hora TEXT NOT NULL,
    produto TEXT NOT NULL,
    url TEXT NOT NULL,
    preco REAL NOT NULL,
    variacao_percent REAL
)
"""

CREATE_INDEX_SQL = f"""
CREATE INDEX IF NOT EXISTS idx_produto_data
    ON {TABLE_NAME} (produto, data_hora DESC)
"""


class SQLiteStorage:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._create_schema()

    def _connect(self) -> sqlite3.Connection:
        """Abre uma conexao nova a cada operacao.

        Conexoes do sqlite3 nao podem ser compartilhadas entre threads por
        padrao, e as operacoes aqui sao curtas e esparsas (uma por hora), entao
        abrir e fechar e mais simples e seguro que manter uma conexao viva.
        """
        return sqlite3.connect(self.db_path, timeout=10)

    def _create_schema(self) -> None:
        try:
            with self._connect() as connection:
                connection.execute(CREATE_TABLE_SQL)
                connection.execute(CREATE_INDEX_SQL)
        except sqlite3.Error as exc:
            raise StorageError(f"Falha ao preparar o banco {self.db_path}: {exc}") from exc

    def get_last_price(self, product_name: str) -> float | None:
        """Retorna o ultimo preco registrado, ou None se nao houver historico."""
        row = self._query_one(
            f"SELECT preco FROM {TABLE_NAME} WHERE produto = ? ORDER BY id DESC LIMIT 1",
            (product_name,),
            action=f"ler o ultimo preco de {product_name!r}",
        )
        return None if row is None else float(row[0])

    def get_min_price(self, product_name: str) -> float | None:
        """Retorna o menor preco ja registrado, ou None se nao houver historico."""
        row = self._query_one(
            f"SELECT MIN(preco) FROM {TABLE_NAME} WHERE produto = ?",
            (product_name,),
            action=f"ler o menor preco de {product_name!r}",
        )
        # MIN() sempre devolve uma linha; sem registros, o valor vem como NULL.
        if row is None or row[0] is None:
            return None
        return float(row[0])

    def append_record(
        self,
        product_name: str,
        url: str,
        price: float,
        variation_percent: float | None,
        recorded_at: datetime | None = None,
    ) -> None:
        """Adiciona um novo registro, preservando os anteriores.

        recorded_at existe para que o modo de demonstracao consiga semear um
        historico com datas passadas; no uso normal fica None e vale "agora".
        """
        timestamp = (recorded_at or datetime.now()).isoformat(timespec="seconds")
        try:
            with self._connect() as connection:
                connection.execute(
                    f"INSERT INTO {TABLE_NAME} "
                    "(data_hora, produto, url, preco, variacao_percent) VALUES (?, ?, ?, ?, ?)",
                    (timestamp, product_name, url, price, variation_percent),
                )
        except sqlite3.Error as exc:
            raise StorageError(f"Falha ao gravar o preco de {product_name!r}: {exc}") from exc

    def _query_one(self, sql: str, params: tuple, action: str):
        try:
            with self._connect() as connection:
                return connection.execute(sql, params).fetchone()
        except sqlite3.Error as exc:
            raise StorageError(f"Falha ao {action}: {exc}") from exc
