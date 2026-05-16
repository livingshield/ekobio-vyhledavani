# Alternativní analýza: Realizace přes Microsoft Power Platform

## 1. Manažerské shrnutí

Tento dokument analyzuje **alternativní scénář**, ve kterém by byl systém „Sémantický index dokumentů" realizován primárně pomocí ekosystému **Microsoft Power Platform** (Power Apps, Power Automate, Dataverse) namísto vlastního open-source řešení (FastAPI + PostgreSQL/pgvector).

> [!CAUTION]
> **Klíčový závěr:** Power Platform **nemůže splnit zadání tak, jak je specifikováno**, protože specifikace explicitně vyžaduje PostgreSQL, pgvector, open-source licence, kontejnerizaci a absenci vendor lock-in. Přesto je tato analýza cenná jako **porovnávací studie** pro rozhodovací orgány AČR, aby pochopily finanční a technické důsledky obou přístupů.

Realizace přes Power Platform by vyžadovala **hybridní architekturu** – Power Platform by sloužil jako orchestrační a uživatelská vrstva, zatímco jádro vektorového vyhledávání by muselo být delegováno na služby Azure (Azure AI Search, Azure Functions, Azure OpenAI). Toto řešení přináší **výrazně vyšší měsíční provozní náklady (OPEX)** a **plnou závislost na cloudu Microsoft**, což je v přímém rozporu s požadavky na on-premise provoz v izolované síti AČR.

---

## 2. Mapování požadavků specifikace na Power Platform

Níže je systematická analýza každého klíčového požadavku specifikace a jeho řešitelnosti v rámci Power Platform.

### 2.1 Požadavky, které Power Platform NESPLŇUJE

| # | Požadavek ze specifikace | Problém na Power Platform | Závažnost |
|:--|:---|:---|:---:|
| §1 | **PostgreSQL + pgvector** jako primární úložiště | Dataverse je proprietární databáze Microsoft, nemá vektorové rozšíření. Nelze nahradit PostgreSQL. | 🔴 Kritická |
| §1 | **UUIDv7** jako primární klíče | Dataverse používá vlastní GUID generátor (v4). UUIDv7 nelze nativně vynutit. | 🟡 Střední |
| Obecné | **Výhradně open-source technologie** (MIT/Apache/BSD) | Power Platform, Dataverse, Power Automate a Power Apps jsou **proprietární** software Microsoftu. | 🔴 Kritická |
| Obecné | **Žádný vendor lock-in** | Celé řešení by bylo uzamčeno v ekosystému Microsoft. Migrace mimo Power Platform je extrémně nákladná. | 🔴 Kritická |
| §2 | **Distribuováno jako Docker kontejnery** | Power Platform nepodporuje kontejnerizaci. Aplikace běží výhradně v cloudu Microsoftu. | 🔴 Kritická |
| §2 | **Provoz bez připojení k internetu** | Power Platform je cloudová služba vyžadující permanentní internetové připojení. Offline provoz není možný. | 🔴 Kritická |
| §3 | **Modulární výměna embedding modelů bez rekompilace** | Na Power Platform neexistuje koncept „rekompilace", ale výměna modelu vyžaduje přepojení konektorů a úpravu flow. | 🟡 Střední |
| §8 | **REST API s OpenAPI specifikací** | Power Apps neposkytuje vlastní REST API. Dataverse Web API existuje, ale nemá strukturu dle specifikace (verzované `/api/v1/`). | 🟠 Vysoká |
| §9 | **Horizontální škálování** | Power Platform škáluje automaticky, ale uživatel nemá nad tím kontrolu. Nelze přidat „worker node". | 🟡 Střední |
| §10 | **Prometheus-kompatibilní metriky** | Power Platform neposkytuje Prometheus endpoint. Monitoring je omezen na Power Platform Admin Center a Application Insights. | 🟡 Střední |
| §12 | **Jazyk C#, Python nebo JavaScript** | Power Automate využívá vizuální flow designer, nikoli kód. Logika se píše v Power Fx (proprietární jazyk). Custom kód vyžaduje Azure Functions. | 🟠 Vysoká |
| §16 | **Předání kompletních zdrojových kódů** | Power Apps a Power Automate flows nejsou „zdrojové kódy" v tradičním smyslu. Export je možný pouze jako řešení (Solution) importovatelné zpět do Power Platform. | 🟠 Vysoká |

### 2.2 Požadavky, které Power Platform SPLŇUJE (s omezeními)

