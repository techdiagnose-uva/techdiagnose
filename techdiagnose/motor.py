from dataclasses import dataclass

LIMIAR = 0.2  # CF mínimo para considerar uma premissa verdadeira


@dataclass
class Resultado:
    fatos: dict       # fato -> CF final
    disparos: list    # regras que dispararam, na ordem
    respostas: dict   # fato -> True/False informado pelo usuário


def combinar_cf(a, b):
    """Duas regras chegam na mesma conclusão: a evidência se soma."""
    return a + b * (1 - a)


def inferir(regras, respostas):
    """Encadeamento para frente com fatores de certeza."""
    fatos = {f: 1.0 for f, v in respostas.items() if v}
    disparos, ja_disparou = [], set()

    mudou = True
    while mudou:
        mudou = False
        for regra in regras:
            if regra["id"] in ja_disparou:
                continue
            cfs = [fatos.get(p, 0.0) for p in regra["se"]]
            if min(cfs) < LIMIAR:
                continue
            cf = min(cfs) * regra["cf"]
            c = regra["entao"]
            fatos[c] = combinar_cf(fatos[c], cf) if c in fatos else cf
            ja_disparou.add(regra["id"])
            disparos.append({"regra": regra, "cf": cf})
            mudou = True
    return Resultado(fatos, disparos, respostas)


def diagnosticos(resultado):
    """Conclusões finais (regras tipo 'diagnostico'), da mais à menos certa."""
    achados = {}
    for d in resultado.disparos:
        r = d["regra"]
        if r["tipo"] == "diagnostico":
            achados[r["entao"]] = {
                "fato": r["entao"],
                "cf": resultado.fatos[r["entao"]],
                "solucao": r["solucao"],
                "encaminhamento": r["encaminhamento"],
            }
    return sorted(achados.values(), key=lambda x: x["cf"], reverse=True)


def explicar(resultado, fato, nivel=0):
    """COMO: monta a cadeia de regras e fatos que levou à conclusão."""
    recuo = "  " * nivel
    if resultado.respostas.get(fato):
        return f"{recuo}- {fato}: informado pelo usuário"
    linhas = []
    for d in resultado.disparos:
        r = d["regra"]
        if r["entao"] == fato:
            linhas.append(f"{recuo}- {fato} (CF {d['cf']:.2f}) pela {r['id']}: {r['descricao']}")
            for premissa in r["se"]:
                linhas.append(explicar(resultado, premissa, nivel + 1))
    return "\n".join(linhas)


def porque(regras, fato):
    """POR QUE: quais regras usam este fato, ou seja, por que perguntamos."""
    return [r for r in regras if fato in r["se"]]
