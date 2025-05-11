"""
PDF handling functionality for the PDF Table Extractor.

This module provides the PDFHandler class, which is responsible for loading PDF files,
navigating between pages, and handling zoom operations.
"""

import json
import fitz  # PyMuPDF
from PIL import Image, ImageTk
import os
from tkinter import filedialog, messagebox

class PDFHandler:
    """
    Handles PDF document loading, page navigation, and zoom operations.
    
    This class manages all interactions with the PDF document itself, including
    opening files, rendering pages, and navigating through the document.
    """
    
    def __init__(self, app):
        """
        Initialise the PDF handler.
        
        Args:
            app: The PDFTableExtractorApp instance
        """
        self.app = app
        
    def open_pdf(self):
        """
        Open a PDF file selected by the user.
        """
        file_path = filedialog.askopenfilename(
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")])
        
        if file_path:
            try:
                self.app.pdf_document = fitz.open(file_path)
                self.app.total_pages = len(self.app.pdf_document)
                self.app.current_page = 0
                self.update_page_display()
                self.app.status_label.config(text=f"Loaded: {os.path.basename(file_path)}")
                
                # Reset table extraction variables
                self.app.column_markers = []
                self.app.row_markers = []
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open PDF: {str(e)}")
    
    def update_page_display(self):
        """
        Update the canvas to display the current page of the PDF.
        """
        if not self.app.pdf_document:
            return
        
        # Update page label
        self.app.page_label.config(text=f"Page: {self.app.current_page + 1}/{self.app.total_pages}")
        
        # Get the current page
        page = self.app.pdf_document[self.app.current_page]
        
        # Get the page as an image with the current zoom level
        zoom = self.app.zoom_factor
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        
        # Convert pixmap to PIL Image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # Convert PIL Image to ImageTk PhotoImage
        self.app.photo = ImageTk.PhotoImage(img)
        
        # Delete only the PDF image, not everything
        self.app.canvas.delete("pdf")
        self.app.canvas.delete("welcome_text")
        
        # Update canvas scroll region
        self.app.canvas.config(scrollregion=(0, 0, self.app.photo.width(), self.app.photo.height()))
        
        # Add the new PDF image (underneath any existing markers)
        self.app.canvas.create_image(0, 0, anchor="nw", image=self.app.photo, tags="pdf")
        
        # Check if there are saved markers for this page and load them
        if self.app.current_page in self.app.page_markers:
            page_marker_data = self.app.page_markers[self.app.current_page]
            self.app.column_markers = page_marker_data['columns']
            self.app.row_markers = page_marker_data['rows']
            
            # Delete existing page indicator before creating a new one
            self.app.canvas.delete("page_marked_indicator")
            
            # Show indicator that this page has saved markers
            self.app.canvas.create_text(
                10, 10,
                text="✓ Page Marked",
                font=("Arial", 10),
                fill="green",
                anchor="nw",
                tags="page_marked_indicator"
            )
        else:
            # Clear markers when moving to a page without saved markers
            self.app.column_markers = []
            self.app.row_markers = []
        
        # Check if there is manual data for this page
        if hasattr(self.app, 'manual_input_manager') and \
        self.app.current_page in self.app.manual_input_manager.all_pages_manual_data:
            # Delete existing indicator before creating a new one
            self.app.canvas.delete("page_data_stored_indicator")
            
            # Show indicator that this page has stored data
            self.app.canvas.create_text(
                self.app.canvas.winfo_width() - 10, 10,
                text="✓ Data Stored",
                font=("Arial", 10),
                fill="#FFD700",  # Gold color
                anchor="ne",
                tags="page_data_stored_indicator"
            )
        
        # Redraw column and row markers
        self.app.marker_manager.redraw_markers()
    
    def next_page(self):
        """
        Navigate to the next page in the PDF.
        """
        if not self.app.pdf_document or self.app.current_page >= self.app.total_pages - 1:
            return
            
        # Exit manual mode if active and store data
        if hasattr(self.app, 'manual_input_manager') and self.app.manual_input_manager.manual_mode_active:
            self.app.manual_input_manager.exit_manual_mode_and_store_data()
        
        # Ask if user wants to save markers before changing pages
        if self.app.column_markers and self.app.row_markers and self.app.current_page not in self.app.page_markers:
            if messagebox.askyesno(
                "Save Markers", 
                f"Do you want to save the markers for page {self.app.current_page + 1} before moving to the next page?"):
                self.app.marker_manager.save_page_markers()
        
        # Move to next page
        self.app.current_page += 1
        self.update_page_display()
    
    def prev_page(self):
        """
        Navigate to the previous page in the PDF.
        """
        if not self.app.pdf_document or self.app.current_page <= 0:
            return
            
        # Exit manual mode if active and store data
        if hasattr(self.app, 'manual_input_manager') and self.app.manual_input_manager.manual_mode_active:
            self.app.manual_input_manager.exit_manual_mode_and_store_data()
        
        # Ask if user wants to save markers before changing pages
        if self.app.column_markers and self.app.row_markers and self.app.current_page not in self.app.page_markers:
            if messagebox.askyesno(
                "Save Markers", 
                f"Do you want to save the markers for page {self.app.current_page + 1} before moving to the previous page?"):
                self.app.marker_manager.save_page_markers()
        
        # Move to previous page
        self.app.current_page -= 1
        self.update_page_display()
    
    def zoom_in(self):
        """
        Increase the zoom level and refresh the page display while preserving markers.
        """
        # Save current markers
        current_column_markers = self.app.column_markers.copy()
        current_row_markers = self.app.row_markers.copy()
        
        # Update zoom factor
        self.app.zoom_factor *= 1.2
        
        # Update the display
        self.update_page_display()
        
        # Restore markers
        self.app.column_markers = current_column_markers
        self.app.row_markers = current_row_markers
        
        # Redraw markers at new zoom level
        self.app.marker_manager.redraw_markers()

    def zoom_out(self):
        """
        Decrease the zoom level and refresh the page display while preserving markers.
        """
        # Save current markers
        current_column_markers = self.app.column_markers.copy()
        current_row_markers = self.app.row_markers.copy()
        
        # Update zoom factor
        self.app.zoom_factor /= 1.2
        if self.app.zoom_factor < 0.1:
            self.app.zoom_factor = 0.1
        
        # Update the display
        self.update_page_display()
        
        # Restore markers
        self.app.column_markers = current_column_markers
        self.app.row_markers = current_row_markers
        
        # Redraw markers at new zoom level
        self.app.marker_manager.redraw_markers()

    def reset_zoom(self):
        """
        Reset the zoom level to 100% and refresh the page display while preserving markers.
        """
        # Save current markers
        current_column_markers = self.app.column_markers.copy()
        current_row_markers = self.app.row_markers.copy()
        
        # Reset zoom factor
        self.app.zoom_factor = 1.0
        
        # Update the display
        self.update_page_display()
        
        # Restore markers
        self.app.column_markers = current_column_markers
        self.app.row_markers = current_row_markers
        
        # Redraw markers at new zoom level
        self.app.marker_manager.redraw_markers()