| # | Požadavek | Řešení na Power Platform | Omezení |
|:--|:---|:---|:---|
| §5 | **Tagy a metadata** | Dataverse tabulky s relacemi (N:N). Globální sada tagů pomocí Option Set nebo dedikované tabulky. | Funguje dobře, ale s limity na Dataverse storage ($40/GB/měsíc). |
| §7 | **Asynchronní zpracování** | Power Automate flow se spustí na trigger. Dlouhotrvající operace řeší přes Azure Durable Functions. | Timeout jednotlivých HTTP akcí ~120s. Celý flow max 30 dní, ale je nutný asynchronní vzor. |
| §11 | **Autentizace přes Entra ID** | **Nativní výhoda.** Power Platform je přímo integrován s Entra ID. SSO, role, security groups – vše funguje out-of-the-box. | Žádné omezení – toto je nejsilnější stránka Power Platform. |
| §14 | **Zálohování a DR** | Dataverse má automatické denní zálohy s retencí 28 dní. Geo-redundance. | Zálohy spravuje Microsoft, uživatel má omezenou kontrolu. |

---

## 3. Navrhovaná hybridní architektura (Power Platform + Azure)

Protože Power Platform nemá nativní podporu vektorového vyhledávání, je nutné vybudovat **hybridní architekturu**, kde Power Platform slouží pouze jako „frontend" a orchestrátor:

```
┌─────────────────────────────────────────────────────────────┐
│                    UŽIVATELSKÁ VRSTVA                        │
│  ┌──────────────┐    ┌──────────────┐    ┌───────────────┐  │
│  │  Power Apps   │    │  Power Apps   │    │   Copilot     │  │
│  │  (Upload UI)  │    │  (Search UI)  │    │   Studio      │  │
│  └──────┬───────┘    └──────┬───────┘    └───────┬───────┘  │
│         │                   │                     │          │
│         ▼                   ▼                     ▼          │
│  ┌────────────────────────────────────────────────────────┐  │
│  │             Power Automate (Orchestrace)               │  │
│  │  • Trigger na upload → spustí Azure Function           │  │
│  │  • Polling stavu zpracování                            │  │
│  │  • Volání Azure AI Search pro vyhledávání              │  │
│  └──────────────────────┬─────────────────────────────────┘  │
│                         │ Custom Connector                   │
└─────────────────────────┼───────────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────────┐
│                    AZURE SLUŽBY                              │
│                         ▼                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Azure Functions (Durable)                            │   │
│  │  • PDF parsing + chunking                             │   │
│  │  • Volání Azure OpenAI pro embeddingy                 │   │
│  │  • Ukládání do Azure AI Search                        │   │
│  └──────────┬────────────────────┬───────────────────────┘   │
│             │                    │                            │
│             ▼                    ▼                            │
│  ┌──────────────────┐  ┌──────────────────────┐              │
│  │  Azure OpenAI     │  │  Azure AI Search     │             │
│  │  (Embeddingy)     │  │  (Vektorový index)   │             │
│  └──────────────────┘  └──────────────────────┘              │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────────┐              │
│  │  Azure Blob       │  │  Dataverse            │             │
│  │  Storage (PDF)    │  │  (Metadata, Tagy)     │             │
│  └──────────────────┘  └──────────────────────┘              │
└──────────────────────────────────────────────────────────────┘
```

### Tok dat:
1. Uživatel nahraje PDF přes **Power Apps** → soubor se uloží do **Azure Blob Storage**.
2. **Power Automate** detekuje nový soubor, vytvoří záznam v **Dataverse** a zavolá **Azure Durable Function**.
3. Azure Function provede: PDF parsing → chunkování → volání **Azure OpenAI** pro generování embeddingů → uložení do **Azure AI Search** indexu.
4. Uživatel vyhledává přes **Power Apps** → Power Automate volá **Azure AI Search** přes Custom Connector → vrací výsledky.

---

## 4. Finanční analýza: Power Platform + Azure (OPEX model)

Na rozdíl od on-premise řešení (jednorázový CAPEX za hardware), Power Platform přechází na **čistě měsíční cloudový model** (OPEX). To znamená permanentní měsíční platby po celou dobu provozu.

### 4.1 Licence Power Platform

| Položka | Počet | Cena/měsíc | Roční náklad |
|:---|:---:|:---:|:---:|
| **Power Apps Premium** (uživatelé systému) | 50 uživatelů | $20 × 50 = **$1 000/měs** | **$12 000** |
| **Power Automate Premium** (orchestrace) | 10 uživatelů | $15 × 10 = **$150/měs** | **$1 800** |
| **Dataverse Database Storage** (metadata, tagy – odhad 5 GB navíc) | 5 GB | $40 × 5 = **$200/měs** | **$2 400** |
| **Dataverse File Storage** (pokud se ukládají PDF lokálně v Dataverse – odhad 50 GB) | 50 GB | $2 × 50 = **$100/měs** | **$1 200** |
| **Celkem Power Platform licence** | | **~$1 450/měs** | **~$17 400/rok** |

