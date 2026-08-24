# Monitor de Preços — Python + Playwright + Supabase

Monitora o preço de um produto de e-commerce periodicamente, guarda o histórico em
uma tabela no Supabase (Postgres) e envia um e-mail de alerta quando o preço cai
de forma significativa.

## Instalação

```bash
python -m venv venv
```

Ativar o ambiente virtual (PowerShell):

```powershell
venv\Scripts\Activate.ps1
```

Instalar as dependências:

```bash
pip install -r requirements.txt
```

Instalar os navegadores usados pelo Playwright (necessário apenas uma vez por máquina):

```bash
playwright install chromium
```

## Configuração

Copie `.env.example` para `.env` e ajuste os valores:

```bash
copy .env.example .env
```

Variáveis:

| Variável | Descrição |
|---|---|
| `MIN_PRICE_DROP_PERCENT` | Queda mínima (%) para disparar um alerta |
| `CHECK_INTERVAL_HOURS` | Intervalo entre verificações, em horas |
| `DELAY_BETWEEN_PRODUCTS_SECONDS` | Pausa entre um produto e outro dentro do mesmo ciclo |
| `ALERTS_ENABLED` | `false` desliga o envio de e-mails sem apagar as credenciais |
| `EMAIL_HOST` / `EMAIL_PORT` | Servidor SMTP (ex.: `smtp.gmail.com` / `587`) |
| `EMAIL_USER` / `EMAIL_PASSWORD` | Credenciais de envio |
| `EMAIL_TO` | Destinatário do alerta |
| `SUPABASE_URL` | Project URL do Supabase (Project Settings → API) |
| `SUPABASE_SECRET_KEY` | Chave secreta do Supabase, usada pelo backend para ler/gravar o histórico |
| `SUPABASE_PUBLISHABLE_KEY` | Chave pública do Supabase (não usada pelo monitor hoje; reservada para uma futura interface/dashboard) |

### Sobre o Supabase

O histórico de preços é armazenado numa tabela `price_history` no Supabase. Antes
da primeira execução, crie a tabela rodando este SQL uma vez no **SQL Editor** do
painel do Supabase:

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

A última linha ativa Row Level Security sem nenhuma política, o que bloqueia a
chave pública de ler/escrever na tabela — só a chave secreta (usada do lado do
servidor, nunca exposta) consegue acessar. Nunca coloque `SUPABASE_SECRET_KEY`
em código versionado ou em qualquer lugar acessível pelo navegador.

### Produtos monitorados (`products.json`)

Os produtos ficam em `products.json`, na raiz do projeto — e não no `.env`, que
fica reservado a credenciais. O arquivo é uma lista, então monitorar vários
produtos é só acrescentar blocos:

```json
[
  {
    "name": "A Light in the Attic",
    "url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
    "price_selector": "p.price_color"
  },
  {
    "name": "Outro produto",
    "url": "https://loja.com/produto",
    "price_selector": "span.preco-final"
  }
]
```

Regras:

- os três campos (`name`, `url`, `price_selector`) são obrigatórios;
- **`name` precisa ser único** — o histórico é guardado por nome, então nomes
  repetidos misturariam os preços de produtos diferentes;
- erros no arquivo (JSON inválido, campo faltando, nome repetido) são detectados
  na inicialização, com mensagem explicando o que corrigir.

Dentro de um ciclo, os produtos são verificados um de cada vez, com uma pausa
entre eles (`DELAY_BETWEEN_PRODUCTS_SECONDS`) para não disparar várias
requisições seguidas ao mesmo site. Se um produto falhar (site fora do ar, por
exemplo), os demais continuam sendo verificados normalmente.

### Sobre o `price_selector`

Cada site organiza o HTML de um jeito diferente, então **não existe seletor
universal**. O valor usado no exemplo (`p.price_color`) funciona no site de
demonstração (`books.toscrape.com`, feito justamente para prática de scraping).
Para monitorar um site real (Mercado Livre, Amazon etc.):

1. Abra a página do produto no navegador.
2. Clique com o botão direito sobre o preço → "Inspecionar".
3. Identifique uma classe ou seletor CSS estável que aponte para o preço.
4. Use-o no campo `price_selector` daquele produto em `products.json`.

Sites reais mudam a estrutura com frequência e podem bloquear automações — respeite
sempre os termos de uso e o `robots.txt` do site escolhido, e evite verificações
muito frequentes (o padrão deste projeto é de 1 em 1 hora).

### Sobre a senha de e-mail (Gmail)

Nunca use a senha pessoal da sua conta Gmail no `.env`. Use uma **App Password**:

1. Ative a verificação em duas etapas na conta Google.
2. Acesse https://myaccount.google.com/apppasswords
3. Gere uma senha de app e use-a em `EMAIL_PASSWORD`.

Para testar o envio sem esperar uma queda real de preço:

```bash
python -m scripts.send_test_email
```

Para **parar de receber os alertas**, prefira `ALERTS_ENABLED=false` no `.env` ou
revogue apenas aquela App Password em https://myaccount.google.com/apppasswords —
as duas opções são reversíveis e cirúrgicas. Desativar a verificação em duas
etapas da conta Google também revoga a senha, mas enfraquece a segurança de toda
a sua conta, então não é o caminho recomendado.

