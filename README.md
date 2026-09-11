# Telex BR

Pipeline que coleta, classifica e cura notícias brasileiras a cada 12 horas,
respeitando um equilíbrio editorial fixo (4 direita · 4 esquerda · 4 centro ·
8 técnica/neutra) e destacando a notícia de maior audiência (proxy) e a de
maior repercussão (proxy) do ciclo. Implementação do blueprint técnico
publicado em [claude.ai/code/artifact/7735ea40-7bab-4654-b95c-c0fe597cda31](https://claude.ai/code/artifact/7735ea40-7bab-4654-b95c-c0fe597cda31).

## Rodando agora, em 2 minutos

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
python -m src.pipeline --demo
```

Isso roda o pipeline inteiro (coleta → classificação → pontuação → curadoria
→ exportação) sobre `data/sample/sample_items.json` — 30 itens de amostra
cobrindo os quatro buckets editoriais — sem nenhuma chamada de rede. Gera
`data/cycles/latest.json` e `data/cycles/latest.csv` e imprime um resumo no
terminal.

Rodar os testes (mesma base, sem rede, é o que roda no CI):

```bash
pip install -r requirements.txt
pytest -q
```

## Antes de rodar de verdade (`python -m src.pipeline`, sem `--demo`)

Abra **`config/sources.json`**. Os buckets `direita`, `esquerda` e `centro`
vêm com slots `"status": "pending_review"` e `"name"/"rss": "PREENCHER"` —
**de propósito**. Não atribuímos linha editorial a veículos reais por conta
própria (é uma chamada contestável e muda com o tempo — ver o blueprint,
seção b). Para ativar um slot:

1. Escolha o veículo, validando contra um observatório de mídia reconhecido
   (não só uma impressão pessoal).
2. Preencha `name` e `rss` (a URL do feed RSS do veículo).
3. Troque `"status": "pending_review"` para `"status": "active"`.

Enquanto os slots continuarem `pending_review`, `curate.py` roda normalmente
com o que tiver — o log avisa quantos slots faltam e o ciclo sai com menos
de 20 itens (a lacuna fica registrada em `quota_status` no JSON de saída, não
escondida). O bucket `tecnica_neutra` já vem preenchido com fontes
factuais/institucionais (agências públicas, dados oficiais, imprensa
econômica, checagem) — essa é uma classificação factual, não política.

## Estrutura

```
src/
  collect.py    01 · RSS (feedparser) + indicadores BCB/IBGE
  classify.py   02 · linha editorial (do bucket da fonte) + categoria (por palavra-chave)
  score.py      03 · cluster de cobertura + proxies opcionais (Trends, Reddit)
  curate.py     04 · seleciona 20 respeitando a cota 4·4·4·8, marca top view/réplica
  export.py     05 · grava JSON + CSV do ciclo
  pipeline.py   orquestra as 5 etapas, CLI (--demo, --window)
config/
  sources.json  tabela de fontes (editável, ver acima)
  keywords.json taxonomia de categoria (política/macroeconomia/manchete)
data/
  sample/       fixture usada pelo --demo
  cycles/       saída real (latest.json, latest.csv, histórico com timestamp)
tests/          smoke test em cima do modo --demo
.github/workflows/cycle.yml   gatilho de 12h (GitHub Actions)
```

## Proxies de impacto — o que é real e o que é estimado

Pageviews e contagens de compartilhamento reais não são públicos por fonte
no Brasil (e o CrowdTangle, caminho gratuito padrão pra isso, foi
descontinuado pela Meta em agosto de 2024). `score.py` compõe dois índices a
partir de sinais que **são** abertos:

| Sinal | Sempre disponível? | Como ligar |
|---|---|---|
| Tamanho do cluster de cobertura (quantas fontes do próprio ciclo publicaram algo parecido) | Sim — não depende de nenhuma credencial | já ligado |
| Google Trends (interesse de busca) | Não — precisa de `pip install -r requirements-optional.txt` | automático se o pacote estiver instalado |
| Menções no Reddit (r/brasil) | Não — precisa de credenciais | preencha `REDDIT_CLIENT_ID`/`REDDIT_CLIENT_SECRET` no `.env` (copie de `.env.example`) |

Sem os dois opcionais, `view_score` e `engagement_proxy_index` caem só no
cluster — funciona, mas dois itens do mesmo cluster empatam com mais
frequência. Vale a pena ligar pelo menos o Reddit (é grátis, só precisa de
um app tipo "script" em reddit.com/prefs/apps).

## Ligar ao Power BI (grátis)

1. `.github/workflows/cycle.yml` já commita `data/cycles/latest.csv` de
   volta no repositório a cada ciclo (veja abaixo).
2. No Power BI Desktop: **Obter Dados → Web** → cole a URL "raw" do
   arquivo no GitHub, algo como
   `https://raw.githubusercontent.com/SEU_USUARIO/telex-br/main/data/cycles/latest.csv`.
3. Publique no Power BI Service. Free tier: até 8 atualizações/dia em
   "Minha área de trabalho" — sobra folga para os 2 refreshes/dia do ciclo
   de 12h. Compartilhar exige **Publicar na Web** (público, sem login) —
   é a única forma de compartilhar sem licença Pro.
4. Se a atualização agendada do Service recusar o Web connector por
   detecção de fonte dinâmica, troque a URL no editor poder Query para uma
   string estática fixa (sem parâmetros) — normalmente resolve.

Looker Studio segue a mesma lógica (Conectar → URL) e não tem o limite de
8 atualizações/dia, se isso virar um problema no futuro.

## Ativar o gatilho de 12h (GitHub Actions)

1. `git init && git add . && git commit -m "telex-br: pipeline inicial"` (se
   ainda não fez isso).
2. Crie o repositório no GitHub e faça `git push`.
3. Pronto — `.github/workflows/cycle.yml` já está configurado para rodar às
   00:00 e 12:00 BRT (`cron: "0 3,15 * * *"`, em UTC) e commitar
   `data/cycles/latest.{json,csv}` de volta. Também dá pra disparar na mão
   pela aba **Actions → Ciclo Telex BR (12h) → Run workflow**.
4. Se for usar o proxy de Reddit: adicione `REDDIT_CLIENT_ID`,
   `REDDIT_CLIENT_SECRET` e `REDDIT_USER_AGENT` em **Settings → Secrets and
   variables → Actions**, e descomente as três linhas correspondentes no
   `cycle.yml`.

100% gratuito nesse desenho: GitHub Actions (cron), RSS + BCB/IBGE (coleta),
Power BI free (visualização). Nenhuma peça paga é necessária para o ciclo
de 12h funcionar de ponta a ponta.

## Limitações conhecidas / próximos passos

- **IBGE (PIB, desemprego):** `collect.py::fetch_ibge_indicator` está pronta
  mas não vem com código de tabela SIDRA pré-preenchido — não íamos
  inventar um número de tabela sem confirmar contra sidra.ibge.gov.br.
  Preencha `IBGE_PIB_TABLE` etc. no `.env` depois de checar a tabela certa.
- **Categoria por palavra-chave** (`config/keywords.json`) é simples de
  propósito. Se começar a classificar muita coisa errado, o próximo passo
  natural é trocar por NLP (spaCy `pt_core_news`) — a interface de
  `classify_category()` não muda, só a implementação interna.
- **GDELT, NewsData.io, Currents** (citados no blueprint como fontes
  adicionais) ainda não estão integrados em `collect.py` — hoje a coleta é
  só RSS + BCB/IBGE. RSS cobre a curadoria toda; os outros valem a pena
  principalmente se a lista de fontes RSS não for suficiente.
- **Perguntas de alinhamento do blueprint** (seção f) — várias ainda valem
  a pena fechar com o time antes de considerar isso "em produção": quem
  valida a tabela de classificação, se há orçamento para upgrades pagos,
  se o dashboard guarda histórico de ciclos, etc.
