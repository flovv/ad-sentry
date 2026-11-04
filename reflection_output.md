### 1. Executive Summary & Ökonomisches Urteil (Hard Truths)

**Urteil: Für das beschriebene Gesamtprodukt nein. Für ein deutlich engeres Agenturprodukt ja — unter Bedingungen und erst nach einer separaten Aufbauphase.**

500 € Monatsumsatz sind keine hohe Vertriebshürde. **Ein datenintegriertes Messprodukt mit Google-Anbindung, statistischer Beratung und Mandantenbetrieb mit höchstens vier Arbeitsstunden monatlich zu betreiben, ist dagegen eine hohe Betriebshürde.** Euer größtes Risiko ist nicht mangelnde Funktionalität, sondern zu viel Produkt für zu wenig Umsatz und Betreiberzeit.

**Bewertungsgrundlage:** Ich bewerte die beschriebene Spezifikation, keinen inspizierten Quellcode und keine tatsächlich ausgeführten API-Abfragen. Die behauptete v26-Kompatibilität, Testabdeckung und Sicherheitsmaßnahmen sind deshalb noch keine unabhängig verifizierten Eigenschaften.

#### Was bedeuten „500 € verdienen“?

Zunächst müssen Umsatz, Überschuss und persönliches Nettoeinkommen auseinandergehalten werden.

| Modell | Rechnung | Ergebnis vor Kosten und Steuern |
|---|---:|---:|
| Einmalaudit zu 149 € | 3 × 149 € | 447 € — Ziel verfehlt |
| Einmalaudit zu 199 € | 3 × 199 € | 597 € |
| Agenturabo zu 99 € | 5 × 99 € | 495 € — Ziel verfehlt |
| Agenturabo zu 149 € | 4 × 149 € | 596 € |
| Agenturabo zu 199 € | 4 × 199 € | 796 € |

Die Preise müssen ausdrücklich als **netto zuzüglich gegebenenfalls anfallender Umsatzsteuer** definiert sein. Bei regulär 19 % Umsatzsteuer entsprechen 500 € vereinnahmtem Bruttopreis nur rund 420 € Nettoumsatz. Umsatzsteuer ist kein Verdienst; bei Anwendung der Kleinunternehmerregelung gelten andere Voraussetzungen.

Auch 596 € Nettoumsatz sind nicht 596 € Einkommen:

- Zahlungsabwicklung, Hosting, Monitoring und weitere laufende Kosten gehen ab.
- Rückerstattungen und Zahlungsausfälle können hinzukommen.
- Einkommensteuer und gegebenenfalls weitere persönliche Belastungen sind individuell.
- Die Aufbauarbeit ist damit noch nicht amortisiert.

**Wenn 500 € monatlicher Betriebsüberschuss vor persönlicher Steuer gemeint sind, sollte das Umsatzziel eher bei 750–900 € netto liegen.** Das ist ein Planungsziel, keine Kostenprognose.

#### Realistischer Zeitbedarf

**Phase 1 — Aufbau und Markteintritt:** Für ein bereits funktionsfähiges Repository würde ich weitere **30–60 konzentrierte Stunden** für einen eng geschnittenen kommerziellen Pilot einplanen: echte Kundendaten, Importhärtung, Referenzreport, Preisvalidierung, Vertragsunterlagen und erste Verkäufe. Das vollständige Hosted-OAuth-/Causal-Produkt kann erheblich mehr benötigen. Externe Genehmigungen verursachen zusätzlich Kalenderzeit.

**Phase 2 — kleiner Bestandsbetrieb:** Vier Stunden monatlich sind erreichbar, wenn:

- keine betreute Datenintegration angeboten wird;
- kein individuelles Experiment-Consulting enthalten ist;
- lokale Verarbeitung beziehungsweise ein enges Importformat Standard ist;
- Support, Kontenzahl und Auswertungsumfang begrenzt sind;
- Kunden bereits kompetente Google-Ads-Anwender sind;
- keine laufenden Sonderwünsche angenommen werden.

