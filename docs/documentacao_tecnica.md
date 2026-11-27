# TechDiagnose: documentação técnica

Sistema especialista de triagem de defeitos em computadores para a TechFix Assistência Técnica
(empresa fictícia). Este documento descreve a base de conhecimento, o motor de inferência, o
módulo de explicação e como o código está organizado.

## 1. Visão geral

O atendente (ou o próprio cliente) escolhe a categoria do problema e responde perguntas sobre os
sintomas. O sistema infere o diagnóstico por **encadeamento para frente** com **fatores de
certeza**, sugere a solução, diz se o caso pode ser resolvido por atendimento **remoto** ou
precisa ir para a **bancada** e explica o raciocínio ("por quê?" e "como?").

Categorias: inicialização, vídeo, superaquecimento, lentidão e internet.

### Organização do código

| Arquivo | Responsabilidade |
|---|---|
| `dados/regras.json` | 32 regras (R01 a R32) |
| `dados/perguntas.json` | uma pergunta por sintoma (39) |
| `dados/historico_atendimentos.csv` | 200 atendimentos fictícios da TechFix |
| `techdiagnose/base_conhecimento.py` | carrega e valida os JSON |
| `techdiagnose/motor.py` | memória de trabalho, ciclo reconhecer-agir, fatores de certeza, seleção de perguntas e descarte de regras |
| `techdiagnose/explicacao.py` | "por quê?", "como?" e regras descartadas |
| `techdiagnose/estatisticas.py` | frequência, tempo e custo médio do histórico |
| `techdiagnose/interface_console.py` | interface de perguntas e respostas no terminal |
| `main.py` | ponto de entrada do console |
| `app.py` | interface web em Streamlit |
| `tests/` | testes com pytest |

O conhecimento fica nos arquivos JSON, separado do código. Para mudar o que o sistema sabe não
é preciso mexer no Python (ver seção 7).

## 2. Base de conhecimento

### Formato de uma regra

```json
{
  "id": "R17",
  "categoria": "superaquecimento",
  "se": ["suspeita_superaquecimento", "sem_limpeza_1_ano"],
  "entao": "poeira_pasta_termica",
  "cf": 0.85,
  "tipo": "diagnostico",
  "descricao": "Superaquecimento + falta de limpeza indica acúmulo de poeira",
  "solucao": "Limpeza interna e troca da pasta térmica",
  "encaminhamento": "bancada"
}
```

| Campo | Significado |
|---|---|
| `id` | identificador único (R01 a R32) |
| `categoria` | categoria da triagem a que a regra pertence |
| `se` | premissas; todas precisam ser verdadeiras (conjunção) |
| `entao` | fato concluído |
| `cf` | fator de certeza da regra, entre 0 e 1 |
| `tipo` | `intermediario` (conclusão parcial) ou `diagnostico` (conclusão final) |
| `descricao` | frase usada nas explicações |
| `solucao`, `encaminhamento` | só em diagnósticos; `encaminhamento` é `remoto` ou `bancada` |

### Formato de uma pergunta

```json
{"fato": "desliga_sozinho", "categoria": "superaquecimento", "texto": "O computador desliga sozinho durante o uso?"}
```

O campo `fato` liga a pergunta às premissas das regras.

### Validação (`base_conhecimento.py`)

`carregar_base()` lê os dois arquivos e levanta `ErroBaseConhecimento`, com mensagem em
português, quando encontra:

- arquivo inexistente ou JSON mal formado (a mensagem informa a linha);
- campo obrigatório faltando; diagnóstico sem `solucao` ou `encaminhamento`;
- `id` repetido; `tipo` diferente de `intermediario`/`diagnostico`; `se` vazio;
- `cf` que não é número entre 0 e 1;
- pergunta repetida para o mesmo fato;
- premissa que não é respondida por nenhuma pergunta nem concluída por nenhuma regra (a regra
  nunca poderia disparar).

## 3. Dicionário de fatos

