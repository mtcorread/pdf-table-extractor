#!/usr/bin/env python3
"""
Entry point for the PDF Table Extractor application.

This module sets up the main tkinter window and starts the application.
"""

import tkinter as tk
from gui.app import PDFTableExtractorApp

def main():
    """
    Main function that creates the tkinter root window and initialises the application.
    """
    root = tk.Tk()
    
    # Set the application name that appears in the macOS dock/taskbar
    root.wm_title("PDF Table Extractor")
    
    # For macOS, set the application name more consistently
    if hasattr(root, 'createcommand'):
        root.createcommand('tk::mac::GetApplicationName', lambda: "PDF Table Extractor")
    
    # Create the application instance
    app = PDFTableExtractorApp(root)
    
    # Start the tkinter main loop
    root.mainloop()

if __name__ == "__main__":
    main()