**Eine garantierte Obergrenze von einer Stunde in jeder einzelnen Woche ist bei einem betriebenen SaaS unrealistisch.** Als Monatsdurchschnitt ist sie bei einem einfachen Produkt plausibler; Sicherheits- und API-Vorfälle erzeugen Spitzen.

#### Welches Modell passt?

**Empfehlung: enges Agenturabo, nicht das vollständige Pro-Versprechen.**

Verkauft einen **wiederholbaren, white-label-fähigen PMax-Evidenzreport mit Reconciliation, Qualitätsprüfung und wirtschaftlicher Einordnung**. Verkauft nicht für 149 € monatlich eine individuelle Inkrementalitätsberatung.

- **Einmalaudits:** gut zur Zahlungsbereitschaftsvalidierung, schlecht als dauerhaftes Vier-Stunden-Modell.
- **Agenturabo:** beste Chance auf planbare Einnahmen, sofern echter wiederkehrender Nutzen entsteht.
- **Free → Pro:** sinnvoller Distributionsweg, aber kein Beweis für einen funktionierenden Vertrieb. GitHub-Nutzer und MCP-Installationen sind keine zahlenden Agenturen.

---

### 2. Detailliertes Scoring (1 - 10)

Die Noten bewerten die **beschriebene Konzeption mit Abschlägen für fehlende Implementierungsnachweise**.

| Dimension | Note | Begründung |
|---|---:|---|
| **A. Domänenmodellierung & fachliche Realität** | **7/10** | Die Trennung von Auslieferung, historischer Diagnose und experimenteller Evidenz sowie die explizite Reconciliation sind fachlich wesentlich sauberer als typische „Spend Leak“-Narrative. Der zentrale Fehler bleibt aber: Eine kontrollierte OLS-Regression identifiziert nicht automatisch inkrementellen ROAS; auch DiD verdient das Label „EXPERIMENTAL“ nicht allein aufgrund des verwendeten Schätzers. |
| **B. Technische Architektur & Code-Design** | **6/10** | Shared Schemas, deterministische Mocks und eine gemeinsame Reconciliation Engine sind gute Grundlagen. Für 500 € Monatsziel sind CLI, MCP, Thin Client, API, Dashboard und mehrere Services jedoch eine übergroße Wartungsoberfläche; 46 Tests und 81 % Statement Coverage belegen weder API-Kompatibilität noch statistische Korrektheit oder Mandantensicherheit. |
| **C. Agentic Readiness & Interfaces** | **8/10** | Typisierte Tools, CLI und versionierte Decision Contracts sind gute maschinenlesbare Schnittstellen und erleichtern reproduzierbare Workflows. Elf Tools sind allerdings kein Qualitätsmaß: Entscheidend sind stabile Fehlercodes, Datenherkunft, Größenlimits und die unverlierbare Weitergabe von Evidenzstatus und Einschränkungen. |
| **D. Betriebssicherheit, Robustheit & DSGVO** | **5/10** | Read-only und Log-Sanitization reduzieren Risiken, ersetzen aber weder sichere Autorisierung noch Löschkonzepte, Token-Schutz und vertragliche Datenschutzgrundlagen. Ohne überprüfte Isolationstests, Backup-Löschung, Aufbewahrungsfristen und Klarheit über externe LLM-Datenflüsse ist eine höhere Note nicht gerechtfertigt. |
| **E. Ökonomische Tragfähigkeit: 500 € / 1h pro Woche** | **4/10** | Das Umsatzniveau ist erreichbar, aber die beschriebene Produktbreite passt nicht zum Zeitbudget. Unter einem CSV-/Local-first-Agenturmodell mit begrenztem Leistungsumfang steigt die Perspektive deutlich; für Hosted Ingestion plus individuelle Kausaldiagnostik bleibt sie schlecht. |

**GESAMT-SCORE: 6/10.** Das ist ein fachlich interessanter Ansatz mit noch nicht bewiesenem Betriebssystem und nicht bewiesener Zahlungsbereitschaft — kein bereits validiertes Kleinst-SaaS.

