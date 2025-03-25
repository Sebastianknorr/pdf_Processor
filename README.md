# PDF Pris-fjerner

Et verktøy som automatisk fjerner priser og prisrelatert informasjon fra PDF-dokumenter.

## Funksjoner
- Fjerner priser i ulike formater (f.eks. "12 345,-", "1234,56 kr")
- Fjerner kampanjeinformasjon og tilhørende priser
- Fjerner totalsummer og priskolonner
- Behandler flere PDF-filer automatisk
- Overvåker input-mappen for nye filer

## Installasjon

1. Sørg for at du har Python 3.6 eller nyere installert
2. Installer nødvendige pakker:
   ```bash
   pip install -r requirements.txt
   ```

## Bruk

1. Start programmet:
   ```bash
   python src/main.py
   ```

2. Legg PDF-filer i `input`-mappen
3. Behandlede filer vil dukke opp i `output`-mappen med prefikset "Prosessert_"
4. Trykk Ctrl+C for å avslutte programmet

## Mappestruktur
- `input/`: Legg PDF-filene som skal behandles her
- `output/`: Behandlede filer lagres her
- `src/`: Inneholder kildekoden

## Krav
- Python 3.6+
- PyMuPDF (fitz)
