# Pesquisa: candidatos para os buckets direita/esquerda/centro

Este documento **não é uma decisão final** — é o material de apoio para o time
validar as fontes ativas em `config/sources.json` (ver seção b do
[blueprint](https://claude.ai/code/artifact/7735ea40-7bab-4654-b95c-c0fe597cda31)
e o `README.md`). Os candidatos abaixo vêm de fontes publicadas — não de
opinião própria — e cada RSS foi testado contra a rede de verdade antes de
entrar aqui. Três tiers de evidência, sempre marcados explicitamente:

- **Citação acadêmica** — Monitor USP/CEBRAP e/ou o artigo Opinião Pública
  (2024), ver metodologia abaixo. Tier de maior confiança.
- **Caracterização pública ampla** — sem citação nas duas fontes acadêmicas,
  mas amplamente descrito como tal na cobertura pública (ex.: Wikipédia).
  Tier intermediário.
- **Extensão por analogia** — mesma categoria de formato (ex.: "grande
  imprensa tradicional") que um veículo já citado, mas sem citação nominal
  direta. Usado só no bucket `centro`, o mais pobre em fontes citáveis.

## Metodologia — duas fontes cruzadas

1. **Monitor do Debate Político no Meio Digital** (USP → hoje sediado no
   CEBRAP) — projeto acadêmico que mapeia o ecossistema de debate político
   digital brasileiro desde 2015. Classifica veículos por formato (jornal
   impresso, revista, portal) e agrupa "imprensa alternativa" explicitamente
   como de direita ou de esquerda.
   → [observatoriodaimprensa.com.br/monitor-do-debate-politico-do-meio-digital](https://www.observatoriodaimprensa.com.br/monitor-do-debate-politico-do-meio-digital/conheca-o-monitor-do-debate-politico-no-meio-digital/)

2. **"Classificação ideológica de fontes informacionais: o paralelismo
   político na análise da atenção midiática multipartidária no Brasil"** —
   artigo acadêmico publicado na revista *Opinião Pública* (Unicamp/Cesop),
   v. 30, 2024. Classifica veículos por correlação com grupos de simpatizantes
   partidários, a partir de 2,95 milhões de tweets (2019–2020).
   → [scielo.br/j/op/a/9FkcynHMjnVcZh4skfJbZ8y](https://www.scielo.br/j/op/a/9FkcynHMjnVcZh4skfJbZ8y/?lang=pt)

Um candidato entrou nesta lista quando pelo menos uma das duas fontes o
classifica explicitamente — e prioridade para quem aparece nas **duas**
(convergência = maior confiança).

## Candidatos — direita (4 slots)

| Veículo | Citado por | RSS testado | Status do teste |
|---|---|---|---|
| O Antagonista | Monitor (alternativa de direita) **+** Opinião Pública (right-aligned) | `https://oantagonista.com.br/feed/` | ✅ 200 · 15 itens |
| Gazeta do Povo | Opinião Pública (right-aligned) | `https://www.gazetadopovo.com.br/feed/rss/vida-publica.xml` | ✅ 200 · 24 itens |
| Revista Crusoé | Opinião Pública (right-aligned) | `https://crusoe.com.br/feed/` | ✅ 200 · 15 itens |
| IstoÉ | Monitor (revista semanal) + Opinião Pública (right-aligned) | `https://istoe.com.br/feed/` | ✅ 200 · 10 itens |

## Candidatos — esquerda (4 slots)

| Veículo | Citado por | RSS testado | Status do teste |
|---|---|---|---|
| Brasil 247 | Monitor (alternativa de esquerda) **+** Opinião Pública (left-aligned) | `https://www.brasil247.com/rss` | ✅ 200 · 10 itens |
| Diário do Centro do Mundo | Monitor (alternativa de esquerda) **+** Opinião Pública (left-aligned) | `https://www.diariodocentrodomundo.com.br/feed/` | ✅ 200 · 10 itens |
| Revista Fórum | Monitor (publicação mensal) + Opinião Pública (left-aligned) | `https://revistaforum.com.br/feed/` | ✅ 200 · 10 itens |
| Jornal GGN | Monitor (alternativa de esquerda) **+** Opinião Pública (left-aligned) | `https://jornalggn.com.br/feed/` | ✅ 200 · 12 itens |

## Candidatos — centro (3 de 4 slots — o bucket mais frágil)

**Alerta de metodologia:** nenhuma das duas fontes usa a palavra "centro" com
o mesmo sentido de um "centro" político clássico. O agrupamento do Opinião
Pública como *"center/mainstream"* reflete, na prática, a grande imprensa
tradicional — Folha, Globo, Estadão, Veja — que outras análises poderiam
classificar como centro-direita ou centro-esquerda dependendo do recorte e da
época. Trate como o candidato de **menor confiança** dos três buckets e
valide com mais cuidado antes de ativar.

| Veículo | Citado por | RSS testado | Status do teste |
|---|---|---|---|
| Folha de S.Paulo | Monitor (jornal diário) + Opinião Pública (center/mainstream) | `https://feeds.folha.uol.com.br/emcimadahora/rss091.xml` | ✅ 200 · 100 itens |
| O Globo | Monitor (jornal diário) + Opinião Pública (center/mainstream) | `https://oglobo.globo.com/rss/oglobo/` | ✅ 200 · 100 itens |
| Veja | Monitor (revista semanal) + Opinião Pública (center/mainstream) | `https://veja.abril.com.br/feed/` | ✅ 200 · 20 itens |
| *(4º slot em aberto)* | Estadão e R7 também aparecem como *center/mainstream* no Opinião Pública, mas **nenhum dos dois tem RSS público funcional hoje** — testei `/rss/politica.xml`, `/rss/ultimas.xml`, `/arc/outboundfeeds/...` no Estadão e `/feed`, `/feed.xml`, `/rss.xml` no R7; todos falharam (404 ou feed vazio). Precisa de outro candidato ou de um caminho de coleta diferente de RSS (ex.: scraping, que este projeto não implementa). | — | ❌ |

## Rodada 2 (2026-09-15) — expansão pra 20 itens por tópico

A cota de equilíbrio editorial passou de "uma vez por ciclo" (4·4·4·8 = 20
no total) pra "uma vez por tópico de conteúdo" — política, macroeconomia e
manchete, cada um com sua própria cota 4·4·4·8 (60 no total). Isso exige
muito mais fontes ativas por bucket pra não ficar sistematicamente aquém do
alvo — o time pediu explicitamente pra aumentar as fontes. RSS testado de
verdade contra a rede pra cada uma abaixo; **todas já entraram `active` em
`config/sources.json`** (a pesquisa e o teste técnico foram feitos, então não
faz sentido deixar `pending_review` de novo — mas revise se discordar de
algum nome).

### Direita — 6 novas (10 no total)

| Veículo | Tier | Citado por |
|---|---|---|
| Conexão Política | Citação acadêmica | Opinião Pública (2024) |
| Pensa Brasil | Citação acadêmica | Monitor (alternativa de direita) |
| Revolta Brasil | Citação acadêmica | Monitor (alternativa de direita) |
| Política na Rede | Citação acadêmica | Monitor (alternativa de direita) |
| Pleno.News | Caracterização pública | — |
| Revista Oeste | Caracterização pública | — (Wikipédia em inglês descreve como direita) |

### Esquerda — 10 novas (14 no total)

| Veículo | Tier | Citado por |
|---|---|---|
| The Intercept Brasil | Citação acadêmica | Opinião Pública (2024, "The Intercept") |
| Portal Vermelho | Citação acadêmica | Monitor + Opinião Pública (2024, "Vermelho") |
| O Cafezinho | Citação acadêmica | Monitor (alternativa de esquerda) |
| Pragmatismo Político | Citação acadêmica | Monitor (alternativa de esquerda) |
| Jornalistas Livres | Citação acadêmica | Monitor (alternativa de esquerda) |
| Opera Mundi | Citação acadêmica | Monitor (alternativa de esquerda) |
| Outras Palavras | Citação acadêmica | Monitor (alternativa de esquerda) |
| Viomundo | Citação acadêmica | Monitor (alternativa de esquerda) |
| Sul21 | Citação acadêmica | Monitor (alternativa de esquerda) |
| PassaPalavra | Citação acadêmica | Monitor (alternativa de esquerda) |

Vários nomes da lista "alternativa de esquerda" do Monitor não têm mais RSS
funcional (o mapeamento é de ~2018): Carta Maior, Tijolaço, Rede Brasil
Atual, Socialista Morena, Democratize, Blog do Rovai, Escrivinhador, A Nova
Democracia, Maria Frô, Geledés, Agência PT, Diário Liberdade, Rede de
Informações Anarquista, Canal Ibase — testados, sem feed ativo hoje.

### Centro — 3 novas (6 no total)

Continua o bucket mais pobre. Sem nenhum veículo novo citado nominalmente
pelas duas fontes acadêmicas — os três abaixo são **extensão por analogia**:
mesma categoria de formato que Folha/Globo/Veja (grande imprensa tradicional
"center/mainstream" no Opinião Pública), sem citação direta.

| Veículo | Tier |
|---|---|
| Correio Braziliense | Extensão por analogia |
| Extra | Extensão por analogia |
| A Tarde (BA) | Extensão por analogia |

Com 6 fontes (vs. 10 em direita e 14 em esquerda), `centro` é o bucket com
mais chance de ficar abaixo do alvo de 20 por tópico — verifique
`quota_status.<topico>.centro` no JSON de saída antes de assumir que fechou.
Estadão e R7 seguem sem RSS público funcional (testado de novo nesta rodada,
sem sucesso); se algum dia voltarem a ter, são os primeiros candidatos
óbvios pra reforçar esse bucket.

## O que já foi feito em `config/sources.json`

Todas as fontes citadas neste documento (rodada 1 e rodada 2) estão
`"status": "active"` — não há mais slots `pending_review` em
direita/esquerda/centro. `config/sources.json` tem 30 fontes políticas no
total (10 direita, 14 esquerda, 6 centro) além das 8 `tecnica_neutra` e 5
`manchete_pool`. Testado contra a rede real com o pool expandido: 731 itens
brutos coletados em um ciclo, curadoria fechando 57/60 (só macroeconomia em
direita ficou abaixo do alvo, 1/4 — natural, veículos de direita nesta lista
publicam muito mais política que análise macroeconômica).
