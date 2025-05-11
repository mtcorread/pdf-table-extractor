"""
Main area creation functions for the PDF Table Extractor.

This module defines functions for creating and configuring the main display area,
including the PDF canvas and text output panel.
"""

import tkinter as tk
import sys

def create_main_area(app):
    """
    Create the main display area with PDF canvas and text output panel.
    
    Args:
        app: The PDFTableExtractorApp instance
    """
    # Create a paned window for resizable layout
    main_paned = tk.PanedWindow(app.root, orient=tk.HORIZONTAL)
    main_paned.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    
    # Create frame for PDF display
    pdf_frame = tk.Frame(main_paned)
    
    # Add horizontal and vertical scrollbars
    h_scrollbar = tk.Scrollbar(pdf_frame, orient=tk.HORIZONTAL)
    h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
    
    v_scrollbar = tk.Scrollbar(pdf_frame)
    v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Create a canvas for displaying the PDF
    app.canvas = tk.Canvas(pdf_frame, 
                         xscrollcommand=h_scrollbar.set,
                         yscrollcommand=v_scrollbar.set,
                         bg='grey')
    app.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    # Configure the scrollbars to the canvas
    h_scrollbar.config(command=app.canvas.xview)
    v_scrollbar.config(command=app.canvas.yview)
    
    # Initial canvas message - we'll add this after adding to the paned window
    main_paned.add(pdf_frame)
    
    # Right panel for displaying extracted text - now in a paned window for resizing
    right_panel = tk.Frame(main_paned)
    
    # Add label and text widget to right panel
    text_frame = tk.Frame(right_panel)
    text_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    
    text_label = tk.Label(text_frame, text="Extracted Text:", anchor=tk.W)
    text_label.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)
    
    # Add scrollbars to the text output
    text_scroll_y = tk.Scrollbar(text_frame)
    text_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
    
    text_scroll_x = tk.Scrollbar(text_frame, orient=tk.HORIZONTAL)
    text_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
    
    # Text widget with scrollbars
    app.text_output = tk.Text(text_frame, wrap=tk.NONE, 
                            xscrollcommand=text_scroll_x.set,
                            yscrollcommand=text_scroll_y.set)
    app.text_output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # Configure scrollbars
    text_scroll_y.config(command=app.text_output.yview)
    text_scroll_x.config(command=app.text_output.xview)
    
    # Add right panel to paned window with a reasonable initial size
    main_paned.add(right_panel)
    
    # Set the initial division point (70% for PDF, 30% for text panel)
    # Using paneconfig instead of sashpos which is not available in all Tkinter versions
    app.root.update()  # Force an update to get the window width
    window_width = app.root.winfo_width()
    main_paned.paneconfigure(pdf_frame, width=int(window_width * 0.7))
    main_paned.paneconfigure(right_panel, width=int(window_width * 0.3))
    
    # Now add the welcome text after the layout is created
    app.root.update()
    app.canvas.create_text(
        app.canvas.winfo_width() // 2, 
        app.canvas.winfo_height() // 3,
        text="No PDF loaded",
        font=("Arial", 18),
        fill="white",
        tags="welcome_text")
    app.canvas.create_text(
        app.canvas.winfo_width() // 2, 
        app.canvas.winfo_height() // 2,
        text="Click 'Open PDF' button",
        font=("Arial", 14),
        fill="white",
        tags="welcome_text")
    
    # Bind mouse events for selecting table lines
    app.canvas.bind("<Button-1>", lambda e: _on_canvas_click(app, e))
    
    # Bind mouse wheel and trackpad events for scrolling
    app.canvas.bind("<MouseWheel>", lambda e: _on_mousewheel(app, e))  # Windows and macOS
    app.canvas.bind("<Button-4>", lambda e: _on_mousewheel(app, e))  # Linux scroll up
    app.canvas.bind("<Button-5>", lambda e: _on_mousewheel(app, e))  # Linux scroll down
    
    # For macOS trackpad scrolling (middle button and motion simulation)
    app.canvas.bind("<2>", lambda e: app.canvas.scan_mark(e.x, e.y))
    app.canvas.bind("<B2-Motion>", lambda e: _on_trackpad_drag(app, e))
    
    # For Mac trackpad gesture support
    app.root.bind("<Key-Up>", lambda e: app.pdf_handler.prev_page())      # Up arrow key for previous page
    app.root.bind("<Key-Down>", lambda e: app.pdf_handler.next_page())    # Down arrow key for next page
    app.root.bind("<Key-Prior>", lambda e: app.pdf_handler.prev_page())   # Page Up key for previous page
    app.root.bind("<Key-Next>", lambda e: app.pdf_handler.next_page())    # Page Down key for next page
    
    # Bind trackpad gestures for macOS
    if hasattr(app.canvas, 'bind_all'):  # Check if bind_all is available
        # For macOS two-finger scroll without any modifier keys
        app.canvas.bind_all('<Control-MouseWheel>', lambda e: _on_ctrl_mousewheel(app, e))  # For zoom control
        
        # Experimental trackpad swipe handling
        app.root.bind_all('<Shift-MouseWheel>', lambda e: _on_shift_mousewheel(app, e))  # Horizontal scroll
        
        # Handle two-finger swipe horizontally for page changes
        if sys.platform == 'darwin':  # macOS specific 
            try:
                app.canvas.bind_all('<Option-MouseWheel>', lambda e: _on_option_mousewheel(app, e))  # Page changes
            except:
                pass

