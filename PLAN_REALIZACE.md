# Plán realizace: Sémantický index dokumentů

> [!NOTE]
> **Harmonogram počítá s využitím pokročilého AI asistenta (Antigravity od Google DeepMind) pro generování kódu.** Původní doba realizace tradičním vývojem (~11 týdnů / 70+ MD) se tímto přístupem zkracuje na **3-4 týdny / ~15 MD**. Vývojář funguje jako „AI pilot" a architekt.

**Aktualizováno: 17.05.2026**

---

## Fáze 1: Inicializace a Infrastruktura ✅ DOKONČENO

| Úkol | Stav | Soubor(y) |
|:---|:---:|:---|
| Vytvoření složky projektu a Git repozitáře | ✅ | `.git/`, `.gitignore` |
| Nastavení `pyproject.toml` a závislostí | ✅ | `pyproject.toml` |
| Konfigurace Docker Compose (Postgres + pgvector, Redis) | ✅ | `docker-compose.yml` |
| Příprava `.env` šablony s konfigurací | ✅ | `.env` |
| Vytvoření vstupního bodu FastAPI | ✅ | `src/main.py` |
| Instalace Git a GitHub CLI na lokální systém | ✅ | winget install |

---

## Fáze 2: Datový model a Databáze ✅ DOKONČENO

| Úkol | Stav | Soubor(y) |
|:---|:---:|:---|
| Konfigurace připojení k databázi (SQLAlchemy) | ✅ | `src/database.py` |
| Inicializace Alembic pro DB migrace | ✅ | `alembic/`, `alembic.ini` |
| Dynamické napojení Alembic na `settings.DATABASE_URL` | ✅ | `alembic/env.py` |
| Definice SQLAlchemy modelů (`Document`, `DocumentChunk`) | ✅ | `src/models.py` |
| Primární klíče jako **UUIDv7** (knihovna `uuid6`) | ✅ | `src/models.py` |
| Sloupec `Vector(768)` přes pgvector | ✅ | `src/models.py` |
| Sloupec `tsvector` pro hybridní full-text vyhledávání | ✅ | `src/models.py` |

> ⏳ **Čeká na:** Spuštění Docker kontejnerů → `alembic revision --autogenerate` → `alembic upgrade head`

---

## Fáze 3: API kostra a Autentizace ✅ DOKONČENO

| Úkol | Stav | Soubor(y) |
|:---|:---:|:---|
| REST API: Upload PDF (`POST /documents`) | ✅ | `src/api.py` |
| REST API: Stav zpracování (`GET /documents/{id}/status`) | ✅ | `src/api.py` |
| REST API: Skeleton hybridního vyhledávání (`GET /search`) | ✅ | `src/api.py` |
| Pydantic Settings (konfigurace z `.env`) | ✅ | `src/config.py` |
| **Entra ID OIDC/OAuth 2.0** – JWT validace tokenů | ✅ | `src/auth/entra_id.py` |
| Dynamické stahování JWKS klíčů z Microsoft tenantu | ✅ | `src/auth/entra_id.py` |

---

## Fáze 4: Asynchronní zpracování (Pipeline) ✅ DOKONČENO

| Úkol | Stav | Soubor(y) |
|:---|:---:|:---|
| Celery aplikace s Redis broker/backend | ✅ | `src/worker.py` |
| Task `process_document_task` (orchestrace celé pipeline) | ✅ | `src/worker.py` |
| **PDF parser** – extrakce textu z PDF (pdfplumber, MIT licence) | ✅ | `src/services/pdf_parser.py` |
| **Chunker** – okenní algoritmus s konfigurovatelným overlap | ✅ | `src/services/chunker.py` |
| **Embedder** – lokální vektorové embeddingy (multilingual-e5-base, 768dim) | ✅ | `src/services/embedder.py` |
| Retry mechanismus (max 3 pokusy, countdown 60s) | ✅ | `src/worker.py` |
| Aktualizace stavu dokumentu po zpracování (`processed` / `error`) | ✅ | `src/worker.py` |

