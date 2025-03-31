import os
import fitz  # PyMuPDF
import logging
import atexit
import shutil

logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self, input_dir='input', output_dir='output'):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.processed_files = set()  # Track processed files
        
        # Clean up any existing files on initialization
        self.cleanup()
        
        # Register cleanup function
        atexit.register(self.cleanup)
        
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
        """Process a single PDF file to remove prices, totals, kampanje sections, and MVA summary."""
        try:
            # Open the PDF
            pdf_document = fitz.open(input_path)
            
            # Process each page
            for page in pdf_document:
                # Get all text instances
                text_instances = page.get_text("words")
                
                # Find column positions and kampanje sections
                columns = self._find_columns(text_instances)
                kampanje_sections = self._find_kampanje_sections(text_instances)
                mva_sections = self._find_mva_sections(text_instances)
                
                if not columns and not kampanje_sections and not mva_sections:
                    logger.warning("No columns, kampanje sections, or MVA sections found on page")
                    continue
                
                # Group text by rows (using y-coordinates)
                rows = {}
                for inst in text_instances:
                    y_coord = round(inst[1], 1)  # Round to 1 decimal to group nearby y-coordinates
                    if y_coord not in rows:
                        rows[y_coord] = []
                    rows[y_coord].append(inst)
                
                # Process each row
                for y_coord in sorted(rows.keys()):
                    row_content = rows[y_coord]
                    # Sort content by x-coordinate
                    row_content.sort(key=lambda x: x[0])
                    
                    # Process each text instance in the row
                    for inst in row_content:
                        x_coord = inst[0]
                        text = inst[4]
                        
                        should_remove = False
                        
                        # Check if this text is in Pris or Total columns and is a number
                        if self._is_in_column(x_coord, columns['pris']) or self._is_in_column(x_coord, columns['total']):
                            if self._is_number(text):
                                should_remove = True
                        
                        # Check if this text is part of a kampanje section
                        for section in kampanje_sections:
                            if self._is_in_kampanje_section(inst, section):
                                should_remove = True
                                break
                                
                        # Check if this text is part of an MVA section
                        for section in mva_sections:
                            if self._is_in_mva_section(inst, section):
                                should_remove = True
                                break
                        
                        if should_remove:
                            # Create a redaction annotation
                            rect = fitz.Rect(inst[0], inst[1], inst[2], inst[3])
                            annot = page.add_redact_annot(rect)
                            # Apply the redaction
                            page.apply_redactions()
            
            # Save the processed PDF
            pdf_document.save(output_path)
            pdf_document.close()
            
            # Track the processed file
            self.processed_files.add(output_path)
            
            logger.info(f"Prosessert fil: {os.path.basename(input_path)}")
            
        except Exception as e:
            logger.error(f"Error processing file {input_path}: {str(e)}")
            raise

    def _find_kampanje_sections(self, text_instances):
        """Find all kampanje sections in the document."""
        kampanje_sections = []
        
        for inst in text_instances:
            text = inst[4].strip().lower()
            if text == "kampanje":
                # When we find a kampanje header, create a section that includes
                # the header and extends to the right of the page
                section = {
                    'x0': 0,  # Start from left edge
                    'y0': inst[1] - 5,  # Slightly above the header
                    'x1': inst[2] + 500,  # Extend well past the header
                    'y1': inst[3] + 30,  # Extend below to catch any related content
                }
                kampanje_sections.append(section)
                logger.info(f"Found Kampanje section at y={inst[1]}")
        
        return kampanje_sections
    
    def _is_in_kampanje_section(self, inst, section):
        """Check if a text instance falls within a kampanje section."""
        return (section['x0'] <= inst[0] and inst[2] <= section['x1'] and
                section['y0'] <= inst[1] and inst[3] <= section['y1'])

    def _find_columns(self, text_instances):
        """Find the x-coordinates of each column."""
        columns = {'pris': None, 'total': None}
        header_y = None
        
        # First find headers and their y-position
        for inst in text_instances:
            text = inst[4].strip().lower()
            if text == "pris" or text == "total":
                header_y = inst[1]
                if text == "pris":
                    columns['pris'] = inst[0]
                    logger.info(f"Found Pris column at x={inst[0]}")
                else:
                    columns['total'] = inst[0]
                    logger.info(f"Found Total column at x={inst[0]}")
        
        # If we found headers, adjust column positions based on content alignment
        if header_y is not None:
            # Look at content just below headers to fine-tune column positions
            for inst in text_instances:
                if inst[1] > header_y and inst[1] < header_y + 50:  # Look within 50 points below headers
                    text = inst[4].strip()
                    if self._is_number(text):
                        # Check which column this number belongs to
                        if columns['pris'] and abs(inst[0] - columns['pris']) < 30:
                            columns['pris'] = inst[0]  # Update to align with actual content
                        elif columns['total'] and abs(inst[0] - columns['total']) < 30:
                            columns['total'] = inst[0]  # Update to align with actual content
        
        return columns
    
    def _is_in_column(self, x_coord, column_x):
        """Check if an x-coordinate falls within a column's range."""
        if column_x is None:
            return False
        return abs(x_coord - column_x) < 30  # Increased tolerance slightly
            
    def _is_number(self, text):
        """Check if the text represents a number (with or without thousand separator and currency suffix)."""
        # Remove any trailing spaces
        text = text.strip()
        
        # Remove currency suffix if present
        text = text.rstrip(",-").rstrip("-")
        
        # Remove all spaces (thousand separators)
        text = text.replace(" ", "")
        
        # Check if what remains is a number
        return text.isdigit()

    def _is_price(self, text):
        """Deprecated: Use _is_number instead."""
        return self._is_number(text)

    def _find_mva_sections(self, text_instances):
        """Find all MVA summary sections in the document."""
        mva_sections = []
        
        # Group text instances by their y-coordinate (same line)
        rows = {}
        for inst in text_instances:
            y_coord = round(inst[1], 1)
            if y_coord not in rows:
                rows[y_coord] = []
            rows[y_coord].append(inst)
        
        # Look for MVA-related content in each row
        for y_coord, row_content in rows.items():
            # Sort content by x-coordinate
            row_content.sort(key=lambda x: x[0])
            row_text = ' '.join(inst[4].lower() for inst in row_content)
            
            # Check for MVA-related patterns
            if ('herav mva' in row_text or 
                'mva' in row_text and '%' in row_text or 
                'totalbeløp uten mva' in row_text or
                'gjennomsnittlig' in row_text):
                
                # Create a section that covers the entire row
                if row_content:
                    section = {
                        'x0': 0,  # Start from left edge
                        'y0': min(inst[1] for inst in row_content) - 2,  # Slightly above
                        'x1': max(inst[2] for inst in row_content) + 500,  # Extend past the content
                        'y1': max(inst[3] for inst in row_content) + 2,  # Slightly below
                    }
                    mva_sections.append(section)
                    logger.info(f"Found MVA section at y={y_coord}")
        
        return mva_sections
    
    def _is_in_mva_section(self, inst, section):
        """Check if a text instance falls within an MVA section."""
        return (section['x0'] <= inst[0] and inst[2] <= section['x1'] and
                section['y0'] <= inst[1] and inst[3] <= section['y1'])

    def cleanup(self):
        """Remove all processed files and input files."""
        try:
            # Clean up input directory
            if os.path.exists(self.input_dir):
                for filename in os.listdir(self.input_dir):
                    if filename.endswith('.pdf'):
                        filepath = os.path.join(self.input_dir, filename)
                        try:
                            os.remove(filepath)
                            logger.info(f"Ryddet opp input fil: {filename}")
                        except Exception as e:
                            logger.error(f"Kunne ikke slette input fil {filename}: {str(e)}")
            
            # Clean up output directory
            if os.path.exists(self.output_dir):
                for filename in os.listdir(self.output_dir):
                    if filename.startswith('Prosessert_'):
                        filepath = os.path.join(self.output_dir, filename)
                        try:
                            os.remove(filepath)
                            logger.info(f"Ryddet opp output fil: {filename}")
                        except Exception as e:
                            logger.error(f"Kunne ikke slette output fil {filename}: {str(e)}")
            
            # Clear the processed files set
            self.processed_files.clear()
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}") 