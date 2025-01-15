import os
from dotenv import load_dotenv
import pandas as pd
from fpdf import FPDF
import openai
from pathlib import Path
import logging
import re

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('processor.log')
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
try:
    load_dotenv()
    openai.api_key = os.getenv('OPENAI_API_KEY')
    if not openai.api_key:
        raise ValueError("OpenAI API key not found in .env file")
    logger.info("Successfully loaded API key from .env file")
except Exception as e:
    logger.error(f"Error loading API key from .env file: {e}")
    exit(1)

def clean_text_for_pdf(text):
    """Clean text to make it PDF-safe."""
    # Replace common special characters
    replacements = {
        '™': '(TM)',
        '®': '(R)',
        '©': '(C)',
        '–': '-',
        '"': '"',
        '"': '"',
        ''': "'",
        ''': "'",
        '…': '...',
        '\u2122': '(TM)',  # Another form of trademark symbol
        '\u00ae': '(R)',   # Another form of registered trademark
        '\u00a9': '(C)',   # Another form of copyright
        '\u2013': '-',     # En dash
        '\u2014': '--',    # Em dash
        '\u2018': "'",     # Left single quotation
        '\u2019': "'",     # Right single quotation
        '\u201c': '"',     # Left double quotation
        '\u201d': '"',     # Right double quotation
    }
    
    # First replace known special characters
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    
    # Then remove any remaining non-ASCII characters
    cleaned_text = ''.join(char if ord(char) < 128 else ' ' for char in text)
    
    # Remove multiple spaces
    cleaned_text = ' '.join(cleaned_text.split())
    
    return cleaned_text

def process_with_gpt(product_data):
    """Use GPT to analyze and structure the product data intelligently."""
    try:
        logger.info(f"Processing with GPT: {product_data['name']}")
        
        # Format the raw data for GPT analysis
        specs_text = "\n".join([
            f"{spec[0]}: {spec[1]}" for spec in product_data['specifications']
            if len(spec) >= 2
        ])
        
        prompt = f"""
        Analyze and organize this product configuration into a structured format.
        Make sure to identify and categorize each specification correctly.
        
        Product: {product_data['name']}
        Price: ${product_data.get('price', 'N/A')}
        
        Raw Specifications:
        {specs_text}

        Organize this into a clean, structured format with proper labels and values.
        Return ONLY a JSON object with this structure:
        {{
            "title": "{product_data['name']}",
            "price": "{product_data.get('price', '')}",
            "main_specs": [
                {{"label": "Processor", "value": "processor details"}},
                {{"label": "Memory", "value": "memory details"}},
                {{"label": "Storage", "value": "storage details"}},
                {{"label": "Display", "value": "display details"}},
                {{"label": "Graphics", "value": "graphics details"}},
                {{"label": "Power", "value": "power details"}},
                {{"label": "Wireless", "value": "wireless details"}},
                {{"label": "Operating System", "value": "OS details"}},
                {{"label": "Warranty", "value": "warranty details"}}
            ],
            "upgrade_options": []
        }}
        
        Include only the specifications that are present in the raw data.
        Format the values to be clear and readable.
        """

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        
        # Parse the GPT response
        content = response['choices'][0]['message']['content']
        
        # Extract the JSON part from the response
        import json
        start_idx = content.find('{')
        end_idx = content.rfind('}') + 1
        if start_idx != -1 and end_idx != -1:
            json_str = content[start_idx:end_idx]
            structured_data = json.loads(json_str)
            logger.info("Successfully processed data with GPT")
            return structured_data
        else:
            raise ValueError("Could not extract JSON from GPT response")
            
    except Exception as e:
        logger.error(f"Error in GPT processing: {e}")
        # Return a basic structure if GPT processing fails
        return {
            "title": product_data['name'],
            "price": product_data.get('price', ''),
            "main_specs": [
                {"label": spec[0], "value": spec[1]}
                for spec in product_data['specifications']
                if len(spec) >= 2
            ],
            "upgrade_options": []
        }

class SpecificationPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        self.set_margins(left=20, top=20, right=20)
        # Use standard Arial font instead of trying to load custom fonts
        self.set_font('Arial', '', 12)

    def create_specification_table(self, structured_data):
        """Create a specification table using GPT-structured data."""
        # Set up colors
        dark_gray = 230  # Background for alternate rows
        light_gray = 245  # Background for other rows
        text_gray = 100  # Color for labels
        
        # Page width calculations
        content_width = self.w - 40  # 40 for margins
        label_width = content_width * 0.3  # 30% for labels
        value_width = content_width * 0.7  # 70% for values
        row_height = 8
        
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
        
        # Add upgrade options if available
        if structured_data.get('upgrade_options'):
            self.ln(10)
            self.set_font('Arial', 'B', 14)
            self.set_text_color(0)
            self.cell(0, 10, "UPGRADE OPTIONS", ln=True, align='L')
            self.ln(5)
            
            self.set_font('Arial', '', 10)
            is_dark_row = True
            
            for upgrade in structured_data['upgrade_options']:
                # Set background color
                self.set_fill_color(dark_gray if is_dark_row else light_gray)
                
                # Calculate row height
                upgrade_text = f"{upgrade['value']}"
                if upgrade.get('price'):
                    upgrade_text += f" - ${upgrade['price']}"
                lines = len(upgrade_text.split('\n'))
                current_row_height = max(row_height, row_height * lines)
                
                # Draw background
                self.rect(self.get_x(), self.get_y(), content_width, current_row_height, 'F')
                
                # Add label
                self.set_text_color(text_gray)
                self.set_font('Arial', 'B', 10)
                self.cell(label_width, current_row_height, clean_text_for_pdf(str(upgrade['label'])), 0, 0, 'L')
                
                # Add value with price
                self.set_text_color(0)
                self.set_font('Arial', '', 10)
                self.multi_cell(value_width, current_row_height/lines, clean_text_for_pdf(upgrade_text), 0, 'L')
                
                is_dark_row = not is_dark_row

