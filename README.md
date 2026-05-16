# Sémantický index dokumentů

Vendor-independent on-premise systém pro sémantické vyhledávání nad PDF dokumenty s využitím vektorových embeddingů a full-text vyhledávání.

## Technologie
- **Backend:** Python 3.12+, FastAPI
- **Databáze:** PostgreSQL 16 + `pgvector`
- **Fronta úloh:** Redis + Celery
- **Autentizace:** Microsoft Entra ID (OIDC)

## Spuštění vývojového prostředí
1. Spuštění infrastruktury:
   ```bash
   docker-compose up -d
   ```
2. Inicializace databáze a spuštění API (brzy bude doplněno).