## Execução

```bash
python run.py
```

O programa roda em loop até ser interrompido com `Ctrl+C` (que é tratado de
forma limpa).

## Funcionamento

```text
iniciar aplicação
        ↓
carregar configurações (.env via settings.py)
        ↓
abrir o navegador (Playwright) e acessar a URL do produto
        ↓
extrair e converter o preço (texto → número)
        ↓
ler o último preço salvo no Supabase
        ↓
calcular a variação percentual
        ↓
salvar o novo registro no Supabase (sem apagar o histórico)
        ↓
se a queda ≥ MIN_PRICE_DROP_PERCENT → enviar e-mail de alerta
        ↓
aguardar CHECK_INTERVAL_HOURS
        ↓
repetir
```

Uma falha em uma única etapa (ex.: site fora do ar numa verificação) é
registrada no log e o programa segue para a próxima verificação — ele não
trava por causa de um erro pontual.

## Estrutura

```text
app/
├── main.py              orquestra o fluxo completo
├── config/settings.py   configurações centralizadas (lê o .env)
├── config/products.py   carrega e valida a lista de produtos do JSON
├── scraper/price_scraper.py   acessa a página e extrai o preço (Playwright)
├── services/price_service.py  calcula variação e decide o alerta
├── services/email_service.py  monta e envia o e-mail (SMTP)
├── storage/supabase_storage.py   lê/escreve o histórico no Supabase
├── storage/excel_storage.py   alternativa em Excel (não usada por padrão, mantida como referência)
└── utils/helpers.py     conversão de preço texto → número, formatação

products.json            lista de produtos monitorados
scripts/send_test_email.py  envia um alerta fictício para testar o SMTP
tests/                   testes da lógica de negócio e do carregador de produtos
run.py                   ponto de entrada (python run.py)
```

Cada módulo tem uma responsabilidade única: o scraper não sabe nada sobre
armazenamento ou e-mail, o `price_service` não sabe nada sobre navegador, e o
`main.py` apenas chama essas peças na ordem certa. Isso é o princípio de
**separação de responsabilidades**: cada arquivo pode ser entendido, testado e
trocado isoladamente — trocar `SupabaseStorage` por `ExcelStorage` (ou por
qualquer outro backend) no `main.py` não exige mudar mais nada, porque os dois
implementam os mesmos métodos (`get_last_price`, `append_record`).

## Testes

```bash
python -m unittest discover tests
```

Cobrem apenas lógica pura (cálculo de variação, regra de alerta, conversão de
preço) — não abrem navegador nem enviam e-mail de verdade.

## Aprendizado

Conceitos de Python praticados neste projeto:

- **Módulos e pacotes**: cada pasta com `__init__.py` é um pacote; `import
  app.services.price_service` funciona porque `app`, `app.services` etc. são
  pacotes Python.
- **Classes e POO**: `PriceScraper`, `SupabaseStorage`, `PriceService` e
  `EmailService` encapsulam estado (ex.: credenciais, configurações) e
  comportamento relacionado.
- **Dataclasses**: `PriceCheckResult` usa `@dataclass` para agrupar dados sem
  escrever um `__init__` manual.
- **Tratamento de exceções**: cada camada define sua própria exceção
  (`PriceScraperError`, `EmailServiceError`) e o `main.py` decide o que fazer
  com cada uma, sem precisar conhecer detalhes internos de Playwright ou SMTP.
- **Variáveis de ambiente**: `python-dotenv` carrega o `.env` uma única vez em
  `settings.py`; nenhuma credencial fica no código-fonte.
- **Web scraping com Playwright**: `page.wait_for_selector` espera o elemento
  aparecer de forma ativa (em vez de `time.sleep` cego), e o navegador é
  sempre fechado num bloco `finally`, mesmo se algo der errado.
- **Supabase (Postgres via REST)**: o cliente `supabase-py` fala com o banco
  por HTTP (PostgREST) em vez de uma conexão SQL direta; `client.table(...).select()/insert()`
  monta a query e `.execute()` a dispara.
- **SMTP**: `smtplib` + `email.message.EmailMessage` (bibliotecas padrão) para
  montar e enviar e-mails com STARTTLS.
- **Logging**: módulo `logging` em vez de `print()`, com timestamp e níveis
  (`info`, `error`), configurado uma única vez em `main.py`.
- **Agendamento simples**: `time.sleep(horas * 3600)` dentro de um `while
  True`, encerrado de forma limpa ao capturar `KeyboardInterrupt`.
- **Separação de responsabilidades**: cada módulo faz uma coisa só, o que
  facilita testar, entender e trocar peças (ex.: outro site, outro banco de
  dados) sem reescrever o projeto inteiro.

## Próximos passos

Não implementados nesta versão, mas possíveis evoluções:

- Dashboard web com gráfico da evolução do preço (consumindo os dados do Supabase).
- Notificação por Telegram/WhatsApp além do e-mail.
- Empacotar em Docker e rodar em um servidor.
- Expor uma API para consultar o histórico.
- Detecção automática de "menor preço histórico".
- Configuração de produtos via arquivo JSON.
- Interface web para cadastrar produtos e visualizar alertas.
- Deploy em nuvem (ex.: um cron job em uma VM ou função serverless).
