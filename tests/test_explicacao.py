"""Testes do módulo de explicação: 'por quê?' e 'como?'."""
from techdiagnose.base_conhecimento import carregar_base
from techdiagnose.explicacao import (
    explicar, explicar_pergunta, explicar_raciocinio, nome_resposta, porque,
    regra_em_teste, texto_regra,
)
from techdiagnose.motor import inferir, regras_descartadas

REGRAS, PERGUNTAS = carregar_base()

FONTE = {"nao_liga": True, "testou_outra_tomada": True, "e_desktop": True}
POEIRA = {
    "desliga_sozinho": True, "ventoinha_barulhenta": True,
    "sem_limpeza_1_ano": True, "lento_ao_esquentar": True,
}


# ---------- nomes e texto das regras ----------

def test_nome_resposta():
    assert nome_resposta(1.0) == "sim"
    assert nome_resposta(True) == "sim"
    assert nome_resposta(0.6) == "provavelmente"
    assert nome_resposta(False) == "não"
    assert nome_resposta(None) == "não sei"


def test_texto_regra_mostra_se_entao_e_cf():
    regra = next(r for r in REGRAS if r["id"] == "R01")
    texto = texto_regra(regra)
    assert texto.startswith("R01: SE nao_liga E testou_outra_tomada")
    assert "ENTÃO falha_alimentacao" in texto
    assert "CF 0.90" in texto


# ---------- POR QUÊ ----------

def test_porque_lista_as_regras_que_usam_o_fato():
    ids = [r["id"] for r in porque(REGRAS, "e_desktop")]
    assert "R02" in ids


def test_porque_de_fato_sem_uso_devolve_lista_vazia():
    assert porque(REGRAS, "fato_que_nao_existe") == []


def test_regra_em_teste_da_primeira_pergunta():
    regra = regra_em_teste(REGRAS, "inicializacao", {}, "nao_liga")
    assert regra["id"] == "R01"


def test_explicar_pergunta_cita_a_regra_em_teste():
    texto = explicar_pergunta(REGRAS, "inicializacao", {}, "nao_liga")
    assert "estou testando a regra" in texto
    assert "R01" in texto
    # R01 conclui falha_alimentacao, que ajuda a testar R02 e R03
    assert "R02" in texto and "R03" in texto


def test_explicar_pergunta_sem_regra_em_teste():
    # com 'não' em nao_liga, nenhuma regra de inicializacao usa mais este fato
    texto = explicar_pergunta(REGRAS, "inicializacao", {"nao_liga": False}, "nao_liga")
    assert "não está ligada a nenhuma regra" in texto


# ---------- COMO ----------

def test_explicar_mostra_a_cadeia_ate_os_fatos_do_usuario():
    res = inferir(REGRAS, FONTE)
    texto = explicar(res, "fonte_queimada")
    assert "R02" in texto and "R01" in texto
    assert "falha_alimentacao" in texto
    assert "nao_liga: informado pelo usuário" in texto
    assert "e_desktop: informado pelo usuário" in texto


def test_explicar_mostra_o_cf_de_cada_passo():
    res = inferir(REGRAS, FONTE)
    texto = explicar(res, "fonte_queimada")
    assert "CF 0.72" in texto
    assert "CF 0.90" in texto


def test_explicar_raciocinio_tem_as_tres_partes():
    res = inferir(REGRAS, FONTE)
    texto = explicar_raciocinio(res, REGRAS, "inicializacao")
    assert "1. Fatos informados" in texto
    assert "2. Regras disparadas" in texto
    assert "3. Regras descartadas" in texto


def test_explicar_raciocinio_mostra_a_conta_do_cf():
    res = inferir(REGRAS, FONTE)
    texto = explicar_raciocinio(res, REGRAS, "inicializacao")
    assert "CF = 0.80 x min(0.90, 1.00) = 0.72" in texto


def test_explicar_raciocinio_mostra_combinacao_de_duas_regras():
    res = inferir(REGRAS, POEIRA)
    texto = explicar_raciocinio(res, REGRAS, "superaquecimento")
    assert "já tinha CF" in texto


def test_explicar_raciocinio_sem_regras_disparadas():
    res = inferir(REGRAS, {"nao_liga": False})
    texto = explicar_raciocinio(res, REGRAS, "inicializacao")
    assert "nenhuma regra teve todas as premissas confirmadas" in texto


def test_explicar_raciocinio_mostra_resposta_provavelmente_e_nao_sei():
    respostas = {"nao_liga": True, "testou_outra_tomada": 0.6, "e_desktop": None}
    res = inferir(REGRAS, respostas)
    texto = explicar_raciocinio(res, REGRAS, "inicializacao")
    assert "testou_outra_tomada: provavelmente" in texto
    assert "e_desktop: não sei" in texto


# ---------- regras descartadas ----------

def test_descarte_por_resposta_nao():
    descartadas = regras_descartadas(REGRAS, {"nao_liga": False})
    assert "nao_liga" in descartadas["R01"]
    assert "'não'" in descartadas["R01"]


def test_descarte_por_nao_sei():
    descartadas = regras_descartadas(REGRAS, {"nao_liga": None})
    assert "'não sei'" in descartadas["R01"]


def test_descarte_em_cascata():
    # R01 cai, então ninguém mais conclui falha_alimentacao e R02/R03 também caem
    descartadas = regras_descartadas(REGRAS, {"nao_liga": False})
    assert "falha_alimentacao" in descartadas["R02"]
    assert "falha_alimentacao" in descartadas["R03"]
