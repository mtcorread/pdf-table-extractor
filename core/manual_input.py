"""
Manual input functionality for the PDF Table Extractor.

This module provides the ManualInputManager class, which enables manual entry
of table cell contents when automatic extraction fails or produces poor results.
"""

import tkinter as tk
from tkinter import ttk, messagebox

class ManualInputManager:
    """
    Manages manual input of table cell contents.
    
    This class provides a manual cell-by-cell input mode that assists users in
    filling tables where automatic text extraction may not be reliable.
    """
    
    def __init__(self, app):
        """
        Initialise the manual input manager.
        
        Args:
            app: The PDFTableExtractorApp instance
        """
        self.app = app
        self.manual_mode_active = False
        self.current_cell = (0, 0)  # (row, column)
        self.manual_table_data = None
        self.cell_coordinates = None  # Will store bounding boxes for cells
        self.input_frame = None
        self.cell_text_entry = None
        self.cell_info_label = None
        self.highlighted_cell_id = None
        
        # Add storage for per-page manual data
        self.all_pages_manual_data = {}  # Dict to store data by page index
        
    def toggle_manual_mode(self):
        """
        Toggle manual input mode on or off.
        """
        if not self.app.pdf_document:
            messagebox.showwarning("Warning", "Please load a PDF first")
            return
                
        if not self.app.column_markers or not self.app.row_markers:
            messagebox.showwarning("Warning", "Please define table structure with column and row markers first")
            return
        
        # Toggle the mode
        self.manual_mode_active = not self.manual_mode_active
        
        if self.manual_mode_active:
            # Start manual input mode
            self._initialize_manual_input()
            
            # Bind canvas click event for cell selection
            self.app.canvas.bind("<Button-1>", self._on_canvas_click)
            
            # Store the original selection mode to restore later
            self.original_selection_mode = self.app.selection_mode
        else:
            # Save the current page data before exiting
            if self.manual_table_data:
                self._save_current_cell_content()  # Save any pending cell edits
                self.all_pages_manual_data[self.app.current_page] = [row[:] for row in self.manual_table_data]  # Make a deep copy
            
            # Exit manual input mode
            self._cleanup_manual_input()
    
    def _on_canvas_click(self, event):
        """
        Handle mouse click events in manual mode to select a cell.
        """
        if not self.manual_mode_active or not self.cell_coordinates:
            return
        
        # Get the position in the document (accounting for zoom and scroll)
        x = int(self.app.canvas.canvasx(event.x) / self.app.zoom_factor)
        y = int(self.app.canvas.canvasy(event.y) / self.app.zoom_factor)
        
        # Find which cell was clicked
        for row in range(len(self.cell_coordinates)):
            for col in range(len(self.cell_coordinates[0])):
                left, top, right, bottom = self.cell_coordinates[row][col]
                
                if left <= x <= right and top <= y <= bottom:
                    # Save current cell content before changing cells
                    self._save_current_cell_content()
                    
                    # Update current cell and highlight
                    self.current_cell = (row, col)
                    self._highlight_current_cell()
                    
                    # Update status to indicate the selected cell
                    self.app.status_label.config(text=f"Selected cell: ({row + 1}, {col + 1})")
                    return
    
    def _initialize_manual_input(self):
        """
        Initialize the manual input interface.
        """
        # Make sure we have a proper grid defined
        sorted_col_markers = sorted(self.app.column_markers)
        sorted_row_markers = sorted(self.app.row_markers)
        
        if len(sorted_col_markers) < 2 or len(sorted_row_markers) < 2:
            messagebox.showwarning("Warning", "Please define at least two column and two row markers")
            self.manual_mode_active = False
            return
        
        # Calculate table dimensions
        rows = len(sorted_row_markers) - 1
        cols = len(sorted_col_markers) - 1
        
        # Check if we have existing data for this page
        current_page = self.app.current_page
        if current_page in self.all_pages_manual_data:
            # Use existing data if dimensions match
            existing_data = self.all_pages_manual_data[current_page]
            if len(existing_data) == rows and len(existing_data[0]) == cols:
                self.manual_table_data = existing_data
            else:
                # Dimensions don't match, create new data but keep old for reference
                self.manual_table_data = [['' for _ in range(cols)] for _ in range(rows)]
        else:
            # Initialize or reset the manual table data if not found
            self.manual_table_data = [['' for _ in range(cols)] for _ in range(rows)]
                
        # Calculate cell coordinates in PDF space
        self.cell_coordinates = []
        for r in range(rows):
            row_coords = []
            for c in range(cols):
                # Get bounding box for this cell (left, top, right, bottom)
                left = sorted_col_markers[c]
                top = sorted_row_markers[r]
                right = sorted_col_markers[c + 1]
                bottom = sorted_row_markers[r + 1]
                row_coords.append((left, top, right, bottom))
            self.cell_coordinates.append(row_coords)
        
        # Set the first cell as the current one
        self.current_cell = (0, 0)
        
        # Create the manual input interface (if not already created)
        self._create_input_interface()
        
        # Highlight the first cell and update the input interface
        self._highlight_current_cell()
        
        # Update status
        self.app.status_label.config(text=f"Manual input mode active - {rows}x{cols} table")
    
    def _create_input_interface(self):
        """
        Create the manual input interface at the bottom of the main window.
        """
        # Create frame for input elements if it doesn't exist
        if self.input_frame is None:
            self.input_frame = tk.Frame(self.app.root, bd=2, relief=tk.RAISED)
            self.input_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
            
            # Create interface elements
            control_frame = tk.Frame(self.input_frame)
            control_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
            
            # Navigation buttons frame
            nav_frame = tk.Frame(control_frame)
            nav_frame.pack(side=tk.LEFT, fill=tk.Y)
            
            # Navigation buttons
            prev_btn = tk.Button(nav_frame, text="Previous Cell", command=self._go_to_previous_cell)
            prev_btn.pack(side=tk.LEFT, padx=5)
            
            next_btn = tk.Button(nav_frame, text="Next Cell", command=self._go_to_next_cell)
            next_btn.pack(side=tk.LEFT, padx=5)
            
            # Cell info label
            self.cell_info_label = tk.Label(control_frame, text="Cell: (1, 1)", font=("Arial", 10))
            self.cell_info_label.pack(side=tk.LEFT, padx=10)
            
            # Store current page button
            store_btn = tk.Button(control_frame, text="Store Page Values", 
                                command=self._store_current_page_values,
                                bg="#FFD700")  # Gold color
            store_btn.pack(side=tk.LEFT, padx=10)
            
            # Multi-page options frame
            multi_page_frame = tk.Frame(control_frame)
            multi_page_frame.pack(side=tk.LEFT, padx=10)
            
            # Add multi-page extraction button
            multi_page_btn = tk.Button(multi_page_frame, text="Extract All Marked Pages", 
                                     command=self.extract_all_marked_pages,
                                     bg="#FFF8DC")
            multi_page_btn.pack(side=tk.LEFT, padx=5)
            
            # Done button (right aligned)
            done_frame = tk.Frame(control_frame)
            done_frame.pack(side=tk.RIGHT)
            
            done_btn = tk.Button(done_frame, text="Save & Exit Manual Mode", 
                               command=self._complete_manual_entry, bg="lightgreen")
            done_btn.pack(side=tk.RIGHT, padx=5)
            
            # Text entry frame
            entry_frame = tk.Frame(self.input_frame)
            entry_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
            
            # Label
            tk.Label(entry_frame, text="Cell Content:").pack(side=tk.LEFT, padx=5)
            
            # Cell content entry
            self.cell_text_entry = ttk.Entry(entry_frame, width=50)
            self.cell_text_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            
            # Bind Return key to move to next cell
            self.cell_text_entry.bind("<Return>", lambda e: self._save_and_advance())
            # Bind arrow keys for navigation
            self.cell_text_entry.bind("<Up>", lambda e: self._go_to_cell(self.current_cell[0]-1, self.current_cell[1]))
            self.cell_text_entry.bind("<Down>", lambda e: self._go_to_cell(self.current_cell[0]+1, self.current_cell[1]))
            self.cell_text_entry.bind("<Left>", lambda e: self._go_to_cell(self.current_cell[0], self.current_cell[1]-1))
            self.cell_text_entry.bind("<Right>", lambda e: self._go_to_cell(self.current_cell[0], self.current_cell[1]+1))
            
            # Focus on the entry
            self.cell_text_entry.focus_set()
    
    def _go_to_cell(self, row, col):
        """
        Navigate to a specific cell, ensuring boundaries are respected.
        """
        if not self.manual_mode_active:
            return
        
        # Save current cell content
        self._save_current_cell_content()
        
        # Get table dimensions
        rows = len(self.manual_table_data)
        cols = len(self.manual_table_data[0]) if rows > 0 else 0
        
        # Ensure row and column are within bounds
        row = max(0, min(row, rows-1))
        col = max(0, min(col, cols-1))
        
        # Update current cell and highlight
        self.current_cell = (row, col)
        self._highlight_current_cell()
        
        # Return 'break' to prevent default key behavior
        return 'break'

    def _cleanup_manual_input(self):
        """
        Clean up the manual input interface when exiting manual mode.
        """
        if self.input_frame:
            self.input_frame.destroy()
            self.input_frame = None
            self.cell_text_entry = None
            self.cell_info_label = None
        
        # Remove cell highlight
        if self.highlighted_cell_id:
            self.app.canvas.delete(self.highlighted_cell_id)
            self.highlighted_cell_id = None
        
        # Unbind canvas click event for manual input
        self.app.canvas.unbind("<Button-1>")
        
        # Restore the original canvas click handler based on the current selection mode
        # This ensures table drawing continues to work after exiting manual mode
        if hasattr(self.app, 'canvas'):
            from gui.main_area import _on_canvas_click
            self.app.canvas.bind("<Button-1>", lambda e: _on_canvas_click(self.app, e))
        
        # Update status
        self.app.status_label.config(text="Manual input mode deactivated")
    
    def _highlight_current_cell(self):
        """
        Highlight the current cell on the canvas.
        """
        if not self.manual_mode_active or not self.cell_coordinates:
            return
        
        # Clear previous highlight
        if self.highlighted_cell_id:
            self.app.canvas.delete(self.highlighted_cell_id)
        
        # Get current cell coordinates
        row, col = self.current_cell
        if (0 <= row < len(self.cell_coordinates) and 
            0 <= col < len(self.cell_coordinates[0])):
            
            left, top, right, bottom = self.cell_coordinates[row][col]
            
            # Scale for zoom
            left_scaled = left * self.app.zoom_factor
            top_scaled = top * self.app.zoom_factor
            right_scaled = right * self.app.zoom_factor
            bottom_scaled = bottom * self.app.zoom_factor
            
            # Draw highlight rectangle
            self.highlighted_cell_id = self.app.canvas.create_rectangle(
                left_scaled, top_scaled, right_scaled, bottom_scaled,
                outline="yellow", width=3, dash=(5, 5), tags="manual_highlight"
            )
            
            # Ensure the cell is visible by scrolling if needed
            # Calculate the center of the cell
            center_x = (left_scaled + right_scaled) / 2
            center_y = (top_scaled + bottom_scaled) / 2
            
            # Get current visible area
            canvas_width = self.app.canvas.winfo_width()
            canvas_height = self.app.canvas.winfo_height()
            visible_left = self.app.canvas.canvasx(0)
            visible_top = self.app.canvas.canvasy(0)
            visible_right = visible_left + canvas_width
            visible_bottom = visible_top + canvas_height
            
            # Check if cell is outside visible area
            x_offset = 0
            y_offset = 0
            
            # If cell is to the right of visible area
            if right_scaled > visible_right:
                x_offset = right_scaled - visible_right + 20  # Add some padding
            # If cell is to the left of visible area
            elif left_scaled < visible_left:
                x_offset = left_scaled - visible_left - 20  # Add some padding
                
            # If cell is below visible area
            if bottom_scaled > visible_bottom:
                y_offset = bottom_scaled - visible_bottom + 20  # Add some padding
            # If cell is above visible area
            elif top_scaled < visible_top:
                y_offset = top_scaled - visible_top - 20  # Add some padding
                
            # Scroll if needed
            if x_offset != 0 or y_offset != 0:
                self.app.canvas.xview_scroll(int(x_offset / 10), "units")
                self.app.canvas.yview_scroll(int(y_offset / 10), "units")
            
            # Update cell info label
            self.cell_info_label.config(text=f"Cell: ({row + 1}, {col + 1})")
            
            # Load existing cell content into the text entry if available
            if 0 <= row < len(self.manual_table_data) and 0 <= col < len(self.manual_table_data[0]):
                content = self.manual_table_data[row][col]
                self.cell_text_entry.delete(0, tk.END)
                self.cell_text_entry.insert(0, content)
                
            # Focus on the text entry
            self.cell_text_entry.focus_set()
    
    def _save_current_cell_content(self):
        """
        Save the current text entry content to the cell data.
        """
        if not self.manual_mode_active or self.cell_text_entry is None:
            return
        
        row, col = self.current_cell
        if (0 <= row < len(self.manual_table_data) and 
            0 <= col < len(self.manual_table_data[0])):
            
            # Get content from text entry
            content = self.cell_text_entry.get()
            
            # Save to manual table data
            self.manual_table_data[row][col] = content
    
    def _go_to_next_cell(self):
        """
        Navigate to the next cell in the table.
        """
        if not self.manual_mode_active:
            return
        
        # Save current cell content
        self._save_current_cell_content()
        
        row, col = self.current_cell
        cols = len(self.manual_table_data[0]) if self.manual_table_data else 0
        rows = len(self.manual_table_data) if self.manual_table_data else 0
        
        # Move to next cell (right or down to next row)
        col += 1
        if col >= cols:
            col = 0
            row += 1
            
        # Check if we've gone past the end
        if row >= rows:
            # Optionally, wrap around to the beginning
            row = 0
        
        # Update current cell and highlight
        self.current_cell = (row, col)
        self._highlight_current_cell()
    
    def _go_to_previous_cell(self):
        """
        Navigate to the previous cell in the table.
        """
        if not self.manual_mode_active:
            return
        
        # Save current cell content
        self._save_current_cell_content()
        
        row, col = self.current_cell
        cols = len(self.manual_table_data[0]) if self.manual_table_data else 0
        rows = len(self.manual_table_data) if self.manual_table_data else 0
        
        # Move to previous cell (left or up to previous row)
        col -= 1
        if col < 0:
            col = cols - 1
            row -= 1
            
        # Check if we've gone past the beginning
        if row < 0:
            # Optionally, wrap around to the end
            row = rows - 1
        
        # Update current cell and highlight
        self.current_cell = (row, col)
        self._highlight_current_cell()
    
    def _save_and_advance(self):
        """
        Save the current cell content and advance to the next cell.
        Called when user presses Enter in the text entry.
        """
        self._save_current_cell_content()
        self._go_to_next_cell()
        
    def _store_current_page_values(self):
        """
        Store the current page's manual input values without exiting manual mode.
        """
        if not self.manual_mode_active:
            return
            
        # Save current cell content
        self._save_current_cell_content()
        
        # Store the manual table data for the current page
        self.all_pages_manual_data[self.app.current_page] = [row[:] for row in self.manual_table_data]  # Make a deep copy
        
        # Update status
        rows = len(self.manual_table_data)
        cols = len(self.manual_table_data[0]) if self.manual_table_data else 0
        self.app.status_label.config(text=f"Stored {rows}x{cols} table for page {self.app.current_page + 1}")
        
        # Add visual indicator that the page data is stored
        self._update_data_stored_indicator()
        
    def _update_data_stored_indicator(self):
        """
        Add visual indicator that the page data is stored.
        """
        self.app.canvas.delete("page_data_stored_indicator")
        self.app.canvas.create_text(
            self.app.canvas.winfo_width() - 10, 10,
            text="✓ Data Stored",
            font=("Arial", 10),
            fill="#FFD700",  # Gold color
            anchor="ne",
            tags="page_data_stored_indicator"
        )
    
    def exit_manual_mode_and_store_data(self):
        """
        Exit manual input mode while saving current data.
        """
        if not self.manual_mode_active:
            return
            
        # Save current cell content
        self._save_current_cell_content()
        
        # Store the data for the current page
        if self.manual_table_data:
            self.all_pages_manual_data[self.app.current_page] = [row[:] for row in self.manual_table_data]
            
        # Exit manual mode
        self.manual_mode_active = False
        self._cleanup_manual_input()
        
        # Update status
        self.app.status_label.config(text="Manual input mode deactivated and data stored")
    
    def _complete_manual_entry(self):
        """
        Finish manual entry and set the data as the current table data.
        """
        if not self.manual_mode_active:
            return
        
        # Save current cell content
        self._save_current_cell_content()
        
        # Store the current page's data in all_pages_manual_data
        self.all_pages_manual_data[self.app.current_page] = [row[:] for row in self.manual_table_data]
        
        # Set as the current table data in the main app
        self.app.table_data = self.manual_table_data
        
        # Format table as CSV for display
        csv_data = ""
        for row in self.manual_table_data:
            csv_data += ",".join(f'"{cell}"' if cell else "" for cell in row) + "\n"
        
        # Display in the text output area
        self.app.text_output.delete(1.0, "end")
        self.app.text_output.insert("end", csv_data)
        
        # Exit manual mode
        self.manual_mode_active = False
        self._cleanup_manual_input()
        
        # Update status
        rows = len(self.manual_table_data)
        cols = len(self.manual_table_data[0]) if self.manual_table_data else 0
        self.app.status_label.config(text=f"Manual table entry complete: {rows}x{cols} table")

    def extract_all_marked_pages(self):
        """
        Extract tables from all marked pages and combine them using the manual input data.
        This works similarly to the table_extractor's extract_from_marked_pages method
        but preserves any manual input data for the current page.
        """
        if not self.app.pdf_document:
            messagebox.showwarning("Warning", "Please load a PDF first")
            return
            
        if not self.app.page_markers:
            messagebox.showwarning("Warning", "No pages have been marked. Use 'Mark Current Page' to save markers for each page.")
            return
        
        # First save the current cell content and save current page's data
        self._save_current_cell_content()
        
        # Store the current page's manual data if it exists
        current_page = self.app.current_page
        if hasattr(self, 'manual_table_data') and self.manual_table_data:
            # Save current page data
            self.all_pages_manual_data[current_page] = self.manual_table_data
        
        # Ask for merge options using a dialog similar to the one in table_extractor
        from gui.dialogs import create_multipage_options_dialog
        options = create_multipage_options_dialog(self.app)
        if not options:
            return  # User cancelled
            
        # Get the selected options
        merge_mode = options['merge_mode']
        do_transpose = options['transpose']
        
        try:
            # Create progress window
            from gui.dialogs import create_progress_dialog, update_progress
            progress_window, progress_label, progress_bar = create_progress_dialog(
                self.app, 
                "Extracting tables...", 
                "Extracting tables from marked pages..."
            )
            
            # Calculate total pages
            total_pages = len(self.app.page_markers)
            
            progress_window.update()
            
            # Extract tables from each marked page
            all_tables = []
            marked_pages = sorted(self.app.page_markers.keys())
            
            for i, page_idx in enumerate(marked_pages):
                # Update progress
                progress_ratio = (i + 1) / total_pages
                update_progress(
                    progress_bar, 
                    progress_label,
                    f"Extracting page {page_idx + 1} ({i + 1}/{len(marked_pages)})...",
                    progress_ratio
                )
                
                # Check if we have manual data for this page
                if page_idx in self.all_pages_manual_data:
                    # Use the manual data we've already collected
                    page_table = self.all_pages_manual_data[page_idx]
                    all_tables.append(page_table)
                else:
                    # Load this page's markers
                    page_marker_data = self.app.page_markers[page_idx]
                    
                    # Create empty table data for this page based on its markers
                    sorted_col_markers = sorted(page_marker_data['columns'])
                    sorted_row_markers = sorted(page_marker_data['rows'])
                    
                    # Number of columns and rows is the number of cells between markers
                    cols = len(sorted_col_markers) - 1 if len(sorted_col_markers) > 1 else 1
                    rows = len(sorted_row_markers) - 1 if len(sorted_row_markers) > 1 else 1
                    
                    # Create an empty table
                    empty_table = [['' for _ in range(cols)] for _ in range(rows)]
                    all_tables.append(empty_table)
            
            # Close progress window
            progress_window.destroy()
                        
            if not all_tables:
                messagebox.showwarning("Warning", "No tables could be extracted from the marked pages.")
                return
            
            # Merge the tables based on the selected mode
            if merge_mode == "vertical":
                merged_table = self.app.table_extractor.merge_tables_vertically(all_tables)
            else:  # horizontal
                merged_table = self.app.table_extractor.merge_tables_horizontally(all_tables)
            
            # Transpose if requested
            if do_transpose:
                # Create a padded table to ensure all rows have the same length
                max_cols = max(len(row) for row in merged_table)
                padded_table = [row + [''] * (max_cols - len(row)) for row in merged_table]
                merged_table = list(map(list, zip(*padded_table)))
            
            # Set as the current table data
            self.app.table_data = merged_table
            
            # Format table as CSV for display
            csv_data = ""
            for row in merged_table:
                csv_data += ",".join(f'"{cell}"' if cell else "" for cell in row) + "\n"
            
            # Display in the text output area
            self.app.text_output.delete(1.0, "end")
            self.app.text_output.insert("end", csv_data)
            
            rows = len(merged_table)
            cols = max(len(row) for row in merged_table) if merged_table else 0
            page_range = ", ".join(str(p + 1) for p in marked_pages)
            
            # Update status
            self.app.status_label.config(text=f"Extracted {rows}x{cols} table from pages: {page_range}")
            
            # Exit manual mode
            self.manual_mode_active = False
            self._cleanup_manual_input()
            
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            messagebox.showerror("Error", f"Failed to extract from marked pages: {str(e)}")
            
    def _merge_tables_vertically(self, tables):
        """
        Merge multiple tables by stacking them vertically.
        
        Args:
            tables: A list of table data (each table is a 2D list)
            
        Returns:
            list: The merged table data
        """
        if not tables:
            return []
            
        merged = []
        for table in tables:
            merged.extend(table)
        return merged
    
    def _merge_tables_horizontally(self, tables):
        """
        Merge multiple tables by appending them horizontally.
        
        Args:
            tables: A list of table data (each table is a 2D list)
            
        Returns:
            list: The merged table data
        """
        if not tables:
            return []
        
        # Find the maximum row count across all tables
        max_rows = max(len(table) for table in tables)
        
        # Pad tables to have the same number of rows
        padded_tables = []
        for table in tables:
            # Ensure all rows in the table have the same length
            cols = max(len(row) for row in table) if table else 0
            padded_table = [row + [''] * (cols - len(row)) for row in table]
            
            # Pad the table to have max_rows rows
            padded_table.extend([[''] * cols for _ in range(max_rows - len(padded_table))])
            padded_tables.append(padded_table)
        
        # Merge the padded tables horizontally
        merged = []
        for row_idx in range(max_rows):
            merged_row = []
            for table in padded_tables:
                merged_row.extend(table[row_idx])
            merged.append(merged_row)
        
        return merged