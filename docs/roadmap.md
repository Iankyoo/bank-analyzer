# Roadmap

Plano de trabalho da v1.0 e registro consciente da dívida técnica.

Este documento existe por dois motivos: manter o escopo fechado enquanto a dívida é paga, e deixar explícito o que **não** está no projeto e por quê. A segunda parte é tão importante quanto a primeira — um projeto que não sabe onde termina não consegue ser explicado de ponta a ponta.

---

## Teto da v1.0

> API local single-process. Sobe com `docker compose up -d` e `task run`. Recebe um PDF de extrato, extrai e categoriza as transações com Gemini usando cache semântico local, gera o insight financeiro **uma vez** durante o processamento, e serve a análise por JSON e por um dashboard web simples. `lint`, `typecheck` e `test` passando no CI.

**Regra de corte:** se uma issue passar de 4h, ela não pertence à v1.0 — vai para a seção de dívida técnica. Sem exceção.

---

## Decisões de escopo

O plano AWS expirou e o projeto passou a rodar apenas localmente. Isso não foi só uma perda: várias inconsistências entre o que o README prometia e o que o código fazia deixaram de existir junto com a nuvem.

| Feature | Decisão | Motivo |
|---|---|---|
| **S3 / boto3** | Remover | Sem AWS vira só custo: 4 variáveis de ambiente, uma dependência pesada e mock em todo teste de upload. Trocar por disco local mantendo `storage.py` como camada preserva o ponto que interessa — a interface está isolada, e trocar de volta custa uma função |
| **ChromaDB** | Manter | É o diferencial do projeto. A crítica principal (memória efêmera no Fargate) **deixa de existir** rodando local: persistência em disco passa a ser a escolha certa, não um erro. Restam dois bugs baratos, tratados na Fase 1 |
| **Dashboard Jinja2** | Manter | 240 linhas e é o único artefato visual. O problema dele é ~1h de trabalho (uma dependency compartilhada). Cortar economizaria pouco e custaria a demonstração |

---

## Fases

Ordem importa: a Fase 0 deleta código que as fases seguintes teriam que corrigir à toa.

### Fase 0 — Simplificação · ~3h30

Remove escopo antes de corrigir qualquer coisa.