Há três tipos de fato:

- **sintoma**: vem da resposta do usuário; tem uma pergunta em `perguntas.json`;
- **intermediário**: conclusão parcial, usada como premissa de outras regras;
- **diagnóstico**: conclusão final, com solução e encaminhamento.

### Sintomas

| Fato | Categoria | Pergunta |
|---|---|---|
| `nao_liga` | inicializacao | O computador não liga (nenhuma luz, nenhum barulho)? |
| `testou_outra_tomada` | inicializacao | Você já testou em outra tomada e continuou sem ligar? |
| `e_desktop` | inicializacao | O computador é de mesa (desktop)? |
| `e_notebook` | inicializacao | O computador é um notebook? |
| `liga_mas_nao_inicia_sistema` | inicializacao | O computador liga, mas o Windows não chega a abrir? |
| `barulho_clique_disco` | inicializacao | Dá para ouvir um barulho de clique vindo do disco? |
| `mensagem_disco_nao_encontrado` | inicializacao | Aparece uma mensagem dizendo que o disco não foi encontrado? |
| `travou_durante_atualizacao` | inicializacao | O problema começou depois de uma atualização que travou ou foi interrompida? |
| `bipes_ao_ligar` | inicializacao | O computador faz bipes ao ligar? |
| `mexeu_no_hardware_recente` | inicializacao | Alguém abriu o computador ou trocou alguma peça recentemente? |
| `tela_preta_com_pc_ligado` | video | A tela fica preta mesmo com o computador ligado? |
| `monitor_com_luz` | video | A luz do monitor está acesa? |
| `imagem_com_listras_ou_artefatos` | video | A imagem aparece com listras, quadradinhos ou cores estranhas? |
| `mexer_no_cabo_muda_imagem` | video | A imagem muda quando você mexe no cabo do monitor? |
| `piora_em_jogos` | video | O problema piora quando você joga ou usa programas pesados de vídeo? |
| `atualizou_driver_video` | video | O problema começou depois de atualizar o driver da placa de vídeo? |
| `imagem_aparece_com_lanterna` | video | Apontando uma lanterna para a tela, dá para ver a imagem bem fraca? |
| `desliga_sozinho` | superaquecimento | O computador desliga sozinho durante o uso? |
| `ventoinha_barulhenta` | superaquecimento | A ventoinha está fazendo mais barulho que o normal? |
| `gabinete_muito_quente` | superaquecimento | O gabinete ou a base do notebook fica muito quente? |
| `sem_limpeza_1_ano` | superaquecimento | Faz mais de um ano que o computador não passa por uma limpeza interna? |
| `ventoinha_parada` | superaquecimento | A ventoinha está parada (não gira)? |
| `lento_ao_esquentar` | superaquecimento | O computador fica lento quando esquenta? |
| `usa_em_superficie_macia` | superaquecimento | Você costuma usar o notebook na cama, no sofá ou no colo? |
| `lento_geral` | lentidao | O computador está lento no uso geral? |
| `disco_100_porcento` | lentidao | No Gerenciador de Tarefas, o disco fica em 100% de uso? |
| `usa_hd_mecanico` | lentidao | O computador usa HD comum (não SSD)? |
| `demora_muito_para_iniciar` | lentidao | O computador demora muito para iniciar? |
| `propagandas_ou_popups` | lentidao | Aparecem propagandas ou janelas abrindo sozinhas? |
| `ram_menor_8gb` | lentidao | O computador tem menos de 8 GB de memória RAM? |
| `muitas_abas_abertas` | lentidao | Você costuma deixar muitas abas do navegador abertas? |
| `disco_quase_cheio` | lentidao | O disco está quase cheio (menos de 10% livre)? |
| `atualizacao_em_andamento` | lentidao | O Windows está baixando ou instalando atualizações agora? |
| `sem_internet` | internet | O computador está sem internet? |
| `outros_aparelhos_conectam` | internet | Outros aparelhos (celular, TV) conseguem usar a internet normalmente? |
| `adaptador_rede_sumiu` | internet | O ícone ou o adaptador de rede sumiu das configurações do Windows? |
| `conecta_mas_nao_navega` | internet | O computador diz que está conectado, mas os sites não abrem? |
| `luz_internet_roteador_apagada` | internet | A luz de internet do roteador está apagada ou vermelha? |
| `reiniciar_roteador_resolve_pouco` | internet | Reiniciar o roteador resolve, mas a internet volta a cair depois? |

