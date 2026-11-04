# Unabhängiges Kritisches Architektur- & Business-Audit: PMax Sentry (`pmax-sentry` & `pmax-sentry-pro`)

Du bist Principal Software Architect, Econometrician und MarTech / Performance-Marketing Experte mit tiefgreifender Praxiserfahrung in Google Ads (insbesondere Performance Max, Smart Bidding, Target ROAS, Merchant Center Feeds), Inkrementalitätsmessung (GeoX, DiD, Synthetic Controls), Agentur-Workflows und Developer Tools / MCP-Servern.

Verzichte auf oberflächliches Lob, Gefälligkeiten oder Sycophancy. Liefere ein ungeschöntes, messerscharfes Review auf Senior-Niveau.

---

## 1. Das Projekt & Der Kontext

**Name:** `PMax Sentry` (Free: `pmax-sentry`, Commercial: `pmax-sentry-pro`)
**Ziel:** Transparenz in die Black-Box "Performance Max" bringen und Werbetreibenden helfen, die Auslieferung zu prüfen und festzustellen, ob berichtete Ergebnisse tatsächlich inkrementell zum Geschäftserfolg beitragen.

### Die 3 Evidenz-Stufen (Strenges Disziplin-Modell):
1. **Delivery Observability (Free Open-Source):**
   - Nutzt die Google Ads API v26 Segmentierung (`ad_network_type`, `ad_using_product_data`, `ad_using_video`).
   - Trennt Kanal (Search, Partners, Display, YouTube, Discover, Gmail, Maps) und Format-Flags sauber als orthogonale Dimensionen (kein doppeltes Zählen überlappender Formate).
   - Führt separate unsegmentierte Kampagnen-Gesamtabfragen durch und reconciliert die Kosten (Raw Difference, Coverage Ratio, Status: `COMPLETE`, `PARTIAL`, `UNAVAILABLE`). Maskiert Residuen niemals mit `max(0, residual)` und deklariert Differenzen niemals ungeprüft als "Display" oder "Waste".
   - Search Demand Insights aus `campaign_search_term_insight`: Fragt **niemals** `metrics.cost_micros` ab. Weist Nutzer darauf hin, dass Suchbegriffskategorien reines Nachfragevolumen sind und keine Budgetallokation belegen.
2. **Historical Diagnosis (Pro):**
   - Verknüpft Kampagnenaktivität mit echten täglichen Geschäftsergebnissen (Gesamtumsatz, organische Erlöse, Non-PMax Spend, Promos, Lagerengpässe).
   - Preflight Data Quality Check: Prüft Mindestlaufzeit (>= 30 Tage), lückenlose Kontinuität, Conversion-Lag Maturation (Reifefenster) und Spend-Varianz ($CV \ge 0.05$). Bei unzureichenden Daten wird `INSUFFICIENT_DATA` gemeldet, statt Zahlen zu erfinden.
   - OLS-Regressionsdiagnostik mit Kontrollvariablen: Ausweisung als `modeled iROAS estimate` mit 95%-Konfidenzintervall.
   - Assoziationsdiagnostik zu organischen Erlösen: Zeigt historische Sensitivität, verbietet aber explizit die Bezeichnung als kausalen "Kannibalisierungsnachweis" ohne Experiment.
3. **Causal Validation & Economics (Pro):**
   - Dynamische Power-Analyse & MDE-Berechnung aus Baseline-Varianz und Conversion-Lag (keine fixen 14-Tage/4-Zellen-Defaults).
   - Experiment-Protokoll-Planung (Geo-Tests / native Splits) mit expliziten erlaubten/verbotenen Kampagnenänderungen und Abbruchbedingungen.
   - Difference-in-Differences (DiD) Auswertung für abgeschlossene Tests mit 95%-Konfidenzintervall, p-Wert und Deklaration als `EXPERIMENTAL / measured iROAS`.
   - Deckungsbeitrags-Hürde: $\text{Break-Even iROAS} = \frac{1}{\mu}$ (wobei $\mu$ die Deckungsbeitragsmarge vor Werbekosten ist). Verdeutlicht, dass der gewinnmaximale Punkt bei marginalem iROAS liegt und durch durchschnittlichen ROAS nicht bestimmt werden kann.
   - Strukturierte Decision Contracts (JSON) mit Versionsnummer, Annahmen, Limitationen und `approval_required: true`. Keine Live-Mutationen in v1.

### Architektur & Tech-Stack:
- **Monorepo / Workspace Topologie:**
  - `packages/pmax_sentry_core`: Shared Pydantic v2 Schemas, API v26 Client (Live + deterministische Offline-Mocks), Reconciliation Engine, CSV/JSON Exporter.
  - `packages/pmax_sentry_cli`: Typer + Rich CLI (`pmax-audit`) mit Dry-Run Preview, Tabellendarstellung, Exporten.
  - `packages/pmax_sentry_mcp`: FastMCP Server mit 11 typisierten Read-Only Tools für KI-Agenten (Claude Desktop, Cursor, etc.).
  - `packages/pmax_sentry_pro`: Thin Client Library (`PMaxSentryProClient`) für ASGI/HTTP.
  - `apps/pro_api`: FastAPI Backend, Mandantenisolierung, Datensatz- und Workspace-Verwaltung, Log-Sanitization (Maskierung von IDs, Tokens, Umsätzen).
  - `apps/pro_web`: Self-Service Web Dashboard & OpenAPI Doku.
  - `services/`: Ingestion, Data Quality Preflight, Incrementality Modeling, Decision Contracts.
  - Testsuite: 46 automatisierte Pytest-Tests (100% Pass Rate, 81% Statement Coverage).

