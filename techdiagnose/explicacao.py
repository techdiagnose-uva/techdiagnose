from techdiagnose.motor import regras_descartadas


def nome_resposta(valor):
    if valor is None:
        return "não sei"
    if valor is False:
        return "não"
    if valor == 1:
        return "sim"
    return "provavelmente"


def texto_regra(regra):
    se = " E ".join(regra["se"])
    return f"{regra['id']}: SE {se} ENTÃO {regra['entao']} (CF {regra['cf']:.2f})"


def porque(regras, fato):
    """Regras que usam este fato como premissa."""
    return [r for r in regras if fato in r["se"]]


def regra_em_teste(regras, categoria, respostas, fato):
    """A regra que fez o sistema perguntar este fato (mesma ordem da proxima_pergunta)."""
    descartadas = regras_descartadas(regras, respostas)
    for regra in regras:
        if (regra["categoria"] == categoria and regra["id"] not in descartadas
                and fato in regra["se"]):
            return regra
    return None


def explicar_pergunta(regras, categoria, respostas, fato):
    """POR QUÊ: mostra a regra em teste e as regras que dependem dela."""
    regra = regra_em_teste(regras, categoria, respostas, fato)
    if regra is None:
        return "Esta pergunta não está ligada a nenhuma regra em teste."
    linhas = [
        "Estou perguntando isso porque estou testando a regra",
        f"  {texto_regra(regra)}",
        f"  ({regra['descricao']})",
    ]
    dependentes = porque(regras, regra["entao"])
    if dependentes:
        linhas.append(f"Se ela for confirmada, {regra['entao']} ajuda a testar:")
        linhas += [f"  {texto_regra(r)}" for r in dependentes]
    else:
        linhas.append(f"Se ela for confirmada, o diagnóstico é {regra['entao']}.")
    return "\n".join(linhas)


def explicar(resultado, fato, nivel=0):
    """COMO: cadeia de regras e fatos que levou a uma conclusão."""
    recuo = "  " * nivel
    valor = resultado.respostas.get(fato)
    if valor:
        return f"{recuo}- {fato}: informado pelo usuário ({nome_resposta(valor)}, CF {float(valor):.2f})"
    linhas = []
    for d in resultado.disparos:
        r = d["regra"]
        if r["entao"] == fato:
            linhas.append(f"{recuo}- {fato} (CF {d['cf']:.2f}) pela {r['id']}: {r['descricao']}")
            for premissa in r["se"]:
                linhas.append(explicar(resultado, premissa, nivel + 1))
    return "\n".join(linhas)


def texto_disparo(d):
    r = d["regra"]
    valores = ", ".join(f"{v:.2f}" for v in d["premissas"].values())
    linhas = [
        f"  {texto_regra(r)}",
        f"     CF = {r['cf']:.2f} x min({valores}) = {d['cf']:.2f}",
    ]
    if d["cf_antes"] is not None:
        # mesmo fato concluído por duas regras: CF1 + CF2 x (1 - CF1)
        a, b = d["cf_antes"], d["cf"]
        linhas.append(
            f"     {r['entao']} já tinha CF {a:.2f}: "
            f"{a:.2f} + {b:.2f} x (1 - {a:.2f}) = {d['cf_final']:.2f}"
        )
    return "\n".join(linhas)


def explicar_raciocinio(resultado, regras, categoria):
    """COMO, passo a passo: fatos, regras disparadas, conta do CF e regras descartadas."""
    linhas = ["1. Fatos informados:"]
    for fato, valor in resultado.respostas.items():
        linhas.append(f"  {fato}: {nome_resposta(valor)}")

    linhas.append("\n2. Regras disparadas, na ordem:")
    if not resultado.disparos:
        linhas.append("  nenhuma regra teve todas as premissas confirmadas")
    for d in resultado.disparos:
        linhas.append(texto_disparo(d))

    linhas.append("\n3. Regras descartadas:")
    descartadas = regras_descartadas(regras, resultado.respostas)
    da_categoria = [r for r in regras if r["categoria"] == categoria and r["id"] in descartadas]
    if not da_categoria:
        linhas.append("  nenhuma")
    for r in da_categoria:
        linhas.append(f"  {r['id']} ({r['entao']}): {descartadas[r['id']]}")
    return "\n".join(linhas)
