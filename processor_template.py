import os
from dotenv import load_dotenv
import pandas as pd
from fpdf import FPDF
import openai
from pathlib import Path
import logging
from PyPDF2 import PdfReader, PdfWriter
from processor import parse_product_blocks, process_with_gpt, clean_text_for_pdf

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('processor_template.log')
    ]
)
logger = logging.getLogger(__name__)

class TemplatedPDF(FPDF):
    def __init__(self, template_path=None):
        super().__init__()
        self.set_auto_page_break(auto=False)
        self.set_margins(left=20, top=20, right=20)
        self.set_font('Arial', '', 12)
        self.template_path = template_path
        
    def create_specification_table(self, structured_data):
        """Create a specification table using GPT-structured data."""
        # Set up colors
        dark_gray = 230
        light_gray = 245
        text_gray = 100
        
        # Page width calculations
        content_width = self.w - 40
        label_width = content_width * 0.3
        value_width = content_width * 0.7
        row_height = 8
        
        # Start content after template header space
        self.set_y(75)  # Adjusted to match new header height
        
        # Add title
        self.set_font('Arial', 'B', 24)
        self.cell(0, 15, clean_text_for_pdf(structured_data['title']), ln=True, align='L')
        
        # Add price if available
        if structured_data.get('price') and structured_data['price'] not in ['None', '', None]:
            self.set_font('Arial', 'B', 32)
            self.set_text_color(0, 0, 0)
            price = clean_text_for_pdf(str(structured_data['price']))
            self.cell(0, 20, f"${price}", ln=True, align='L')
        self.ln(5)
        
        # Main specifications with alternating backgrounds
        self.set_font('Arial', '', 10)
        is_dark_row = True
        
        # Calculate available space (adjusted for new footer position)
        max_y = 220  # Matches the new content end marker
        
        for spec in structured_data['main_specs']:
            if not spec.get('value'):  # Skip empty specifications
                continue
                
            # Set background color
            self.set_fill_color(dark_gray if is_dark_row else light_gray)
            
            # Calculate row height based on content
            value_lines = len(str(spec['value']).split('\n'))
            # Get the actual width of the text to calculate wrapped lines
            value_text = str(spec['value'])
            text_width = self.get_string_width(value_text)
            wrapped_lines = max(1, int(text_width / value_width) + 1)
            total_lines = max(value_lines, wrapped_lines)
            current_row_height = row_height * total_lines
            
            # Store current position
            start_y = self.get_y()
            
            # Draw background for the full height
            self.rect(self.get_x(), start_y, content_width, current_row_height, 'F')
            
            # Add label
            self.set_text_color(text_gray)
            self.set_font('Arial', 'B', 10)
            label = clean_text_for_pdf(str(spec['label']))
            self.cell(label_width, current_row_height, label, 0, 0, 'L')
            
            # Add value
            self.set_text_color(0)
            self.set_font('Arial', '', 10)
            value = clean_text_for_pdf(str(spec['value']))
            self.multi_cell(value_width, row_height, value, 0, 'L')
            
            # Move to next row position
            self.set_y(start_y + current_row_height)
            
            is_dark_row = not is_dark_row

def create_templated_pdf(product, template_path):
    """Create a PDF with template and specifications."""
    try:
        # Process the data with GPT
        structured_data = process_with_gpt(product)
        logger.info(f"Creating PDF for {product['name']}")
        
        # Create content PDF
        content_pdf = TemplatedPDF()
        content_pdf.add_page()
        content_pdf.create_specification_table(structured_data)
        
        # Save content to temporary file
        temp_content = Path("temp_content.pdf")
        content_pdf.output(str(temp_content))
        
        # Merge template with content
        template_reader = PdfReader(template_path)
        content_reader = PdfReader(str(temp_content))
        
        writer = PdfWriter()
        
        # Get only the first page of the template
        template_page = template_reader.pages[0]
        content_page = content_reader.pages[0]
        
        # Merge template and content
        template_page.merge_page(content_page)
        writer.add_page(template_page)
        
        return writer
        
    except Exception as e:
        logger.error(f"Error creating PDF for {product['name']}: {e}")
        raise
    finally:
        # Clean up temporary file
        if temp_content.exists():
            temp_content.unlink()

def main():
    try:
        logger.info("Starting templated PDF generation process")
        script_dir = Path(__file__).parent
        template_path = script_dir / 'template.pdf'
        
        if not template_path.exists():
            raise FileNotFoundError("Template PDF not found. Please create template.pdf first.")
        
        # Ask for markdown file location
        print("\nPlease specify the markdown file to process:")
        print("(You can drag and drop the file here or type the path)")
        config_file = input("> ").strip().strip('"').strip("'")  # Remove quotes if present
        config_file = Path(config_file)
        
        if not config_file.exists():
            raise FileNotFoundError(f"Could not find markdown file: {config_file}")
        
        # Ask for output folder name
        print("\nPlease specify the name for the output folder:")
        output_folder_name = input("> ").strip()
        
        # Create output directory with user-specified name
        output_dir = script_dir / output_folder_name
        output_dir.mkdir(exist_ok=True)
        
        logger.info(f"Reading configuration file: {config_file}")
        with open(config_file, 'r', encoding='utf-8') as file:
            markdown_content = file.read()
        
        products = parse_product_blocks(markdown_content)
        if not products:
            logger.error("No products found in the configuration file")
            return
        
        print(f"\nFound {len(products)} products to process.")
        print(f"Output will be saved to: {output_dir}\n")
        
        for i, product in enumerate(products, 1):
            logger.info(f"Processing product {i} of {len(products)}: {product['name']}")
            print(f"Processing {i}/{len(products)}: {product['name']}")
            
            # Create PDF with template
            pdf_writer = create_templated_pdf(product, template_path)
            
            # Save the PDF
            safe_filename = "".join(x for x in product['name'] if x.isalnum() or x in (' ', '-', '_'))
            output_file = output_dir / f"{safe_filename}_spec.pdf"
            
            with open(output_file, 'wb') as output:
                pdf_writer.write(output)
            
            logger.info(f"Generated PDF: {output_file}")
        
        print(f"\nProcessing complete! {len(products)} PDFs have been generated.")
        print(f"Files are located in: {output_dir}")
        logger.info("PDF generation process completed successfully")
            
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        print(f"\nError: {e}")
        print("Please check the log file for more details.")

if __name__ == "__main__":
    main() 