### Intermediários

| Fato | Categoria | Concluído por | Usado por |
|---|---|---|---|
| `falha_alimentacao` | inicializacao | R01 | R02, R03 |
| `falha_armazenamento` | inicializacao | R04, R05 | R06 |
| `problema_video` | video | R09, R10 | R11, R12, R13 |
| `suspeita_superaquecimento` | superaquecimento | R15, R16 | R17, R18, R19 |
| `throttling_termico` | superaquecimento | R19 | R20, R21 |
| `problema_rede_no_pc` | internet | R28 | R29, R30 |

### Diagnósticos

| Fato | Categoria | Regras | Solução | Encaminhamento |
|---|---|---|---|---|
| `fonte_queimada` | inicializacao | R02 | Teste da fonte com multímetro e troca da fonte de alimentação | bancada |
| `carregador_defeituoso` | inicializacao | R03 | Teste com outro carregador compatível; troca do carregador ou da bateria | bancada |
| `disco_defeituoso` | inicializacao | R06 | Backup dos dados, se possível, e troca do HD/SSD | bancada |
| `sistema_corrompido` | inicializacao | R07 | Reparo de inicialização ou restauração do Windows | remoto |
| `memoria_ram_mal_encaixada` | inicializacao | R08 | Retirar, limpar os contatos e reencaixar a memória RAM | bancada |
| `cabo_video_defeituoso` | video | R11 | Reencaixar ou trocar o cabo HDMI/DisplayPort | remoto |
| `placa_video_defeituosa` | video | R12 | Teste com outra placa de vídeo e troca da placa | bancada |
| `driver_video_problema` | video | R13 | Reinstalar ou voltar para a versão anterior do driver de vídeo | remoto |
| `backlight_queimado` | video | R14 | Troca do backlight ou da tela do notebook | bancada |
| `poeira_pasta_termica` | superaquecimento | R17, R21 | Limpeza interna e troca da pasta térmica | bancada |
| `cooler_defeituoso` | superaquecimento | R18 | Troca do cooler | bancada |
| `ventilacao_obstruida` | superaquecimento | R20 | Usar o notebook sobre superfície rígida ou suporte com ventilação | remoto |
| `hd_lento` | lentidao | R22 | Troca do HD por SSD com clonagem do sistema | bancada |
| `excesso_programas_inicializacao` | lentidao | R23 | Desativar programas desnecessários na inicialização | remoto |
| `malware` | lentidao | R24 | Varredura com antivírus e remoção do malware | remoto |
| `memoria_insuficiente` | lentidao | R25 | Upgrade de memória RAM | bancada |
| `armazenamento_cheio` | lentidao | R26 | Limpeza de arquivos temporários e liberação de espaço no disco | remoto |
| `atualizacao_segundo_plano` | lentidao | R27 | Aguardar o fim das atualizações e reiniciar o computador | remoto |
| `driver_rede_problema` | internet | R29 | Reinstalar o driver da placa de rede | remoto |
| `configuracao_ip_dns` | internet | R30 | Renovar o IP e limpar o DNS (ipconfig /release, /renew e /flushdns) | remoto |
| `problema_provedor` | internet | R31 | Entrar em contato com o provedor de internet | remoto |
| `roteador_defeituoso` | internet | R32 | Atualizar o firmware ou trocar o roteador | remoto |

## 4. Tabela de regras

