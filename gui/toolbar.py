"""
Toolbar creation functions for the PDF Table Extractor.

This module defines functions for creating and configuring the application's
toolbars with various buttons and controls.
"""

import tkinter as tk
from tkinter import ttk

def create_toolbar(app):
    """
    Create the application toolbar with tabbed interface.
    
    Args:
        app: The PDFTableExtractorApp instance
    """
    # Create a toolbar frame with tabs for better organisation on smaller screens
    toolbar_frame = tk.Frame(app.root)
    toolbar_frame.pack(side=tk.TOP, fill=tk.X)
    
    # Create a notebook (tabbed interface) for the toolbar
    toolbar_tabs = ttk.Notebook(toolbar_frame)
    toolbar_tabs.pack(fill=tk.X)
    
    # Create tabs for different functionality groups
    file_tab = tk.Frame(toolbar_tabs, pady=2)
    edit_tab = tk.Frame(toolbar_tabs, pady=2)
    view_tab = tk.Frame(toolbar_tabs, pady=2)
    table_tab = tk.Frame(toolbar_tabs, pady=2)
    export_tab = tk.Frame(toolbar_tabs, pady=2)
    manual_tab = tk.Frame(toolbar_tabs, pady=2)  # New tab for manual input
    
    toolbar_tabs.add(file_tab, text="File")
    toolbar_tabs.add(edit_tab, text="Edit")
    toolbar_tabs.add(view_tab, text="View")
    toolbar_tabs.add(table_tab, text="Table")
    toolbar_tabs.add(export_tab, text="Export")
    toolbar_tabs.add(manual_tab, text="Manual Input")  # Add the new tab
    
    # Add tab selection event handler
    def on_tab_selected(event):
        """
        Handle tab selection to switch between drawing and manual input modes.
        """
        selected_tab = event.widget.select()
        tab_text = event.widget.tab(selected_tab, "text")
        
        # If leaving Manual Input tab and manual mode is active, exit it and save data
        if tab_text != "Manual Input" and hasattr(app, 'manual_input_manager') and app.manual_input_manager.manual_mode_active:
            app.manual_input_manager.exit_manual_mode_and_store_data()

            # If leaving Edit tab, disable line drawing modes
        if tab_text != "Edit" and app.selection_mode in ['column', 'row', 'area']:
            app.selection_mode = None
            app.status_label.config(text="Drawing mode deactivated")
        
        # If entering Manual Input tab and we have a table structure, activate manual mode
        elif tab_text == "Manual Input" and app.column_markers and app.row_markers and not app.manual_input_manager.manual_mode_active:
            app.manual_input_manager.toggle_manual_mode()
    
    # Bind the tab selection event
    toolbar_tabs.bind("<<NotebookTabChanged>>", on_tab_selected)
    
    # ----- File Tab -----
    open_btn = tk.Button(file_tab, text="Open PDF", command=lambda: app.pdf_handler.open_pdf(), bg="lightblue")
    open_btn.pack(side=tk.LEFT, padx=5, pady=2)

    # Replace the Table configuration controls
    tk.Button(file_tab, text="Save Markers & Data", command=lambda: app.config_manager.save_all_page_markers(), 
            bg="lightgrey").pack(side=tk.LEFT, padx=5, pady=2)
    tk.Button(file_tab, text="Load Markers & Data", command=lambda: app.config_manager.load_all_page_markers(), 
            bg="lightgrey").pack(side=tk.LEFT, padx=5, pady=2)
    
    # ----- Edit Tab -----
    # Table extraction controls
    tk.Button(edit_tab, text="Select Columns", command=lambda: app.set_selection_mode('column'), 
             bg="lightblue").pack(side=tk.LEFT, padx=5, pady=2)
    tk.Button(edit_tab, text="Select Rows", command=lambda: app.set_selection_mode('row'), 
             bg="lightpink").pack(side=tk.LEFT, padx=5, pady=2)
    tk.Button(edit_tab, text="Select Area", command=lambda: app.set_selection_mode('area'), 
             bg="#FFFF99").pack(side=tk.LEFT, padx=5, pady=2)  # Light yellow colour
    tk.Button(edit_tab, text="Process Selection", command=lambda: app.area_processor.process_selected_area(), 
             bg="#98FB98").pack(side=tk.LEFT, padx=5, pady=2)  # Light green colour
    tk.Button(edit_tab, text="Clear Lines", command=lambda: app.marker_manager.clear_lines()).pack(side=tk.LEFT, padx=5, pady=2)
    tk.Button(edit_tab, text="Undo", command=lambda: app.marker_manager.undo_last_marker(), 
             bg="#FFE4E1").pack(side=tk.LEFT, padx=5, pady=2)  # Light mistyrose colour
    
    # ----- View Tab -----
    # Page navigation
    tk.Button(view_tab, text="Previous Page", command=lambda: app.pdf_handler.prev_page()).pack(side=tk.LEFT, padx=5, pady=2)
    app.page_label = tk.Label(view_tab, text="Page: 0/0")
    app.page_label.pack(side=tk.LEFT, padx=5, pady=2)
    tk.Button(view_tab, text="Next Page", command=lambda: app.pdf_handler.next_page()).pack(side=tk.LEFT, padx=5, pady=2)
    
    # Add separator
    tk.Frame(view_tab, width=2, bd=1, relief=tk.SUNKEN).pack(side=tk.LEFT, padx=5, pady=2, fill=tk.Y)
    
    # Zoom controls
    tk.Button(view_tab, text="Zoom In", command=lambda: app.pdf_handler.zoom_in()).pack(side=tk.LEFT, padx=5, pady=2)
    tk.Button(view_tab, text="Zoom Out", command=lambda: app.pdf_handler.zoom_out()).pack(side=tk.LEFT, padx=5, pady=2)
    tk.Button(view_tab, text="Reset Zoom", command=lambda: app.pdf_handler.reset_zoom()).pack(side=tk.LEFT, padx=5, pady=2)
    
    # ----- Table Tab -----
    tk.Button(table_tab, text="Extract Table", command=lambda: app.table_extractor.extract_table(), 
             bg="lightgreen").pack(side=tk.LEFT, padx=5, pady=2)
    tk.Button(table_tab, text="Transpose", command=lambda: app.table_extractor.transpose_table(),
             bg="#E6E6FA").pack(side=tk.LEFT, padx=5, pady=2)  # Light lavender colour
    tk.Button(table_tab, text="Correct Text Orientation", 
             command=lambda: app.table_extractor.force_text_orientation_correction(),
             bg="#FFD700").pack(side=tk.LEFT, padx=5, pady=2)
    
    # Multi-page controls with more descriptive labels
    tk.Label(table_tab, text="Multi-page:").pack(side=tk.LEFT, padx=5, pady=2)
    tk.Button(table_tab, text="Mark Current Page", command=lambda: app.marker_manager.save_page_markers(),
             bg="#FFF8DC").pack(side=tk.LEFT, padx=5, pady=2)  # Light cornsilk
    tk.Button(table_tab, text="Extract All Marked Pages", command=lambda: app.table_extractor.extract_from_marked_pages(),
             bg="#FFF8DC").pack(side=tk.LEFT, padx=5, pady=2)  # Light pink
    
    # ----- Export Tab -----
    # Export controls
    tk.Button(export_tab, text="Save as CSV", command=lambda: app.table_extractor.save_extracted_text('csv'),
             bg="lightyellow").pack(side=tk.LEFT, padx=5, pady=2)
    tk.Button(export_tab, text="Save as Excel", command=lambda: app.table_extractor.save_extracted_text('excel'),
             bg="#CCFFCC").pack(side=tk.LEFT, padx=5, pady=2)
    
    # ----- Manual Input Tab -----
    # Toggle manual mode
    tk.Button(manual_tab, text="Toggle Manual Mode", 
             command=lambda: app.manual_input_manager.toggle_manual_mode(),
             bg="#FFDAB9").pack(side=tk.LEFT, padx=5, pady=2)  # Peach color
             
    
