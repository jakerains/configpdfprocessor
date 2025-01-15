# Dell Configuration PDF Generator 🖨️

An automated tool that converts Dell product configurations from markdown format into professionally formatted PDF documents. This tool uses GPT-4o-mini to intelligently parse and structure the specifications, ensuring accurate and consistent formatting.

## 🌟 Features

- **Intelligent Parsing**: Uses GPT to accurately categorize and structure product specifications
- **Professional PDF Layout**: 
  - Clean, two-column design
  - Alternating row backgrounds
  - Properly formatted specifications
  - Clear hierarchy with bold labels
- **Bulk Processing**: Handles multiple product configurations in one run
- **Error Handling**: Robust error handling and logging
- **Special Character Support**: Handles trademark symbols and special characters
- **Configurable Output**: Customizable PDF formatting and styling

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- Virtual environment (recommended)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/jakerains/configpdfprocessor.git
cd configpdfprocessor
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your OpenAI API key:
```bash
OPENAI_API_KEY=your-api-key-here
```

### Usage

1. Place your configuration markdown file as `2024config.md` in the project directory
2. Run the processor:
```bash
python processor.py
```
3. Find generated PDFs in the `output` directory

## 📋 Input Format

The tool expects a markdown file with product configurations in this format:

```markdown
| 2024 Product | Configurations | Price |
| --- | --- | --- |
| Product Name | Base Configuration | $XXX.XX |
| NaN | Specification Label | Value |
```

## 📄 Output Format

Generated PDFs include:
- Product name and price
- Categorized specifications
- Alternating row backgrounds
- Professional formatting
- Upgrade options (if available)

## 🛠️ Configuration

The tool can be customized by modifying:
- PDF styling (colors, fonts, spacing)
- Specification categories
- Output format
- GPT processing parameters

## 📝 Logging

The tool provides detailed logging:
- Console output for immediate feedback
- Log file (`processor.log`) for debugging
- Progress tracking for bulk processing

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenAI for GPT-4o-mini API
- FPDF for PDF generation
- Python-dotenv for environment management

## 📞 Support

For support, please open an issue in the GitHub repository.
