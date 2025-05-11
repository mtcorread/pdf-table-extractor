"""
Marker management functionality for the PDF Table Extractor.

This module provides the MarkerManager class, which is responsible for managing
row and column markers used to define table structures in PDF documents.
"""

from tkinter import messagebox

class MarkerManager:
    """
    Manages row and column markers for table extraction.
    
    This class handles the creation, storage, and visualization of markers that
    define table boundaries and cells within PDF documents.
    """
    
    def __init__(self, app):
        """
        Initialise the marker manager.
        
        Args:
            app: The PDFTableExtractorApp instance
        """
        self.app = app
    
    def redraw_markers(self):
        """
        Redraw all markers on the canvas.
        """
        # Clear existing lines and highlights
        self.app.canvas.delete("marker")
        self.app.canvas.delete("table_highlight")
        self.app.canvas.delete("intersection")
        self.app.canvas.delete("area_selection")
        
        # Get canvas dimensions
        if not self.app.pdf_document:
            return
            
        canvas_height = self.app.photo.height()
        canvas_width = self.app.photo.width()
        
        # Draw column markers (vertical lines)
        for x in self.app.column_markers:
            x_scaled = x * self.app.zoom_factor
            self.app.canvas.create_line(
                x_scaled, 0, x_scaled, canvas_height,
                fill="blue", width=2, tags="marker"
            )
        
        # Draw row markers (horizontal lines)
        for y in self.app.row_markers:
            y_scaled = y * self.app.zoom_factor
            self.app.canvas.create_line(
                0, y_scaled, canvas_width, y_scaled,
                fill="red", width=2, tags="marker"
            )
            
        # Draw intersection points to make it easier to see the grid
        for x in self.app.column_markers:
            for y in self.app.row_markers:
                x_scaled = x * self.app.zoom_factor
                y_scaled = y * self.app.zoom_factor
                self.app.canvas.create_oval(
                    x_scaled-4, y_scaled-4, x_scaled+4, y_scaled+4,
                    fill="purple", outline="white", tags="intersection"
                )
        
        # If we have at least 2 column and 2 row markers, highlight the table area
        if len(self.app.column_markers) >= 2 and len(self.app.row_markers) >= 2:
            min_x = min(self.app.column_markers)
            max_x = max(self.app.column_markers)
            min_y = min(self.app.row_markers)
            max_y = max(self.app.row_markers)
            self.highlight_table_area(min_x, min_y, max_x, max_y)
            
        # Draw area selection if exists
        if self.app.selection_start and self.app.selection_end:
            x1, y1 = self.app.selection_start
            x2, y2 = self.app.selection_end
            
            # Scale coordinates to account for zoom
            x1_scaled = x1 * self.app.zoom_factor
            y1_scaled = y1 * self.app.zoom_factor
            x2_scaled = x2 * self.app.zoom_factor
            y2_scaled = y2 * self.app.zoom_factor
            
            # Create rectangle for area selection
            self.app.canvas.create_rectangle(
                x1_scaled, y1_scaled, x2_scaled, y2_scaled,
                outline="yellow", width=2, dash=(5, 5), tags="area_selection"
            )
    
    def highlight_table_area(self, min_x, min_y, max_x, max_y):
        """
        Highlight the table area on the canvas based on the min/max coordinates.
        
        Args:
            min_x: The minimum x-coordinate
            min_y: The minimum y-coordinate
            max_x: The maximum x-coordinate
            max_y: The maximum y-coordinate
        """
        if not self.app.pdf_document:
            return
            
        # Scale coordinates based on current zoom
        min_x_scaled = min_x * self.app.zoom_factor
        min_y_scaled = min_y * self.app.zoom_factor
        max_x_scaled = max_x * self.app.zoom_factor
        max_y_scaled = max_y * self.app.zoom_factor
        
        # Create a semi-transparent rectangle representing the table area
        self.app.canvas.delete("table_highlight")
        
        # Draw table border
        self.app.canvas.create_rectangle(
            min_x_scaled, min_y_scaled, max_x_scaled, max_y_scaled,
            outline="green", width=3, tags="table_highlight"
        )
        
        # Count the actual cells (not the markers)
        col_count = len([m for m in self.app.column_markers if min_x < m < max_x]) + 1
        row_count = len([m for m in self.app.row_markers if min_y < m < max_y]) + 1
        
        self.app.canvas.create_text(
            min_x_scaled + 5,
            min_y_scaled - 10,
            text=f"Table: {row_count}x{col_count}",
            fill="green",
            anchor="sw",
            tags="table_highlight"
        )
    
    def save_page_markers(self):
        """
        Save the current column and row markers for the current page.
        """
        if not self.app.pdf_document:
            messagebox.showwarning("Warning", "Please load a PDF first")
            return
            
        if not self.app.column_markers or not self.app.row_markers:
            messagebox.showwarning("Warning", "Please set column and row markers first")
            return
        
        # Check if updating existing markers
        updating = self.app.current_page in self.app.page_markers
        
        # Store markers for the current page
        self.app.page_markers[self.app.current_page] = {
            'columns': self.app.column_markers.copy(),
            'rows': self.app.row_markers.copy()
        }
        
        # Update status
        marked_pages = len(self.app.page_markers)
        if updating:
            self.app.status_label.config(text=f"Updated markers for page {self.app.current_page + 1}. Total marked pages: {marked_pages}")
        else:
            self.app.status_label.config(text=f"Markers saved for page {self.app.current_page + 1}. Total marked pages: {marked_pages}")
            
        # Add visual indicator that the page is marked
        self.app.canvas.delete("page_marked_indicator")
        self.app.canvas.create_text(
            10, 10,
            text="✓ Page Marked",
            font=("Arial", 10),
            fill="green",
            anchor="nw",
            tags="page_marked_indicator"
        )
    
    def clear_page_markers(self):
        """
        Clear all stored page markers.
        """
        if not self.app.page_markers:
            messagebox.showinfo("Info", "No page markers to clear")
            return
            
        # Confirm with user
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all saved page markers?"):
            self.app.page_markers = {}
            self.app.status_label.config(text="All page markers cleared")
    
    def undo_last_marker(self):
        """
        Remove the last added marker.
        """
        if not self.app.marker_history:
            self.app.status_label.config(text="Nothing to undo")
            return
        
        # Get the last marker added
        last_marker = self.app.marker_history.pop()
        
        # Remove the marker based on type
        if last_marker['type'] == 'column':
            try:
                self.app.column_markers.remove(last_marker['value'])
                self.app.status_label.config(text=f"Removed column marker at x={last_marker['value']}")
            except ValueError:
                self.app.status_label.config(text="Could not remove marker (not found)")
        elif last_marker['type'] == 'row':
            try:
                self.app.row_markers.remove(last_marker['value'])
                self.app.status_label.config(text=f"Removed row marker at y={last_marker['value']}")
            except ValueError:
                self.app.status_label.config(text="Could not remove marker (not found)")
        
        # Redraw markers
        self.redraw_markers()
    
    def clear_lines(self):
        """
        Clear all column and row markers.
        """
        self.app.column_markers = []
        self.app.row_markers = []
        self.app.marker_history = []  # Clear the undo history as well
        self.app.selection_start = None
        self.app.selection_end = None
        self.redraw_markers()
        self.app.status_label.config(text="All lines cleared")
    
    def load_markers_for_current_page(self):
        """
        Load markers for the current page if they exist.
        """
        if self.app.current_page in self.app.page_markers:
            page_marker_data = self.app.page_markers[self.app.current_page]
            self.app.column_markers = page_marker_data['columns']
            self.app.row_markers = page_marker_data['rows']
            
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
    
    def reset_markers(self):
        """
        Reset all markers, including page markers.
        """
        self.app.column_markers = []
        self.app.row_markers = []
        self.app.marker_history = []
        self.app.page_markers = {}
        self.app.selection_start = None
        self.app.selection_end = None