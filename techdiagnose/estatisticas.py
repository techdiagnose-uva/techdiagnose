"""Estatísticas do histórico de atendimentos da TechFix.

Lê dados/historico_atendimentos.csv e calcula, por diagnóstico:
quantas vezes apareceu, tempo médio de atendimento e custo médio.
"""
import csv
from pathlib import Path

ARQUIVO_HISTORICO = Path(__file__).resolve().parent.parent / "dados" / "historico_atendimentos.csv"

COLUNAS = ["id", "data", "categoria", "diagnostico", "encaminhamento",
           "tempo_min", "custo_reais", "resolvido"]


class ErroHistorico(Exception):
    pass


def carregar_historico(caminho=ARQUIVO_HISTORICO):
    """Devolve a lista de atendimentos (cada um é um dicionário)."""
    caminho = Path(caminho)
    try:
        with open(caminho, encoding="utf-8", newline="") as arquivo:
            leitor = csv.DictReader(arquivo)
            faltando = [c for c in COLUNAS if c not in (leitor.fieldnames or [])]
            if faltando:
                raise ErroHistorico(f"{caminho.name} sem a(s) coluna(s): {', '.join(faltando)}")
            atendimentos = []
            for linha, item in enumerate(leitor, start=2):
                try:
                    item["tempo_min"] = int(item["tempo_min"])
                    item["custo_reais"] = float(item["custo_reais"])
                except (TypeError, ValueError):
                    raise ErroHistorico(f"{caminho.name}, linha {linha}: tempo ou custo inválido")
                atendimentos.append(item)
            return atendimentos
    except FileNotFoundError:
        raise ErroHistorico(f"Arquivo não encontrado: {caminho}")


def frequencia(atendimentos, campo="diagnostico"):
    """Quantas vezes cada valor aparece, do mais comum ao menos comum."""
    contagem = {}
    for a in atendimentos:
        contagem[a[campo]] = contagem.get(a[campo], 0) + 1
    return dict(sorted(contagem.items(), key=lambda x: (-x[1], x[0])))


def media(valores):
    valores = list(valores)
    return sum(valores) / len(valores) if valores else 0.0


def resumo_por_diagnostico(atendimentos):
    """diagnostico -> {quantidade, percentual, tempo_medio, custo_medio}."""
    total = len(atendimentos)
    resumo = {}
    for diag, qtd in frequencia(atendimentos).items():
        casos = [a for a in atendimentos if a["diagnostico"] == diag]
        resumo[diag] = {
            "quantidade": qtd,
            "percentual": qtd / total * 100,
            "tempo_medio": media(a["tempo_min"] for a in casos),
            "custo_medio": media(a["custo_reais"] for a in casos),
        }
    return resumo


def resumo_diagnostico(atendimentos, diagnostico):
    """Resumo de um diagnóstico só (ou None se nunca apareceu no histórico).

    Serve para mostrar junto do resultado do motor, por exemplo:
    "Em 14 atendimentos parecidos, o tempo médio foi 70 min e o custo médio R$ 150,00".
    """
    return resumo_por_diagnostico(atendimentos).get(diagnostico)


def resumo_geral(atendimentos):
    resolvidos = sum(1 for a in atendimentos if a["resolvido"] == "sim")
    return {
        "total": len(atendimentos),
        "tempo_medio": media(a["tempo_min"] for a in atendimentos),
        "custo_medio": media(a["custo_reais"] for a in atendimentos),
        "taxa_resolucao": resolvidos / len(atendimentos) * 100 if atendimentos else 0.0,
        "por_categoria": frequencia(atendimentos, "categoria"),
        "por_encaminhamento": frequencia(atendimentos, "encaminhamento"),
    }


def formatar_reais(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def relatorio(atendimentos):
    """Texto pronto para mostrar no console."""
    geral = resumo_geral(atendimentos)
    linhas = [
        "=== Histórico de atendimentos da TechFix ===",
        f"Total de atendimentos: {geral['total']}",
        f"Tempo médio: {geral['tempo_medio']:.0f} min",
        f"Custo médio: {formatar_reais(geral['custo_medio'])}",
        f"Resolvidos: {geral['taxa_resolucao']:.0f}%",
        "",
        "Por categoria:",
    ]
    for cat, qtd in geral["por_categoria"].items():
        linhas.append(f"  {cat:<20} {qtd:>4}")
    linhas += ["", f"{'Diagnóstico':<34}{'Qtd':>5}{'%':>7}{'Tempo':>9}{'Custo':>14}"]
    for diag, r in resumo_por_diagnostico(atendimentos).items():
        linhas.append(
            f"{diag:<34}{r['quantidade']:>5}{r['percentual']:>6.1f}%"
            f"{r['tempo_medio']:>6.0f} min{formatar_reais(r['custo_medio']):>14}"
        )
    return "\n".join(linhas)


if __name__ == "__main__":
    try:
        print(relatorio(carregar_historico()))
    except ErroHistorico as erro:
        print(f"Erro: {erro}")
