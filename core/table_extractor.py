"""
Table extraction functionality for the PDF Table Extractor.

This module provides the TableExtractor class, which is responsible for extracting
table data from PDF documents based on row and column markers.
"""

import fitz  # PyMuPDF
import os
from tkinter import filedialog, messagebox
from gui.dialogs import create_multipage_options_dialog, create_progress_dialog, update_progress

class TableExtractor:
    """
    Extracts table data from PDF documents based on markers.
    
    This class contains methods for extracting tabular data from PDF pages using
    row and column markers, and exporting the extracted data to various formats.
    """
    
    def __init__(self, app):
        """
        Initialise the table extractor.
        
        Args:
            app: The PDFTableExtractorApp instance
        """
        self.app = app
    
    def extract_table(self):
        """
        Extract a table from the current page using the defined markers.
        """
        if not self.app.pdf_document or not self.app.column_markers or not self.app.row_markers:
            messagebox.showwarning("Warning", "Please load a PDF and set column and row markers first")
            return
        
        # Show extraction mode dialog every time
        self._show_extraction_mode_dialog()
        
        try:
            # Get the current page
            page = self.app.pdf_document[self.app.current_page]
            
            # Use the markers to define the table boundaries
            min_x = min(self.app.column_markers) if self.app.column_markers else 0
            max_x = max(self.app.column_markers) if self.app.column_markers else page.rect.width
            min_y = min(self.app.row_markers) if self.app.row_markers else 0
            max_y = max(self.app.row_markers) if self.app.row_markers else page.rect.height
            
            # Create a grid based on row and column markers
            # Sort the markers to ensure correct order
            sorted_col_markers = sorted(self.app.column_markers)
            sorted_row_markers = sorted(self.app.row_markers)
            
            # Define cell boundaries - we use ONLY the markers, not min/max or page boundaries
            col_bounds = sorted_col_markers  # We don't add min_x or max_x
            row_bounds = sorted_row_markers  # We don't add min_y or max_y
            
            # Number of columns and rows is the number of cells between markers
            cols = len(col_bounds) - 1 if len(col_bounds) > 1 else 1
            rows = len(row_bounds) - 1 if len(row_bounds) > 1 else 1
            
            # Initialize an empty grid for the table
            table = [['' for _ in range(cols)] for _ in range(rows)]
            
            # Get text from the page
            text_page = page.get_text("dict")
            
            # Draw the table outline for visual reference
            self.app.marker_manager.highlight_table_area(min_x, min_y, max_x, max_y)
            
            # Assign text blocks to appropriate cells
            for block in text_page["blocks"]:
                if block["type"] == 0:  # Type 0 is text
                    for line in block["lines"]:
                        for span in line["spans"]:
                            # Get text and its bounding box
                            text = span["text"]
                            text_rect = fitz.Rect(span["bbox"])
                            
                            # Find which cell this text belongs to (use the center point)
                            center_x = text_rect.x0 + (text_rect.x1 - text_rect.x0) / 2
                            center_y = text_rect.y0 + (text_rect.y1 - text_rect.y0) / 2
                            
                            # Check if the text is within our table boundaries
                            if not (min_x <= center_x <= max_x and min_y <= center_y <= max_y):
                                continue
                            
                            # Find column index
                            col_idx = -1
                            for i in range(len(col_bounds) - 1):
                                if col_bounds[i] <= center_x < col_bounds[i + 1]:
                                    col_idx = i
                                    break
                            
                            # Find row index
                            row_idx = -1
                            for i in range(len(row_bounds) - 1):
                                if row_bounds[i] <= center_y < row_bounds[i + 1]:
                                    row_idx = i
                                    break
                            
                            # Add text to the appropriate cell
                            if col_idx >= 0 and row_idx >= 0 and col_idx < cols and row_idx < rows:
                                if table[row_idx][col_idx]:
                                    table[row_idx][col_idx] += "\n" + text  # Use newline instead of space
                                else:
                                    table[row_idx][col_idx] = text
            
            # Store the extracted table data for later use (CSV or Excel export)
            self.app.table_data = table
            
            # Format table as CSV for display
            csv_data = ""
            for row in table:
                csv_data += ",".join(f'"{cell}"' if cell else "" for cell in row) + "\n"
            
            # Display in the text output area
            self.app.text_output.delete(1.0, "end")
            self.app.text_output.insert("end", csv_data)
            
            self.app.status_label.config(text=f"Table extracted successfully: {rows}x{cols} grid")
            
            # Check for text orientation issues
            if self._detect_orientation_issues(table):
                if messagebox.askyesno("Text Orientation Issue", 
                                    "Text appears to be incorrectly oriented. Want to apply correction?"):
                    self._correct_text_orientation(table)
                    
                    # Update display with corrected data
                    csv_data = ""
                    for row in self.app.table_data:
                        csv_data += ",".join(f'"{cell}"' if cell else "" for cell in row) + "\n"
                    
                    self.app.text_output.delete(1.0, "end")
                    self.app.text_output.insert("end", csv_data)
                    self.app.status_label.config(text=f"Table extracted with orientation correction: {rows}x{cols} grid")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to extract table: {str(e)}")
    
    def _detect_orientation_issues(self, table):
        """
        Detect if the extracted text has orientation issues.
        
        Args:
            table: The extracted table data
            
        Returns:
            bool: True if orientation issues are detected
        """
        # Flatten the table data for easier analysis
        all_text = []
        for row in table:
            for cell in row:
                if cell:
                    all_text.append(cell)
        
        # If no text, no issues to detect
        if not all_text:
            return False
        
        vertical_text_count = 0
        
        for cell in all_text:
            # Check for cells with newlines where most lines are short (1-2 chars)
            if '\n' in cell:
                lines = cell.split('\n')
                short_lines = [line for line in lines if len(line.strip()) <= 2 and len(line.strip()) > 0]
                if len(lines) >= 3 and len(short_lines) > len(lines) * 0.5:
                    vertical_text_count += 1
        
        # If more than 20% of non-empty cells have vertical text patterns, likely an issue
        return vertical_text_count > 0 and vertical_text_count / len(all_text) >= 0.2

    def _correct_text_orientation(self, table):
        """
        Correct text orientation issues in the table.
        
        Args:
            table: The extracted table data
        """
        # Make a backup of the original table
        original_table = [row[:] for row in table]
        
        # For each cell, correct vertical text
        for row_idx, row in enumerate(table):
            for col_idx, cell in enumerate(row):
                if not cell or len(cell.strip()) < 3:
                    continue
                
                # Check if this cell has vertical text (has newlines)
                if '\n' in cell:
                    # Split into lines and clean up
                    lines = [line.strip() for line in cell.split('\n') if line.strip()]
                    
                    if len(lines) < 2:
                        continue
                    
                    # For the specific pattern in your examples:
                    # 1. Reverse each segment (read right-to-left)
                    # 2. Reverse the order of segments (read bottom-to-top)
                    corrected_segments = []
                    for segment in reversed(lines):
                        corrected_segments.append(segment[::-1])
                    
                    # Join all segments
                    corrected_text = ''.join(corrected_segments)
                    
                    # Clean up any special characters
                    corrected_text = corrected_text.replace('\\n', '')
                    
                    # Update the cell with corrected text
                    self.app.table_data[row_idx][col_idx] = corrected_text
    
    def force_text_orientation_correction(self):
        """
        Force text orientation correction regardless of detection results.
        """
        if not hasattr(self.app, 'table_data') or not self.app.table_data:
            messagebox.showwarning("Warning", "No table data to correct. Please extract a table first.")
            return
            
        try:
            # Apply correction directly without detection
            self._correct_text_orientation(self.app.table_data)
            
            # Update display with corrected data
            csv_data = ""
            for row in self.app.table_data:
                csv_data += ",".join(f'"{cell}"' if cell else "" for cell in row) + "\n"
            
            self.app.text_output.delete(1.0, "end")
            self.app.text_output.insert("end", csv_data)
            self.app.status_label.config(text="Forced text orientation correction applied")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to correct text orientation: {str(e)}")
    
    def transpose_table(self):
        """
        Transpose the table data (swap rows and columns).
        """
        if not hasattr(self.app, 'table_data') or not self.app.table_data:
            messagebox.showwarning("Warning", "No table data to transpose. Please extract a table first.")
            return
            
        try:
            # Get the dimensions of the current table
            rows = len(self.app.table_data)
            cols = max(len(row) for row in self.app.table_data) if self.app.table_data else 0
            
            if rows == 0 or cols == 0:
                messagebox.showwarning("Warning", "Cannot transpose an empty table.")
                return
            
            # Create a new transposed table (ensure all rows have the same length)
            padded_table = [row + [''] * (cols - len(row)) for row in self.app.table_data]
            transposed = list(map(list, zip(*padded_table)))
            
            # Update the table data
            self.app.table_data = transposed
            
            # Format table as CSV for display
            csv_data = ""
            for row in transposed:
                csv_data += ",".join(f'"{cell}"' if cell else "" for cell in row) + "\n"
            
            # Display in the text output area
            self.app.text_output.delete(1.0, "end")
            self.app.text_output.insert("end", csv_data)
            
            self.app.status_label.config(text=f"Table transposed: {cols}x{rows} grid")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to transpose table: {str(e)}")
    
    def save_extracted_text(self, format_type='csv'):
        """
        Save the extracted table data as CSV or Excel.
        
        Args:
            format_type: The file format to save as ('csv' or 'excel')
        """
        if not hasattr(self.app, 'table_data') or not self.app.table_data:
            messagebox.showwarning("Warning", "No extracted table data to save")
            return
        
        if format_type == 'csv':
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("Text files", "*.txt"), ("All files", "*.*")],
                title="Save as CSV")
            
            if file_path:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        for row in self.app.table_data:
                            f.write(",".join(f'"{cell}"' if cell else "" for cell in row) + "\n")
                    self.app.status_label.config(text=f"Saved to CSV: {os.path.basename(file_path)}")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save CSV file: {str(e)}")
        
        elif format_type == 'excel':
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                title="Save as Excel")
            
            if file_path:
                try:
                    # Check if pandas and openpyxl are available
                    try:
                        import pandas as pd
                        import openpyxl
                    except ImportError as e:
                        if "pandas" in str(e):
                            messagebox.showerror("Error", "The pandas package is required for Excel export. \n\nPlease run: pip install pandas openpyxl")
                            return
                        elif "openpyxl" in str(e):
                            messagebox.showerror("Error", "The openpyxl package is required for Excel export. \n\nPlease run: pip install openpyxl")
                            return
                        else:
                            raise e
                    
                    # Convert table data to pandas DataFrame
                    df = pd.DataFrame(self.app.table_data)
                    
                    # Write DataFrame to Excel
                    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                        df.to_excel(writer, sheet_name='Extracted Table', index=False, header=False)
                    
                    self.app.status_label.config(text=f"Saved to Excel: {os.path.basename(file_path)}")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save Excel file: {str(e)}")
    
    def extract_from_marked_pages(self):
        """
        Extract tables from all marked pages and combine them.
        """
        if not self.app.pdf_document:
            messagebox.showwarning("Warning", "Please load a PDF first")
            return
            
        if not self.app.page_markers:
            messagebox.showwarning("Warning", "No pages have been marked. Use 'Mark Current Page' to save markers for each page.")
            return
        
        # Always show extraction mode dialog
        self._show_extraction_mode_dialog()
        
        # Then ask for merge and transpose options
        options = create_multipage_options_dialog(self.app)
        if not options:
            return  # User cancelled
            
        # Get the selected options
        merge_mode = options['merge_mode']
        do_transpose = options['transpose']
        
        # Remember current page and markers to restore later
        original_page = self.app.current_page
        original_column_markers = self.app.column_markers.copy()
        original_row_markers = self.app.row_markers.copy()
        
        try:
            # Create progress window
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
                
                # Load this page's markers
                page_marker_data = self.app.page_markers[page_idx]
                self.app.column_markers = page_marker_data['columns']
                self.app.row_markers = page_marker_data['rows']
                
                # Navigate to this page
                self.app.current_page = page_idx
                self.app.pdf_handler.update_page_display()
                
                # Extract table from this page (already uses the selected extraction mode)
                page_table = self._extract_table_data(page_idx)
                if page_table:
                    all_tables.append(page_table)
            
            # Close progress window
            progress_window.destroy()
            
            if not all_tables:
                messagebox.showwarning("Warning", "No tables could be extracted from the marked pages.")
                return
            
            # Merge the tables based on the selected mode
            if merge_mode == "vertical":
                merged_table = self.merge_tables_vertically(all_tables)
            else:  # horizontal
                merged_table = self.merge_tables_horizontally(all_tables)
            
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
            
            self.app.status_label.config(text=f"Extracted {rows}x{cols} table from pages: {page_range}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to extract from marked pages: {str(e)}")
        finally:
            # Restore original page and markers
            self.app.current_page = original_page
            self.app.column_markers = original_column_markers
            self.app.row_markers = original_row_markers
            self.app.pdf_handler.update_page_display()
    
    def _extract_table_data(self, page_index):
        """
        Extract table data from a specific page without updating the UI.
        
        Args:
            page_index: The index of the page to extract from
            
        Returns:
            list: The extracted table data as a 2D list, or None if extraction failed
        """
        try:
            # Get the page
            page = self.app.pdf_document[page_index]
            
            # Use the markers to define the table boundaries
            min_x = min(self.app.column_markers) if self.app.column_markers else 0
            max_x = max(self.app.column_markers) if self.app.column_markers else page.rect.width
            min_y = min(self.app.row_markers) if self.app.row_markers else 0
            max_y = max(self.app.row_markers) if self.app.row_markers else page.rect.height
            
            # Create a grid based on row and column markers
            sorted_col_markers = sorted(self.app.column_markers)
            sorted_row_markers = sorted(self.app.row_markers)
            
            # Define cell boundaries
            col_bounds = sorted_col_markers
            row_bounds = sorted_row_markers
            
            # Number of columns and rows
            cols = len(col_bounds) - 1 if len(col_bounds) > 1 else 1
            rows = len(row_bounds) - 1 if len(row_bounds) > 1 else 1
            
            # Initialize an empty grid for the table
            table = [['' for _ in range(cols)] for _ in range(rows)]
            
            # Get text from the page
            text_page = page.get_text("dict")
            
            # Assign text blocks to appropriate cells
            for block in text_page["blocks"]:
                if block["type"] == 0:  # Type 0 is text
                    for line in block["lines"]:
                        for span in line["spans"]:
                            # Get text and its bounding box
                            text = span["text"]
                            text_rect = fitz.Rect(span["bbox"])
                            
                            # Find which cell this text belongs to (use the center point)
                            center_x = text_rect.x0 + (text_rect.x1 - text_rect.x0) / 2
                            center_y = text_rect.y0 + (text_rect.y1 - text_rect.y0) / 2
                            
                            # Check if the text is within our table boundaries
                            if not (min_x <= center_x <= max_x and min_y <= center_y <= max_y):
                                continue
                            
                            # Find column index
                            col_idx = -1
                            for i in range(len(col_bounds) - 1):
                                if col_bounds[i] <= center_x < col_bounds[i + 1]:
                                    col_idx = i
                                    break
                            
                            # Find row index
                            row_idx = -1
                            for i in range(len(row_bounds) - 1):
                                if row_bounds[i] <= center_y < row_bounds[i + 1]:
                                    row_idx = i
                                    break
                            
                            # Add text to the appropriate cell
                            if col_idx >= 0 and row_idx >= 0 and col_idx < cols and row_idx < rows:
                                if table[row_idx][col_idx]:
                                    if self.extraction_mode == "space":
                                        table[row_idx][col_idx] += " " + text
                                    elif self.extraction_mode == "newline":
                                        table[row_idx][col_idx] += "\n" + text
                                else:
                                    table[row_idx][col_idx] = text
            
            return table
        except Exception as e:
            print(f"Error extracting table from page {page_index + 1}: {str(e)}")
            return None

    def _show_extraction_mode_dialog(self):
        """
        Show a dialog to select the extraction mode for text.
        """
        from tkinter import Toplevel, Label, Button, StringVar, Radiobutton, Frame
        
        # Default to space mode
        self.extraction_mode = "space"
        
        # Create dialog window
        options_dialog = Toplevel(self.app.root)
        options_dialog.title("Choose Extraction Mode")
        options_dialog.geometry("500x350")  # Significantly larger size
        options_dialog.minsize(500, 350)    # Set minimum size to prevent resizing issues
        options_dialog.transient(self.app.root)
        options_dialog.grab_set()
        
        # Main container with padding
        main_container = Frame(options_dialog, padx=20, pady=20)
        main_container.pack(fill="both", expand=True)
        
        # Top section for title and description
        top_section = Frame(main_container)
        top_section.pack(fill="x", pady=(0, 20))
        
        # Title
        Label(top_section, text="Which mode of text extraction do you want to use?", 
            font=("bold")).pack(anchor="w", pady=(0, 15))
        
        # Middle section for radio buttons
        radio_section = Frame(main_container)
        radio_section.pack(fill="x", pady=10)
        
        # Mode selection
        mode_var = StringVar(value="space")
        
        # Mode 1
        mode1_frame = Frame(radio_section)
        mode1_frame.pack(fill="x", pady=10)
        
        Radiobutton(mode1_frame, text="Mode 1 (Spaces)", 
                variable=mode_var, value="space").pack(side="left")
        Label(mode1_frame, text="- Better for normal text").pack(side="left", padx=(10, 0))
        
        # Mode 2
        mode2_frame = Frame(radio_section)
        mode2_frame.pack(fill="x", pady=10)
        
        Radiobutton(mode2_frame, text="Mode 2 (Newlines)", 
                variable=mode_var, value="newline").pack(side="left")
        Label(mode2_frame, text="- Better for detecting orientation issues").pack(side="left", padx=(10, 0))
        
        # Explicitly create a frame at the bottom with fixed height
        bottom_container = Frame(options_dialog, height=80)
        bottom_container.pack(side="bottom", fill="x")
        bottom_container.pack_propagate(False)  # Force the height
        
        # Button frame centered within the bottom container
        button_frame = Frame(bottom_container)
        button_frame.pack(expand=True, pady=20)
        
        # Function to set the mode and close dialog
        def set_mode():
            self.extraction_mode = mode_var.get()
            options_dialog.destroy()
        
        # Large, clearly visible OK button
        ok_btn = Button(button_frame, text="OK", command=set_mode, width=15, height=2)
        ok_btn.pack()
        
        # Center the dialog on the screen
        options_dialog.update_idletasks()
        width = options_dialog.winfo_width()
        height = options_dialog.winfo_height()
        x = (options_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (options_dialog.winfo_screenheight() // 2) - (height // 2)
        options_dialog.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        
        # Wait for user selection
        self.app.root.wait_window(options_dialog)
    
    def merge_tables_vertically(self, tables):
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
    
    def merge_tables_horizontally(self, tables):
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