**Benchmark-Einordnung:**

- **Gegenüber Mike-Rhodes-artigen Skripten und Looker Studio:** Potenziell besser bei nachvollziehbarer Reconciliation, Unsicherheitskommunikation, Datenqualitätsgates und wiederholbaren Entscheidungsartefakten. Bei Anschaffungskosten, Bekanntheit, Einrichtung und Vertrautheit gewinnen häufig die etablierten Lösungen.
- **Gegenüber Measured oder Haus:** Keine belegte Vergleichbarkeit bei Experimentbetrieb, Messvalidierung, Datenintegration und fachlicher Betreuung. PMax Sentry wäre zunächst ein enger Workflow-Baustein, kein gleichwertiger Ersatz.
- **Lifetimely ist kein identischer Benchmark:** Profitabilitäts-, LTV- und Attributionstools adressieren teilweise andere Aufgaben als Geo-Experimentplattformen. Diese Kategorien sollten im Vertrieb nicht vermischt werden.

---

### 3. Die 3 stärksten Differenzierungsmerkmale (UVP)

#### 1. Nachvollziehbare Evidenz statt vermeintlicher „Budgetverschwendungs“-Erkennung

Die stärkste fachliche Eigenschaft ist nicht die Kanalaufteilung, sondern die **kontrollierte Aussagegrenze**:

- Beobachtete Auslieferung wird von Formaten getrennt.
- Fehlende Abdeckung bleibt sichtbar.
- Negative und positive Reconciliation-Differenzen werden nicht versteckt.
- Suchnachfrage wird nicht zu erfundenem Kanalbudget.
- Unbekannte Auslieferung wird nicht zu angeblicher Verschwendung umetikettiert.

**Verkaufsfähige Übersetzung:** „Sie können Ihrem Kunden erklären, was die Daten tatsächlich belegen — und was nicht.“

Das ist wertvoll für Agenturen, die sich gegen unbegründete PMax-Vorwürfe verteidigen oder problematische Auslieferung sauber dokumentieren müssen. Es ist allerdings kein starker Schutzwall: Technisch können Wettbewerber diese Regeln übernehmen.

#### 2. Verbindung von Messung und Deckungsbeitragsentscheidung

Die Hürde

\[
\text{Break-even iROAS}=\frac{1}{\mu}
\]

ist wirtschaftlich wesentlich relevanter als ein pauschaler Ziel-ROAS — **wenn** inkrementeller Nettoumsatz und tatsächlich passende Deckungsbeitragsmarge verwendet werden.

Bei 40 % Marge liegt die Hürde bei 2,5. Ein gemessener inkrementeller Umsatz von 2 € je zusätzlichem Werbe-Euro wäre dann trotz positivem Umsatzbeitrag nicht kostendeckend.

Der Mehrwert entsteht aus der vollständigen Kette:

> Datenqualität → Evidenzstärke → Unsicherheit → wirtschaftliche Hürde → zulässige Entscheidung.

**Wichtig:** Ein historischer Durchschnittseffekt rechtfertigt keine Aussage über den gewinnoptimalen nächsten Budget-Euro.

#### 3. Standardisierte, prüfbare Arbeitsprodukte für Agenturen und Agenten

Ein versionierter Decision Contract kann mehr leisten als ein Dashboard:

- nachvollziehbare Datenbasis;
- dokumentierte Annahmen;
- gesperrte Schlussfolgerungen bei unzureichender Evidenz;
- wirtschaftliche Schwellen;
- konkrete nächste Prüfung;
- menschliche Freigabe.

**Der Käufer zahlt nicht für JSON oder MCP. Er zahlt für weniger Berichtserstellung, weniger fachliche Haftungsfläche und ein verwendbares Kundenartefakt.**

White-Label-PDF beziehungsweise Präsentationsvorlage ist deshalb wahrscheinlich verkaufsnäher als ein weiteres MCP-Tool. White-Label darf dabei Einschränkungen und Datenherkunft nicht entfernen.

