# Monitor de Preços — Python + Playwright + Excel

Monitora o preço de um produto de e-commerce periodicamente, guarda o histórico em
uma planilha Excel e envia um e-mail de alerta quando o preço cai de forma
significativa.

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
| `PRODUCT_URL` | URL do produto a ser monitorado |
| `PRODUCT_NAME` | Nome do produto, usado no Excel e no e-mail |
| `PRICE_SELECTOR` | Seletor CSS do elemento que contém o preço na página |
| `MIN_PRICE_DROP_PERCENT` | Queda mínima (%) para disparar um alerta |
| `CHECK_INTERVAL_HOURS` | Intervalo entre verificações, em horas |
| `EMAIL_HOST` / `EMAIL_PORT` | Servidor SMTP (ex.: `smtp.gmail.com` / `587`) |
| `EMAIL_USER` / `EMAIL_PASSWORD` | Credenciais de envio |
| `EMAIL_TO` | Destinatário do alerta |

### Sobre o `PRICE_SELECTOR`

Cada site organiza o HTML de um jeito diferente, então **não existe seletor
universal**. O valor padrão (`p.price_color`) funciona no site de demonstração
(`books.toscrape.com`, feito justamente para prática de scraping). Para monitorar
um site real (Mercado Livre, Amazon etc.):

1. Abra a página do produto no navegador.
2. Clique com o botão direito sobre o preço → "Inspecionar".
3. Identifique uma classe ou seletor CSS estável que aponte para o preço.
4. Atualize `PRICE_SELECTOR` no `.env`.

Sites reais mudam a estrutura com frequência e podem bloquear automações — respeite
sempre os termos de uso e o `robots.txt` do site escolhido, e evite verificações
muito frequentes (o padrão deste projeto é de 1 em 1 hora).

### Sobre a senha de e-mail (Gmail)

Nunca use a senha pessoal da sua conta Gmail no `.env`. Use uma **App Password**:

1. Ative a verificação em duas etapas na conta Google.
2. Acesse https://myaccount.google.com/apppasswords
3. Gere uma senha de app e use-a em `EMAIL_PASSWORD`.

## Execução

```bash
python run.py
```

O programa roda em loop até ser interrompido com `Ctrl+C` (que é tratado de
forma limpa, sem travar ou corromper o Excel).

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
ler o último preço salvo no Excel
        ↓
calcular a variação percentual
        ↓
salvar o novo registro no Excel (sem apagar o histórico)
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
├── scraper/price_scraper.py   acessa a página e extrai o preço (Playwright)
├── services/price_service.py  calcula variação e decide o alerta
├── services/email_service.py  monta e envia o e-mail (SMTP)
├── storage/excel_storage.py   lê/escreve o histórico no Excel
└── utils/helpers.py     conversão de preço texto → número, formatação

data/price_history.xlsx  histórico de preços (criado automaticamente)
tests/test_price_service.py  testes da lógica de negócio
run.py                   ponto de entrada (python run.py)
```

Cada módulo tem uma responsabilidade única: o scraper não sabe nada sobre Excel
ou e-mail, o `price_service` não sabe nada sobre navegador, e o `main.py` apenas
chama essas peças na ordem certa. Isso é o princípio de **separação de
responsabilidades**: cada arquivo pode ser entendido, testado e trocado
isoladamente.

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
- **Classes e POO**: `PriceScraper`, `ExcelStorage`, `PriceService` e
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
- **Excel com pandas/openpyxl**: leitura e escrita de `.xlsx` como
  `DataFrame`, com `pd.concat` para adicionar linhas sem perder as anteriores.
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

- Monitorar vários produtos ao mesmo tempo (lista de produtos configurável).
- Trocar o Excel por um banco de dados (SQLite/PostgreSQL).
- Dashboard web com gráfico da evolução do preço.
- Notificação por Telegram/WhatsApp além do e-mail.
- Empacotar em Docker e rodar em um servidor.
- Expor uma API para consultar o histórico.
- Detecção automática de "menor preço histórico".
- Configuração de produtos via arquivo JSON.
- Interface web para cadastrar produtos e visualizar alertas.
- Deploy em nuvem (ex.: um cron job em uma VM ou função serverless).
