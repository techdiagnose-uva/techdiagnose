"""Testes do motor de inferencia: encadeamento para frente, CF e resolucao de conflito."""
import pytest

from techdiagnose.base_conhecimento import carregar_base
from techdiagnose.motor import ( combinar_cf, diagnosticos, inferir, proxima_pergunta, regras_descartadas, )

REGRAS, PERGUNTAS = carregar_base()

def cf_de(resultado, fato):
    """CF final de um diagnostico, ou None se ele nao foi concluido."""
    for d in diagnosticos(resultado):
        if d["fato"] == fato:
            return d["cf"]
    return None

# combinacao de fatores de certeza 

def test_combinar_cf_soma_a_evidencia():
    # 0.6 + 0.5 x (1 - 0.6) = 0.8
    assert combinar_cf(0.6, 0.5) == pytest.approx(0.8)

def test_combinar_cf_e_comutativo_e_nunca_passa_de_1():
    assert combinar_cf(0.7, 0.4) == pytest.approx(combinar_cf(0.4, 0.7))
    assert combinar_cf(0.99, 0.99) <= 1.0

def test_combinar_cf_com_zero_nao_muda_nada():
    assert combinar_cf(0.7, 0) == pytest.approx(0.7)

# cenarios por categoria 

def test_fonte_queimada_em_desktop_que_nao_liga():
    # R01: nao_liga + testou_outra_tomada -> falha_alimentacao (0.9)
    # R02: falha_alimentacao + e_desktop  -> fonte_queimada (0.8 x 0.9 = 0.72)
    res = inferir(REGRAS, {"nao_liga": True, "testou_outra_tomada": True, "e_desktop": True})
    assert cf_de(res, "fonte_queimada") == pytest.approx(0.72)
    assert cf_de(res, "carregador_defeituoso") is None

def test_carregador_defeituoso_em_notebook_que_nao_liga():
    res = inferir(REGRAS, {"nao_liga": True, "testou_outra_tomada": True, "e_notebook": True})
    assert cf_de(res, "carregador_defeituoso") == pytest.approx(0.9 * 0.7)
    assert cf_de(res, "fonte_queimada") is None

def test_backlight_queimado_so_com_lanterna():
    res = inferir(REGRAS, {"tela_preta_com_pc_ligado": True, "imagem_aparece_com_lanterna": True})
    assert cf_de(res, "backlight_queimado") == pytest.approx(0.9)

def test_provedor_fora_do_ar():
    res = inferir(REGRAS, {"sem_internet": True, "luz_internet_roteador_apagada": True})
    assert cf_de(res, "problema_provedor") == pytest.approx(0.85)

def test_lentidao_por_malware():
    res = inferir(REGRAS, {"lento_geral": True, "propagandas_ou_popups": True})
    assert cf_de(res, "malware") == pytest.approx(0.85)

# duas regras na mesma conclusao 

def test_cf_combinado_de_duas_regras_diagnosticas():
    # R17 (via suspeita_superaquecimento) e R21 (via throttling_termico)
    # concluem poeira_pasta_termica: 0.595 e 0.42 -> 0.595 + 0.42 x (1 - 0.595)
    res = inferir(REGRAS, {
        "desliga_sozinho": True, "ventoinha_barulhenta": True,
        "sem_limpeza_1_ano": True, "lento_ao_esquentar": True,
    })
    assert cf_de(res, "poeira_pasta_termica") == pytest.approx(0.765, abs=1e-3)

def test_regra_espera_o_reforco_da_premissa_antes_de_disparar():
    # suspeita_superaquecimento vem de R15 (0.7) e R16 (0.6) = 0.88.
    # R17 só pode disparar depois dos dois reforços: 0.85 x 0.88 = 0.748
    res = inferir(REGRAS, {
        "desliga_sozinho": True, "ventoinha_barulhenta": True,
        "gabinete_muito_quente": True, "sem_limpeza_1_ano": True,
    })
    assert res.fatos["suspeita_superaquecimento"] == pytest.approx(0.88)
    assert cf_de(res, "poeira_pasta_termica") == pytest.approx(0.748, abs=1e-3)

# respostas "provavelmente", "nao" e "nao sei" 

