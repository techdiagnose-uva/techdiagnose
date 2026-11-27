import streamlit as st
from techdiagnose.base_conhecimento import carregar_base, ErroBaseConhecimento
from techdiagnose.motor import inferir, diagnosticos
from techdiagnose.explicacao import explicar, porque

st.set_page_config(page_title="TechDiagnose", page_icon="🛠️")
st.title("TechDiagnose")
st.caption("Triagem técnica para assistência de informática")

try:
    regras, perguntas = carregar_base()
except ErroBaseConhecimento as erro:
    st.error(f"Erro na base de conhecimento: {erro}")
    st.stop()

categorias = sorted({p["categoria"] for p in perguntas.values()})
categoria = st.selectbox("Qual é o tipo de problema?", categorias)

with st.form("formulario"):
    respostas = {}
    for fato, p in perguntas.items():
        if p["categoria"] == categoria:
            resp = st.radio(p["texto"], ["Não", "Sim"], horizontal=True, key=fato)
            respostas[fato] = resp == "Sim"
            with st.expander("Por que você pergunta isso?"):
                for r in porque(regras, fato):
                    st.write(f"**{r['id']}**: {r['descricao']}")
    enviar = st.form_submit_button("Diagnosticar")

if enviar:
    resultado = inferir(regras, respostas)
    lista = diagnosticos(resultado)

    if not lista:
        st.warning("Não foi possível concluir com as informações fornecidas.")
    for d in lista:
        st.subheader(d["fato"].replace("_", " ").capitalize())
        st.progress(min(d["cf"], 1.0), text=f"Certeza: {d['cf']:.0%}")
        st.write(f"**Solução:** {d['solucao']}")
        st.write(f"**Encaminhamento:** {d['encaminhamento']}")
        with st.expander("Como cheguei nessa conclusão?"):
            st.text(explicar(resultado, d["fato"]))
