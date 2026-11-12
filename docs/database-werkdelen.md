# Pokémon-database — afgebakende werkdelen

## Deel 1: vastgelopen import herstellen

Status: alle 168 importregels lokaal verwerkt en de database gevalideerd; publicatie wordt in deze chat gecontroleerd.

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