---

### 4. Blinde Flecken, technische & geschäftliche Risiken

#### A. Die historische Modellierung ist noch keine Inkrementalitätsmessung

Der Ausdruck **„modeled iROAS estimate“** suggeriert mehr Kausalität, als eine gewöhnliche OLS mit Kontrollvariablen hergibt.

PMax-Spend ist endogen: Budgets, Nachfrage, Gebote, Promotions und erwartete Verkaufsmöglichkeiten beeinflussen einander. Kontrollen beseitigen das nicht automatisch. Mehr Kontrollvariablen können die Schätzung sogar verschlechtern, etwa wenn sie selbst durch Werbung beeinflusst werden.

**Konkrete Korrektur:** Standardmäßig als „adjustierte historische Umsatz-Spend-Assoziation“ oder „modellbasierte Umsatzsensitivität“ ausweisen. Ein kausaler iROAS braucht eine begründete Identifikationsstrategie, nicht nur ein Konfidenzintervall.

Weitere Probleme:

- **30 Tage sind eine Untergrenze, kein Eignungsnachweis.** Bei mehreren Kontrollvariablen, Autokorrelation und Wochentagseffekten ist das oft unzureichend.
- **Spend-CV ≥ 0,05 garantiert keine Identifikation.** Die Variation kann vollständig mit Nachfrage oder Aktionen zusammenfallen.
- Organischer Umsatz kann ein **beeinflusstes Ergebnis** sein, nicht bloß eine harmlose Kontrollvariable.
- Klassische OLS-Standardfehler sind bei Zeitreihen häufig ungeeignet.
- Viele getestete Spezifikationen erzeugen scheinbar überzeugende Zufallsergebnisse.

`INSUFFICIENT_DATA` sollte deshalb auch Rangdefizite, geringe effektive Stichprobe, ungeeignete Variation und instabile Modelle erfassen.

#### B. DiD plus p-Wert ist nicht automatisch ein Experiment

Für `EXPERIMENTAL / measured iROAS` muss das **Design** die Bezeichnung tragen.

Erforderlich sind unter anderem:

- dokumentierte Zuweisung beziehungsweise nachvollziehbare Identifikation;
- Prüfung auf Spillovers und Kontamination;
- passende Vergleichsgruppen;
- Prüfung der Vorperioden und Paralleltrend-Plausibilität;
- Inferenz auf Ebene der Zuweisung, etwa Geo-Cluster;
- vorab definierte Zielgrößen und Abbruchregeln.

Wenige Regionen bleiben wenige unabhängige Einheiten, auch wenn viele Tageszeilen vorliegen. Ein nicht signifikanter Pretrend-Test beweist keine Paralleltrends.

Außerdem ist iROAS ein Quotient:

\[
\widehat{iROAS}=\frac{\widehat{\Delta Umsatz}}{\widehat{\Delta Spend}}
\]

Liegt der Spend-Unterschied nahe null, kann das Ergebnis praktisch uninterpretierbar werden. Dafür braucht ihr ein eigenes Gate und eine zum Design passende Intervallschätzung.

Power und MDE hängen nicht nur von Baseline-Varianz und Conversion-Lag ab, sondern auch von Clusterstruktur, Autokorrelation, Testaufteilung, erwarteter Spend-Differenz, Signifikanzniveau und gewünschter Power. Native Split-Möglichkeiten müssen je Kampagnentyp und aktueller Produktunterstützung geprüft werden.

**Für das Vier-Stunden-Geschäft: Experimentbetrieb zunächst nicht als enthaltene Leistung verkaufen.**

#### C. API v26 und Segmentkompatibilität sind Annahmen, bis sie live getestet sind

Die genannten Ressourcen und Segmente müssen für die tatsächlich verwendete API-Version überprüft werden. Ich kann ihre aktuelle v26-Verfügbarkeit hier nicht unabhängig bestätigen.