---

## Fáze 5: Vyhledávací Engine (Semantic & Hybrid Search) 🚧 NA ŘADĚ

| Úkol | Stav | Poznámka |
|:---|:---:|:---|
| Vektorové vyhledávání (Cosine Similarity přes pgvector) | ⬜ | `1 - (vector <#> query_vector)` |
| Full-textové vyhledávání (PostgreSQL `tsquery`) | ⬜ | BM25-like ranking |
| Hybridní fúze výsledků (RRF – Reciprocal Rank Fusion) | ⬜ | Kombinace obou metod |
| Filtrování výsledků přes tagy (AND/OR/NOT) | ⬜ | Dle specifikace §8.3 |
| HNSW / IVFFlat index pro výkon < 2s | ⬜ | Dle specifikace §9 |
| Batch zpracování embeddingů | ⬜ | Dávková reindexace |

---

## Fáze 6: Observabilita a Bezpečnost ⬜ PLÁNOVÁNO

| Úkol | Stav | Poznámka |
|:---|:---:|:---|
| Health check endpoint (`/health`) | ⬜ | FastAPI dependency |
| Prometheus metriky (`/metrics`) | ⬜ | Knihovna `prometheus-client` |
| Audit log (kdo, kdy, co) | ⬜ | Tabulka `AUDIT_LOG` v DB |
| TLS konfigurace | ⬜ | Reverse proxy (nginx/traefik) |
| Multi-tenant izolace (příprava) | ⬜ | Row-level security v Postgres |

---

## Fáze 7: Finalizace a Odevzdání ⬜ PLÁNOVÁNO

| Úkol | Stav | Poznámka |
|:---|:---:|:---|
| Integrační testy (`pytest`) | ⬜ | End-to-end pipeline test |
| OpenAPI dokumentace (automaticky z FastAPI) | ⬜ | `/docs` endpoint |
| Deployment guide a provozní dokumentace | ⬜ | `docs/` složka |
| Dockerfile pro produkční build | ⬜ | Multi-stage build |
| Finální push na GitHub (repozitář `ACRBRNO`) | ⬜ | Čeká na `gh auth login` |

---

## Strategická dokumentace ✅ DOKONČENO

| Dokument | Stav | Popis |
|:---|:---:|:---|
| `analyza_a_plan.md` | ✅ | Kompletní technická analýza specifikace (§1-§16), architektura, datový model, harmonogram |
| `FINANCNI_ANALIZA_ACR.md` | ✅ | TCO analýza pro AČR – CAPEX hardware, vývoj s AI Antigravity, OPEX provoz |
| `ANALYZA_POWER_PLATFORM.md` | ✅ | Srovnávací analýza Power Platform vs. on-premise řešení (proč PP nesplňuje specifikaci) |
| `Semanticky_index_Analyza.pdf` | ✅ | Grafické PDF s kompletní analýzou pro tisk/prezentaci (generováno přes Edge headless) |

---

## Souhrn postupu

```
Fáze 1  ████████████████████  100%  Infrastruktura
Fáze 2  ████████████████████  100%  Datový model
Fáze 3  ████████████████████  100%  API + Auth
Fáze 4  ████████████████████  100%  Pipeline (Parse→Chunk→Embed)
Fáze 5  ░░░░░░░░░░░░░░░░░░░░    0%  Vyhledávání
Fáze 6  ░░░░░░░░░░░░░░░░░░░░    0%  Observabilita
Fáze 7  ░░░░░░░░░░░░░░░░░░░░    0%  Finalizace
─────────────────────────────────
Celkem  ████████████░░░░░░░░   57%
```

**Další krok:** Spustit Docker (`docker compose up -d`), aplikovat migrace a implementovat vyhledávací engine (Fáze 5).
