from dataclasses import dataclass

LIMIAR_FRACO = 0.40  # abaixo disso o diagnóstico é só uma hipótese fraca


@dataclass
class Resultado:
    fatos: dict       # memória de trabalho: fato -> CF
    disparos: list    # rastro: regras que dispararam, na ordem
    respostas: dict   # fato -> CF informado pelo usuário (False/None = não / não sei)


def combinar_cf(a, b):
    """Duas regras chegam na mesma conclusão: a evidência se soma."""
    return a + b * (1 - a)


def casar(regras, memoria, disparadas):
    """Match: regras não disparadas com todas as premissas na memória de trabalho."""
    prontas = [
        r for r in regras
        if r["id"] not in disparadas and all(p in memoria for p in r["se"])
    ]
    # uma regra espera se outra regra pronta ainda vai reforçar uma premissa dela,
    # senão ela dispararia com um CF que ainda não é o final (ex.: R17 antes da R16)
    conclusoes = {r["entao"] for r in prontas}
    return [r for r in prontas if not conclusoes & set(r["se"])]


def escolher_regra(conflito):
    """Resolução de conflito: mais premissas primeiro, depois maior CF."""
    return max(conflito, key=lambda r: (len(r["se"]), r["cf"]))


def disparar(regra, memoria, disparos):
    premissas = {p: memoria[p] for p in regra["se"]}
    # conjunção: a premissa mais fraca limita a regra
    cf = regra["cf"] * min(premissas.values())
    conclusao = regra["entao"]
    cf_antes = memoria.get(conclusao)
    if cf_antes is None:
        memoria[conclusao] = cf
    else:
        memoria[conclusao] = combinar_cf(cf_antes, cf)
    disparos.append({
        "regra": regra,
        "cf": cf,
        "premissas": premissas,
        "cf_antes": cf_antes,
        "cf_final": memoria[conclusao],
    })


def inferir(regras, respostas):
    """Encadeamento para frente: ciclo reconhecer-agir até o ponto fixo."""
    # "não" e "não sei" ficam fora da memória; True vale 1.0
    memoria = {f: float(v) for f, v in respostas.items() if v}
    disparos, disparadas = [], set()

    conflito = casar(regras, memoria, disparadas)
    while conflito:
        regra = escolher_regra(conflito)
        disparar(regra, memoria, disparos)
        disparadas.add(regra["id"])  # refração: cada regra dispara uma vez só
        conflito = casar(regras, memoria, disparadas)
    return Resultado(memoria, disparos, respostas)


def motivo_descarte(regra, regras, respostas, descartadas):
    for premissa in regra["se"]:
        if premissa in respostas and not respostas[premissa]:
            resposta = "não" if respostas[premissa] is False else "não sei"
            return f"{premissa} respondido '{resposta}'"
        produtoras = [r for r in regras if r["entao"] == premissa]
        if produtoras and all(r["id"] in descartadas for r in produtoras):
            return f"nenhuma regra pode mais concluir {premissa}"
    return None


def regras_descartadas(regras, respostas):
    """Regras que não podem mais disparar -> motivo.

    Repete até não descartar mais nada, porque descartar uma regra pode tornar
    impossível um intermediário e, com ele, as regras que dependem dele.
    """
    descartadas = {}
    mudou = True
    while mudou:
        mudou = False
        for regra in regras:
            if regra["id"] in descartadas:
                continue
            motivo = motivo_descarte(regra, regras, respostas, descartadas)
            if motivo:
                descartadas[regra["id"]] = motivo
                mudou = True
    return descartadas


def categorias(regras):
    return list(dict.fromkeys(r["categoria"] for r in regras))


def proxima_pergunta(regras, perguntas, categoria, respostas):
    """Próximo sintoma a perguntar, ou None quando não há mais o que perguntar.

    Só olha as regras da categoria que ainda podem disparar, na ordem do JSON,
    e pula sintomas já respondidos.
    """
    descartadas = regras_descartadas(regras, respostas)
    for regra in regras:
        if regra["categoria"] != categoria or regra["id"] in descartadas:
            continue
        for premissa in regra["se"]:
            if premissa in perguntas and premissa not in respostas:
                return premissa
    return None


def diagnosticos(resultado):
    """Conclusões finais (regras tipo 'diagnostico'), da mais à menos certa."""
    achados = {}
    for d in resultado.disparos:
        r = d["regra"]
        if r["tipo"] == "diagnostico":
            cf = resultado.fatos[r["entao"]]
            achados[r["entao"]] = {
                "fato": r["entao"],
                "cf": cf,
                "fraca": cf < LIMIAR_FRACO,
                "solucao": r["solucao"],
                "encaminhamento": r["encaminhamento"],
            }
    return sorted(achados.values(), key=lambda x: x["cf"], reverse=True)
