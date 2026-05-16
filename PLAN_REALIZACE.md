# Plán realizace: Sémantický index dokumentů

Tento dokument obsahuje krok za krokem rozepsaný plán implementace projektu. Slouží k přehlednému sledování postupu.

## Fáze 1: Inicializace a Infrastruktura (✅ Dokončeno)
- [x] Vytvoření složky projektu a repozitáře
- [x] Nastavení `pyproject.toml` a instalace závislostí (FastAPI, SQLAlchemy, pgvector, Celery, Redis)
- [x] Konfigurace `docker-compose.yml` (Postgres + pgvector, Redis)
- [x] Příprava `.env` šablony a úvodního `.gitignore`
- [x] Vytvoření vstupního bodu API (`src/main.py`)

## Fáze 2: Datový model a Databáze (🚧 Na řadě)
- [ ] Konfigurace připojení k databázi přes SQLAlchemy
- [ ] Inicializace nástroje Alembic pro databázové migrace (`alembic init`)
- [ ] Definice SQLAlchemy modelů (`Document`, `DocumentChunk`)
  - [ ] Použití `UUIDv7` pro primární klíče (dle specifikace)
  - [ ] Přidání sloupce `Vector` přes rozšíření `pgvector`
  - [ ] Přidání sloupce `tsvector` pro hybridní full-text vyhledávání
- [ ] Vygenerování a aplikace první migrační dávky na běžící Postgres kontejner

## Fáze 3: API Kostra a Autentizace
- [ ] Nastavení OAuth2 / OpenID Connect validace tokenů proti Microsoft Entra ID
  - *Poznámka:* Využijeme testovací údaje (kytyrova@zsbuky.cz) nalezené z předchozích projektů pro validaci.
- [ ] Vytvoření základních endpointů (`POST /documents`, `GET /documents/{id}`)
- [ ] Zapojení validace uživatele do těchto endpointů

## Fáze 4: Asynchronní Zpracování (Celery Workery)
- [ ] Nastavení Celery aplikace pro asynchronní komunikaci s Redisem
- [ ] Vytvoření tasku pro parsování a textovou extrakci z nahrávaných PDF dokumentů
- [ ] Implementace algoritmu pro "chunkování" (rozdělení dlouhého textu dokumentu na sémantické pasáže)
- [ ] Vektorizace (Embedding)
  - [ ] Vygenerování vektorů pomocí lokálního modelu z rodiny `sentence-transformers` (např. mE5 nebo BGE, pro off-line vendor-independent provoz)
- [ ] Ukládání zpracovaných chunků s vektory do databáze (`DocumentChunk` tabulka)

## Fáze 5: Vyhledávací Engine (Semantic & Hybrid Search)
- [ ] Sestavení databázového dotazu pro vektorové vyhledávání (např. využití Cosine Similarity `1 - (vector <#> query_vector)`)
- [ ] Implementace full-textového vyhledávání přes lexikální matching (`tsquery`)
- [ ] Expozice endpointu `GET /search`, který tyto dvě metody kombinuje (Hybridní vyhledávání, možná fúze výsledků přes algoritmus RRF - Reciprocal Rank Fusion)

## Fáze 6: Kompletace a Odevzdání
- [ ] Pokrytí klíčových funkcí pomocí `pytest`
- [ ] Vyčištění kódu a aktualizace dokumentace
- [ ] Finální commit a push do vzdáleného repozitáře (GitHub) za účelem archivace