def parse_product_blocks(content):
    """Parse markdown content into structured product data."""
    logger.info("Starting to parse product blocks")
    products = []
    current_product = None
    current_specs = []
    current_price = None
    
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    
    # Common hardware specification labels
    spec_labels = {
        'Processor': ['processor', 'intel', 'amd', 'core', 'celeron', 'xeon'],
        'Memory': ['memory', 'gb:', 'ram', 'rdimm', 'ddr'],
        'Storage': ['storage', 'ssd', 'hdd', 'emmc', 'hard drive', 'nvme'],
        'Display': ['display', 'screen', 'lcd', '"', 'fhd', 'hd', 'monitor'],
        'Graphics': ['graphics', 'gpu', 'radeon', 'nvidia', 'intel® uhd'],
        'Power': ['adapter', 'battery', 'cell', 'wh', 'expresscharge'],
        'Wireless': ['wireless', 'wi-fi', 'bluetooth', 'ax201', 'ax211'],
        'Operating System': ['windows', 'chrome'],
        'Warranty': ['warranty', 'service', 'support']
    }
    
    def determine_spec_type(value):
        """Determine the specification type based on the value."""
        value_lower = value.lower()
        for label, keywords in spec_labels.items():
            if any(keyword in value_lower for keyword in keywords):
                return label
        return 'Other'

    for line in lines:
        if '|' not in line or all(c in '|-' for c in line):
            continue
            
        cells = [cell.strip() for cell in line.split('|') if cell.strip()]
        if not cells:
            continue

        # Check for price in the cells
        price_cell = next((cell for cell in cells if isinstance(cell, str) and cell.startswith('$')), None)
        if price_cell:
            current_price = price_cell.replace('$', '').replace(',', '')
        
        # Check if this is a new product
        if cells[0] != 'NaN' and ('Base Configuration' in line or 'Base configuration' in line):
            if current_product and current_specs:
                products.append({
                    'name': current_product,
                    'price': current_price,
                    'specifications': current_specs
                })
            current_product = cells[0]
            current_specs = []
            logger.info(f"Starting to parse new product: {current_product}")
        elif current_product and cells:
            # Handle specification lines
            if len(cells) >= 2:
                if cells[0] == 'NaN':
                    # This is a specification line
                    spec_value = cells[1]
                    spec_type = determine_spec_type(spec_value)
                    current_specs.append([spec_type, spec_value])
                else:
                    # This might be a direct label-value pair
                    current_specs.append([cells[0], cells[1]])
    
    # Add the last product
    if current_product and current_specs:
        products.append({
            'name': current_product,
            'price': current_price,
            'specifications': current_specs
        })
    
    logger.info(f"Completed parsing {len(products)} products")
    return products

def create_spec_pdf(product):
    """Create a PDF with GPT-processed specifications."""
    try:
        # Process the data with GPT
        structured_data = process_with_gpt(product)
        logger.info(f"Creating PDF for {product['name']}")
        
        # Create PDF
        pdf = SpecificationPDF()
        pdf.add_page()
        pdf.create_specification_table(structured_data)
        
        return pdf
        
    except Exception as e:
        logger.error(f"Error creating PDF for {product['name']}: {e}")
        raise

def main():
    try:
        logger.info("Starting PDF generation process")
        script_dir = Path(__file__).parent
        config_file = script_dir / '2024config.md'
        
        logger.info(f"Reading configuration file: {config_file}")
        with open(config_file, 'r', encoding='utf-8') as file:
            markdown_content = file.read()
        
        products = parse_product_blocks(markdown_content)
        if not products:
            logger.error("No products found in the configuration file")
            return
        
        output_dir = script_dir / 'output'
        output_dir.mkdir(exist_ok=True)
        logger.info(f"Created output directory: {output_dir}")
        
        for i, product in enumerate(products, 1):
            logger.info(f"Processing product {i} of {len(products)}: {product['name']}")
            
            # Create PDF for the product
            pdf = create_spec_pdf(product)
            
            # Save the PDF
            safe_filename = "".join(x for x in product['name'] if x.isalnum() or x in (' ', '-', '_'))
            output_file = output_dir / f"{safe_filename}_spec.pdf"
            pdf.output(str(output_file))
            logger.info(f"Generated PDF: {output_file}")
        
        logger.info("PDF generation process completed successfully")
            
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    main()