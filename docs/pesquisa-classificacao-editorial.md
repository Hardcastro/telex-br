# Pesquisa: candidatos para os buckets direita/esquerda/centro

Este documento **não é uma decisão final** — é o material de apoio para o time
validar e ativar os slots `pending_review` em `config/sources.json` (ver
seção b do [blueprint](https://claude.ai/code/artifact/7735ea40-7bab-4654-b95c-c0fe597cda31)
e o `README.md`). Os candidatos abaixo vêm de duas fontes publicadas — não de
opinião própria — e cada RSS foi testado contra a rede de verdade antes de
entrar aqui.

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

## O que já foi feito em `config/sources.json`

Preenchi `name` e `rss` dos 11 slots com RSS confirmado (deixei o 12º —
centro, slot 4 — como estava, já que não achei um candidato com feed
funcional). **Todos continuam com `"status": "pending_review"`** — a
ativação (trocar para `"active"`) é a etapa que falta, e é do time, não
minha: dá uma olhada nos nomes/fontes acima, principalmente no bucket
centro, e troca o status de quem aprovar.