### 4.2 Služby Azure (výpočetní jádro)

| Služba | Konfigurace | Cena/měsíc | Roční náklad |
|:---|:---|:---:|:---:|
| **Azure AI Search** (vektorový index) | Tier S1, 1 replika, 1 partition | **~$245/měs** | **$2 940** |
| **Azure OpenAI** (embeddingy, text-embedding-3-small) | Odhad 10M tokenů/měsíc (průběžné indexování) | **~$0.22/měs** | **~$3** |
| **Azure OpenAI** (embeddingy, dávková reindexace – 500M tokenů jednorázově) | Jednorázový batch | **~$11** | **$11 (jednorázově)** |
| **Azure Functions** (Durable – PDF parsing, chunking) | Consumption plan, odhad 50 000 exec/měsíc | **~$20/měs** | **$240** |
| **Azure Blob Storage** (úložiště originálních PDF) | 100 GB, Hot tier | **~$2/měs** | **$24** |
| **Celkem Azure služby** | | **~$270/měs** | **~$3 220/rok** |

### 4.3 Vývoj a integrace (jednorázový CAPEX)

| Položka | Odhad MD | Cena (CZK bez DPH) |
|:---|:---:|:---:|
| **Vývoj Power Apps UI** (upload + search formuláře) | 15 MD | 225 000 Kč |
| **Vývoj Power Automate flows** (orchestrace, error handling) | 10 MD | 150 000 Kč |
| **Azure Durable Functions** (PDF parsing, chunking, embedding pipeline) | 25 MD | 375 000 Kč |
| **Custom Connectors** (napojení Power Platform ↔ Azure AI Search, Azure Functions) | 8 MD | 120 000 Kč |
| **Dataverse datový model** (tabulky, relace, security roles) | 5 MD | 75 000 Kč |
| **Testování a nasazení** | 7 MD | 105 000 Kč |
| **Celkem Vývoj** | **70 MD** | **1 050 000 Kč** |

---

## 5. Srovnání: On-Premise (vlastní řešení) vs. Power Platform

### 5.1 Finanční srovnání (TCO za 5 let)

| Období | On-Premise (FastAPI + pgvector) | Power Platform + Azure |
|:---|:---:|:---:|
| **Rok 0 – Počáteční investice** | | |
| Hardware (servery, GPU) | 3 000 000 Kč | 0 Kč |
| Vývoj a integrace | 2 150 000 Kč | 1 050 000 Kč |
| **Rok 0 celkem** | **5 150 000 Kč** | **1 050 000 Kč** |
| **Roky 1–5 – Provozní náklady (ročně)** | | |
| Licence SW | 0 Kč | 0 Kč (open-source) |
| Cloudové licence (Power Platform) | 0 Kč | ~435 000 Kč/rok ($17 400) |
| Cloudové služby (Azure) | 0 Kč | ~80 500 Kč/rok ($3 220) |
| SLA, údržba, patch management | 800 000 Kč/rok | 400 000 Kč/rok |
| **Provozní náklady za 5 let** | **4 000 000 Kč** | **4 577 500 Kč** |
| | | |
| **TCO za 5 let celkem** | **~9 150 000 Kč** | **~5 627 500 Kč** |

> [!IMPORTANT]
> Na první pohled vychází Power Platform o **~3,5M Kč levněji** za 5 let. Toto číslo je však **zavádějící**, protože:
> 1. **Nezahrnuje bezpečnostní audit NÚKIB** – Power Platform řešení by vyžadovalo schválení provozu utajovaných dat v cloudu Microsoft, což je pro AČR mnohem složitější proces.
> 2. **Nezahrnuje riziko cenových změn** – Microsoft pravidelně upravuje ceny Power Platform (naposledy odebrání Per-App plánu v lednu 2026). Za 5 let mohou náklady vzrůst o 30–50 %.
> 3. **Nezahrnuje vendor lock-in náklady** – při budoucí migraci mimo Microsoft bude nutné celý systém přepsat od nuly.
> 4. **Nesplňuje specifikaci** – řešení by neprošlo akceptačními kritérii (§13), protože nepoužívá PostgreSQL/pgvector a není open-source.

### 5.2 Technické srovnání