Ein existierendes Feld ist nicht automatisch mit jeder Ressource, Metrik und Segmentkombination abfragbar. Ebenso ist eine Kanalbezeichnung im Schema kein Beweis, dass die API diese Auslieferung separat liefert.

Erforderlich sind echte Kompatibilitätstests für:

- Kampagnentyp und Abfragekombination;
- NULL-, UNKNOWN- und UNSPECIFIED-Werte;
- Format-Flags innerhalb einer kanonischen Zeilengranularität;
- Zeitzone, Währung und identischen Datumsbereich;
- Aktualisierungszeitpunkt und nachträgliche Datenänderungen.

**Reconciliation-Status und Reconciliation-Differenz sind unterschiedliche Dinge.** Eine kleine Differenz innerhalb dokumentierter Toleranz kann akzeptabel sein; `COMPLETE` sollte nicht stillschweigend als mathematisch exakt verstanden werden.

Ein unvollständiger API-Auszug, ein historischer Re-Export und ein nicht unterstütztes Segment brauchen unterschiedliche Fehlerursachen — nicht nur dieselbe gelbe Warnung.

#### D. Google-Zugang: zwei getrennte Genehmigungsflächen

**Developer Token und OAuth-Verifizierung sind verschiedene Themen.**

- Ein Zugang ausschließlich für Testkonten reicht nicht für Kundenauswertungen.
- Für echte Konten ist eine dafür freigegebene Developer-Token-Zugriffsstufe erforderlich. Basic kann für kleine Nutzungsvolumen genügen; Standard ist keine automatische Pflicht.
- Die aktuelle Tier-Struktur, gegebenenfalls weitere Stufen, Kontingente und zulässige Nutzung müssen anhand der aktuellen Google-Dokumentation geprüft werden.
- Eine externe OAuth-Anwendung mit Google-Ads-Zugriff kann zusätzlich eine Verifizierung benötigen. Read-only macht diese Prüfung nicht automatisch entbehrlich.
- Token-Approval und OAuth-Verifizierung lösen einander nicht ab.

**Was hilft wirklich?**

1. **CSV-Import ohne eigene Ads-Verbindung:** Für diesen Workflow benötigt ihr keinen eigenen Google-Ads-API-Zugang.
2. **Lokaler Betrieb mit kundeneigenem, zulässigem API-Zugang:** Kann die zentrale Tokenhaltung vermeiden, verschiebt aber Einrichtung und Support auf den Kunden.
3. **Interne Kundenanwendung:** Kann unter passenden organisatorischen Voraussetzungen helfen, ist aber keine allgemeine Abkürzung für öffentliche SaaS-Nutzung.

Nicht tragfähig sind das Teilen eines Tokens entgegen den Bedingungen, ein dauerhaftes Ausweichen in OAuth-Testkonfigurationen oder die Behauptung „CLI braucht keine Google-Freigaben“.

**Keine seriöse Planung verspricht eine bestimmte Genehmigungsdauer.** Umgehen solltet ihr nicht die Anforderungen, sondern die Abhängigkeit davon: zunächst ohne eigene Live-Anbindung verkaufen.

#### E. CSV-first reduziert nur dann Support, wenn der Export wirklich existiert

„Einfach CSV hochladen“ ist kein fertiges Onboarding.

Vor dem Verkauf muss geprüft sein, ob der Kunde die benötigten Felder tatsächlich aus einem verfügbaren Export erhält. Eine Standard-Google-Ads-CSV muss nicht dieselbe Granularität und Segmentkombination bieten wie eure API-Abfrage.

CSV-Risiken:

- Dezimaltrennzeichen und Zeichencodierung;
- Brutto-/Nettoumsatz, Retouren und Umsatzsteuer;
- Währungswechsel;
- doppelte oder fehlende Tage;
- unterschiedliche Zeitzonen;
- veränderte Überschriften;
- Conversion-Lag versus Retouren- beziehungsweise Umsatzreife.

**Nicht beliebige Dateien akzeptieren. Ein geprüftes Exportrezept und genau ein versioniertes Importformat anbieten.** Fehlen notwendige Daten, muss der Bericht seinen Umfang reduzieren, nicht die Information rekonstruieren.

