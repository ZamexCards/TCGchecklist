ZamexCards Pokémon TCG Checklist – centrale database

1. Upload ALLE bestanden en mappen uit deze ZIP naar de ROOT van je GitHub Pages repository.
   Inclusief de verborgen map .github/workflows en de map scripts.
2. GitHub repository > Settings > Actions > General > Workflow permissions:
   kies Read and write permissions. Sla op.
3. Ga naar Actions > Update Pokemon checklist data > Run workflow.
   De eerste run verzamelt alle set- en kaartgegevens. Dit kan aanzienlijk langer duren.
   Wacht tot de workflow klaar is en de data/sets.json is bijgewerkt.
4. Zet GitHub Pages op Deploy from a branch, main / (root).
5. Gebruik de iframe-code uit JouwWeb-embedcode.txt en vervang de voorbeeld-URL.
6. Daarna controleert de workflow dagelijks nieuwe sets. Oude JSON blijft beschikbaar
   als de externe API tijdelijk uitvalt.

Let op: De centrale data is tijdens het maken van deze ZIP niet online gevuld omdat
de uitvoeromgeving de API niet kon bereiken. De eerste GitHub Action-run is dus
noodzakelijk. Tot die tijd gebruikt de pagina de ingebouwde API-reservebron.
Kaartafbeeldingen blijven externe CDN-links. Bij een ontbrekende afbeelding wordt
een lokale nette placeholder getoond. Ball-varianten worden alleen toegevoegd
wanneer de bron dit expliciet meldt; ongedocumenteerde varianten worden niet verzonnen.
