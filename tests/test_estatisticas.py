import pytest

from techdiagnose.base_conhecimento import carregar_base
from techdiagnose.estatisticas import (
    ErroHistorico, carregar_historico, frequencia, resumo_diagnostico,
    resumo_geral, resumo_por_diagnostico, relatorio,
)

CABECALHO = "id,data,categoria,diagnostico,encaminhamento,tempo_min,custo_reais,resolvido\n"


def criar_csv(tmp_path, linhas):
    caminho = tmp_path / "historico.csv"
    caminho.write_text(CABECALHO + "".join(linhas), encoding="utf-8")
    return caminho


def test_historico_real_tem_uns_200_atendimentos():
    atendimentos = carregar_historico()
    assert 180 <= len(atendimentos) <= 220


def test_diagnosticos_do_historico_existem_nas_regras():
    regras, _ = carregar_base()
    diagnosticos = {r["entao"] for r in regras if r["tipo"] == "diagnostico"}
    for a in carregar_historico():
        assert a["diagnostico"] in diagnosticos


def test_medias_e_frequencia(tmp_path):
    caminho = criar_csv(tmp_path, [
        "A1,2026-01-01,lentidao,malware,remoto,60,100,sim\n",
        "A2,2026-01-02,lentidao,malware,remoto,90,200,sim\n",
        "A3,2026-01-03,internet,problema_provedor,remoto,15,30,nao\n",
    ])
    atendimentos = carregar_historico(caminho)

    assert frequencia(atendimentos) == {"malware": 2, "problema_provedor": 1}
    malware = resumo_diagnostico(atendimentos, "malware")
    assert malware["quantidade"] == 2
    assert malware["tempo_medio"] == 75
    assert malware["custo_medio"] == 150
    assert resumo_diagnostico(atendimentos, "nao_existe") is None

    geral = resumo_geral(atendimentos)
    assert geral["total"] == 3
    assert round(geral["taxa_resolucao"]) == 67
    assert sum(r["percentual"] for r in resumo_por_diagnostico(atendimentos).values()) == pytest.approx(100)


def test_arquivo_inexistente(tmp_path):
    with pytest.raises(ErroHistorico):
        carregar_historico(tmp_path / "nao_existe.csv")


def test_coluna_faltando(tmp_path):
    caminho = tmp_path / "ruim.csv"
    caminho.write_text("id,data\nA1,2026-01-01\n", encoding="utf-8")
    with pytest.raises(ErroHistorico):
        carregar_historico(caminho)


def test_custo_invalido(tmp_path):
    caminho = criar_csv(tmp_path, ["A1,2026-01-01,lentidao,malware,remoto,60,abc,sim\n"])
    with pytest.raises(ErroHistorico):
        carregar_historico(caminho)


def test_relatorio_gera_texto():
    texto = relatorio(carregar_historico())
    assert "Total de atendimentos" in texto
    assert "malware" in texto
