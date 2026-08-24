"""Excecao compartilhada pelos backends de armazenamento.

Fica num modulo proprio para que SQLite e Supabase possam levantar o mesmo
erro sem um importar o outro -- e para que quem chama trate as duas
implementacoes de forma identica.
"""


class StorageError(Exception):
    """Falha ao ler ou gravar o historico de precos.

    Existe para que o resto do projeto nao precise conhecer as excecoes
    especificas de cada backend (sqlite3, PostgREST, rede). Quem chama trata
    StorageError e pronto.
    """
