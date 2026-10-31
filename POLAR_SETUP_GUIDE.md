# PMax Sentry Pro — Polar.sh Setup & Monetization Guide

Dieses Dokument führt dich Schritt für Schritt durch das Setup deines **Polar.sh Accounts**, die Erstellung deiner Produkte und Benefits (License Keys + Download-Bundle) sowie die Integration in die CLI und AI Agent Skills.

---

## 1. Warum Polar.sh für PMax Sentry?

Polar.sh (`https://polar.sh`) ist ein spezialisierter **Merchant of Record (MoR)** für Developer Tools, Open-Source-Maintainer und Indie-Hacker:
- **Steuerbefreiung / MoR:** Polar übernimmt Rechnungsstellung, Mehrwertsteuer / VAT MOSS weltweit, Stripe-Konto-Führung und Chargebacks. Gebühr: 4% + 40¢ pro Transaktion.
- **Integrierte Lizenzschlüssel:** Polar generiert automatisch kryptografische License Keys (z.B. `pmax_lic_...`), verwaltet Aktivierungslimits und stellt eine Validierungs-API bereit.
- **Kauf-Links:** Sofort einsatzbereite Checkout-URLs für Typer-CLI, GitHub READMEs und AI Agent Skills.
- **Zero Instandhaltungsaufwand:** Keine eigene Datenbank, keine Auth0/Supabase-Infrastruktur nötig.

---

## 2. Schritt-für-Schritt Einrichtung (5 Minuten)

### Schritt 2.1: Account & Organisation anlegen
1. Gehe auf [https://polar.sh](https://polar.sh) und logge dich via GitHub oder E-Mail ein.
2. Erstelle eine **Organization**:
   - Name: `PMax Sentry` (oder dein Agency/Developer-Name)
   - Handle: z.B. `pmax-sentry`
3. Kopiere deine **Organization ID**:
   - Gehe in die Organization Settings.
   - Kopiere die UUID (z.B. `a1b2c3d4-e5f6-7890-abcd-ef1234567890`).

### Schritt 2.2: Benefit "License Keys" erstellen
Gehe im Polar Dashboard auf **Products -> Benefits** und klicke auf **New Benefit**:
- **Type:** `License Keys`
- **Description:** `PMax Sentry Pro License Key`
- **Key Prefix:** `pmax_`
- **Activation Limit:** z.B. `50` (für Agency) bzw. `1` (für Single Pass)

*(Optional: Erstelle einen zweiten Benefit vom Typ `Downloadable File` und lade die Datei `polar_upload/dist/pmax-sentry-pro-0.1.0-bundle.zip` hoch).*

### Schritt 2.3: Die 2 Monetarisierungs-Produkte anlegen

Gehe auf **Products -> Create Product**:

#### Produkt 1: Single Audit Pass
- **Name:** `PMax Sentry - Single Audit Pass`
- **Pricing:** One-time purchase
- **Price:** `149 €` (oder 149 USD)
- **Description:** 
  > Full Performance Max Channel & Format Audit for 1 Google Ads Account.
  > Includes Strict Reconciliation, Break-Even Economics (1/mu), Search Demand Cannibalization Check, and Client-Ready White-Label Pitch Deck (HTML/PDF).
- **Benefits anhängen:** Wähle den zuvor erstellten `License Keys` Benefit.
- **Slug / URL:** `single-pass`

#### Produkt 2: Agency Pro Retainer
- **Name:** `PMax Sentry - Agency Pro Retainer`
- **Pricing:** Monthly subscription
- **Price:** `149 € / month` (oder 199 € / month)
- **Description:**
  > Unlimited White-Label Pitch Decks for New-Business Acquisition.
  > Up to 50 client Google Ads accounts, Causal Incrementality Experiment Design (DiD + Dynamic Power/MDE Protocol), CSV Data Quality Preflight Engine, and FastMCP Server for Cursor & Claude Desktop.
- **Benefits anhängen:** Wähle den `License Keys` Benefit (und ggf. `Downloadable File`).
- **Slug / URL:** `agency-pro`

---

## 3. CLI & Code mit deinem Polar Account verknüpfen

Nachdem du deine Organisation angelegt hast, kannst du deine Organization ID und deinen Checkout-Link dauerhaft in deiner CLI hinterlegen:

```bash
# Setze deine reale Polar Organization ID
pmax-audit license config --org-id "DEINE_POLAR_ORGANIZATION_UUID"

# Setze deine Polar Store URL (falls abweichend)
pmax-audit license config --checkout-url "https://polar.sh/DEIN_HANDLE"
```

Alternativ kannst du Umgebungsvariablen nutzen:
```bash
export POLAR_ORG_ID="DEINE_POLAR_ORGANIZATION_UUID"
export POLAR_CHECKOUT_URL="https://polar.sh/DEIN_HANDLE"
```

---

## 4. Wie der Kunde kauft & aktiviert

1. **Der Lead/Kunde klickt auf den Buy-Link** (z.B. `pmax-audit license buy` oder Link im Pitch Deck / Skill):
   - `https://polar.sh/pmax-sentry/products/single-pass`
   - `https://polar.sh/pmax-sentry/products/agency-pro`
2. **Checkout via Polar:** Kunde zahlt per Kreditkarte, Apple Pay, Google Pay oder SEPA.
3. **Key-Bereitstellung:**
   - Direkt auf dem Erfolgs-Bildschirm sieht der Kunde seinen Key (z.B. `pmax_lic_8f9e2b1a...`).
   - Gleichzeitig erhält er eine E-Mail mit Key und Link zum Polar Customer Portal.
4. **Aktivierung in 1 Sekunde:**
   Der Kunde führt im Terminal aus:
   ```bash
   pmax-audit license activate pmax_lic_8f9e2b1a...
   ```
5. **Ergebnis:**
   - Der Key wird lokal in `~/.pmax_license_key` gespeichert.
   - PMax Sentry Pro validiert den Key gegen Polar.sh (`/v1/customer-portal/license-keys/validate`) und cacht das Ergebnis mit HMAC-Signatur für 24h lokal.
   - Alle Pro-Features (White-Label Decks, DiD Experiment Protocols, MCP Server) sind sofort entsperrt!

---

## 5. Offline & Test-Modus für Entwickler

Für CI/CD, automatische Tests und lokale Demos stehen fest integrierte Test-Keys zur Verfügung (funktionieren offline ohne Netzwerkaufruf):
- `PMAX_TEST_AGENCY_PRO_KEY_12345` -> Schaltet den **Agency Pro** Modus frei.
- `PMAX_TEST_SINGLE_PASS_KEY_12345` -> Schaltet den **Single Audit Pass** frei.

Testbefehl:
```bash
pmax-audit license activate PMAX_TEST_AGENCY_PRO_KEY_12345
pmax-audit license status
```

---

## 6. Payouts (Auszahlung)

1. Gehe im Polar Dashboard auf **Finance -> Payouts**.
2. Verknüpfe dein deutsches/europäisches Bankkonto (SEPA via Stripe Connect).
3. Polar überweist deine Einnahmen automatisch monatlich oder auf Abruf (ab 10 € Guthaben).
4. Für deine Steuer: Polar stellt dir monatlich eine saubere "Merchant of Record"-Sammelabrechnung mit ausgewiesener USt bereit (keine Einzel-Kundenrechnungen für die Steuererklärung nötig!).
