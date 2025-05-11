"""
Main application class for the PDF Table Extractor.

This module defines the PDFTableExtractorApp class, which serves as the central
controller for the application, integrating all UI components and core functionality.
"""

from .toolbar import create_toolbar
from .main_area import create_main_area
from .status_bar import create_status_bar
from core.pdf_handler import PDFHandler
from core.table_extractor import TableExtractor
from core.marker_manager import MarkerManager
from core.config_manager import ConfigManager
from core.manual_input import ManualInputManager
from image.area_processor import AreaProcessor
from core.text_orientation_corrector import TextOrientationCorrector


class PDFTableExtractorApp:
    """
    Main application class that initialises and manages all components of the PDF Table Extractor.
    
    This class serves as the central hub for all application functionality, integrating
    the GUI components with the core processing logic.
    """
    
    def __init__(self, root):
        """
        Initialise the PDF Table Extractor application.
        
        Args:
            root: The tkinter root window
        """
        self.root = root
        self.root.title("PDF Table Extractor")
        self.root.geometry("1200x800")
        
        # Initialise core components
        self.pdf_handler = PDFHandler(self)
        self.marker_manager = MarkerManager(self)
        self.table_extractor = TableExtractor(self)
        self.config_manager = ConfigManager(self)
        self.area_processor = AreaProcessor(self)
        self.manual_input_manager = ManualInputManager(self)
        self.text_orientation_corrector = TextOrientationCorrector(self)

        
        # PDF viewing variables
        self.pdf_document = None
        self.current_page = 0
        self.total_pages = 0
        self.zoom_factor = 1.0
        
        # Table extraction variables
        self.column_markers = []
        self.row_markers = []
        self.selection_mode = None
        self.table_data = []
        
        # Area selection variables
        self.selection_start = None
        self.selection_end = None
        self.processed_image = None
        
        # Per-page markers storage
        self.page_markers = {}
        
        # Undo history
        self.marker_history = []
        
        # UI components
        self.canvas = None
        self.text_output = None
        self.status_label = None
        self.coord_label = None
        self.page_label = None
        self.photo = None  # To prevent garbage collection of displayed image
        
        # Create GUI elements
        create_toolbar(self)
        create_main_area(self)
        create_status_bar(self)
        
        # Set up keyboard shortcuts
        self.setup_keyboard_shortcuts()
    
    def setup_keyboard_shortcuts(self):
        """Set up keyboard shortcuts for common actions."""
        self.root.bind('<Control-o>', lambda e: self.pdf_handler.open_pdf())
        self.root.bind('<Control-s>', lambda e: self.table_extractor.save_extracted_text('csv'))
        self.root.bind('<Control-e>', lambda e: self.table_extractor.save_extracted_text('excel'))
        self.root.bind('<Control-z>', lambda e: self.marker_manager.undo_last_marker())
        self.root.bind('<Control-l>', lambda e: self.pdf_handler.load_pdf())
        self.root.bind('<Left>', lambda e: self.pdf_handler.prev_page())
        self.root.bind('<Right>', lambda e: self.pdf_handler.next_page())
        self.root.bind('<Control-plus>', lambda e: self.pdf_handler.zoom_in())
        self.root.bind('<Control-minus>', lambda e: self.pdf_handler.zoom_out())
        
        # For Mac users
        self.root.bind('<Command-o>', lambda e: self.pdf_handler.open_pdf())
        self.root.bind('<Command-s>', lambda e: self.table_extractor.save_extracted_text('csv'))
        self.root.bind('<Command-e>', lambda e: self.table_extractor.save_extracted_text('excel'))
        self.root.bind('<Command-z>', lambda e: self.marker_manager.undo_last_marker())
        self.root.bind('<Command-plus>', lambda e: self.pdf_handler.zoom_in())
        self.root.bind('<Command-minus>', lambda e: self.pdf_handler.zoom_out())
    
    def set_selection_mode(self, mode):
        """
        Set the current selection mode (column, row, or area).
        
        Args:
            mode: The selection mode to set ('column', 'row', or 'area')
        """
        self.selection_mode = mode
        if mode == 'column':
            self.status_label.config(text="Click to add column markers (vertical lines)")
        elif mode == 'row':
            self.status_label.config(text="Click to add row markers (horizontal lines)")
        elif mode == 'area':
            self.status_label.config(text="Click and drag to select an area")
            
            # Reset selection points when changing to area mode
            self.selection_start = None
            self.selection_end = None
            self.marker_manager.redraw_markers()