"""
Status bar creation functions for the PDF Table Extractor.

This module defines functions for creating and configuring the status bar
at the bottom of the application window.
"""

import tkinter as tk

def create_status_bar(app):
    """
    Create the status bar at the bottom of the application window.
    
    Args:
        app: The PDFTableExtractorApp instance
    """
    status_bar = tk.Frame(app.root, bd=1, relief=tk.SUNKEN)
    status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    # Status message on the left
    app.status_label = tk.Label(status_bar, text="Ready", anchor=tk.W)
    app.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    # Keyboard shortcuts indicator in the middle
    shortcuts_text = "Shortcuts: Cmd+Z=Undo | Arrow Keys=Navigation | Trackpad=Scroll"
    shortcuts_label = tk.Label(status_bar, text=shortcuts_text, font=("Arial", 9), fg="#555555")
    shortcuts_label.pack(side=tk.LEFT, padx=10)
    
    # Coordinates on the right
    app.coord_label = tk.Label(status_bar, text="(x: 0, y: 0)", anchor=tk.E, width=12)
    app.coord_label.pack(side=tk.RIGHT, padx=5)
    
    # Track mouse position
    app.canvas.bind("<Motion>", lambda e: update_mouse_position(app, e))

def update_mouse_position(app, event):
    """
    Update the mouse position display in the status bar.
    
    Args:
        app: The PDFTableExtractorApp instance
        event: The mouse motion event
    """
    # Convert canvas position to document position (accounting for zoom)
    x = int(app.canvas.canvasx(event.x) / app.zoom_factor)
    y = int(app.canvas.canvasy(event.y) / app.zoom_factor)
    app.coord_label.config(text=f"(x: {x}, y: {y})")