# Monitorização omendigotv — Twitch & Telegram

Sistema que regista a cada 30 minutos o número de seguidores Twitch de `omendigotv`
e o número de membros do canal Telegram, permitindo comparar a performance de cada
streamer durante o seu turno de 4 horas.

## Como funciona

1. Um workflow GitHub Actions corre a cada 30 minutos (gratuito em repositório público)
2. Chama a API do Twitch e a API Bot do Telegram
3. Adiciona uma linha em `data/log.csv` e faz commit no repositório
4. O Excel lê esse CSV via Power Query e calcula automaticamente os deltas por turno

## Turnos monitorizados (hora de Lisboa)

| Turno | Horário | Streamer |
|-------|---------|----------|
| 1 | 10h00 → 14h00 | Streamer 1 |
| 2 | 14h00 → 18h00 | Streamer 2 |
| 3 | 18h00 → 22h00 | Streamer 3 |
| 4 | 22h00 → 02h00 | Streamer 4 |

O turno noturno (4) que atravessa a meia-noite é atribuído à data em que começa
(ex: turno do dia 30/04 das 22h até 01/05 às 02h = "turno 4 do dia 30/04").

## Configuração em 13 passos

### A. GitHub

1. Cria uma conta no GitHub (gratuito) se ainda não tiveres
2. Cria um novo repositório **público** (ex: `omendigotv-monitor`)
3. Carrega todos os ficheiros desta pasta para o repositório

### B. API do Twitch

4. Vai a https://dev.twitch.tv/console/apps e clica em "Register Your Application"
   - Name: `omendigotv-monitor` (ou o que quiseres)
   - OAuth Redirect URLs: `http://localhost`
   - Category: `Application Integration`
   - Anota o **Client ID** mostrado
   - Clica em "New Secret" e anota o **Client Secret** (só é visível uma vez!)

### C. Bot do Telegram

5. No Telegram, abre uma conversa com [@BotFather](https://t.me/BotFather)
   - Envia `/newbot`
   - Dá um nome e depois um username (tem de terminar em `bot`)
   - Anota o **token** (formato `123456789:ABC-DEF...`)

6. Adiciona o teu bot como **administrador** do teu canal
   (Definições do canal → Administradores → Adicionar admin → procura o username do bot).
   Permissões mínimas: nenhuma escrita necessária, basta ser admin para ler estatísticas.

7. Obtém o **ID do canal**:
   - Publica qualquer mensagem no canal
   - No browser, abre:
     `https://api.telegram.org/bot<O_TEU_TOKEN>/getUpdates`
   - Procura `"chat":{"id":-100xxxxxxxxxx,...}` — esse número negativo (começa por `-100`)
     é o teu CHAT_ID

### D. GitHub Secrets

8. No teu repositório GitHub: **Settings → Secrets and variables → Actions → New repository secret**.
   Cria estes 4 secrets:

| Nome | Valor |
|------|-------|
| `TWITCH_CLIENT_ID` | (passo 4) |
| `TWITCH_CLIENT_SECRET` | (passo 4) |
| `TELEGRAM_BOT_TOKEN` | (passo 5) |
| `TELEGRAM_CHAT_ID` | (passo 7, com o `-100` no início) |

### E. Primeiro teste

9. Separador **Actions** do repositório → "Log Twitch + Telegram metrics" → botão **Run workflow**.
   Espera ~1 min, verifica que fica verde. Depois abre `data/log.csv` — deve ter uma linha.

10. Anota o URL "raw" do teu CSV:
    `https://raw.githubusercontent.com/O_TEU_USER/O_TEU_REPO/main/data/log.csv`
    Abre-o no browser — deves ver o conteúdo CSV em texto simples.

### F. Excel

11. Abre `Monitor-omendigotv.xlsx` → folha "Código Power Query" → copia todo o código,
    e substitui `SUBSTITUIR_USER` e `SUBSTITUIR_REPO` pelos teus valores reais

12. No Excel: **Dados → Obter Dados → De Outras Fontes → Consulta em Branco**.
    No editor Power Query: **Ver → Editor Avançado**. Cola o código modificado.
    Clica em **OK** e depois em **Fechar e Carregar Para...** → escolhe "Tabela" e
    "Folha de cálculo existente: Dashboard".

13. **Auto-refresh**: painel direito "Consultas e Ligações" → clique direito sobre a tua consulta →
    **Propriedades** → marca:
    - ☑ "Atualizar ao abrir o ficheiro"
    - ☑ "Atualizar a cada `30` minutos"

Está feito. Sempre que abrires o ficheiro (e a cada 30 min depois), o Excel vai buscar os novos dados
ao GitHub e recalcula os deltas por turno.

## Personalizar os nomes dos streamers

Edita o código Power Query, secção "Nome do streamer":

```
"Streamer 1 (10h-14h)" → "João (10h-14h)"
"Streamer 2 (14h-18h)" → "Maria (14h-18h)"
...
```

Fecha e recarrega a consulta.

## Colunas do Dashboard

| Coluna | Descrição |
|--------|-----------|
| DataTurno | Data do turno |
| NumTurno | 1 / 2 / 3 / 4 |
| Streamer | Nome do streamer |
| SeguidoresInicio | Seguidores Twitch no início do turno |
| SeguidoresFim | Seguidores Twitch no fim |
| DeltaSeguidores | Seguidores ganhos (negativo = perda) |
| MembrosInicio | Membros Telegram no início |
| MembrosFim | Membros Telegram no fim |
| DeltaMembros | Membros Telegram ganhos |
| **GanhoTotal** | DeltaSeguidores + DeltaMembros — **a métrica para comparar** |
| NumMedicoes | Número de medições na janela (deve ser ~9 para um turno de 4h) |

Para comparar streamers, podes adicionar uma tabela dinâmica sobre a tabela carregada:
- Linhas: `Streamer`
- Valores: `Média de GanhoTotal`, `Soma de DeltaSeguidores`, `Soma de DeltaMembros`

## Custo

100% gratuito:
- GitHub Actions: ilimitado para repositórios públicos
- API do Twitch: 800 pedidos/min, fazemos 3 a cada 30 min = 0.1/min
- API do Telegram: sem limite razoável atingido
- Excel: já o tens

## Limitações

- Os crons do GitHub podem atrasar 5-15 min em horas de pico. Sem impacto na análise
  porque pegamos apenas na primeira e última medição de cada turno.
- Se o Twitch ou o Telegram tiver downtime, a célula fica vazia para essa medição.
- Se alguém sair / for removido do canal Telegram durante um turno, isso aparece como
  delta negativo. Tem isto em conta na interpretação dos números.

## Estrutura do projeto

```
omendigotv-monitor/
├── .github/
│   └── workflows/
│       └── log.yml          # Workflow GitHub Actions (cron 30 min)
├── data/
│   └── log.csv              # Logs gerados (commitados automaticamente)
├── logger.py                # Script Python que faz o registo
├── requirements.txt         # Dependências Python
├── .gitignore
├── README.md                # Este ficheiro
└── Monitor-omendigotv.xlsx  # Template Excel com Power Query
```
