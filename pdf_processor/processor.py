import os
import fitz  # PyMuPDF
import logging

logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self, input_dir='input', output_dir='output'):
        self.input_dir = input_dir
        self.output_dir = output_dir
        
    def process_files(self):
        """Process all PDF files in the input directory."""
        logger.info("PDF Processor er startet!")
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Process each PDF file in the input directory
        for filename in os.listdir(self.input_dir):
            if filename.endswith('.pdf'):
                input_path = os.path.join(self.input_dir, filename)
                output_path = os.path.join(self.output_dir, f'Prosessert_{filename}')
                self.process_single_file(input_path, output_path)
                
    def process_single_file(self, input_path, output_path):
        """Process a single PDF file to remove prices."""
        try:
            # Open the PDF
            pdf_document = fitz.open(input_path)
            
            # Process each page
            for page in pdf_document:
                # Get all text instances
                text_instances = page.get_text("words")
                
                # Find and remove price-like text
                for inst in text_instances:
                    text = inst[4]
                    if self._is_price(text):
                        # Create a white rectangle to cover the price
                        rect = fitz.Rect(inst[0], inst[1], inst[2], inst[3])
                        page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
            
            # Save the processed PDF
            pdf_document.save(output_path)
            pdf_document.close()
            
            logger.info(f"Prosessert fil: {os.path.basename(input_path)}")
            
        except Exception as e:
            logger.error(f"Error processing file {input_path}: {str(e)}")
            raise
            
    def _is_price(self, text):
        """Check if the text looks like a price."""
        # Remove spaces and common separators
        text = text.replace(" ", "").replace(",", "").replace(".", "")
        
        # Check if it's a number and has a reasonable length for a price
        return text.isdigit() and 2 <= len(text) <= 8 