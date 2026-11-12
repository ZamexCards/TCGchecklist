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

Met de huidige grens van maximaal 25 items per groep zijn **252 delen gepland**: 224 delen voor speciale afbeeldingen (2 uitgevoerd en 222 resterend) en 28 delen voor ontbrekende kaartgegevens (22 illustratorgroepen, 5 kaarttekstgroepen en 1 setaantalverschil). Een zoekdeel kan ook eindigen met expliciet vastgelegde onbeschikbare bronnen; dat telt niet als volledig aangevulde kaartdata. Nieuwe broninformatie kan de planning veranderen.

## Eerstvolgende chats na deel 2

De gegenereerde batchnummers beginnen opnieuw bij de resterende kaartuitvoeringen. Gebruik de exacte kaart-ID’s en variantkeys hieronder als startpunt; een nummer alleen is geen bewijs dat het om dezelfde eerdere groep gaat.

| Deel | Actuele batch-ID | Inhoud | Aantal uitvoeringen |
| --- | --- | --- | ---: |
| 3 | sv10.5b-001 | Black Bolt | 25 |
| 4 | sv10.5b-002 | Black Bolt | 17 |
| 5 | sv10.5w-001 | White Flare | 2 |
| 6 | sv08.5-001 | Prismatic Evolutions | 18 |
| 7 | me06-001 | Delta Reign | 25 |

### Exact startpunt voor deel 3

De volgende 25 nog niet afgewerkte uitvoeringen vormen deel 3. Zoek uitsluitend bijpassende Engelse afbeeldingen, controleer kaartnummer en fysieke uitvoering, importeer alleen passende beelden en leg per regel het resultaat vast.

| Kaart-ID | Naam | Uitvoering | Variantkey |
| --- | --- | --- | --- |
| sv10.5b-031 | Eelektrik | Master Ball | 2asus05yghmpd1ud1sdmlq3as4e |
| sv10.5b-031 | Eelektrik | Poké Ball | 3739bbtj3i910y5ynn9xc6ryf |
| sv10.5b-032 | Eelektross | Master Ball | 2asus05yghmpd1ud1sdmlq3as4e |
| sv10.5b-033 | Thundurus | Master Ball | 2asus05yghmpd1ud1sdmlq3as4e |
| sv10.5b-034 | Zekrom ex | Holo · ultra-ball-league | 1c79txmtnonthck609704l3ls0zo4i1 |
| sv10.5b-035 | Munna | Master Ball | 2asus05yghmpd1ud1sdmlq3as4e |
| sv10.5b-036 | Musharna | Master Ball | 2asus05yghmpd1ud1sdmlq3as4e |
| sv10.5b-037 | Solosis | Master Ball | 2asus05yghmpd1ud1sdmlq3as4e |
| sv10.5b-038 | Duosion | Master Ball | 2asus05yghmpd1ud1sdmlq3as4e |
| sv10.5b-039 | Reuniclus | Master Ball | 2asus05yghmpd1ud1sdmlq3as4e |
| sv10.5b-041 | Beheeyem | Master Ball | 2asus05yghmpd1ud1sdmlq3as4e |
| sv10.5b-042 | Golett | Master Ball | 2asus05yghmpd1ud1sdmlq3as4e |
| sv10.5b-043 | Golurk | Master Ball | 2asus05yghmpd1ud1sdmlq3as4e |
| sv10.5b-045 | Drilbur | Master Ball | 2asus05yghmpd1ud1sdmlq3as4e |
| sv10.5b-048 | Gurdurr | Master Ball | 2asus05yghmpd1ud1sdmlq3as4e |
| sv10.5b-049 | Conkeldurr | Master Ball | 2asus05yghmpd1ud1sdmlq3as4e |
| sv10.5b-050 | Throh | Master Ball | 2asus05yghmpd1ud1sdmlq3as4e |
| sv10.5b-051 | Dwebble | Master Ball | 2asus05yghmpd1ud1sdmlq3as4e |
| sv10.5b-052 | Crustle | Master Ball | 2asus05yghmpd1ud1sdmlq3as4e |
| sv10.5b-053 | Landorus | Master Ball | 2asus05yghmpd1ud1sdmlq3as4e |
| sv10.5b-054 | Venipede | Master Ball | 2asus05yghmpd1ud1sdmlq3as4e |
| sv10.5b-056 | Scolipede | Master Ball | 2asus05yghmpd1ud1sdmlq3as4e |
| sv10.5b-058 | Krokorok | Master Ball | 2asus05yghmpd1ud1sdmlq3as4e |
| sv10.5b-059 | Krookodile | Master Ball | 2asus05yghmpd1ud1sdmlq3as4e |
| sv10.5b-060 | Escavalier | Master Ball | 2asus05yghmpd1ud1sdmlq3as4e |