| ID | Categoria | SE | ENTÃO | CF | Tipo |
|---|---|---|---|---|---|
| R01 | inicializacao | `nao_liga` E `testou_outra_tomada` | `falha_alimentacao` | 0.90 | intermediario |
| R02 | inicializacao | `falha_alimentacao` E `e_desktop` | `fonte_queimada` | 0.80 | diagnostico |
| R03 | inicializacao | `falha_alimentacao` E `e_notebook` | `carregador_defeituoso` | 0.70 | diagnostico |
| R04 | inicializacao | `liga_mas_nao_inicia_sistema` E `barulho_clique_disco` | `falha_armazenamento` | 0.80 | intermediario |
| R05 | inicializacao | `liga_mas_nao_inicia_sistema` E `mensagem_disco_nao_encontrado` | `falha_armazenamento` | 0.70 | intermediario |
| R06 | inicializacao | `falha_armazenamento` | `disco_defeituoso` | 0.80 | diagnostico |
| R07 | inicializacao | `liga_mas_nao_inicia_sistema` E `travou_durante_atualizacao` | `sistema_corrompido` | 0.75 | diagnostico |
| R08 | inicializacao | `bipes_ao_ligar` E `mexeu_no_hardware_recente` | `memoria_ram_mal_encaixada` | 0.85 | diagnostico |
| R09 | video | `tela_preta_com_pc_ligado` E `monitor_com_luz` | `problema_video` | 0.80 | intermediario |
| R10 | video | `imagem_com_listras_ou_artefatos` | `problema_video` | 0.85 | intermediario |
| R11 | video | `problema_video` E `mexer_no_cabo_muda_imagem` | `cabo_video_defeituoso` | 0.85 | diagnostico |
| R12 | video | `problema_video` E `piora_em_jogos` | `placa_video_defeituosa` | 0.80 | diagnostico |
| R13 | video | `problema_video` E `atualizou_driver_video` | `driver_video_problema` | 0.75 | diagnostico |
| R14 | video | `tela_preta_com_pc_ligado` E `imagem_aparece_com_lanterna` | `backlight_queimado` | 0.90 | diagnostico |
| R15 | superaquecimento | `desliga_sozinho` E `ventoinha_barulhenta` | `suspeita_superaquecimento` | 0.70 | intermediario |
| R16 | superaquecimento | `gabinete_muito_quente` | `suspeita_superaquecimento` | 0.60 | intermediario |
| R17 | superaquecimento | `suspeita_superaquecimento` E `sem_limpeza_1_ano` | `poeira_pasta_termica` | 0.85 | diagnostico |
| R18 | superaquecimento | `suspeita_superaquecimento` E `ventoinha_parada` | `cooler_defeituoso` | 0.90 | diagnostico |
| R19 | superaquecimento | `suspeita_superaquecimento` E `lento_ao_esquentar` | `throttling_termico` | 0.80 | intermediario |
| R20 | superaquecimento | `throttling_termico` E `usa_em_superficie_macia` | `ventilacao_obstruida` | 0.80 | diagnostico |
| R21 | superaquecimento | `throttling_termico` E `sem_limpeza_1_ano` | `poeira_pasta_termica` | 0.75 | diagnostico |
| R22 | lentidao | `lento_geral` E `disco_100_porcento` E `usa_hd_mecanico` | `hd_lento` | 0.85 | diagnostico |
| R23 | lentidao | `lento_geral` E `demora_muito_para_iniciar` | `excesso_programas_inicializacao` | 0.70 | diagnostico |
| R24 | lentidao | `lento_geral` E `propagandas_ou_popups` | `malware` | 0.85 | diagnostico |
| R25 | lentidao | `lento_geral` E `ram_menor_8gb` E `muitas_abas_abertas` | `memoria_insuficiente` | 0.80 | diagnostico |
| R26 | lentidao | `lento_geral` E `disco_quase_cheio` | `armazenamento_cheio` | 0.75 | diagnostico |
| R27 | lentidao | `lento_geral` E `atualizacao_em_andamento` | `atualizacao_segundo_plano` | 0.60 | diagnostico |
| R28 | internet | `sem_internet` E `outros_aparelhos_conectam` | `problema_rede_no_pc` | 0.90 | intermediario |
| R29 | internet | `problema_rede_no_pc` E `adaptador_rede_sumiu` | `driver_rede_problema` | 0.80 | diagnostico |
| R30 | internet | `problema_rede_no_pc` E `conecta_mas_nao_navega` | `configuracao_ip_dns` | 0.70 | diagnostico |
| R31 | internet | `sem_internet` E `luz_internet_roteador_apagada` | `problema_provedor` | 0.85 | diagnostico |
| R32 | internet | `sem_internet` E `reiniciar_roteador_resolve_pouco` | `roteador_defeituoso` | 0.70 | diagnostico |

