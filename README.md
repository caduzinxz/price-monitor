# Monitor de Preços

[![tests](https://github.com/caduzinxz/price-monitor/actions/workflows/tests.yml/badge.svg)](https://github.com/caduzinxz/price-monitor/actions/workflows/tests.yml)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Automação em Python que acompanha o preço de produtos de e-commerce, guarda o
histórico e avisa quando vale a pena comprar — por **e-mail**, **Telegram** ou
no próprio terminal.

Dispara alerta em duas situações: queda percentual acima do limite configurado,
ou **menor preço já registrado** para aquele produto.

**Stack:** Python 3.11+ · Playwright · SQLite / PostgreSQL (Supabase) · SMTP ·
Telegram Bot API · GitHub Actions

---

## Rodando em 1 minuto

Sem cadastro, sem credencial, sem banco de dados externo:

```bash
git clone https://github.com/caduzinxz/price-monitor.git
cd price-monitor
pip install -r requirements.txt
playwright install chromium
python run.py --demo
```

O modo `--demo` busca um preço real com Playwright, semeia um histórico e simula
uma queda, para você ver o alerta disparando sem esperar dias:

```text
[1/3] Buscando um preco REAL com o Playwright...
[A Light in the Attic] Preco encontrado: R$ 51,77

[2/3] Semeando o historico de 'Notebook Gamer (simulado)'...
      17:30 -> R$ 3.500,00
      18:30 -> R$ 3.400,00
      19:30 -> R$ 3.299,00

[3/3] Nova verificacao encontra R$ 2.799,00...
[Notebook Gamer (simulado)] Variacao: 15.16%
[Notebook Gamer (simulado)] MENOR PRECO HISTORICO! Recorde anterior: R$ 3.299,00
[Notebook Gamer (simulado)] Queda significativa. Enviando alertas...
================================================================
  MENOR PRECO HISTORICO: Notebook Gamer (simulado)
----------------------------------------------------------------
  Preco anterior : R$ 3.299,00
  Preco atual    : R$ 2.799,00
  Queda          : 15.16%
  Recorde anterior: R$ 3.299,00
================================================================
```

Outros modos:

```bash
python run.py --once    # uma verificação e encerra
python run.py           # monitora de hora em hora (Ctrl+C para parar)
python -m unittest discover tests    # 48 testes, < 1 segundo
```

Nada é obrigatório: sem configuração, o histórico vai para um SQLite local e os
alertas aparecem no terminal. E-mail, Telegram e Supabase são opcionais.

---

## Como funciona

```text
                         ┌──────────────┐
                         │ products.json│  lista de produtos
                         └──────┬───────┘
                                ▼
   ┌────────────┐        ┌─────────────┐        ┌──────────────┐
   │ PriceScraper│──────▶│   main.py   │◀──────▶│   Storage    │
   │ (Playwright)│ preço  │ orquestração│ histórico│ SQLite/Supabase│
   └────────────┘        └──────┬──────┘        └──────────────┘
                                │
                                ▼
                         ┌─────────────┐
                         │ PriceService│  calcula variação e
                         │             │  decide se alerta
                         └──────┬──────┘
                                ▼
                    ┌───────────────────────┐
                    │  NotificationService  │
                    └───┬───────┬───────┬───┘
                        ▼       ▼       ▼
                     E-mail  Telegram  Console
```

Cada ciclo, para cada produto: acessa a página → extrai e converte o preço →
lê o histórico → calcula a variação → grava o novo registro → decide se alerta
→ notifica pelos canais ativos → aguarda o intervalo → repete.

---

## Decisões de projeto

As escolhas que definiram a forma do código:

**Alerta de menor preço histórico, além da queda percentual.** Um preço que cai
2% por dia durante uma semana nunca cruza o limite de 10% numa única
verificação, mas termina no menor valor de todos os tempos. O alerta de queda
enxerga o último salto; o de recorde enxerga o acumulado.

**Comparação estrita (`<`) para o recorde.** Com `<=`, um preço parado no valor
mínimo empataria consigo mesmo e geraria alerta a cada hora, para sempre. E a
primeira verificação não conta como recorde — sem histórico, qualquer preço
seria trivialmente "o menor de todos".

**Erros isolados por produto e por canal.** O `try/except` fica dentro do laço:
um site fora do ar não impede a verificação dos outros produtos, e um canal de
notificação quebrado não impede os demais de entregarem o alerta.

**Cada camada traduz suas falhas.** `StorageError`, `PriceScraperError` e
`NotificationError` isolam o `main.py` de conhecer `postgrest`, `playwright` ou
`smtplib`. Trocar qualquer uma dessas bibliotecas não afeta quem chama.

**SQLite como padrão, Supabase como opção.** Os dois backends expõem os mesmos
métodos e levantam o mesmo erro, então o resto do projeto não sabe qual está em
uso. O padrão local é o que permite clonar e rodar sem criar conta em lugar
nenhum.

**Configuração separada por natureza.** Credenciais no `.env` (fora do Git);
produtos no `products.json` (versionado). Arquivo que mistura segredo com
não-segredo acaba sendo compartilhado por engano.

**Sem dependências desnecessárias.** São três no total. O Telegram usa `urllib`
da biblioteca padrão em vez de adicionar um cliente HTTP, e o SQLite vem no
próprio Python.

---

## Testes

```bash
python -m unittest discover tests
```

48 testes rodando em menos de um segundo, porque nenhum acessa rede, navegador
ou banco de verdade — as dependências externas são substituídas por dublês.

| Arquivo | Cobre |
|---|---|
| `test_price_service.py` | cálculo de variação, regra de alerta, menor preço histórico |
| `test_products.py` | validação do JSON: campos faltando, nomes duplicados, formato inválido |
| `test_sqlite_storage.py` | gravação, leitura, persistência entre execuções |
| `test_notification_service.py` | envio por múltiplos canais e isolamento de falhas |
| `test_price_scraper.py` | conversão de preço e tratamento de formato inesperado |
| `test_resilience.py` | o ciclo sobrevive a site fora do ar e a banco indisponível |

Rodam automaticamente a cada push, em Python 3.11 e 3.13, junto com o linter
`ruff` — veja [.github/workflows/tests.yml](.github/workflows/tests.yml).

```bash
pip install -r requirements-dev.txt
ruff check .
```

---

## Estrutura

```text
app/
├── main.py                          orquestra o fluxo completo
├── demo.py                          modo de demonstração (--demo)
├── config/
│   ├── settings.py                  configurações centralizadas (lê o .env)
│   └── products.py                  carrega e valida a lista de produtos
├── scraper/
│   └── price_scraper.py             acessa a página e extrai o preço (Playwright)
├── services/
│   ├── price_service.py             calcula variação e decide o alerta
│   ├── notification_service.py      envia por todos os canais ativos
│   ├── email_service.py             e-mail via SMTP
│   ├── telegram_service.py          Telegram Bot API
│   └── console_service.py           terminal (canal de reserva)
├── storage/
│   ├── errors.py                    StorageError, compartilhado pelos backends
│   ├── sqlite_storage.py            histórico em arquivo local (padrão)
│   └── supabase_storage.py          histórico em Postgres na nuvem (opcional)
└── utils/
    └── helpers.py                   conversão "R$ 1.299,90" → 1299.90

scripts/
├── send_test_alert.py               alerta fictício por todos os canais
└── get_telegram_chat_id.py          descobre o TELEGRAM_CHAT_ID

products.json                        produtos monitorados
tests/                               48 testes
run.py                               ponto de entrada
```

O scraper não conhece armazenamento nem e-mail; o `price_service` não conhece
navegador; o `main.py` apenas chama as peças na ordem certa. Cada arquivo pode
ser entendido, testado e substituído isoladamente.

---

## Configuração

Tudo é opcional. Para personalizar, copie o exemplo:

```bash
cp .env.example .env
```

| Variável | Padrão | Descrição |
|---|---|---|
| `STORAGE_BACKEND` | `sqlite` | `sqlite` (local) ou `supabase` (nuvem) |
| `MIN_PRICE_DROP_PERCENT` | `10` | Queda mínima (%) para alertar |
| `ALERT_ON_HISTORIC_LOW` | `true` | Alertar ao bater o menor preço histórico |
| `CHECK_INTERVAL_HOURS` | `1` | Intervalo entre verificações |
| `DELAY_BETWEEN_PRODUCTS_SECONDS` | `5` | Pausa entre produtos no mesmo ciclo |
| `ALERTS_ENABLED` | `true` | `false` silencia os alertas sem apagar credenciais |
| `EMAIL_*` | vazio | SMTP: host, porta, usuário, senha, destinatário |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` | vazio | Bot do Telegram |
| `SUPABASE_URL` / `SUPABASE_SECRET_KEY` | vazio | Necessários se usar Supabase |

### Produtos (`products.json`)

Uma lista — acrescentar produtos é acrescentar blocos:

```json
[
  {
    "name": "A Light in the Attic",
    "url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
    "price_selector": "p.price_color"
  }
]
```

Os três campos são obrigatórios e o `name` precisa ser único — o histórico é
guardado por nome, então repetir misturaria produtos diferentes. Erros no
arquivo são detectados na inicialização, com mensagem explicando o que corrigir.

### Seletor de preço

Cada site organiza o HTML de um jeito diferente, então **não existe seletor
universal**. Para descobrir o de um site: botão direito sobre o preço →
"Inspecionar" → identifique uma classe estável → use em `price_selector`.

O exemplo aponta para [books.toscrape.com](https://books.toscrape.com), site
feito para praticar scraping. Sites reais mudam de estrutura e podem bloquear
automações — respeite os termos de uso e o `robots.txt`, e evite verificações
frequentes demais (o padrão aqui é de 1 em 1 hora).

### E-mail (opcional)

Para Gmail, use uma **App Password**, nunca a senha da conta:

1. Ative a verificação em duas etapas.
2. Gere uma senha em https://myaccount.google.com/apppasswords
3. Use em `EMAIL_PASSWORD`, e preencha `EMAIL_USER` e `EMAIL_TO`.

### Telegram (opcional)

1. Envie `/newbot` para o **@BotFather** e cole o token em `TELEGRAM_BOT_TOKEN`.
2. Mande qualquer mensagem para o seu bot — obrigatório, porque um bot só pode
   escrever para quem falou com ele primeiro.
3. Rode `python -m scripts.get_telegram_chat_id` e copie o número.

Teste os canais configurados com:

```bash
python -m scripts.send_test_alert
```

### Supabase (opcional)

Coloque `STORAGE_BACKEND=supabase` no `.env`, preencha as chaves e crie a tabela
no **SQL Editor** do painel:

```sql
create table if not exists price_history (
  id bigint generated always as identity primary key,
  data_hora timestamptz not null default now(),
  produto text not null,
  url text not null,
  preco numeric not null,
  variacao_percent numeric
);

create index if not exists idx_price_history_produto
  on price_history (produto, data_hora desc);

alter table price_history enable row level security;
```

A última linha ativa Row Level Security sem políticas, bloqueando a chave
pública — só a chave secreta, usada no servidor, acessa a tabela.

---

## Conceitos aplicados

- **POO e separação de responsabilidades**: cada classe encapsula um serviço
  externo (navegador, banco, SMTP) e uma responsabilidade única.
- **Polimorfismo**: `NotificationService` envia por qualquer objeto que tenha
  `send_price_alert`, sem saber se é e-mail, Telegram ou console.
- **Hierarquia de exceções**: `EmailServiceError` e `TelegramServiceError`
  herdam de `NotificationError`, permitindo tratar qualquer canal num só
  `except`.
- **Dataclasses**: `PriceCheckResult` e `Product` agrupam dados com campos
  explícitos.
- **Injeção de dependência**: `check_product()` recebe scraper e storage por
  parâmetro, o que permite substituí-los por dublês nos testes.
- **Web scraping**: `wait_for_selector` espera o elemento de forma ativa (em vez
  de `sleep` cego) e o navegador fecha em `finally`, mesmo com erro.
- **Variáveis de ambiente**: `python-dotenv` carregado uma única vez; nenhuma
  credencial no código.
- **Logging estruturado** em vez de `print()`, configurado num único ponto.
- **Encerramento limpo**: `KeyboardInterrupt` tratado para o Ctrl+C não deixar
  o navegador aberto.

---

## Próximos passos

- Dashboard web com gráfico da evolução dos preços.
- Empacotar em Docker e agendar num servidor (hoje depende do terminal aberto).
- Reaproveitar uma única instância do navegador entre produtos do mesmo ciclo.
- API para consultar o histórico.
- Notificação por WhatsApp (exige WhatsApp Business API e template aprovado).

---

## Licença

[MIT](LICENSE)
