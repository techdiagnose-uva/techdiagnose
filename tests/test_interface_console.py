"""Testes da interface de console: leitura de respostas e fluxo completo de um atendimento.

Como o terminal pede dados com input(), os testes trocam o input() por uma função falsa
(monkeypatch) que responde sozinha, e leem o que foi impresso com o capsys.
"""
import builtins

import pytest

from techdiagnose.base_conhecimento import carregar_base
from techdiagnose.interface_console import (
    PORQUE, escolher_categoria, executar, fazer_perguntas, ler_resposta,
    ler_sim_nao, nome_diagnostico, normalizar,
)
from techdiagnose.motor import categorias

REGRAS, PERGUNTAS = carregar_base()


def digitar(monkeypatch, *respostas):
    """Faz o input() devolver as respostas, uma por chamada."""
    fila = iter(respostas)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(fila))


def atendimento_automatico(monkeypatch, categoria, por_fato, padrao="n"):
    """Simula um atendimento inteiro: escolhe a categoria e responde cada pergunta pelo fato."""
    numero = str(categorias(REGRAS).index(categoria) + 1)
    texto_para_fato = {p["texto"]: fato for fato, p in PERGUNTAS.items()}

    def falso_input(prompt=""):
        if prompt.startswith("Digite o número"):
            return numero
        for texto, fato in texto_para_fato.items():
            if texto in prompt:
                return por_fato.get(fato, padrao)
        return "n"  # "Quer ver como...?" e "Fazer outro atendimento?"

    monkeypatch.setattr("builtins.input", falso_input)


# ---------- funções pequenas ----------

def test_normalizar_tira_acento_maiuscula_e_espacos():
    assert normalizar("  NÃO   Sei ") == "nao sei"


def test_nome_diagnostico():
    assert nome_diagnostico("fonte_queimada") == "Fonte queimada"


# ---------- ler_resposta ----------

@pytest.mark.parametrize("digitado, esperado", [
    ("sim", 1.0), ("S", 1.0), ("provavelmente", 0.6), ("talvez", 0.6),
    ("Não", False), ("n", False), ("não sei", None), ("ns", None),
])
def test_ler_resposta_aceita_as_variacoes(monkeypatch, digitado, esperado):
    digitar(monkeypatch, digitado)
    assert ler_resposta("Pergunta?") == esperado


@pytest.mark.parametrize("digitado", ["?", "por que", "Por quê?", "porque"])
def test_ler_resposta_reconhece_o_pedido_de_porque(monkeypatch, digitado):
    digitar(monkeypatch, digitado)
    assert ler_resposta("Pergunta?") == PORQUE


def test_ler_resposta_repete_ate_ser_valida(monkeypatch, capsys):
    digitar(monkeypatch, "banana", "", "sim")
    assert ler_resposta("Pergunta?") == 1.0
    assert capsys.readouterr().out.count("Não entendi") == 2


# ---------- ler_sim_nao ----------

def test_ler_sim_nao_repete_ate_ser_valida(monkeypatch, capsys):
    digitar(monkeypatch, "talvez", "sim")
    assert ler_sim_nao("Continuar?") is True
    assert "Responda sim ou não" in capsys.readouterr().out


def test_ler_sim_nao_aceita_nao(monkeypatch):
    digitar(monkeypatch, "NÃO")
    assert ler_sim_nao("Continuar?") is False


# ---------- escolher_categoria ----------

def test_escolher_categoria_rejeita_opcao_invalida(monkeypatch, capsys):
    digitar(monkeypatch, "0", "abc", "99", "2")
    assert escolher_categoria(REGRAS) == categorias(REGRAS)[1]
    assert capsys.readouterr().out.count("Opção inválida") == 3


# ---------- fazer_perguntas ----------

def test_fazer_perguntas_guarda_as_respostas(monkeypatch):
    atendimento_automatico(monkeypatch, "inicializacao", {
        "nao_liga": "sim", "testou_outra_tomada": "provavelmente", "e_desktop": "sim",
    })
    respostas = fazer_perguntas(REGRAS, PERGUNTAS, "inicializacao")
    assert respostas["nao_liga"] == 1.0
    assert respostas["testou_outra_tomada"] == 0.6
    assert respostas["e_desktop"] == 1.0


def test_pedir_porque_mostra_a_regra_e_repete_a_pergunta(monkeypatch, capsys):
    digitar(monkeypatch, "?", *["n"] * len(PERGUNTAS))
    respostas = fazer_perguntas(REGRAS, PERGUNTAS, "inicializacao")
    assert "estou testando a regra" in capsys.readouterr().out
    assert respostas["nao_liga"] is False  # a pergunta voltou e foi respondida depois


# ---------- atendimento completo ----------

def test_atendimento_completo_com_diagnostico(monkeypatch, capsys):
    atendimento_automatico(monkeypatch, "inicializacao", {
        "nao_liga": "sim", "testou_outra_tomada": "sim", "e_desktop": "sim",
    })
    executar(REGRAS, PERGUNTAS, atendimentos=None)
    saida = capsys.readouterr().out
    assert "Resultado da triagem" in saida
    assert "Fonte queimada - certeza 72%" in saida
    assert "Encaminhamento:" in saida
    assert "Obrigado por usar o TechDiagnose" in saida


def test_atendimento_sem_conclusao_avisa_o_usuario(monkeypatch, capsys):
    atendimento_automatico(monkeypatch, "internet", {})  # tudo "não"
    executar(REGRAS, PERGUNTAS, atendimentos=None)
    saida = capsys.readouterr().out
    assert "Não foi possível concluir com as informações fornecidas" in saida
    assert "Certeza" not in saida and "certeza" not in saida


def test_depois_do_diagnostico_pode_ver_o_como(monkeypatch, capsys):
    respostas = iter(["sim"])  # "Quer ver como cheguei nessa conclusão?" -> sim

    atendimento_automatico(monkeypatch, "inicializacao", {
        "nao_liga": "sim", "testou_outra_tomada": "sim", "e_desktop": "sim",
    })
    base = builtins.input  # o input falso do atendimento automático

    def com_como(prompt=""):
        if "Quer ver como" in prompt:
            return next(respostas)
        return base(prompt)

    monkeypatch.setattr("builtins.input", com_como)
    executar(REGRAS, PERGUNTAS, atendimentos=None)
    saida = capsys.readouterr().out
    assert "Como cheguei nessa conclusão" in saida
    assert "1. Fatos informados" in saida
