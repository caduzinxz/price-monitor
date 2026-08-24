"""Ponto de entrada do projeto.

    python run.py           monitora continuamente (Ctrl+C para parar)
    python run.py --once    executa uma unica verificacao e encerra
    python run.py --demo    demonstra o fluxo completo, sem configuracao
"""

import argparse

from app.demo import run_demo
from app.main import main


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Monitor de precos de e-commerce.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "exemplos:\n"
            "  python run.py           monitora de hora em hora\n"
            "  python run.py --once    verifica uma vez e encerra\n"
            "  python run.py --demo    mostra tudo funcionando em ~20s\n"
        ),
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--once",
        action="store_true",
        help="executa uma unica verificacao e encerra, em vez de ficar em loop",
    )
    group.add_argument(
        "--demo",
        action="store_true",
        help="demonstra scraping, historico e alerta sem exigir credenciais",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.demo:
        run_demo()
    else:
        main(run_once=args.once)