| Issue | Título |
|---|---|
| [#8](https://github.com/Iankyoo/bank-analyzer/issues/8) | `refactor:` substitui S3 por armazenamento local em disco |
| [#9](https://github.com/Iankyoo/bank-analyzer/issues/9) | `chore:` higiene do repositório (chroma_db versionado, .env.example, remote) |

### Fase 1 — Correções críticas · ~6h30

Corretude. É o que um sênior olharia primeiro.

| Issue | Título |
|---|---|
| [#10](https://github.com/Iankyoo/bank-analyzer/issues/10) | `fix:` processamento em background bloqueia o event loop |
| [#11](https://github.com/Iankyoo/bank-analyzer/issues/11) | `refactor:` gera e persiste o insight durante o processamento |
| [#12](https://github.com/Iankyoo/bank-analyzer/issues/12) | `fix:` idempotência garantida só na aplicação, sem constraint no banco |
| [#13](https://github.com/Iankyoo/bank-analyzer/issues/13) | `fix:` memória semântica compartilhada entre usuários |

### Fase 2 — Robustez · ~7h30

O caminho de erro, que hoje é o menos exercitado.

| Issue | Título |
|---|---|
| [#14](https://github.com/Iankyoo/bank-analyzer/issues/14) | `fix:` saída do LLM entra no domínio sem validação e derruba o extrato inteiro |
| [#15](https://github.com/Iankyoo/bank-analyzer/issues/15) | `fix:` categorização em lote casa por descrição e falha em silêncio |
| [#16](https://github.com/Iankyoo/bank-analyzer/issues/16) | `fix:` validação de upload quebra com file.size nulo e confia no content-type |
| [#17](https://github.com/Iankyoo/bank-analyzer/issues/17) | `refactor:` unifica autenticação por cookie do dashboard em uma dependency |
| [#18](https://github.com/Iankyoo/bank-analyzer/issues/18) | `fix:` except Exception no login mascara falhas reais |
| [#19](https://github.com/Iankyoo/bank-analyzer/issues/19) | `feat:` expõe status e listagem de statements na API |

### Fase 3 — Qualidade e apresentação · ~8h

O que torna o trabalho das fases anteriores verificável por quem não vai clonar o repositório.

| Issue | Título |
|---|---|
| [#20](https://github.com/Iankyoo/bank-analyzer/issues/20) | `chore:` faz lint e typecheck passarem de verdade |
| [#21](https://github.com/Iankyoo/bank-analyzer/issues/21) | `ci:` adiciona pipeline no GitHub Actions |
| [#22](https://github.com/Iankyoo/bank-analyzer/issues/22) | `feat:` adiciona /health e ajusta Docker para execução local |
| [#23](https://github.com/Iankyoo/bank-analyzer/issues/23) | `docs:` reescreve o README e documenta a dívida técnica |

**Total: ~25h.** Um commit por issue, seguindo a convenção já usada no histórico.

Se for preciso cortar, corte a **Fase 2 antes da Fase 3**: um projeto com bugs conhecidos e documentados vende melhor que um projeto correto que ninguém consegue rodar ou entender.

---

## Fora do teto — dívida técnica consciente

Nada aqui é esquecimento. Cada item foi avaliado e deixado de fora por um motivo.

### Processamento em `BackgroundTasks`, não em fila

**Por que ficou de fora:** rodando local e single-process, `BackgroundTasks` é a escolha **correta** — responde o upload na hora sem bloquear o cliente, sem adicionar Redis nem um worker para operar.

**Limitação real:** não tem retry nem persistência. Se o processo cair no meio do processamento, o statement fica `PENDING` para sempre e não há como reprocessar.

**O que eu faria:** ARQ ou Celery com Redis, estado do job no banco, retry com backoff exponencial e um endpoint de reprocessamento manual.

### ChromaDB local, não pgvector

**Por que ficou de fora:** com um único processo e um único disco, o Chroma persistente resolve. Trocar de banco vetorial no meio da correção de dívida seria inflar escopo por elegância.

**Limitação real:** memória em processo separado do Postgres, sem transação conjunta. Se o statement for revertido, os embeddings gravados permanecem.

**O que eu faria:** pgvector no mesmo Postgres, com os embeddings escritos na mesma transação das transações — o que elimina a inconsistência e um serviço da stack.

### Armazenamento em disco, não object storage

**Por que ficou de fora:** o plano AWS expirou. Manter a integração pelo símbolo seria manter dependência e configuração sem uso.

**Limitação real:** não escala além de uma máquina, e o disco não é durável.

**O que eu faria:** voltar para S3 ou MinIO. O custo é baixo justamente porque o acesso está isolado em `services/storage.py`.

### Sem refresh token nem logout

**Por que ficou de fora:** JWT de 30 minutos sem revogação é suficiente para demonstrar o fluxo de autenticação, que é o objetivo aqui.

**Limitação real:** um token vazado é válido até expirar, e não há como deslogar de fato.

**O que eu faria:** refresh token com rotação, guardado em cookie `httponly`, mais uma denylist de JTI em Redis para revogação imediata.

### Sem paginação

**Por que ficou de fora:** um usuário de teste tem dezenas de statements, não milhares.

**Limitação real:** `GET /statements` cresce sem limite.

**O que eu faria:** paginação por cursor sobre `uploaded_at`, que é estável sob inserção concorrente — offset não é.

### Sem CORS, logging estruturado ou request-id

**Por que ficou de fora:** não há front separado consumindo a API, e sem deploy não há log para agregar.

**O que eu faria:** `CORSMiddleware` restrito à origem do front, logs em JSON com `structlog` e um middleware de `X-Request-ID` propagado até o processamento em background.

### Testes criam o schema com `create_all`, não com as migrations

**Por que ficou de fora:** `create_all` é mais rápido e não amarra a suíte à cadeia de revisões.

**Limitação real:** **as migrations nunca são exercidas.** Uma migration quebrada passa no CI e só aparece quando alguém tenta subir o banco do zero.

**O que eu faria:** um job separado no CI rodando `alembic upgrade head` seguido de `alembic downgrade base` contra um banco limpo. É o teste mais barato de todos os listados aqui e provavelmente o próximo a ser feito.

### Sem deploy público

**Por que ficou de fora:** plano AWS expirado.

**O que eu faria:** Fly.io ou Render com Postgres gerenciado — o Dockerfile já está pronto e roda como usuário não-root.

---

## Depois da v1.0

A lista acima não é para ser resolvida neste repositório. Fila de tarefas real, memória vetorial no Postgres, multi-tenant e observabilidade formam o escopo de um **projeto seguinte**, com ambição maior — e não um remendo neste, cujo valor está em ser inteiramente explicável por quem o escreveu.
