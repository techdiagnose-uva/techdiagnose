import sys

from techdiagnose.base_conhecimento import carregar_base, ErroBaseConhecimento
from techdiagnose.estatisticas import carregar_historico, ErroHistorico
from techdiagnose.interface_console import executar


def main():
    # garante os acentos no terminal do Windows
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdin.reconfigure(encoding="utf-8")

    try:
        regras, perguntas = carregar_base()
    except ErroBaseConhecimento as erro:
        print(f"Não foi possível carregar a base de conhecimento: {erro}")
        return 1

    try:
        atendimentos = carregar_historico()
    except ErroHistorico as erro:
        print(f"Aviso: histórico indisponível ({erro}). Seguindo sem estatísticas.")
        atendimentos = None

    try:
        executar(regras, perguntas, atendimentos)
    except (KeyboardInterrupt, EOFError):
        # Ctrl+C ou fim da entrada: sai sem mostrar erro do Python
        print("\n\nAtendimento encerrado. Até logo!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
