# Pokémon-database — afgebakende werkdelen

## Deel 1: vastgelopen import herstellen

Status: **afgerond en online gecontroleerd op 12 november 2026**. Alle 168 importregels zijn verwerkt: 165 nieuwe baluitvoeringen en 3 eerdere Prismatic Evolutions-stempelkaarten.

- Reparatie en vaste bronbestanden: [ed92411](https://github.com/ZamexCards/TCGchecklist/commit/ed92411ae54c53251dc14e607412adf1d6877754).
- Gepubliceerde database: [049c06f](https://github.com/ZamexCards/TCGchecklist/commit/049c06f2939588713677fff0941d77a33c3b88d8).
- [Databaseverwerking en publicatie geslaagd](https://github.com/ZamexCards/TCGchecklist/actions/runs/43299158019).
- 17 tests geslaagd; 217 sets, 23.923 kaarten en 37.977 uitvoeringen gevalideerd. Online zijn alle 168 importregels in de setbestanden én de volledige downloadexport gecontroleerd. Voorbeeldafbeeldingen zijn gedownload en op hun bestandshash gecontroleerd.
- Actueel resterend: 3.891 speciale variantafbeeldingen, 535 illustratorvelden, 101 kaartteksten en 1 setaantalverschil. De 8.425 gewone reverse-holo-presentaties gebruiken de basiskaart met glanseffect en staan buiten de zoeklijsten.

| Set | Poké Ball | Master Ball | Andere uitvoeringen |
| --- | ---: | ---: | ---: |
| Black Bolt | 12 | 4 | 0 |
| White Flare | 79 | 70 | 0 |
| Prismatic Evolutions | 0 | 0 | 3 eerder gevonden stempelkaarten |

De exacte bronbestanden zijn vastgezet in `assets/reviewed-sources/`. De import gebruikt deze bestanden en controleert hun SHA-256. De oorspronkelijke bronpagina, oude en actuele bronhash en visuele controlepunten blijven bewaard in `data/imports/reviewed-variant-images.json`.

## Volgende delen: maximaal 25 kaartuitvoeringen per chat

De actuele, exacte werklijsten staan in [`data/research/batches.json`](../data/research/batches.json). De lijst wordt na de databaseverwerking opnieuw gegenereerd, met maximaal 25 uitvoeringen van één set per deel. Voorrang: Black Bolt, White Flare, Prismatic Evolutions; daarna de overige sets in de bestaande setvolgorde.

Eén deel omvat zoeken, taal/kaartnummer/uitvoering controleren, gevonden beelden opslaan, database en exports bijwerken, valideren en publiceren. Wat na een begrensde zoekronde niet beschikbaar is, krijgt een expliciet resultaat met de geraadpleegde bronnen. Een afgeronde zoekronde betekent niet dat ontbrekende gegevens ineens compleet zijn.

Iedere chat eindigt met de uitgevoerde batch-ID, aantallen toegevoegd/niet gevonden, een GitHub-commit, publicatiestatus en de volgende batch-ID. Sla dat resultaat in dit bestand op vóór een volgende zoekronde.

Gewone reverse holo’s blijven buiten de zoeklijsten: de basisafbeelding krijgt een duidelijk gesimuleerd glanseffect. Andere ontbrekende gegevens, zoals illustratoren en kaartteksten, worden later per type in eigen groepen van maximaal 25 behandeld.

## Hervatten in een nieuwe chat

Lees eerst dit bestand, controleer de laatste geslaagde GitHub Actions-publicatie en lees de eerste nog onbehandelde batch uit `data/research/batches.json`. Herhaal geen al gepubliceerde imports. Voer één batch uit en werk dit voortgangsbestand bij.

## Geplande eerstvolgende chats

| Deel | Batch-ID | Inhoud | Aantal uitvoeringen |
| --- | --- | --- | ---: |
| 2 | sv10.5b-001 | Black Bolt, eerste groep | 25 |
| 3 | sv10.5b-002 | Black Bolt, tweede groep | 25 |
| 4 | sv10.5b-003 | Black Bolt, derde groep | 17 |
| 5 | sv10.5w-001 | White Flare, resterende groep | 2 |
| 6 | sv08.5-001 | Prismatic Evolutions, resterende groep | 18 |

Daarna volgen de overige sets met maximaal 25 uitvoeringen per groep. Bovenstaande indeling is de momentopname na deel 1. Controleer bij het hervatten altijd de opgeslagen kaart-ID’s en variantkeys; na toevoegingen kan de gegenereerde volgorde veranderen.

### Exact startpunt voor deel 2

De volgende 25 kaartuitvoeringen vormen deel 2. Zoek uitsluitend bijpassende Engelse afbeeldingen; leg per regel een gevonden beeld of het resultaat van de begrensde zoekronde vast.

| Kaart-ID | Naam | Uitvoering | Variantkey |
| --- | --- | --- | --- |
| sv10.5b-002 | Servine | Poké Ball | 3739bbtj3i910y5ynn9xc6ryf |
| sv10.5b-005 | Simisage | Poké Ball | 3739bbtj3i910y5ynn9xc6ryf |
| sv10.5b-007 | Lilligant | Poké Ball | 3739bbtj3i910y5ynn9xc6ryf |
| sv10.5b-009 | Karrablast | Master Ball | 2asus05yghmpd1ud1sdmlq3as4e |
| sv10.5b-010 | Foongus | Master Ball | 2asus05yghmpd1ud1sdmlq3as4e |
| sv10.5b-010 | Foongus | Poké Ball | 3739bbtj3i910y5ynn9xc6ryf |
| sv10.5b-012 | Victini | Master Ball | 2asus05yghmpd1ud1sdmlq3as4e |
| sv10.5b-014 | Darmanitan | Master Ball | 2asus05yghmpd1ud1sdmlq3as4e |
| sv10.5b-016 | Volcarona | Master Ball | 2asus05yghmpd1ud1sdmlq3as4e |
| sv10.5b-016 | Volcarona | Poké Ball | 3739bbtj3i910y5ynn9xc6ryf |
| sv10.5b-017 | Panpour | Master Ball | 2asus05yghmpd1ud1sdmlq3as4e |
| sv10.5b-017 | Panpour | Poké Ball | 3739bbtj3i910y5ynn9xc6ryf |
| sv10.5b-018 | Simipour | Master Ball | 2asus05yghmpd1ud1sdmlq3as4e |
| sv10.5b-019 | Tympole | Master Ball | 2asus05yghmpd1ud1sdmlq3as4e |
| sv10.5b-020 | Palpitoad | Master Ball | 2asus05yghmpd1ud1sdmlq3as4e |
| sv10.5b-020 | Palpitoad | Poké Ball | 3739bbtj3i910y5ynn9xc6ryf |
| sv10.5b-021 | Seismitoad | Master Ball | 2asus05yghmpd1ud1sdmlq3as4e |
| sv10.5b-022 | Tirtouga | Poké Ball | 3739bbtj3i910y5ynn9xc6ryf |
| sv10.5b-023 | Carracosta | Master Ball | 2asus05yghmpd1ud1sdmlq3as4e |
| sv10.5b-025 | Cubchoo | Poké Ball | 3739bbtj3i910y5ynn9xc6ryf |
| sv10.5b-026 | Beartic | Master Ball | 2asus05yghmpd1ud1sdmlq3as4e |
| sv10.5b-027 | Cryogonal | Master Ball | 2asus05yghmpd1ud1sdmlq3as4e |
| sv10.5b-028 | Kyurem ex | Holo · Jumbo | slwlv6rn87 |
| sv10.5b-029 | Emolga | Master Ball | 2asus05yghmpd1ud1sdmlq3as4e |
| sv10.5b-030 | Tynamo | Poké Ball | 3739bbtj3i910y5ynn9xc6ryf |
