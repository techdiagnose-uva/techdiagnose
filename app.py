import pandas as pd
import streamlit as st

from techdiagnose.base_conhecimento import carregar_base, ErroBaseConhecimento
from techdiagnose.estatisticas import (
    carregar_historico, ErroHistorico, frequencia, resumo_diagnostico, formatar_reais,
)
from techdiagnose.explicacao import explicar, explicar_pergunta, explicar_raciocinio
from techdiagnose.interface_console import NOMES_CATEGORIA, nome_diagnostico
from techdiagnose.motor import categorias, diagnosticos, inferir, proxima_pergunta

OPCOES = {"Sim": 1.0, "Provavelmente": 0.6, "Não": False, "Não sei": None}

st.set_page_config(page_title="TechDiagnose")
st.title("TechDiagnose")
st.caption(
    "TechFix Assistência Técnica: triagem inicial de problemas em computadores. "
    "Responda as perguntas e o sistema indica a causa provável, a solução e se dá para "
    "resolver por atendimento remoto ou se o computador precisa vir para a bancada."
)

try:
    regras, perguntas = carregar_base()
except ErroBaseConhecimento as erro:
    st.error(f"Erro na base de conhecimento: {erro}")
    st.stop()

try:
    atendimentos = carregar_historico()
except ErroHistorico:
    atendimentos = None


def recomecar():
    st.session_state.respostas = {}


categoria = st.selectbox(
    "Qual é o tipo de problema?",
    categorias(regras),
    format_func=lambda c: NOMES_CATEGORIA.get(c, c),
    on_change=recomecar,
)
if "respostas" not in st.session_state:
    recomecar()
respostas = st.session_state.respostas


def mostrar_pergunta(fato):
    st.subheader(f"Pergunta {len(respostas) + 1}")
    st.write(perguntas[fato]["texto"])
    for coluna, (rotulo, valor) in zip(st.columns(len(OPCOES)), OPCOES.items()):
        if coluna.button(rotulo, key=f"{fato}_{rotulo}", use_container_width=True):
            respostas[fato] = valor
            st.rerun()
    with st.expander("Por que você pergunta isso?"):
        st.text(explicar_pergunta(regras, categoria, respostas, fato))


def mostrar_diagnostico(d, resultado):
    st.subheader(nome_diagnostico(d["fato"]))
    st.progress(min(d["cf"], 1.0), text=f"Certeza: {d['cf']:.0%}")
    if d["fraca"]:
        st.warning("Hipótese fraca: as respostas não deixam o sistema muito seguro.")
    st.write(f"**Solução:** {d['solucao']}")
    if d["encaminhamento"] == "remoto":
        st.write("**Encaminhamento:** dá para resolver por atendimento remoto")
    else:
        st.write("**Encaminhamento:** o computador precisa vir para a bancada")
    historico = resumo_diagnostico(atendimentos, d["fato"]) if atendimentos else None
    if historico:
        st.write(
            f"Na TechFix: {historico['quantidade']} casos parecidos, tempo médio "
            f"{historico['tempo_medio']:.0f} min, custo médio "
            f"{formatar_reais(historico['custo_medio'])}"
        )
    with st.expander("Cadeia de regras deste diagnóstico"):
        st.text(explicar(resultado, d["fato"]))


def mostrar_resultado():
    resultado = inferir(regras, respostas)
    lista = diagnosticos(resultado)
    st.header("Resultado da triagem")
    if not lista:
        st.warning(
            "Não foi possível concluir com as informações fornecidas. "
            "Recomendamos trazer o computador para uma avaliação na bancada."
        )
    for d in lista:
        mostrar_diagnostico(d, resultado)
    with st.expander("Como cheguei aqui"):
        st.text(explicar_raciocinio(resultado, regras, categoria))


def mostrar_historico():
    st.header("Histórico de atendimentos da TechFix")
    da_categoria = [a for a in atendimentos if a["categoria"] == categoria]
    st.write(
        f"{len(da_categoria)} atendimentos de {len(atendimentos)} foram desta categoria. "
        "Diagnósticos mais comuns:"
    )
    contagem = pd.Series(frequencia(da_categoria), name="atendimentos")
    contagem.index = [nome_diagnostico(f) for f in contagem.index]
    st.bar_chart(contagem, horizontal=True)


fato = proxima_pergunta(regras, perguntas, categoria, respostas)
if fato is not None:
    mostrar_pergunta(fato)
else:
    mostrar_resultado()

if respostas:
    st.button("Recomeçar", on_click=recomecar)

if atendimentos:
    mostrar_historico()
