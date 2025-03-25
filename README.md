# PDF Processor

En web-applikasjon for å fjerne priser fra PDF-filer.

## Funksjoner

- Last opp PDF-filer via drag-and-drop eller filvelger
- Automatisk fjerning av priser fra PDF-dokumenter
- Last ned behandlede filer
- Enkel og brukervennlig nettgrensesnitt

## Installasjon

1. Klon repositoriet:
```bash
git clone https://github.com/Sebastianknorr/pdf_Processor.git
cd pdf_processor
```

2. Installer avhengigheter:
```bash
pip install -r requirements.txt
```

## Kjøring

Start applikasjonen:
```bash
python main.py
```

Applikasjonen vil være tilgjengelig på `http://localhost:5002`

## Mappestruktur

```
pdf_processor/              # Rotmappe for prosjektet
├── main.py                # Hovedapplikasjonsfil (Flask-appen)
├── pdf_processor/         # Python-pakkemappe
│   ├── processor.py      # PDF-prosesseringslogikk
│   └── __init__.py       # Pakkeinitialisering
├── static/               # Statiske filer
├── templates/            # HTML-maler
└── data/                # Data-mapper
    ├── input/           # Innkommende PDF-filer
    └── output/          # Prosesserte PDF-filer
```

## Lisens

MIT License 