## 5. Motor de inferência (`motor.py`)

### Respostas e memória de trabalho

A **memória de trabalho** é um dicionário `fato -> CF`. As respostas entram assim:

| Resposta | Valor | Efeito |
|---|---|---|
| sim | 1.0 | entra na memória com CF 1.0 |
| provavelmente | 0.6 | entra na memória com CF 0.6 |
| não | `False` | não entra na memória |
| não sei | `None` | não entra na memória (desconhecido) |

### Ciclo reconhecer-agir

`inferir(regras, respostas)` repete o ciclo abaixo até não haver mais o que disparar:

1. **Match** (`casar`): seleciona as regras ainda não disparadas cujas premissas estão todas na
   memória de trabalho. Esse é o **conjunto de conflito**.
2. **Resolução de conflito** (`escolher_regra`): escolhe a regra com mais premissas (a mais
   específica); no empate, a de maior CF.
3. **Disparo** (`disparar`): calcula o CF da conclusão, grava na memória e registra no rastro
   (`disparos`) os valores usados.
4. **Refração**: a regra disparada entra em `disparadas` e não dispara de novo.
5. **Ponto fixo**: quando o conjunto de conflito fica vazio, o motor para.

Detalhe do match: uma regra espera enquanto outra regra do conjunto de conflito ainda vai
concluir uma das premissas dela. Sem isso, a resolução de conflito faria a R17 (2 premissas)
disparar antes da R16 (1 premissa), com `suspeita_superaquecimento` em 0.70 em vez de 0.88, e
pela refração o valor não seria corrigido. A regra funciona porque não há ciclos entre as regras
da base.

### Fatores de certeza (MYCIN simplificado)

| Situação | Cálculo |
|---|---|
| conjunção das premissas | menor CF entre as premissas |
| aplicação da regra | CF da regra x CF das premissas |
| mesmo fato concluído por duas regras | CF1 + CF2 x (1 - CF1) |
| diagnóstico com CF < 0.40 | marcado como hipótese fraca |

Exemplo (superaquecimento, todas as respostas "sim"):

```
R15: desliga_sozinho (1.0) E ventoinha_barulhenta (1.0) -> suspeita_superaquecimento
     0.70 x min(1.0, 1.0) = 0.70
R16: gabinete_muito_quente (1.0) -> suspeita_superaquecimento
     0.60 x 1.0 = 0.60;  combinado: 0.70 + 0.60 x (1 - 0.70) = 0.88
R17: suspeita_superaquecimento (0.88) E sem_limpeza_1_ano (1.0) -> poeira_pasta_termica
     0.85 x min(0.88, 1.0) = 0.75
```

### Seleção de perguntas e descarte de regras

- **Triagem por categoria**: o usuário escolhe a categoria e só são feitas perguntas sobre
  sintomas usados pelas regras dessa categoria.
- `regras_descartadas(regras, respostas)` devolve `{id: motivo}` das regras que não podem mais
  disparar: alguma premissa foi respondida "não" ou "não sei", ou (em cascata) todas as regras
  que concluem um intermediário usado como premissa já foram descartadas. Repete até não
  descartar mais nada.
