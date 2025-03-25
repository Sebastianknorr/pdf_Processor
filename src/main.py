#!/usr/bin/env python3
"""
PDF Price Remover
----------------
Dette programmet fjerner priser og prisrelatert informasjon fra PDF-filer.
Legg PDF-filer i input-mappen, og de behandlede filene vil dukke opp i output-mappen.
"""

import fitz  # PyMuPDF
import re
import os
from pathlib import Path
import time
import logging

# Sett opp logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class PDFProcessor:
    # Prismønstre som skal fjernes
    PRICE_PATTERNS = [
        r'\d{1,3}(?: \d{3})*,-',     # F.eks. "12 345,-"
        r'\d+[.,]\d{2}',             # F.eks. "1234,50"
        r'\d+[.,]\d{2}\s*(?:kr|NOK|kroner)',  # F.eks. "1234,50 kr"
        r'\d+\s*(?:kr|NOK|kroner)',  # F.eks. "1234 kr"
        r'\d+%'                      # Prosenter
    ]
    
    # Ord som indikerer prisrelatert informasjon
    PRICE_RELATED_WORDS = [
        'pris', 'total', 'sum', 'beløp', 'kostnad',
        'rabatt', 'kampanje', 'tilbud', 'kr', 'kroner',
        'NOK', '%', 'prosent'
    ]

    def __init__(self):
        self.script_dir = Path(__file__).parent.parent
        self.input_dir = self.script_dir / 'input'
        self.output_dir = self.script_dir / 'output'
        
        # Opprett mapper hvis de ikke eksisterer
        self.input_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)

    def remove_prices_from_pdf(self, input_path: Path, output_path: Path) -> None:
        """Fjerner priser fra en PDF-fil."""
        try:
            doc = fitz.open(str(input_path))
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                blocks = page.get_text("dict")["blocks"]
                
                for block in blocks:
                    if "lines" not in block:
                        continue
                        
                    for line in block["lines"]:
                        line_text = " ".join(span["text"] for span in line["spans"])
                        
                        # Sjekk om linjen inneholder prisrelatert informasjon
                        should_remove = any(
                            word.lower() in line_text.lower() 
                            for word in self.PRICE_RELATED_WORDS
                        )
                        
                        # Sjekk om linjen inneholder prismønstre
                        if not should_remove:
                            should_remove = any(
                                re.search(pattern, line_text, re.IGNORECASE) 
                                for pattern in self.PRICE_PATTERNS
                            )
                        
                        if should_remove:
                            # Fjern hele linjen ved å tegne en hvit boks over
                            for span in line["spans"]:
                                bbox = span["bbox"]
                                page.draw_rect(bbox, color=(1, 1, 1), fill=(1, 1, 1))
            
            doc.save(str(output_path))
            doc.close()
            logging.info(f"✓ Vellykket behandling av: {input_path.name}")
            
        except Exception as e:
            logging.error(f"Feil ved behandling av {input_path.name}: {str(e)}")
            raise

    def process_files(self) -> None:
        """Hovedfunksjon som overvåker input-mappen og behandler nye filer."""
        logging.info("PDF Processor er startet!")
        logging.info(f"Legg PDF-filer i mappen: {self.input_dir.absolute()}")
        logging.info(f"Behandlede filer vil bli lagret i: {self.output_dir.absolute()}")
        logging.info("Trykk Ctrl+C for å avslutte programmet")
        
        processed_files = set()
        
        while True:
            try:
                # Finn alle PDF-filer i input-mappen
                pdf_files = list(self.input_dir.glob("*.pdf"))
                
                for pdf_file in pdf_files:
                    if pdf_file.name not in processed_files:
                        output_file = self.output_dir / f"Prosessert_{pdf_file.name}"
                        self.remove_prices_from_pdf(pdf_file, output_file)
                        processed_files.add(pdf_file.name)
                
                time.sleep(1)  # Vent litt før neste sjekk
                
            except KeyboardInterrupt:
                logging.info("\nAvslutter programmet...")
                break
            except Exception as e:
                logging.error(f"En uventet feil oppstod: {str(e)}")
                time.sleep(5)  # Vent litt før neste forsøk

def main():
    processor = PDFProcessor()
    processor.process_files()

if __name__ == "__main__":
    main() 