#### F. Read-only schützt nicht vor Datenabfluss

Die Kernfragen sind nicht nur „Kann das Tool Budgets ändern?“, sondern:

- Kann Mandant A Datensätze oder Exporte von Mandant B abrufen?
- Werden Tokens verschlüsselt und korrekt widerrufen?
- Landen Umsätze in Fehlertracking, Traces oder Support-Tickets?
- Werden Rohdaten durch MCP an externe KI-Anbieter weitergegeben?
- Umfasst Löschung auch Dateien, Caches und zeitversetzt Backups?
- Sind Auftragsverarbeitung, Unterauftragnehmer und Speicherorte dokumentiert?

Lokale Verarbeitung ist außerdem nicht automatisch privat, sobald ein Thin Client oder Agent die Daten an den Pro-Service sendet.

**Wichtig für MCP:** Suchbegriffe, Produktdaten und andere Textfelder sind nicht vertrauenswürdige Eingaben. Sie dürfen nicht als Agentenanweisungen behandelt werden. `approval_required: true` ist lediglich ein Vertragsfeld, keine technisch erzwungene Sicherheitsgrenze.

#### G. Das Abo hat ein Wiederholungsproblem

Eine Agentur kann einen guten PMax-Audit einmal durchführen, Erkenntnisse übernehmen und kündigen. „Monatlicher Report“ allein schafft keinen dauerhaften Nutzen.

Tragfähiger wiederkehrender Wert entsteht durch:

- neue Kundenkonten;
- regelmäßige Kundenreviews;
- vergleichbare Monatsstände;
- automatisierte Änderungs- und Qualitätsprüfung;
- verlässlich gepflegte Export- und API-Kompatibilität.

Bei vier Kunden kostet eine Kündigung 25 % des MRR. Beispielhaft entsprechen 5 % monatlicher Logo-Churn langfristig ungefähr 20 Monaten mittlerer Kundenlebensdauer unter stark vereinfachten Annahmen. Das ist kein Forecast, zeigt aber: Auch ein Kleinstabo braucht Ersatzakquise.

---

### 5. Strategischer Go-to-Market Fahrplan für 500 €/Monat (1h/Woche)

#### Schritt 1: Das Verkaufsversprechen verengen

**Angebot: „PMax Evidence Review für Agenturen“**

Enthalten:

- standardisierter Delivery-Report;
- Reconciliation und Datenqualitätsstatus;
- Vergleich mit einem vorherigen Bericht;
- einfache Deckungsbeitrags-Szenarien aus Kundeneingaben;
- white-label-fähiger Kundenreport;
- klare Aussagegrenzen und nächste Prüfschritte.

Nicht enthalten:

- individuelle Datenbereinigung;
- maßgeschneiderte Regressionen;
- betreute Geo-Experimente;
- garantierter Kannibalisierungsnachweis;
- Kampagnenoptimierung oder Erfolgsversprechen;
- unbegrenzte Konten und Support.

**Vertriebssatz:** „Ein belastbarer PMax-Kundenreview ohne eigenes Skript- und Reporting-Chaos.“

Nicht: „Wir decken mit KI die wahre Inkrementalität Ihrer PMax-Kampagnen auf.“

#### Schritt 2: Ein funktionierendes Exportrezept vor dem Hosted-Produkt liefern

Ein Referenzkonto nehmen und den gesamten Kundenweg durchspielen:

1. Daten nach dokumentierter Anleitung exportieren.
2. Lokal validieren.
3. Bericht erzeugen.
4. Fehler ohne Gründerhilfe verstehen.
5. Bericht an einen Endkunden weitergeben.

Diesen Ablauf müssen mindestens zwei externe Anwender ohne Bildschirmfreigabe schaffen. Sonst ist das Produkt noch kein Vier-Stunden-Geschäft.

