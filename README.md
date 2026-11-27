# TechDiagnose

Sistema especialista em Python que faz a triagem de problemas em computadores para a **TechFix**, uma assistência técnica fictícia.

O usuário responde algumas perguntas sobre os sintomas e o sistema, usando regras e um motor de inferência, diz o que provavelmente está errado, sugere a solução, indica se o atendimento pode ser **remoto** ou precisa ir para a **bancada** e explica como chegou em cada conclusão.

Trabalho da disciplina **Programação de Sistemas Especialistas**, Universidade Veiga de Almeida (UVA).

🔗 Versão web: https://techdiagnose-dsy6edz5dnhujzrk2zuvuk.streamlit.app/

Contexto de negócio

A TechFix recebe todos os dias clientes com defeitos de computador e perde tempo na triagem inicial: é preciso descobrir a causa provável, decidir se dá para resolver por atendimento remoto ou se o equipamento precisa vir para a bancada, e estimar tempo e custo. O TechDiagnose automatiza essa triagem, registrando o conhecimento do técnico em regras e justificando cada conclusão.

## O que ele diagnostica

São 5 categorias de problema, cobertas por 32 regras (`dados/regras.json`):

| Categoria | Exemplos de diagnóstico |
|---|---|
| Inicialização | fonte queimada, carregador com defeito, disco com defeito, sistema corrompido, memória mal encaixada |
| Vídeo | cabo de vídeo, placa de vídeo, driver de vídeo, backlight queimado |
| Superaquecimento | poeira e pasta térmica, cooler com defeito, ventilação obstruída |
| Lentidão | HD lento, malware, memória insuficiente, disco cheio, programas na inicialização |
| Internet | driver de rede, IP/DNS, provedor, roteador com defeito |

## Como funciona

- **Base de conhecimento** (`dados/`): as regras ficam em `regras.json` e as perguntas em `perguntas.json`, separadas do código. Dá para mudar o conhecimento sem mexer no Python.
- **Motor de inferência** (`techdiagnose/motor.py`): encadeamento para frente. Ele aplica as regras repetidamente até nenhuma regra nova disparar (ponto fixo), e cada regra dispara uma vez só (refração).
- **Fatores de certeza (CF)**: cada regra tem um CF entre 0 e 1. Quando duas regras chegam na mesma conclusão, as certezas se somam (`a + b * (1 - a)`). A resposta "provavelmente" vale 0.6, e um diagnóstico com CF abaixo de 0.40 aparece como hipótese fraca.
- **Explicação**: o sistema responde **"por quê?"** (por que está fazendo aquela pergunta) e **"como?"** (qual cadeia de regras levou ao diagnóstico).
- **Histórico** (`dados/historico_atendimentos.csv`): 200 atendimentos fictícios da TechFix, usados para mostrar quantas vezes cada problema aparece e o tempo e o custo médios de cada um.

## Instalação

Precisa do **Python 3.10 ou mais novo**.

```bash
git clone https://github.com/techdiagnose-uva/techdiagnose.git
cd techdiagnose

# (opcional, mas recomendado) ambiente virtual
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

## Como rodar

**Console (versão principal):**

```bash
python main.py
```

**Interface web (Streamlit):**

```bash
streamlit run app.py
```

Ele abre no navegador. O endereço aparece no terminal em **Local URL** (normalmente `http://localhost:8501`) e só funciona enquanto o comando estiver rodando. Para parar, use `Ctrl+C`.

Para usar sem instalar nada, acesse a [versão web](https://techdiagnose-dsy6edz5dnhujzrk2zuvuk.streamlit.app/).

**Estatísticas do histórico de atendimentos:**

```bash
python -m techdiagnose.estatisticas
```

**Testes:**

```bash
pytest
```

## Exemplos para testar
Cenário	Respostas	Resultado esperado
Fonte queimada	Inicialização: não liga = sim, testou outra tomada = sim, computador de mesa = sim	Fonte queimada, certeza 72%
Duas regras na mesma conclusão	Superaquecimento: desliga sozinho, ventoinha barulhenta, sem limpeza há mais de 1 ano e lento ao esquentar = sim	Poeira e pasta térmica, certeza de cerca de 76% (R17 e R21 combinadas)
Sem conclusão	Qualquer categoria, todas as respostas "não"	"Não foi possível concluir com as informações fornecidas"

## Estrutura do projeto

```
techdiagnose/
├── app.py                      # interface web (Streamlit)
├── main.py                     # interface de console
├── dados/
│   ├── regras.json             # 32 regras (R01 a R32)
│   ├── perguntas.json          # uma pergunta por sintoma
│   └── historico_atendimentos.csv
├── techdiagnose/
│   ├── base_conhecimento.py    # carrega e valida os JSON
│   ├── motor.py                # encadeamento para frente e fatores de certeza
│   ├── explicacao.py           # "por quê?" e "como?"
│   ├── interface_console.py    # perguntas e respostas no terminal
│   └── estatisticas.py         # frequência, tempo e custo médio
├── tests/                      # testes com pytest
└── docs/
    └── documentacao_tecnica.md # documentação técnica
```
## Documentação técnica

O dicionário de fatos, a tabela das 32 regras, o funcionamento do motor, o módulo de explicação, o tratamento de exceções, como adicionar uma regra e as limitações do sistema estão em docs/documentacao_tecnica.md.

## Limitações

Só encadeamento para frente; não há encadeamento para trás.
As premissas das regras são só conjunções (E), sem OU nem negação.
O CF das respostas é fixo (1.0 e 0.6).
O conhecimento cobre 22 defeitos comuns; casos fora deles terminam em "não foi possível concluir".

## Integrantes

| Nome | GitHub |
|---|---|
| João Gabriel Augusto Cardoso - 1250108567 | [@Auguxtow](https://github.com/Auguxtow) |
| Rafael Ribeiro de Souza - 1250110204 | [@L0zart](https://github.com/L0zart) |
| Rafael Pinto de Souza Salgueiro - 1250109417| [@szpeeKi](https://github.com/szpeeKi) |