def test_resposta_provavelmente_reduz_a_certeza():
    # a premissa mais fraca (0.6) limita a cadeia: 0.9 x 0.6 = 0.54; 0.8 x 0.54 = 0.432
    res = inferir(REGRAS, {"nao_liga": True, "testou_outra_tomada": 0.6, "e_desktop": True})
    assert cf_de(res, "fonte_queimada") == pytest.approx(0.432)

def test_diagnostico_abaixo_de_40_por_cento_e_hipotese_fraca():
    res = inferir(REGRAS, {"lento_geral": True, "atualizacao_em_andamento": 0.6})
    d = diagnosticos(res)[0]
    assert d["fato"] == "atualizacao_segundo_plano"
    assert d["cf"] == pytest.approx(0.36)
    assert d["fraca"] is True

def test_diagnostico_forte_nao_e_marcado_como_fraco():
    res = inferir(REGRAS, {"nao_liga": True, "testou_outra_tomada": True, "e_desktop": True})
    assert diagnosticos(res)[0]["fraca"] is False

def test_nao_sei_equivale_a_nao_ter_a_informacao():
    res = inferir(REGRAS, {"nao_liga": True, "testou_outra_tomada": None, "e_desktop": True})
    assert diagnosticos(res) == []

def test_resposta_nao_nao_dispara_regra():
    res = inferir(REGRAS, {"nao_liga": True, "testou_outra_tomada": False, "e_desktop": True})
    assert diagnosticos(res) == []

# sem conclusao

def test_sem_respostas_nao_conclui_nada():
    assert diagnosticos(inferir(REGRAS, {})) == []

def test_todas_as_respostas_nao_nao_conclui_nada():
    respostas = {fato: False for fato in PERGUNTAS}
    assert diagnosticos(inferir(REGRAS, respostas)) == []

# propriedades do motor

def test_cada_regra_dispara_no_maximo_uma_vez():
    res = inferir(REGRAS, {
        "desliga_sozinho": True, "ventoinha_barulhenta": True,
        "gabinete_muito_quente": True, "sem_limpeza_1_ano": True,
        "lento_ao_esquentar": True,
    })
    ids = [d["regra"]["id"] for d in res.disparos]
    assert len(ids) == len(set(ids))

def test_diagnosticos_vem_do_mais_ao_menos_certo():
    res = inferir(REGRAS, {
        "desliga_sozinho": True, "ventoinha_barulhenta": True,
        "sem_limpeza_1_ano": True, "ventoinha_parada": True,
    })
    cfs = [d["cf"] for d in diagnosticos(res)]
    assert len(cfs) >= 2
    assert cfs == sorted(cfs, reverse=True)

def test_diagnostico_traz_solucao_e_encaminhamento():
    res = inferir(REGRAS, {"nao_liga": True, "testou_outra_tomada": True, "e_desktop": True})
    d = diagnosticos(res)[0]
    assert d["solucao"]
    assert d["encaminhamento"] in ("remoto", "bancada")

def test_cf_dos_fatos_fica_entre_0_e_1():
    res = inferir(REGRAS, {fato: True for fato in PERGUNTAS})
    assert all(0 <= cf <= 1 for cf in res.fatos.values())

# escolha da proxima pergunta

def test_primeira_pergunta_da_categoria():
    assert proxima_pergunta(REGRAS, PERGUNTAS, "inicializacao", {}) == "nao_liga"

def test_resposta_nao_descarta_regras_e_pula_perguntas_inuteis():
    respostas = {"nao_liga": False}
    descartadas = regras_descartadas(REGRAS, respostas)
    assert "R01" in descartadas and "R02" in descartadas
    proxima = proxima_pergunta(REGRAS, PERGUNTAS, "inicializacao", respostas)
    assert proxima not in ("testou_outra_tomada", "e_desktop", "e_notebook")

def test_nao_pergunta_o_que_ja_foi_respondido():
    respostas = {"nao_liga": True}
    assert proxima_pergunta(REGRAS, PERGUNTAS, "inicializacao", respostas) != "nao_liga"

def test_termina_de_perguntar_quando_nao_ha_mais_o_que_perguntar():
    respostas = {}
    for _ in range(len(PERGUNTAS) + 1):
        fato = proxima_pergunta(REGRAS, PERGUNTAS, "internet", respostas)
        if fato is None:
            break
        respostas[fato] = False
    assert fato is None
