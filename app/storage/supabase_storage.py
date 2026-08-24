"""Responsavel por persistir o historico de precos no Supabase (Postgres).

Mesma interface publica do ExcelStorage (get_last_price, append_record), para
que o main.py nao precise saber qual backend de armazenamento esta sendo
usado -- apenas troca-se a classe instanciada.
"""

from supabase import Client, create_client

TABLE_NAME = "price_history"


class SupabaseStorage:
    def __init__(self, url: str, secret_key: str):
        self.client: Client = create_client(url, secret_key)

    def get_last_price(self, product_name: str) -> float | None:
        response = (
            self.client.table(TABLE_NAME)
            .select("preco")
            .eq("produto", product_name)
            .order("data_hora", desc=True)
            .limit(1)
            .execute()
        )
        if not response.data:
            return None
        return float(response.data[0]["preco"])

    def get_min_price(self, product_name: str) -> float | None:
        """Retorna o menor preco ja registrado para o produto, ou None se nao
        houver historico.

        Ordenar por preco e pegar o primeiro deixa o trabalho com o banco de
        dados, que faz isso de forma eficiente -- melhor do que baixar todo o
        historico e calcular o minimo em Python.
        """
        response = (
            self.client.table(TABLE_NAME)
            .select("preco")
            .eq("produto", product_name)
            .order("preco", desc=False)
            .limit(1)
            .execute()
        )
        if not response.data:
            return None
        return float(response.data[0]["preco"])

    def append_record(
        self,
        product_name: str,
        url: str,
        price: float,
        variation_percent: float | None,
    ) -> None:
        self.client.table(TABLE_NAME).insert(
            {
                "produto": product_name,
                "url": url,
                "preco": price,
                "variacao_percent": variation_percent,
            }
        ).execute()