# Event handler functions
def _on_canvas_click(app, event):
    """Handle mouse click events on the canvas."""
    if not app.selection_mode or not app.pdf_document:
        return
    
    # Get the position in the document (accounting for zoom and scroll)
    x = int(app.canvas.canvasx(event.x) / app.zoom_factor)
    y = int(app.canvas.canvasy(event.y) / app.zoom_factor)
    
    if app.selection_mode == 'column':
        # Add column marker
        if x not in app.column_markers:
            # Add to history for undo
            app.marker_history.append({'type': 'column', 'value': x})
            # Add column marker
            app.column_markers.append(x)
            app.column_markers.sort()  # Keep markers in order
    elif app.selection_mode == 'row':
        # Add row marker
        if y not in app.row_markers:
            # Add to history for undo
            app.marker_history.append({'type': 'row', 'value': y})
            # Add row marker
            app.row_markers.append(y)
            app.row_markers.sort()  # Keep markers in order
    elif app.selection_mode == 'area':
        # Start area selection
        app.selection_start = (x, y)
        app.selection_end = (x, y)  # Initialize end point to same as start
        
        # Bind motion and release events for drag operation
        app.canvas.bind("<B1-Motion>", lambda e: _on_canvas_drag(app, e))
        app.canvas.bind("<ButtonRelease-1>", lambda e: _on_canvas_release(app, e))
    
    # Redraw markers
    app.marker_manager.redraw_markers()

def _on_canvas_drag(app, event):
    """Handle mouse drag for area selection."""
    if app.selection_mode != 'area' or not app.selection_start:
        return
        
    # Get the current position (accounting for zoom and scroll)
    x = int(app.canvas.canvasx(event.x) / app.zoom_factor)
    y = int(app.canvas.canvasy(event.y) / app.zoom_factor)
    
    # Update end point of selection
    app.selection_end = (x, y)
    
    # Redraw to show updated selection rectangle
    app.marker_manager.redraw_markers()

def _on_canvas_release(app, event):
    """Handle mouse release after area selection."""
    if app.selection_mode != 'area' or not app.selection_start:
        return
        
    # Get the final position (accounting for zoom and scroll)
    x = int(app.canvas.canvasx(event.x) / app.zoom_factor)
    y = int(app.canvas.canvasy(event.y) / app.zoom_factor)
    
    # Set the final end point
    app.selection_end = (x, y)
    
    # Ensure rectangle has positive width/height
    x1, y1 = app.selection_start
    x2, y2 = app.selection_end
    
    # Normalize coordinates (make sure start is top-left, end is bottom-right)
    if x1 > x2:
        x1, x2 = x2, x1
    if y1 > y2:
        y1, y2 = y2, y1
        
    app.selection_start = (x1, y1)
    app.selection_end = (x2, y2)
    
    # Show selection information
    width = x2 - x1
    height = y2 - y1
    app.status_label.config(text=f"Area selected: {width}x{height} pixels")
    
    # Redraw to show the final selection
    app.marker_manager.redraw_markers()
    
    # Unbind motion and release events
    app.canvas.unbind("<B1-Motion>")
    app.canvas.unbind("<ButtonRelease-1>")

def _on_mousewheel(app, event):
    """Handle mouse wheel and trackpad scroll events."""
    if not app.pdf_document:
        return
        
    # Handle platform-specific scroll values
    delta = 0
    if hasattr(event, 'num') and (event.num == 4 or event.num == 5):  # Linux
        delta = 1 if event.num == 4 else -1
    else:  # Windows and macOS
        delta = event.delta
        
    # Check for larger values (mouse wheel) vs smaller values (trackpad)
    if abs(delta) < 30:  # Likely a trackpad gesture with small delta
        # For vertical scrolling
        app.canvas.yview_scroll(int(-1 * (delta)), "units")
    else:  # Likely a mouse wheel or a more significant gesture
        # Normalize delta for consistent behaviour (especially for Windows)
        normalized_delta = int(delta / 120) if abs(delta) > 120 else (-1 if delta < 0 else 1)
        
        # Check if Shift key is pressed for horizontal scrolling
        if event.state & 0x1:  # Shift key
            app.canvas.xview_scroll(-normalized_delta, "units")
        else:
            app.canvas.yview_scroll(-normalized_delta, "units")
    
    # For very significant gestures, we might want to change pages
    if hasattr(event, 'state') and (event.state & 0x8) and abs(delta) > 200:  # Alt/Option key + large gesture
        if delta > 0:
            app.pdf_handler.prev_page()
        else:
            app.pdf_handler.next_page()

def _on_trackpad_drag(app, event):
    """Handle direct trackpad dragging (two-finger scroll on Mac)."""
    if not app.pdf_document:
        return
        
    # This handles the actual dragging motion
    app.canvas.scan_dragto(event.x, event.y, gain=1)

def _on_ctrl_mousewheel(app, event):
    """Handle Ctrl+MouseWheel for zooming."""
    if not app.pdf_document:
        return
        
    # Positive delta = zoom in, negative = zoom out
    if event.delta > 0:
        app.pdf_handler.zoom_in()
    else:
        app.pdf_handler.zoom_out()

def _on_shift_mousewheel(app, event):
    """Handle Shift+MouseWheel for horizontal scrolling."""
    if not app.pdf_document:
        return
        
    # Scroll horizontally based on delta
    app.canvas.xview_scroll(int(-1 * (event.delta/120)), "units")

def _on_option_mousewheel(app, event):
    """Handle Option+MouseWheel (Alt+MouseWheel) for page navigation."""
    if not app.pdf_document:
        return
        
    # Navigate pages based on delta
    if event.delta > 0:
        app.pdf_handler.prev_page()
    else:
        app.pdf_handler.next_page()