CSV-first bedeutet anfangs gegebenenfalls weniger Funktionen. Das ist besser als ein vollständiges, aber betreuungsintensives Versprechen.

#### Schritt 3: Drei bezahlte Piloten statt Free-User-Reichweite sammeln

Zielgruppe: kleine spezialisierte Agenturen mit wiederkehrenden PMax-Kundenreviews, nicht Marketinganfänger mit einem einzigen Konto.

- Zunächst 10–15 passende Kontakte aus vorhandenem Netzwerk oder individuell recherchierten Agenturen ansprechen.
- Einen anonymisierten Musterreport zeigen.
- Einen **bezahlten Pilot zu 199 € netto** anbieten.
- Pro Pilot höchstens ein kurzes strukturiertes Feedbackgespräch.

Prüfen:

- Spart das Artefakt nachweisbar Arbeit?
- Wird es tatsächlich im Kundengespräch verwendet?
- Gibt es innerhalb weniger Wochen einen zweiten Einsatz?
- Wird eine Anschlusszahlung zum vorgesehenen Preis akzeptiert?

**Lob ist kein Validierungskriterium. Wiederverwendung und Zahlung sind es.**

Diese Pilotphase gehört zur Aufbauzeit, nicht in die spätere Ein-Stunden-Woche.

#### Schritt 4: Auf vier Agenturen zu 199 € netto zielen

Vier Agenturen ergeben **796 € MRR**. Nach Ausfall eines Kunden bleiben 597 € Umsatz; bei vier Agenturen zu 149 € wären es nur noch 447 €.

Dafür muss das Paket begrenzt sein, beispielsweise:

- bis zu fünf definierte Kundenkonten;
- ein monatlicher Standardreport je Konto;
- ein Importformat;
- asynchroner Produktsupport;
- keine individuelle Messberatung.

Die genaue Grenze ist nach gemessener Nutzung festzulegen. „Unbegrenzte Multi-Account-Audits für 99 €“ wäre angesichts des Zeitbudgets eine schlechte Wette.

Falls Agenturen keinen wiederkehrenden Einsatz sehen: **kein Abo erzwingen.** Dann sind Audit-Guthaben oder ein Jahrespaket ehrlicher — allerdings mit weniger planbarem Monatsumsatz.

#### Schritt 5: Betreuung explizit begrenzen

- Keine regulären Support-Calls im Basispaket.
- Keine individuellen CSV-Mappings.
- Klare, realistische Antwortfrist für normalen Support.
- Sicherheitsmeldungen separat behandeln.
- Dokumentierte unterstützte Dateiversionen.
- Automatisierte Abrechnung und Kündigung.
- Fehlerberichte ohne sensible Rohdaten.
- Keine stillschweigende Beratungspflicht über Chat.

White-Label-Vorlagen und kurze Erläuterungstexte verhindern, dass jede Agentur dieselbe Statistikfrage erneut an den Gründer delegiert.

#### Schritt 6: Das monatliche Zeitbudget messen

Ein mögliches Zielbudget:

| Tätigkeit | Minuten pro Monat |
|---|---:|
| Technische Wartung und Versionsprüfung | 60 |
| Support | 60 |
| Ersatzakquise und Empfehlungen | 45 |
| Abrechnung und Administration | 30 |
| Reserve | 45 |
| **Gesamt** | **240** |

Das ist **eine Betriebshypothese, kein Versprechen**. Anfangs jede Minute erfassen, einschließlich Dokumentationspflege, Zahlungsproblemen und „nur kurz“-Nachrichten.

**Abbruch- beziehungsweise Anpassungsregel:** Wenn nach drei Monaten kleiner Bestandsnutzung regelmäßig mehr als vier Stunden monatlich benötigt werden, muss der Umfang sinken, der Preis steigen oder der Hosted-Anteil entfallen. Nicht das Zeitbudget durch unbezahlte Gründerarbeit schönrechnen.

---

### 6. Priorisierte Roadmap (P0 - P2)

#### P0: Sofort / Kritisch

**Vor dem ersten Verkaufsgespräch erforderlich:**

