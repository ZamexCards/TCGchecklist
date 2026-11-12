# Pokémon-database — afgebakende werkdelen

## Deel 1: vastgelopen import herstellen

Status: **afgerond en online gecontroleerd op 12 november 2026**. Alle 168 importregels zijn verwerkt: 165 nieuwe baluitvoeringen en 3 eerdere Prismatic Evolutions-stempelkaarten.

- Reparatie en vaste bronbestanden: [ed92411](https://github.com/ZamexCards/TCGchecklist/commit/ed92411ae54c53251dc14e607412adf1d6877754).
- Gepubliceerde database: [049c06f](https://github.com/ZamexCards/TCGchecklist/commit/049c06f2939588713677fff0941d77a33c3b88d8).
- [Databaseverwerking en publicatie geslaagd](https://github.com/ZamexCards/TCGchecklist/actions/runs/43299158019).
- 17 tests geslaagd; 217 sets, 23.923 kaarten en 37.977 uitvoeringen gevalideerd. Online zijn alle 168 importregels in de setbestanden én de volledige downloadexport gecontroleerd. Voorbeeldafbeeldingen zijn gedownload en op hun bestandshash gecontroleerd.
- Stand na deel 1: 3.891 speciale variantafbeeldingen, 535 illustratorvelden, 101 kaartteksten en 1 setaantalverschil. De 8.425 gewone reverse-holo-presentaties gebruiken de basiskaart met glanseffect en staan buiten de zoeklijsten.

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

## Deel 2: eerste 25 resterende Black Bolt-uitvoeringen

Status: **afgerond en online gecontroleerd op 12 november 2026**. Alle 25 afbeeldingen zijn geïmporteerd en gepubliceerd. De 25 variantkoppelingen zijn online gecontroleerd in het Black Bolt-setbestand en de volledige downloadexport. Voorbeelden van Poké Ball, Master Ball en Jumbo zijn gedownload en op de opgeslagen bestandshash gecontroleerd.

- 10 Poké Ball, 14 Master Ball en 1 Kyurem ex Jumbo (028/086).
- 25 van 25 gevonden; 0 niet gevonden. De exacte afgewerkte lijst met bronnen en bestandshashes staat in [`data/research/completed/part-002-black-bolt.json`](../data/research/completed/part-002-black-bolt.json).
- Bronfoto’s van Magic Madhouse (24) en Pittsburg TCG and Collectibles (1). Bij de Jumbo-uitvoering komt het formaattype uit de bijbehorende productbeschrijving; het kaartnummer en de Engelse tekst zijn op de foto gecontroleerd.
- 17 tests geslaagd; 217 sets, 23.923 kaartrecords en 37.977 uitvoeringen gevalideerd. Na import: 25.686 uitvoeringen met een eigen afbeelding, 8.425 gewone reverse-presentaties met glanslaag, 3.866 nog te onderzoeken speciale variantafbeeldingen.
- Kleine beoordeelde imports verwerken voortaan alleen de vastgezette bronbestanden en de bestaande database. De volledige externe bronverversing blijft voor de geplande volledige updates beschikbaar.

- Toevoeging en import: [25d1cd7](https://github.com/ZamexCards/TCGchecklist/commit/25d1cd7f8eb0ba1f2430dd9dff6f2c0a879fe505).
- Gepubliceerde database: [a0a33b9](https://github.com/ZamexCards/TCGchecklist/commit/a0a33b9a00ca29dc602e80eae95a116479c471f0).
- [Databaseverwerking en publicatie deel 2 geslaagd](https://github.com/ZamexCards/TCGchecklist/actions/runs/43307775489).

## Hoeveel delen?

Met de huidige grens van maximaal 25 items per groep zijn **252 delen gepland**: 224 delen voor speciale afbeeldingen (4 zoekdelen uitgevoerd en 220 resterend) en 28 delen voor ontbrekende kaartgegevens (22 illustratorgroepen, 5 kaarttekstgroepen en 1 setaantalverschil). Een zoekdeel kan ook eindigen met expliciet vastgelegde onbeschikbare bronnen; dat telt niet als volledig aangevulde kaartdata. Nieuwe broninformatie kan de planning veranderen.

## Deel 3 en 4: resterende Black Bolt-uitvoeringen

Status: **beide zoekronden zijn afgewerkt en de 38 geverifieerde afbeeldingen zijn online gepubliceerd en gecontroleerd op 12 november 2026**. Deel 3 heeft 25 van 25 beelden; deel 4 heeft 13 van 17 beelden. Vier handtekeninguitvoeringen uit deel 4 blijven als ontbrekend geregistreerd. De online setgegevens, zoekrapporten en volledige export zijn gecontroleerd; alle 231 eerder en nieuw beoordeelde variantkoppelingen zijn in de online export teruggevonden. Voorbeelden van Master Ball, Poké Ball en Ultra Ball League zijn gedownload en op hun bestandshash gecontroleerd.

| Deel | Gecontroleerd | Beelden gevonden | Nog zonder geverifieerd beeld |
| --- | ---: | ---: | ---: |
| 3 | 25 | 25 | 0 |
| 4 | 17 | 13 | 4 |

Deel 3 bevat 23 Master Ball-foto’s, 1 Poké Ball-foto en Zekrom ex 034/086 met zichtbaar Ultra Ball League-logo. Deel 4 voegt 13 Master Ball-foto’s toe. Alle foto’s zijn gecontroleerd op Engelse taal, kaartnummer en het balpatroon of de bijzondere stempel. Het product van Eelektross heeft een spelfout in de winkeltitel; de daadwerkelijke kaartfoto is gecontroleerd op Eelektross en BLK EN 032/086.

De exacte resultaten en geraadpleegde bronadressen staan in [deel 3](../data/research/completed/part-003-black-bolt.json) en [deel 4](../data/research/completed/part-004-black-bolt.json).

- Toevoegingen en beide zoekrapporten: [6c5aea0](https://github.com/ZamexCards/TCGchecklist/commit/6c5aea02982731f499d7d262d1d3846b43cf0c57).
- Gepubliceerde database: [8e1ca5b](https://github.com/ZamexCards/TCGchecklist/commit/8e1ca5b407cde92b4a069de963a11230cbd05173).
- [Databaseverwerking en publicatie deel 3 en 4 geslaagd](https://github.com/ZamexCards/TCGchecklist/actions/runs/43312538859).

### Open na de zoekronde van deel 4

| Kaart | Nummer | Uitvoering |
| --- | --- | --- |
| Genesect ex | 067/086 | Liao Fu Guan |
| Air Balloon | 079/086 | Liao Fu Guan |
| Air Balloon | 079/086 | José Cruz Galindo-Resendiz |
| Pokégear 3.0 | 084/086 | Liao Fu Guan |

De productpagina’s van Cape Fear Collectibles tonen het winkellogo als afbeelding, zonder controleerbare kaartscan. De alternatieve product- en beeldbronnen retourneerden 403 of 404. Deze vier items blijven in de kwaliteitsrapportage als ontbrekend staan. De afgesloten zoekronde wordt apart getoond onder `reviewedUnavailable` in de werklijst, zodat dezelfde items niet automatisch de volgende zoekronde vullen. Opnieuw onderzoeken kan op verzoek of met nieuwe broninformatie; pas dan de betreffende `retryPolicy` aan of voeg een geverifieerde import toe.

19 tests zijn geslaagd. De databasevalidatie controleerde 217 sets, 23.923 kaarten, 37.977 uitvoeringen en 25.943 gearchiveerde beeldbestanden. De volledige export bevat de 38 nieuwe variantkoppelingen. De gewone reverse holo’s blijven buiten het zoekwerk.

### Actuele telling na deel 3 en 4

- 4 zoekdelen uitgevoerd; 248 nieuwe werkdelen resterend: 220 voor afbeeldingen en 28 voor kaartgegevens.
- 3.828 speciale afbeeldingen nog ontbrekend, waarvan 3.824 nog te onderzoeken en 4 vastgelegd als niet gevonden in deze begrensde ronde.
- Een afgewerkt zoekdeel is geen bewering dat alle ontbrekende kaarten zijn aangevuld.

## Eerstvolgende chats na deel 4

| Deel | Actuele batch-ID | Inhoud | Aantal uitvoeringen |
| --- | --- | --- | ---: |
| 5 | sv10.5w-001 | White Flare | 2 |
| 6 | sv08.5-001 | Prismatic Evolutions | 18 |
| 7 | me06-001 | Delta Reign | 25 |
| 8 | me06-002 | Delta Reign | 25 |

### Exact startpunt voor deel 5

| Kaart-ID | Naam | Uitvoering | Variantkey |
| --- | --- | --- | --- |
| sv10.5w-011 | Tepig | Holo · Tinsel | 6z2xz7qsvmqlfamgn6z2 |
| sv10.5w-021 | Oshawott | Holo · Tinsel | 6z2xz7qsvmqlfamgn6z2 |
