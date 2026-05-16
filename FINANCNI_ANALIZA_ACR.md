# Analýza finančních nákladů: Sémantický index dokumentů (pro potřeby AČR)

Tento dokument poskytuje odhad finančních nákladů (TCO - Total Cost of Ownership) na implementaci, provoz a údržbu systému "Sémantický index dokumentů" v zabezpečeném prostředí Armády České republiky (AČR).

## 1. Manažerské shrnutí
Klíčovou strategickou výhodou navržené architektury je **nulový vendor-lock-in** a **100% On-Premise provoz**. Systém je postaven primárně na open-source technologiích (PostgreSQL, pgvector, FastAPI, Redis, lokální AI modely), což znamená, že **licenční poplatky za software tvoří 0 Kč**. Rozpočet se tak alokuje výhradně do robustního hardwaru, vlastního vývoje, bezpečnosti a dlouhodobé podpory.

---

## 2. Infrastruktura a Hardware (CAPEX)
Vzhledem k požadavkům na bezpečnost (zpracování utajovaných či citlivých informací AČR) nesmí data opustit lokální síť. Systém vyžaduje dedikovaný hardware, zejména pro výpočetně náročné generování vektorových embeddingů.

| Položka | Popis a parametry | Odhadovaná cena (CZK bez DPH) |
| :--- | :--- | :--- |
| **Databázový uzel (Vector DB)** | Server s rychlým NVMe SSD polem a vysokou kapacitou RAM (min. 128 GB) pro efektivní in-memory indexaci v `pgvector`. | 350 000 Kč |
| **Aplikační/Worker uzel** | Běžný aplikační server (např. 16-32 jader, 64 GB RAM) pro FastAPI a Celery frontu. | 200 000 Kč |
| **Inference uzel (GPU Server)** | Zásadní prvek. Pro rychlé parsování milionů dokumentů a výpočet AI embeddingů (např. BGE/mE5) bez odesílání dat ven je nutný server s GPU akcelerátory (např. 2x NVIDIA L40S nebo A100). | 1 500 000 - 2 500 000 Kč |
| **Zálohování a síť. prvky** | Dedikovaný storage pro bezpečné repliky databáze a odpovídající síťová infrastruktura. | 300 000 Kč |
| **Celkem Hardware** | | **~ 2 350 000 - 3 350 000 Kč** |

---

## 3. Softwarové licence (OPEX)
Systém nevyužívá proprietární SaaS služby.

| Položka | Poskytovatel | Odhadovaná roční cena |
| :--- | :--- | :--- |
| **OS a Databáze** | Linux, PostgreSQL, Redis | 0 Kč (Open-Source) |
| **LLM a Embedding Modely** | HuggingFace (MIT/Apache 2.0) | 0 Kč (Open-Source) |
| **Autentizace (Entra ID)** | Microsoft | Využity existující licence AČR (M365/Azure) |
| **Celkem Licence** | | **0 Kč** |

---

## 4. Vývoj, Integrace a Bezpečnost (Služby - CAPEX)
Náklady na lidské zdroje (Man-Days - MD) nutné k naprogramování, integraci s vojenskými systémy a certifikaci.

| Položka | Odhad náročnosti (MD) | Odhadovaná cena (CZK bez DPH) |
| :--- | :--- | :--- |
| **Vývoj Backend architektury** | Datové modelování, FastAPI, Celery workery, integrace pgvector (cca 40 MD). | 600 000 Kč |
| **AI integrace a ladění** | Zprovoznění lokálních embeddingů, nastavení chunkingu, RRF (Hybrid Search) evaluace (cca 25 MD). | 450 000 Kč |
| **Front-end / Integrace na UI** | Napojení do existujících portálů AČR nebo vývoj klientské aplikace (cca 30 MD). | 450 000 Kč |
| **Integrace na Entra ID (OIDC)** | Napojení a konfigurace rolí, SSO (cca 10 MD). | 150 000 Kč |
| **Bezpečnostní Audit (NÚKIB)** | Nezávislý penetrační test a audit architektury pro schválení provozu ve vnitřní síti. | 350 000 Kč |
| **Instalace a Deployment** | Fyzické nasazení na servery AČR, kontejnerizace (Docker/Kubernetes). | 150 000 Kč |
| **Celkem Implementace** | | **~ 2 150 000 Kč** |

---

## 5. Údržba, SLA a Podpora (OPEX - ročně)
Dlouhodobý provoz vyžaduje údržbu kódu, aktualizace bezpečnostních záplat a rozvoj modelů.

| Položka | Popis | Odhadovaná roční cena (CZK bez DPH) |
| :--- | :--- | :--- |
| **SLA a incident management** | Garantovaná doba reakce na kritické výpadky (např. 24/7 nebo 8/5 s reakcí do 4h). | 400 000 Kč |
| **Patch management** | Bezpečnostní aktualizace závislostí (Python, Postgres, Redis, knihovny). | 150 000 Kč |
| **AI Model Update (Retraining)**| Pravidelné vylepšování chunkingu a embedding modelů v závislosti na nově indexovaných vojenských dokumentech. | 250 000 Kč |
| **Celkem Roční Podpora** | | **~ 800 000 Kč / rok** |

---

## 6. Závěrečná kalkulace
Řešení na míru bez závislosti na cloudových dodavatelích znamená vyšší počáteční investici do výpočetního výkonu (GPU), ale z dlouhodobého hlediska nabízí stabilnější provozní náklady a maximální kontrolu nad informační bezpečností státu.

* **Počáteční investice (CAPEX - HW + Služby):** 4 500 000 - 5 500 000 Kč bez DPH
* **Předpokládané roční provozní náklady (OPEX):** cca 800 000 Kč bez DPH

*(Uvedené částky jsou hrubým expertním odhadem pro rozpočtové plánování a mohou se měnit v závislosti na konkrétní ceně GPU akcelerátorů na trhu a výsledné smluvní hodinové sazbě za vývojové práce).*
