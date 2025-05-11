"""
Data export functionality for the PDF Table Extractor.

This module provides functions for exporting extracted table data to various
file formats, including CSV and Excel.
"""

from tkinter import filedialog, messagebox

def export_to_csv(table_data, parent_window=None, suggested_filename=None):
    """
    Export table data to a CSV file.
    
    Args:
        table_data: A 2D list containing the table data
        parent_window: The parent window for dialog boxes (optional)
        suggested_filename: A suggested filename (optional)
        
    Returns:
        bool: True if the export was successful, False otherwise
    """
    if not table_data:
        messagebox.showwarning("Warning", "No table data to export", parent=parent_window)
        return False
    
    # Set up file dialog options
    options = {
        'defaultextension': ".csv",
        'filetypes': [("CSV files", "*.csv"), ("Text files", "*.txt"), ("All files", "*.*")],
        'title': "Save as CSV"
    }
    
    # Add suggested filename if provided
    if suggested_filename:
        options['initialfile'] = suggested_filename
    
    # Get file path from user
    file_path = filedialog.asksaveasfilename(**options)
    
    if not file_path:
        return False  # User cancelled
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            for row in table_data:
                # Format each cell (quote if contains commas or quotes)
                formatted_row = []
                for cell in row:
                    cell_str = str(cell) if cell is not None else ""
                    if ',' in cell_str or '"' in cell_str:
                        # Escape quotes and wrap in quotes
                        cell_str = '"' + cell_str.replace('"', '""') + '"'
                    elif cell_str == "":
                        cell_str = '""'  # Empty cells as empty quotes
                    formatted_row.append(cell_str)
                
                # Write the row to the file
                f.write(",".join(formatted_row) + "\n")
        
        return True
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save CSV file: {str(e)}", parent=parent_window)
        return False

def export_to_excel(table_data, parent_window=None, suggested_filename=None):
    """
    Export table data to an Excel file.
    
    Args:
        table_data: A 2D list containing the table data
        parent_window: The parent window for dialog boxes (optional)
        suggested_filename: A suggested filename (optional)
        
    Returns:
        bool: True if the export was successful, False otherwise
    """
    if not table_data:
        messagebox.showwarning("Warning", "No table data to export", parent=parent_window)
        return False
    
    # Set up file dialog options
    options = {
        'defaultextension': ".xlsx",
        'filetypes': [("Excel files", "*.xlsx"), ("All files", "*.*")],
        'title': "Save as Excel"
    }
    
    # Add suggested filename if provided
    if suggested_filename:
        options['initialfile'] = suggested_filename
    
    # Get file path from user
    file_path = filedialog.asksaveasfilename(**options)
    
    if not file_path:
        return False  # User cancelled
    
    try:
        # Check if pandas and openpyxl are available
        try:
            import pandas as pd
            import openpyxl
        except ImportError as e:
            if "pandas" in str(e):
                messagebox.showerror(
                    "Error", 
                    "The pandas package is required for Excel export.\n\nPlease run: pip install pandas openpyxl", 
                    parent=parent_window
                )
                return False
            elif "openpyxl" in str(e):
                messagebox.showerror(
                    "Error", 
                    "The openpyxl package is required for Excel export.\n\nPlease run: pip install openpyxl", 
                    parent=parent_window
                )
                return False
            else:
                raise e
        
        # Convert table data to pandas DataFrame
        df = pd.DataFrame(table_data)
        
        # Write DataFrame to Excel
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Extracted Table', index=False, header=False)
        
        return True
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save Excel file: {str(e)}", parent=parent_window)
        return False