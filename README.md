# Bank Analyzer

API REST para análise inteligente de extratos bancários com IA. Construída para aprender desenvolvimento backend moderno em Python enquanto resolvo um problema real: entender para onde meu dinheiro vai todo mês.

## O que faz

Você faz upload de um extrato bancário em PDF. A API extrai as transações, categoriza cada uma usando Gemini (em lote, não uma chamada por transação), detecta gastos fora do padrão e gera um insight financeiro personalizado. Tem um dashboard web para visualizar tudo isso.

## Stack

- **FastAPI** + SQLAlchemy 2.0 async + PostgreSQL
- **Gemini** para categorização e geração de insights
- **ChromaDB** com embeddings para memória semântica — transações similares já categorizadas não precisam chamar o Gemini novamente
- **AWS S3** para armazenar os PDFs, **ECS Fargate** + **RDS** em produção
- **Jinja2** para o dashboard web
- Docker, Alembic, Poetry

## Decisões técnicas relevantes

**Categorização em lote:** em vez de chamar o Gemini N vezes (uma por transação), monto um prompt com todas as transações desconhecidas e faço uma única chamada. Reduziu de ~26 chamadas para 2 por extrato.

**ChromaDB como memória:** transações similares às já processadas são categorizadas localmente via busca semântica, sem custo de API. Útil para transações ambíguas que sempre aparecem (ex: "PIX João" — pode ser qualquer coisa).

**Idempotência por hash SHA256:** o mesmo PDF enviado duas vezes retorna o statement existente sem reprocessar.

**Async desde o início:** FastAPI + SQLAlchemy 2.0 + psycopg, tudo async. Evita refatoração dolorosa depois.

## Rodando localmente

```bash
git clone https://github.com/Iankyoo/bank-analyzer
cd bank-analyzer

# dependências
poetry install

# sobe os bancos
docker-compose up -d

# migrations
alembic upgrade head

# inicia
task run
```

Acesse `http://localhost:8000/docs` para a API ou `http://localhost:8000/login` para o dashboard.

### Variáveis de ambiente (.env)

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/bank_analyzer
SECRET_KEY=sua_secret_key
ALGORITHM=HS256
TOKEN_EXPIRE_IN_MINUTES=30
GEMINI_API_KEY=sua_chave
GEMINI_MODEL=gemini-2.0-flash
AWS_ACCESS_KEY_ID=sua_chave
AWS_SECRET_ACCESS_KEY=sua_secret
AWS_BUCKET_NAME=seu_bucket
AWS_REGION=sa-east-1
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=bank_analyzer
TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5433/bank_analyzer_test
```

## Endpoints principais

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/auth/register` | Cria usuário |
| POST | `/auth/token` | Login, retorna JWT |
| POST | `/statements/upload` | Upload de PDF |
| GET | `/statements/{id}/analysis` | Análise em JSON |
| GET | `/dashboard/{id}` | Dashboard web |

## Testes

```bash
task test
```

86% de cobertura com testes unitários e de integração. S3 e Gemini são mockados nos testes.
