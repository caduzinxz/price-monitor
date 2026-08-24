"""Responsavel por persistir o historico de precos no Supabase (Postgres).

Nenhuma outra parte do projeto fala com o banco diretamente: tudo passa por
esta classe, para que a forma de armazenamento possa ser trocada no futuro sem
afetar o resto do codigo.
"""

from supabase import Client, create_client

from app.storage.errors import StorageError

TABLE_NAME = "price_history"


class SupabaseStorage:
    def __init__(self, url: str, secret_key: str):
        if not url or not secret_key:
            raise StorageError(
                "SUPABASE_URL e SUPABASE_SECRET_KEY precisam estar preenchidos no .env."
            )
        try:
            self.client: Client = create_client(url, secret_key)
        except Exception as exc:
            raise StorageError(f"Nao foi possivel conectar ao Supabase: {exc}") from exc

    def get_last_price(self, product_name: str) -> float | None:
        """Retorna o ultimo preco registrado, ou None se nao houver historico."""
        response = self._execute(
            lambda: self.client.table(TABLE_NAME)
            .select("preco")
            .eq("produto", product_name)
            .order("data_hora", desc=True)
            .limit(1)
            .execute(),
            acao=f"ler o ultimo preco de {product_name!r}",
        )
        if not response.data:
            return None
        return float(response.data[0]["preco"])

    def get_min_price(self, product_name: str) -> float | None:
        """Retorna o menor preco ja registrado, ou None se nao houver historico.

        Ordenar por preco e pegar o primeiro deixa o trabalho com o banco, que
        faz isso de forma eficiente -- melhor do que baixar todo o historico e
        calcular o minimo em Python.
        """
        response = self._execute(
            lambda: self.client.table(TABLE_NAME)
            .select("preco")
            .eq("produto", product_name)
            .order("preco", desc=False)
            .limit(1)
            .execute(),
            acao=f"ler o menor preco de {product_name!r}",
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
        """Adiciona um novo registro, preservando os anteriores."""
        self._execute(
            lambda: self.client.table(TABLE_NAME)
            .insert(
                {
                    "produto": product_name,
                    "url": url,
                    "preco": price,
                    "variacao_percent": variation_percent,
                }
            )
            .execute(),
            acao=f"gravar o preco de {product_name!r}",
        )

    @staticmethod
    def _execute(operacao, acao: str):
        """Executa uma operacao no banco convertendo qualquer falha em StorageError.

        O `except Exception` amplo e intencional aqui: esta e a fronteira com um
        servico externo, e as falhas possiveis sao muitas (erro da API, DNS,
        timeout, conexao recusada). O que importa para quem chama e apenas que
        a operacao falhou -- e o programa precisa sobreviver a isso, nao morrer.
        """
        try:
            return operacao()
        except Exception as exc:
            raise StorageError(f"Falha ao {acao}: {exc}") from exc
