"""Responsavel por persistir o historico de precos em um arquivo Excel.

Nenhuma outra parte do projeto deve ler ou escrever o .xlsx diretamente --
tudo passa por esta classe, para que a forma de armazenamento possa ser
trocada no futuro (ex.: SQLite) sem afetar o resto do codigo.
"""

from datetime import datetime
from pathlib import Path

import pandas as pd

COLUMNS = ["Data/Hora", "Produto", "URL", "Preco", "Variacao %"]


class ExcelStorage:
    def __init__(self, file_path: Path):
        self.file_path = Path(file_path)
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            pd.DataFrame(columns=COLUMNS).to_excel(self.file_path, index=False)

    def get_last_price(self, product_name: str) -> float | None:
        """Retorna o ultimo preco registrado para o produto, ou None se nao houver historico."""
        df = pd.read_excel(self.file_path)
        registros = df[df["Produto"] == product_name]
        if registros.empty:
            return None
        return float(registros.iloc[-1]["Preco"])

    def append_record(
        self,
        product_name: str,
        url: str,
        price: float,
        variation_percent: float | None,
    ) -> None:
        """Adiciona um novo registro ao historico, preservando os anteriores."""
        df = pd.read_excel(self.file_path)
        novo_registro = pd.DataFrame(
            [
                {
                    "Data/Hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                    "Produto": product_name,
                    "URL": url,
                    "Preco": price,
                    "Variacao %": (
                        "-" if variation_percent is None else round(variation_percent, 2)
                    ),
                }
            ]
        )
        df = pd.concat([df, novo_registro], ignore_index=True)
        df.to_excel(self.file_path, index=False)
