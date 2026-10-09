# Bank Analyzer

API REST que lê um extrato bancário em PDF, extrai e categoriza as transações com IA e devolve uma análise financeira do mês. Construída para aprender backend moderno em Python resolvendo um problema real: entender para onde meu dinheiro vai.

## O que faz

1. O usuário faz upload do extrato em PDF.
2. O texto é extraído com `pdfplumber` e o Gemini transforma o texto em transações estruturadas.
3. Cada transação é categorizada: primeiro por similaridade com transações que o usuário já teve (embeddings no pgvector); só as desconhecidas vão para o Gemini, todas em uma única chamada.
4. A análise calcula receita, despesas, taxa de economia, gasto por categoria, ticket médio e transações fora do padrão, e o Gemini escreve um insight em texto.
5. O resultado sai em JSON pela API e em um dashboard web simples.

## Stack

- **FastAPI** + **SQLAlchemy 2.0 async** + **PostgreSQL** (psycopg 3) com **pgvector**
- **Alembic** para migrations
- **Gemini** via LangChain para extração, categorização e insight
- **Embeddings do Gemini** (`gemini-embedding-001`, 768 dimensões) como memória semântica
- **Jinja2** para o dashboard
- JWT (PyJWT) + Argon2 (pwdlib) para autenticação, **slowapi** para rate limiting
- Poetry, Docker, pytest, ruff, mypy

## Decisões técnicas

**Categorização em lote.** Em vez de uma chamada ao Gemini por transação, as transações desconhecidas vão juntas em um único prompt. Um extrato que gerava ~26 chamadas passou a gerar 2 (extração + categorização).

**Memória semântica com pgvector.** Toda transação categorizada pelo Gemini tem o embedding da descrição salvo no Postgres. No extrato seguinte, os embeddings de todas as descrições são gerados em uma única chamada, e cada um busca a transação mais próxima do mesmo usuário por distância de cosseno (`ORDER BY embedding <=> :vetor LIMIT 1`). Abaixo do limite, a categoria é reaproveitada sem chamar o LLM. Num teste com dois extratos de meses seguidos, o segundo foi categorizado inteiro pela memória.

O limite (`SIMILARITY_DISTANCE_THRESHOLD=0.18`) foi calibrado com embeddings reais: variações da mesma transação ("IFOOD \*RESTAURANTE" × "iFood Almoco", "NETFLIX.COM" × "Netflix") ficaram entre 0.05 e 0.13; transações diferentes, acima de 0.24.

Os embeddings ficam no mesmo banco das transações: são gravados na mesma transação SQL (se o processamento falha, nada fica pela metade) e isolados por usuário com um `WHERE user_id`. O projeto usou ChromaDB antes; trocar por pgvector eliminou um segundo banco para manter em sincronia.

**Idempotência por hash.** O SHA-256 do PDF é guardado no upload; o mesmo arquivo enviado de novo pelo mesmo usuário retorna o extrato existente sem reprocessar.

**Processamento em background.** O upload responde na hora com status `pending`; a extração e a categorização rodam em `BackgroundTasks`, e o status passa por `processing` até `completed` ou `error`.

**Armazenamento isolado em uma camada.** Os PDFs ficam em disco local, mas todo acesso passa por `services/storage.py`. O projeto já usou S3; voltar para object storage é trocar duas funções.

**Segurança.** Cada consulta de análise filtra pelo dono do extrato (sem IDOR), o cookie do dashboard é `HttpOnly` + `Secure` + `SameSite=Lax`, e os endpoints de login e registro são limitados a 5 requisições por minuto por IP.

## Rodando localmente

Pré-requisitos: Python 3.13+, Poetry, Docker e uma chave da API do Gemini.

```bash
git clone https://github.com/Iankyoo/bank-analyzer
cd bank-analyzer

cp .env.example .env        # preencha GEMINI_API_KEY e SECRET_KEY
poetry install
docker compose up -d db     # PostgreSQL + pgvector na porta 5432
poetry run alembic upgrade head
poetry run task run
```

- API e documentação interativa: http://localhost:8000/docs
- Dashboard: http://localhost:8000/login

Todas as variáveis estão descritas em [.env.example](.env.example).

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| POST | `/auth/register` | Cria usuário |
| POST | `/auth/token` | Login, retorna JWT |
| POST | `/statements/upload` | Upload do PDF (processado em background) |
| GET | `/statements/{id}/analysis` | Análise do extrato em JSON |
| GET | `/login` | Login do dashboard |
| GET | `/statements` | Lista de extratos (dashboard) |
| GET | `/dashboard/{id}` | Análise do extrato (dashboard) |

## Testes

Os testes de integração usam um PostgreSQL separado, na porta 5433:

```bash
docker compose up -d db_test
poetry run task test
```

35 testes unitários e de integração, 85% de cobertura. As chamadas ao Gemini são mockadas; a busca vetorial roda de verdade contra o pgvector do banco de testes.

## Limitações conhecidas

Este é um projeto de estudo que roda localmente, em um único processo. As limitações abaixo são conhecidas e estão registradas, com o que eu faria em cada caso, em [docs/roadmap.md](docs/roadmap.md):

- O insight é gerado pelo Gemini a cada consulta da análise, em vez de uma vez no processamento.
- O processamento em background faz chamadas síncronas (leitura do PDF e Gemini) e bloqueia o event loop enquanto roda.
- Sem fila: se o processo cair durante o processamento, o extrato fica `pending` e não há reprocessamento.
- A resposta do LLM na extração (datas, valores, tipo) não é validada antes de entrar no banco; um campo malformado leva o extrato inteiro para `error`.
- A API não expõe a listagem nem o status dos extratos (só o dashboard).
- Não há deploy público.

## Estrutura

```
src/bank_analyzer/
├── api/         # rotas (auth, statements, dashboard) e dependências
├── core/        # configuração, banco, segurança, rate limiter
├── models/      # modelos SQLAlchemy
├── schemas/     # schemas Pydantic
├── services/    # parser, categorizer, memory, analytics, insight, storage
└── templates/   # HTML do dashboard
migrations/      # Alembic
tests/           # unit/ e integration/
```