| Kritérium | On-Premise | Power Platform |
|:---|:---:|:---:|
| **Splnění specifikace** | ✅ Plné | ❌ Nesplňuje 6+ kritických bodů |
| **Vendor lock-in** | ✅ Žádný | ❌ Plný (Microsoft) |
| **Offline provoz** | ✅ Ano | ❌ Ne (vyžaduje internet) |
| **Kontrola nad daty** | ✅ Plná (fyzické servery AČR) | ⚠️ Data v Azure cloudu |
| **Kontrola nad výkonem** | ✅ Plná (vlastní GPU) | ⚠️ Závislé na Azure SLA |
| **Rychlost vyhledávání** | ✅ < 2s (lokální pgvector) | ⚠️ Závisí na latenci Power Automate → Azure AI Search (~2–5s) |
| **Horizontální škálování** | ✅ Docker kontejnery | ⚠️ Automatické, ale nekontrolovatelné |
| **Autentizace Entra ID** | ✅ Ano (OIDC/OAuth) | ✅ Nativní (výhoda) |
| **OpenAPI dokumentace** | ✅ Automaticky (FastAPI) | ❌ Power Apps neposkytuje |
| **Zdrojové kódy** | ✅ Plné předání | ⚠️ Export Solution (proprietární formát) |
| **Prometheus metriky** | ✅ Ano | ❌ Ne |
| **Reindexace dokumentů** | ✅ Nativní (Celery task) | ⚠️ Nutný custom Azure Function |
| **Bezpečnostní klasifikace** | ✅ Jednodušší (on-premise) | ❌ Složitější (cloud, data sovereignty) |

---

## 6. Kritické technické problémy Power Platform řešení

### 6.1 Absence vektorového vyhledávání
Dataverse **nemá nativní podporu vektorů ani embeddingů**. Veškeré vektorové operace musí být delegovány na Azure AI Search, což přidává:
- **Síťovou latenci** (Power Platform → Custom Connector → Azure AI Search)
- **Další bod selhání** (pokud Azure AI Search spadne, vyhledávání nefunguje)
- **Dodatečné náklady** ($245/měsíc za S1 tier)

### 6.2 API throttling
Dataverse má přísné limity:
- **6 000 požadavků / 5 minut** na uživatele (Service Protection)
- **40 000 požadavků / 24 hodin** na licencovaného uživatele (Entitlement)
- Custom Connector: **~500 požadavků/minutu**

Při dávkovém zpracování tisíců dokumentů (chunking + embedding) tyto limity snadno způsobí chyby `429 Too Many Requests`.

### 6.3 Timeout omezení
Power Automate HTTP akce mají timeout ~120 sekund. Zpracování velkého PDF (desítky stran, extrakce tabulek, generování embeddingů) v jednom HTTP callu není možné. Je nutný asynchronní vzor přes Azure Durable Functions, což výrazně zvyšuje složitost.

### 6.4 Nemožnost offline provozu
Specifikace (§2) vyžaduje, aby systém **nevyžadoval trvalé připojení k internetu**. Power Platform je cloudová služba – bez internetu nefunguje vůbec. Toto je **nepřekonatelná překážka** pro nasazení v izolovaných vojenských sítích.

---

## 7. Kdy má Power Platform smysl?

Navzdory výše uvedeným omezením existují scénáře, kde Power Platform **dává smysl jako doplněk** (nikoliv náhrada) vlastního řešení:

| Scénář | Přínos Power Platform |
|:---|:---|
| **Admin dashboard** | Power Apps jako rychlé UI pro správu dokumentů, tagů a monitoringu nad existující databází (přes Custom Connector na FastAPI). |
| **Notifikace a workflow** | Power Automate pro upozornění na dokončení indexace, chyby, schvalovací procesy. |
| **Prototypování** | Rychlé vytvoření MVP pro demonstraci konceptu před investicí do plného vývoje. |
| **Integrace s M365** | Automatické indexování dokumentů ze SharePoint, OneDrive nebo Teams. |

---

## 8. Závěrečné doporučení

### Pro splnění zadání veřejné zakázky:
> **Doporučení: On-Premise řešení (FastAPI + PostgreSQL/pgvector)**

Power Platform nelze použít jako primární platformu, protože:
1. ❌ Nesplňuje požadavek na **PostgreSQL + pgvector** (§1)
2. ❌ Nesplňuje požadavek na **open-source licence** (Obecné podmínky)
3. ❌ Nesplňuje požadavek na **offline provoz** (§2)
4. ❌ Nesplňuje požadavek na **kontejnerizaci** (§2)
5. ❌ Nesplňuje požadavek na **absenci vendor lock-in** (Obecné podmínky)
6. ❌ Nesplňuje požadavek na **předání zdrojových kódů** v otevřeném formátu (§16)

### Možná hybridní strategie do budoucna:
Po úspěšném nasazení on-premise řešení lze zvážit **volitelnou integraci** Power Platform jako uživatelského rozhraní pro nekritické operace (správa tagů, notifikace), přičemž jádro systému (vektorové vyhledávání, zpracování dokumentů) zůstane na vlastní infrastruktuře AČR.

---

*Dokument vypracován: květen 2026*
*Kurz použitý pro přepočet: 1 USD ≈ 25 CZK*
