import unicodedata

from techdiagnose.motor import categorias, proxima_pergunta, inferir, diagnosticos
from techdiagnose.explicacao import explicar_pergunta, explicar_raciocinio, explicar
from techdiagnose.estatisticas import resumo_diagnostico, formatar_reais

LINHA = "-" * 64

NOMES_CATEGORIA = {
    "inicializacao": "Computador não liga ou não inicia",
    "video": "Problema de imagem / vídeo",
    "superaquecimento": "Esquenta demais ou desliga sozinho",
    "lentidao": "Computador lento",
    "internet": "Sem internet",
}

# chaves já normalizadas (minúsculas e sem acento)
RESPOSTAS = {
    "sim": 1.0, "s": 1.0,
    "provavelmente": 0.6, "p": 0.6, "talvez": 0.6,
    "nao": False, "n": False,
    "nao sei": None, "ns": None,
}
PORQUE = "porque"
OPCOES = "sim (s), provavelmente (p), não (n), não sei (ns) ou ? para saber o porquê"


def tela_inicial():
    print(LINHA)
    print("TechFix Assistência Técnica - TechDiagnose")
    print(LINHA)
    print("Triagem inicial de problemas em computadores.")
    print("Vou fazer algumas perguntas sobre o defeito e indicar a causa provável,")
    print("a solução e se dá para resolver por atendimento remoto ou se o")
    print("computador precisa vir para a bancada.")
    print()
    print("Responda com: sim (s), provavelmente (p), não (n) ou não sei (ns).")
    print("Digite ? em qualquer pergunta para saber por que estou perguntando.")
    print("Para sair a qualquer momento, aperte Ctrl+C.")


def normalizar(texto):
    """'  NÃO   Sei ' -> 'nao sei': minúsculas, sem acento e sem espaços sobrando."""
    sem_acento = unicodedata.normalize("NFD", texto).encode("ascii", "ignore").decode()
    return " ".join(sem_acento.lower().split())


def ler_resposta(texto):
    """Repete a pergunta até a resposta ser válida."""
    while True:
        resposta = normalizar(input(f"\n{texto}\n> "))
        if resposta == "?" or resposta.rstrip("?").strip() in ("por que", "porque"):
            return PORQUE
        if resposta in RESPOSTAS:
            return RESPOSTAS[resposta]
        print(f"Não entendi. Responda com: {OPCOES}.")


def ler_sim_nao(texto):
    while True:
        resposta = normalizar(input(f"\n{texto} (sim/não)\n> "))
        if resposta in ("sim", "s"):
            return True
        if resposta in ("nao", "n"):
            return False
        print("Não entendi. Responda sim ou não.")


def escolher_categoria(regras):
    lista = categorias(regras)
    print("\nQual é o tipo de problema?")
    for i, categoria in enumerate(lista, start=1):
        print(f"  {i}. {NOMES_CATEGORIA.get(categoria, categoria)}")
    while True:
        opcao = input("Digite o número: ").strip()
        if opcao.isdigit() and 1 <= int(opcao) <= len(lista):
            return lista[int(opcao) - 1]
        print(f"Opção inválida. Digite um número de 1 a {len(lista)}.")


def fazer_perguntas(regras, perguntas, categoria):
    respostas = {}
    fato = proxima_pergunta(regras, perguntas, categoria, respostas)
    while fato is not None:
        resposta = ler_resposta(perguntas[fato]["texto"])
        if resposta == PORQUE:
            print(explicar_pergunta(regras, categoria, respostas, fato))
            continue
        respostas[fato] = resposta
        fato = proxima_pergunta(regras, perguntas, categoria, respostas)
    return respostas


def nome_diagnostico(fato):
    return fato.replace("_", " ").capitalize()


def mostrar_diagnostico(d, atendimentos):
    print(f"\n{nome_diagnostico(d['fato'])} - certeza {d['cf']:.0%}")
    if d["fraca"]:
        print("  (hipótese fraca: as respostas não deixam o sistema muito seguro)")
    print(f"  Solução: {d['solucao']}")
    if d["encaminhamento"] == "remoto":
        print("  Encaminhamento: dá para resolver por atendimento remoto")
    else:
        print("  Encaminhamento: o computador precisa vir para a bancada")
    if atendimentos:
        historico = resumo_diagnostico(atendimentos, d["fato"])
        if historico:
            print(
                f"  Na TechFix: {historico['quantidade']} casos parecidos, "
                f"tempo médio {historico['tempo_medio']:.0f} min, "
                f"custo médio {formatar_reais(historico['custo_medio'])}"
            )


def mostrar_resultado(resultado, atendimentos):
    print(f"\n{LINHA}\nResultado da triagem\n{LINHA}")
    lista = diagnosticos(resultado)
    if not lista:
        print("Não foi possível concluir com as informações fornecidas.")
        print("Recomendamos trazer o computador para uma avaliação na bancada.")
        return
    for d in lista:
        mostrar_diagnostico(d, atendimentos)


def mostrar_como(resultado, regras, categoria):
    print(f"\n{LINHA}\nComo cheguei nessa conclusão\n{LINHA}")
    print(explicar_raciocinio(resultado, regras, categoria))
    for d in diagnosticos(resultado):
        print(f"\nCadeia de {d['fato']}:")
        print(explicar(resultado, d["fato"]))


def atender(regras, perguntas, atendimentos):
    categoria = escolher_categoria(regras)
    respostas = fazer_perguntas(regras, perguntas, categoria)
    resultado = inferir(regras, respostas)
    mostrar_resultado(resultado, atendimentos)
    if ler_sim_nao("Quer ver como cheguei nessa conclusão?"):
        mostrar_como(resultado, regras, categoria)


def executar(regras, perguntas, atendimentos):
    tela_inicial()
    atender(regras, perguntas, atendimentos)
    while ler_sim_nao("Fazer outro atendimento?"):
        atender(regras, perguntas, atendimentos)
    print("\nObrigado por usar o TechDiagnose.")
