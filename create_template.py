from fpdf import FPDF
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('template_creator.log')
    ]
)
logger = logging.getLogger(__name__)

class TemplatePDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=False)
        self.set_margins(left=20, top=20, right=20)
        self.set_font('Arial', '', 12)
    
    def create_template(self):
        """Create template with placeholder header and footer areas."""
        self.add_page()
        
        # Header area (light gray background)
        self.set_fill_color(240, 240, 240)  # Light gray
        self.rect(0, 0, 210, 70, 'F')  # Header area
        
        # Header placeholder text
        self.set_font('Arial', 'B', 14)
        self.set_xy(20, 30)
        self.set_text_color(128, 128, 128)  # Gray text
        self.cell(0, 10, 'HEADER AREA - Edit in PDF editor', 0, 1, 'C')
        
        # Content area markers
        self.set_font('Arial', '', 12)
        self.set_text_color(200, 200, 200)  # Light gray text
        self.set_xy(20, 75)
        self.cell(0, 10, '--- Content will start here ---', 0, 1, 'L')
        self.set_xy(20, 220)
        self.cell(0, 10, '--- Content will end here ---', 0, 1, 'L')
        
        # Footer area (light gray background)
        self.set_fill_color(240, 240, 240)  # Light gray
        self.rect(0, 257, 210, 40, 'F')  # Adjusted to reach bottom of page (297 - 40 = 257)
        
        # Footer placeholder text
        self.set_font('Arial', 'B', 14)
        self.set_text_color(128, 128, 128)  # Gray text
        self.set_xy(20, 272)  # Centered in footer area
        self.cell(0, 10, 'FOOTER AREA - Edit in PDF editor', 0, 1, 'C')
        
        # Add guidelines
        self.set_draw_color(200, 200, 200)  # Light gray lines
        self.line(20, 70, 190, 70)  # Header boundary
        self.line(20, 257, 190, 257)  # Footer boundary

def main():
    try:
        logger.info("Starting template creation")
        script_dir = Path(__file__).parent
        template_path = script_dir / 'template.pdf'
        
        # Create template
        template = TemplatePDF()
        template.create_template()
        
        # Save template
        template.output(str(template_path))
        logger.info(f"Template created successfully: {template_path}")
        
        # Print instructions
        print("\nTemplate created successfully!")
        print("\nInstructions:")
        print("1. Open template.pdf in your PDF editor")
        print("2. Add your desired header content in the gray header area")
        print("3. Add your desired footer content in the gray footer area")
        print("4. Save the modified template")
        print("5. The template is now ready to use with processor_template.py")
        print("\nNote: Do not modify the content area between the markers")
        
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    main() 