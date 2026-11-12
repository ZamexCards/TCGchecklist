# Herbruikbare Engelse Pokémon-database

De centrale bestanden zijn beschikbaar vanaf:

`https://zamexcards.github.io/TCGchecklist/`

## Bestanden

| Bestand | Inhoud |
| --- | --- |
| `data/catalogue.json` | Schemaversie, gegevensdekking en alle endpoints |
| `data/sets.json` | Sets, series, taal, releasedatum, officiële aantallen, logo’s |
| `data/series.json` | Series met de bijbehorende set-ID’s |
| `data/sets/{setId}.json` | Volledige opgeslagen kaartobjecten per set |
| `data/cards-index.json` | Zoekindex met stabiele kaart-ID’s en verwijzingen naar de setbestanden |
| `data/exports/pokemon-en.json.gz` | Alle sets en kaartgegevens als gecomprimeerde JSON-download |
| `data/image-assets.json` | Lokaal opgeslagen afbeeldingen met absolute URL, SHA-256, afmetingen en bestandsgrootte |
| `data/catalogue-quality.json` | Werkelijk behaalde gegevens- en afbeeldingsdekking per set |
| `data/research/open.json` | Alle resterende concrete bronvragen |
| `data/research/sets/{setId}.json` | Bronvragen per set, kaart en uitvoering |

## Kaartobject

De bestaande velden (`id`, `name`, `number`, `supertype`, `subtypes`, `types`, `rarity`, `images`, `availableVariants`) blijven beschikbaar. Onder andere de volgende bronvelden worden nu ook bewaard als ze bestaan: `category`, `illustrator`, `hp`, `dexId`, `evolveFrom`, `evolveTo`, `stage`, `abilities`, `attacks`, `effect`, `description`, `weaknesses`, `resistances`, `retreat`, `regulationMark`, `legal`, `boosters`, `thirdParty`, `pricing`.

`language` is `en`. `setId` is het stabiele centrale set-ID. `set.game` onderscheidt fysieke TCG-kaarten van digitale Pokémon TCG Pocket-kaarten. Een niet toepasselijk veld, zoals een regulatiemarkering op een oude kaart, wordt niet gevuld met "onbekend".

`printings` bevat de afzonderlijke uitvoeringen: `key`, `variantId` indien de bron die levert, `label`, `type`, `foil`, `subtype`, `stamp`, `size`, `images`, `pricing`, `thirdParty`, `source`, `verification`, `imageStatus`. De bron bepaalt welke uitvoeringen bestaan. Bestaande gecontroleerde lokale uitvoeringen en afbeeldingstoewijzingen blijven behouden.

`provenance.primary` bevat bron-URL, ophaaldatum, brondatum en de gecontroleerde identiteitsvelden. Een eventuele tweede bron staat in `provenance.secondary`, met precies de velden die ermee zijn aangevuld. `supplemental.pokemonTcg` bewaart aanvullende historische bronvelden apart. Oude spellegaliteit uit die bron is geen garantie voor de huidige wedstrijdlegaliteit.

`dataQuality` vermeldt per kaart of details en een basisafbeelding zijn opgeslagen en hoeveel uitvoeringen, uitvoeringafbeeldingen en open controlepunten er zijn. Het algemene rapport is pas `complete: true` als er geen open punten meer zijn. Volledige dekking wordt dus niet afgeleid uit het aantal setnamen.

## Afbeeldingen gebruiken

Een `./assets/...`-pad is relatief aan de database-root, niet aan je eigen app. Maak het als volgt absoluut:

```js
const BASE = 'https://zamexcards.github.io/TCGchecklist/';
const set = await fetch(new URL('data/sets/sv08.5.json', BASE)).then(r => r.json());
const card = set.cards.find(c => c.number === '007');
const image = new URL(card.images.small, BASE).href;
const variants = card.printings.map(p => ({
  ...p,
  imageUrl: p.images?.small ? new URL(p.images.small, BASE).href : null
}));
```

Een lege variantafbeelding betekent dat voor die specifieke uitvoering nog geen afzonderlijke scan is bevestigd. Toon dan expliciet een referentieafbeelding. Een reverse-glanslaag is een presentatie-effect en wordt nooit als een echte scan opgeslagen. Afbeeldingen van Poké Ball/Master Ball worden alleen gekoppeld als de bron een bijbehorend specifiek product-ID levert. Afzonderlijke edities, stempels en Jumbo-formaten krijgen niet automatisch dezelfde marketplace-afbeelding.

`images.sourceLarge` is een externe bronverwijzing; dit is geen toezegging dat de hoge-resolutieversie lokaal is opgeslagen. Voor de lokaal opgeslagen bestanden zijn de werkelijke afmetingen en controlesommen beschikbaar in `data/image-assets.json`. Er worden geen vermeende hogere-resolutieafbeeldingen gegenereerd of uitvergroot.

## Actualiseren

De workflow **Archive full English Pokemon catalogue** vult de hele bestaande database aan en publiceert de bestanden. De bestaande maandagupdate voert dezelfde verrijking uit na het bijwerken van sets. Identiteitscontrole gebruikt kaart-ID, set-ID, kaartnummer én kaartnaam. Een historische tweede dataset wordt alleen gebruikt bij één unieke setmatch op naam en officieel kaartaantal en daarna op kaartnaam en nummer. Bestaande kaartrecords worden niet verwijderd wanneer een bron tijdelijk minder kaarten teruggeeft.

Marktprijzen blijven gedateerde bronmomentopnamen en worden niet als actuele ZamexCards-verkoopprijzen, Near Mint-prijzen of landgebonden prijzen gepresenteerd. De gegevens zijn voor hergebruik beschikbaar; rechten op Pokémon-illustraties blijven bij de rechthebbenden.
