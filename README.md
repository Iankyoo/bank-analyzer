# Bank Analyzer

API REST que lê um extrato bancário em PDF, extrai e categoriza as transações com IA e devolve uma análise financeira do mês. Construída para aprender backend moderno em Python resolvendo um problema real: entender para onde meu dinheiro vai.

## O que faz

1. O usuário faz upload do extrato em PDF.
2. O texto é extraído com `pdfplumber` e o Gemini transforma o texto em transações estruturadas.
3. Cada transação é categorizada: primeiro por similaridade com transações já vistas (ChromaDB); só as desconhecidas vão para o Gemini, todas em uma única chamada.
4. A análise calcula receita, despesas, taxa de economia, gasto por categoria, ticket médio e transações fora do padrão, e o Gemini escreve um insight em texto.
5. O resultado sai em JSON pela API e em um dashboard web simples.

## Stack

- **FastAPI** + **SQLAlchemy 2.0 async** + **PostgreSQL** (psycopg 3)
- **Alembic** para migrations
- **Gemini** via LangChain para extração, categorização e insight
- **ChromaDB** com embeddings do Gemini como memória semântica local
- **Jinja2** para o dashboard
- JWT (PyJWT) + Argon2 (pwdlib) para autenticação, **slowapi** para rate limiting
- Poetry, Docker, pytest, ruff, mypy

## Decisões técnicas

**Categorização em lote.** Em vez de uma chamada ao Gemini por transação, as transações desconhecidas vão juntas em um único prompt. Um extrato que gerava ~26 chamadas passou a gerar 2 (extração + categorização).

**Memória semântica com ChromaDB.** Descrições parecidas com transações já categorizadas reaproveitam a categoria sem chamar a API. A busca só é aceita abaixo de uma distância máxima (`CHROMA_DISTANCE_THRESHOLD`), para que uma correspondência fraca não contamine a categoria.

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
docker compose up -d db     # PostgreSQL na porta 5432
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

32 testes unitários e de integração, 82% de cobertura. O Gemini e o ChromaDB são mockados; nenhum teste chama API externa.

## Limitações conhecidas

Este é um projeto de estudo que roda localmente, em um único processo. As limitações abaixo são conhecidas e estão registradas, com o que eu faria em cada caso, em [docs/roadmap.md](docs/roadmap.md):

- O insight é gerado pelo Gemini a cada consulta da análise, em vez de uma vez no processamento.
- O processamento em background faz chamadas síncronas (PDF, Gemini, ChromaDB) e bloqueia o event loop enquanto roda.
- Sem fila: se o processo cair durante o processamento, o extrato fica `pending` e não há reprocessamento.
- A memória semântica é compartilhada entre usuários.
- A resposta do LLM não é validada antes de entrar no banco; uma categoria inválida leva o extrato inteiro para `error`.
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
