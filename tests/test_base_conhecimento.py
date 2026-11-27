"""Testes da carga e validação da base de conhecimento (regras.json e perguntas.json)."""
import json

import pytest

from techdiagnose.base_conhecimento import PASTA_DADOS, ErroBaseConhecimento, carregar_base

REGRAS = json.loads((PASTA_DADOS / "regras.json").read_text(encoding="utf-8"))
PERGUNTAS = json.loads((PASTA_DADOS / "perguntas.json").read_text(encoding="utf-8"))


def salvar(pasta, regras=REGRAS, perguntas=PERGUNTAS):
    (pasta / "regras.json").write_text(json.dumps(regras), encoding="utf-8")
    (pasta / "perguntas.json").write_text(json.dumps(perguntas), encoding="utf-8")
    return pasta


def copia_regras():
    return json.loads(json.dumps(REGRAS))


def test_base_real_carrega():
    regras, perguntas = carregar_base()
    assert len(regras) == 32
    assert len(perguntas) == 39


def test_json_invalido(tmp_path):
    salvar(tmp_path)
    (tmp_path / "regras.json").write_text('[{"id": "R01",}]', encoding="utf-8")
    with pytest.raises(ErroBaseConhecimento, match="JSON inválido"):
        carregar_base(tmp_path)


def test_arquivo_inexistente(tmp_path):
    with pytest.raises(ErroBaseConhecimento, match="não encontrado"):
        carregar_base(tmp_path)


def test_campo_obrigatorio_faltando(tmp_path):
    regras = copia_regras()
    del regras[0]["cf"]
    with pytest.raises(ErroBaseConhecimento, match="cf"):
        carregar_base(salvar(tmp_path, regras))


def test_diagnostico_sem_solucao(tmp_path):
    regras = copia_regras()
    del regras[1]["solucao"]  # R02 é diagnóstico
    with pytest.raises(ErroBaseConhecimento, match="solucao"):
        carregar_base(salvar(tmp_path, regras))


@pytest.mark.parametrize("cf", [1.5, -0.1, "alto"])
def test_cf_fora_de_0_e_1(tmp_path, cf):
    regras = copia_regras()
    regras[0]["cf"] = cf
    with pytest.raises(ErroBaseConhecimento, match="entre 0 e 1"):
        carregar_base(salvar(tmp_path, regras))


def test_id_repetido(tmp_path):
    regras = copia_regras()
    regras[1]["id"] = "R01"
    with pytest.raises(ErroBaseConhecimento, match="repetida"):
        carregar_base(salvar(tmp_path, regras))


def test_fato_sem_pergunta_nem_regra(tmp_path):
    regras = copia_regras()
    regras[0]["se"].append("cheiro_de_queimado")
    with pytest.raises(ErroBaseConhecimento, match="cheiro_de_queimado"):
        carregar_base(salvar(tmp_path, regras))
