# PDF Table Extractor

A desktop application to extract tabular data from PDF documents, with support for challenging PDFs including those with rotated text or complex layouts.

## Features

- **Visual Table Selection**: Draw column and row markers directly on the PDF to define table boundaries
- **Automatic Line Detection**: Identify table structure from visual elements
- **Text Orientation Correction**: Automatically detects and corrects issues with vertical or rotated text
- **Multi-page Extraction**: Extract and combine tables across multiple PDF pages
- **Data Export**: Save extracted data to CSV or Excel formats
- **Manual Input Mode**: Manually edit table cells when automatic extraction isn't perfect
- **Configuration Save/Load**: Save table markers and extraction settings for future use

## Installation

### Requirements

- Python 3.7 or higher
- Required packages (install using `pip install -r requirements.txt`):
  - PyMuPDF (imported as fitz)
  - Pillow
  - numpy
  - pandas
  - openpyxl

### Setup

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/pdf-table-extractor.git
   cd pdf-table-extractor
   ```

2. Install required packages:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python main.py
   ```

## Usage Guide

### Basic Operation

1. **Load a PDF**:
   - Click "Open PDF" in the File tab or use Ctrl+O (Cmd+O on Mac)
   
2. **Define Table Structure**:
   - Go to the Edit tab
   - Click "Select Columns" and click on the PDF to add vertical lines
   - Click "Select Rows" and click on the PDF to add horizontal lines
   
3. **Extract Table**:
   - Go to the Table tab
   - Click "Extract Table" to process the defined area
   
4. **Export Data**:
   - Go to the Export tab
   - Choose "Save as CSV" or "Save as Excel"

### Advanced Features

#### Automatic Table Detection

1. Click "Select Area" and drag to select a region containing a table
2. Click "Process Selection" to automatically detect table lines
3. Review the detected lines and click "Apply Detected Lines" to use them

#### Text Orientation Correction

If extracted text appears scrambled or incorrectly oriented:
1. Extract the table first
2. Click "Correct Text Orientation" to fix vertical or rotated text issues

#### Manual Input Mode

When automatic extraction doesn't work well:
1. Define table structure with column and row markers
2. Go to the "Manual Input" tab to enter cell values manually
3. Navigate between cells using arrow keys or Tab
4. Click "Save & Exit Manual Mode" when finished

#### Multi-page Extraction

To extract tables from multiple pages:
1. Navigate to each page containing tables
2. Set up markers and click "Mark Current Page" for each page
3. Click "Extract All Marked Pages" to process all marked pages
4. Choose how to merge the tables (vertically or horizontally)

## Keyboard Shortcuts

- **Ctrl+O / Cmd+O**: Open PDF
- **Ctrl+S / Cmd+S**: Save as CSV
- **Ctrl+E / Cmd+E**: Save as Excel
- **Ctrl+Z / Cmd+Z**: Undo last marker
- **Left/Right Arrow**: Previous/Next page
- **+/-**: Zoom in/out

## Troubleshooting

### Text Not Extracting Correctly

- Try the "Correct Text Orientation" feature
- Switch to Manual Input Mode for problematic tables
- Experiment with different marker placements

### Application Not Starting

- Ensure Python 3.7+ is installed
- Verify all dependencies are installed with `pip install -r requirements.txt`
- Check console output for specific error messages

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [PyMuPDF](https://github.com/pymupdf/PyMuPDF) for PDF processing
- [Pillow](https://python-pillow.org/) for image processing
- Created by Martha Correa