1. **Ein enges Angebot mit Preis und Ausschlüssen.**  
   Eine Seite genügt. Keine Vermischung von Delivery-Audit und kausaler Erfolgsmessung.

2. **Ein überzeugender Beispielreport.**  
   Einschließlich `PARTIAL`-/`UNAVAILABLE`-Fall, negativer Reconciliation-Differenz und ehrlicher Aussagegrenzen.

3. **Ein nachweislich ausführbares Export- und Importrezept.**  
   Nicht nur ein künstliches Mock-CSV, sondern ein praktisch beschaffbarer Datensatz.

4. **Korrigierte Evidenzlabels.**  
   OLS nicht standardmäßig als inkrementellen Effekt verkaufen; `EXPERIMENTAL` an Designkriterien koppeln.

5. **API-Abhängigkeiten transparent benennen.**  
   Verifizierte Fähigkeiten von geplanten v26-Fähigkeiten unterscheiden.

**Vor Verarbeitung echter Kundendaten zusätzlich erforderlich:**

6. **Risiko-orientierte Tests statt Coverage-Marketing.**
   - Keine Doppelzählung von Formatkombinationen.
   - Währungs-, Zeitzonen- und Reconciliation-Tests.
   - Ablehnung unzulässiger Daten und instabiler Modelle.
   - Mandantenübergriff- und Export-Autorisierungstests bei Hosting.
   - Getrennte Kennzeichnung von Mock- und Echtdaten.

7. **Minimal belastbarer Datenschutz- und Sicherheitsrahmen.**  
   Datenfluss, Löschfristen, Tokenbehandlung, relevante Verträge und Incident-Prozess.

#### P1: Hoher Mehrwert

1. **Importvalidierung mit konkreten Selbsthilfeanweisungen.**  
   Fehler wie „Datum fehlt am 12. März“ statt „Validation failed“.

2. **Deterministische Reportgenerierung.**  
   PDF/HTML plus versioniertes JSON aus derselben Datenbasis; Evidenzstatus in allen Formaten identisch.

3. **Self-Service-Onboarding und Abrechnung.**  
   Musterdatei, kurzer Ablauf, Lizenzverwaltung, Rechnung, Kündigung.

4. **Vorperiodenvergleich und gespeicherte Berichtsstände.**  
   Das schafft eher wiederkehrenden Nutzen als zusätzliche Einmaldiagnostik.

5. **Wenige echte Integrations- und Kompatibilitätstests.**  
   Mit minimalen, autorisierten Testabfragen gegen unterstützte reale Konfigurationen; Mocks allein erkennen API-Drift nicht.

6. **Messung der eigenen Wirtschaftlichkeit.**  
   Aktivierung, zweiter Einsatz, Verlängerung, Supportminuten je Agentur und tatsächlich realisierte Preise.

#### P2: Spätere Skalierung

- Hosted OAuth und zentraler Google-Ads-Zugang.
- Individuelle Business-Data-Connectoren.
- Ausgebaute historische Modelle.
- Geo-Experimentplanung und statistisch validierte Auswertung.
- Automatisierte Power-Simulationen.
- Zusätzliche MCP-Tools.
- Umfangreiches Dashboard und weitere Organisationsfunktionen.
- Zusätzliche Exportformate und White-Label-Anpassungen.

**Diese Funktionen erst bauen, wenn zahlende Kunden dafür wiederholt einen konkreten Bedarf und einen passenden Preis bestätigen.** Live-Mutationen bleiben für dieses Geschäftsmodell unnötig.

**Abschließendes Urteil:** PMax Sentry kann 500 € monatlich erwirtschaften. Das beschriebene Gesamtprodukt kann aber nicht glaubwürdig schon jetzt als Vier-Stunden-Nebengeschäft kalkuliert werden. Der realistischste Weg ist ein kleines, standardisiertes Agenturwerkzeug mit vier zahlenden Kunden — nicht eine unterpreisige Inkrementalitätsplattform mit Full-Service-Erwartungen.