---

## 2. Die Kernfrage des Gründers (Wirtschaftlichkeit & Zeiteinsatz)

Der Gründer fragt explizit:
> **"Bewerte das Projekt: Kann dieses Produkt 500 € pro Monat bei einem Zeitaufwand von maximal 1 Stunde pro Woche erwirtschaften? Was muss konkret getan werden, um dorthin zu kommen?"**

Mögliche Monetarisierungsansätze:
- **Modell A (Single Audit Pass):** 149 € bis 199 € einmalig für einen tiefen PMax Delivery & Reconciled Audit Report + Deckungsbeitrags-Analyse. (Bedarf: 3 Verkäufe/Monat).
- **Modell B (Agency Pro Retainer):** 99 € bis 149 € / Monat pro Agentur für Multi-Account Audits, Experiment-Planung, White-Label Decision Contracts für Pitches. (Bedarf: 4-5 aktive Agentur-Abonnements).
- **Modell C (Micro-SaaS / Hybrid):** Kostenloser CLI/MCP Audit-Hook -> Upsell auf Pro Business Data Ingestion & Causal Validation.

Bitte analysiere diesen spezifischen Case schonungslos:
1. **Mathematik & Realitäts-Check:** 500 €/Monat brutto vs. netto; Churn bei Agenturen vs. Tretmühle bei Einmal-Audits.
2. **Der 1h/Woche Constraint (4h/Monat):** Ist das bei Support, Google Ads API Token-Approval, OAuth-Verifizierung, CSV-Importproblemen und Akquise realistisch?
3. **Agentur-Schmerzpunkt vs. Eigenbaulösungen:** Warum sollte eine Agentur PMax Sentry nutzen, statt ein kostenloses Google Ads Script (z. B. Mike Rhodes PMax Script) oder Standard-Dashboards (Looker Studio) zu nutzen? Worin liegt der echte Unique Value Proposition (UVP)?
4. **Verkaufshürden:** Braucht PMax Sentry Google API Developer Token Production Approval? Wie umgeht man monatelange Google-Audit-Hürden mit 1h/Woche?
5. **Was ist die realistischste Strategie, um stabil 500 €/Monat mit minimalem Zeitaufwand einzufahren?**

---

## 3. Bewertungsauftrag & Struktur

Bitte strukturiere deine Antwort exakt wie folgt:

### 1. Executive Summary & Ökonomisches Urteil (Hard Truths)
- Klares Ja / Nein / Ja-unter-Bedingungen zur Frage: "500 €/Monat bei max. 1h/Woche".
- Realistischer Zeiteinsatz in Phase 1 (Setup/Go-to-Market) vs. Phase 2 (Wartung & Support).
- Welches Preismodell (Einmal-Audit vs. Agentur-Abo) das Ziel am ehesten ermöglicht.

### 2. Detailliertes Scoring (1 - 10)
Bewerte folgende Dimensionen und begründe jede Note in 2-3 prägnanten Sätzen:
- **A. Domänenmodellierung & fachliche Realität (1-10):** Wie akkurat sind die 3 Evidenzstufen, die dimensionale Kanaltrennung und die ökonomische Hürde $1/\mu$ gegenüber realer PMax-Praxis?
- **B. Technische Architektur & Code-Design (1-10):** Monorepo, Schemas, Testabdeckung (46 Tests, 81% Coverage), Offline-Mocks, FastAPI & FastMCP.
- **C. Agentic Readiness & Interfaces (1-10):** MCP-Server (11 Tools), Typer CLI, JSON Decision Contracts, Integrationsfähigkeit in Cursor / Claude.
- **D. Betriebssicherheit, Robustheit & DSGVO (1-10):** Read-Only Boundary, Log-Sanitization, Mandantenisolierung, Datenlöschung.
- **E. Ökonomische Tragfähigkeit (500 € / 1h/Woche) (1-10):** Akquiseaufwand, Google-Ads-API Hürden, Support-Last bei Datenimporten.
- **GESAMT-SCORE (1-10)** mit Benchmark-Vergleich zu Standard-PMax-Skripten (Mike Rhodes / Looker Studio) und Enterprise-Messplattformen (z. B. Measured, Haus, Lifetimely).

### 3. Die 3 stärksten Differenzierungsmerkmale (UVP)
Welche Aspekte heben das Projekt fundamental von den typischen "PMax Spend Leak"-Skripten ab?

### 4. Blinde Flecken, technische & geschäftliche Risiken
Konkrete Gefahren: Google Ads API Developer Token Tiering (Test Account vs Basic vs Standard Access), OAuth Consent Screen Verifikation, Agency Churn, Erklärungsbedürftigkeit von Inkrementalität.

### 5. Strategischer Go-to-Market Fahrplan für 500 €/Monat (1h/Woche)
Schritt-für-Schritt-Plan, wie man mit minimalem Zeiteinsatz die ersten zahlenden Kunden gewinnt und den Betrieb unter 1 Stunde pro Woche hält (z. B. "Local CLI / CSV-First statt Hosted OAuth", White-Label Pitch Decks).

### 6. Priorisierte Roadmap (P0 - P2)
- **P0: Sofort / Kritisch** (Was muss vor dem ersten Verkaufsgespräch existieren?)
- **P1: Hoher Mehrwert** (Was automatisiert den Funnel und eliminiert Support-Zeit?)
- **P2: Spätere Skalierung** (Nice-to-have, wenn Zeit übrig ist)