- `proxima_pergunta(...)` percorre as regras da categoria que não foram descartadas, na ordem do
  JSON, e devolve o primeiro sintoma ainda não respondido; devolve `None` quando não há mais
  perguntas úteis.

Exemplo: em superaquecimento, respondendo "não" para `desliga_sozinho` e `gabinete_muito_quente`,
R15 e R16 caem, `suspeita_superaquecimento` fica impossível e R17 a R21 caem em cascata. O
atendimento termina com 2 das 7 perguntas da categoria.

## 6. Módulo de explicação (`explicacao.py`)

- **Por quê?** (`explicar_pergunta`): quando o usuário digita `?`, mostra a regra em teste (a
  primeira regra viva da categoria que usa aquele sintoma) e as regras que dependem da conclusão
  dela.
- **Como?** (`explicar_raciocinio`): ao final, mostra
  1. os fatos informados;
  2. as regras disparadas, na ordem, com a conta do CF de cada uma e da combinação;
  3. as regras descartadas da categoria e o motivo.
- `explicar(resultado, fato)`: cadeia em árvore do diagnóstico até as respostas do usuário.

## 7. Como adicionar uma regra

1. Acrescentar a regra em `dados/regras.json` com um `id` novo.
2. Se ela usa um sintoma novo, acrescentar a pergunta em `dados/perguntas.json` com a mesma
   categoria.
3. Rodar o programa. Se faltar algum campo ou a pergunta do sintoma novo, a validação mostra qual
   regra e qual fato estão com problema.

Nenhuma linha de Python precisa ser alterada.

## 8. Tratamento de exceções

| Situação | Comportamento |
|---|---|
| base de conhecimento inválida | mensagem da `ErroBaseConhecimento` e saída com código 1, sem traceback |
| histórico CSV ausente ou inválido | aviso e o programa segue sem estatísticas |
| resposta inválida | `ler_resposta` repete a pergunta; aceita maiúsculas, falta de acento e abreviações (s, p, n, ns) |
| opção de menu inválida | repete até receber um número válido |
| nenhum diagnóstico | "Não foi possível concluir com as informações fornecidas." |
| Ctrl+C ou fim da entrada | "Atendimento encerrado." e saída normal |

## 9. Histórico e estatísticas (`estatisticas.py`)

`historico_atendimentos.csv` tem 200 atendimentos fictícios (janeiro a outubro de 2026) com as
colunas `id, data, categoria, diagnostico, encaminhamento, tempo_min, custo_reais, resolvido`.
Todos os diagnósticos do CSV existem nas regras, com a mesma categoria e encaminhamento.

O console mostra, junto de cada diagnóstico, quantos casos parecidos a TechFix já atendeu e o
tempo e custo médios. O Streamlit mostra também um gráfico com a frequência dos diagnósticos da
categoria.

## 10. Testes

Rodar com `pytest` na raiz do projeto.

| Arquivo | O que cobre |
|---|---|
| `tests/test_base_conhecimento.py` | carga da base real, JSON inválido, campo faltando, CF fora de 0 e 1, id repetido, fato sem origem |
| `tests/test_motor.py` | combinação de CF, cenário por categoria, refração, "provavelmente"/"não"/"não sei", hipótese fraca, sem conclusão, seleção de perguntas |
| `tests/test_explicacao.py` | "por quê?", "como?", conta do CF e regras descartadas |
| `tests/test_estatisticas.py` | médias, frequência e erros do CSV |

## 11. Limitações

- Só encadeamento para frente; não há encadeamento para trás para confirmar uma hipótese.
- As premissas são só conjunções (E); não há regras com OU nem com negação.
- O CF das respostas é fixo (1.0 e 0.6); o usuário não informa um valor próprio.
- A espera por reforço no match supõe que não há ciclos entre as regras.
- O conhecimento cobre 22 defeitos comuns; casos fora deles terminam em "não foi possível
  concluir".
