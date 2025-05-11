"""
Configuration management functionality for the PDF Table Extractor.

This module provides the ConfigManager class, which is responsible for saving and
loading table configurations, including column and row markers.
"""

import json
import os
import pandas as pd
from tkinter import filedialog, messagebox

class ConfigManager:
    """
    Manages saving and loading of table configurations.
    
    This class handles the storage and retrieval of configuration data, including
    marker positions, that define table structures in PDF documents.
    """
    
    def __init__(self, app):
        """
        Initialise the configuration manager.
        
        Args:
            app: The PDFTableExtractorApp instance
        """
        self.app = app
    
    def save_table_config(self):
        """
        Save the current table configuration (marker positions) to a JSON file.
        """
        if not self.app.column_markers or not self.app.row_markers:
            messagebox.showwarning("Warning", "Please set column and row markers first")
            return
        
        # Create a configuration dictionary
        config = {
            'column_markers': self.app.column_markers,
            'row_markers': self.app.row_markers,
            'page': self.app.current_page if self.app.pdf_document else 0,
            'created_date': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
            'description': 'Table configuration for PDF Table Extractor'
        }
        
        # Ask for a file to save to
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Table Configuration")
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(config, f, indent=4)
                self.app.status_label.config(text=f"Configuration saved to: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")
    
    def load_table_config(self):
        """
        Load a table configuration (marker positions) from a JSON file.
        """
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load Table Configuration")
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    config = json.load(f)
                
                # Extract the markers from the configuration
                if 'column_markers' in config and 'row_markers' in config:
                    self.app.column_markers = config['column_markers']
                    self.app.row_markers = config['row_markers']
                    
                    # Redraw markers
                    self.app.marker_manager.redraw_markers()
                    
                    # Set page if available and PDF is loaded
                    if self.app.pdf_document and 'page' in config:
                        # Make sure the page is within valid range
                        if 0 <= config['page'] < self.app.total_pages:
                            self.app.current_page = config['page']
                            self.app.pdf_handler.update_page_display()
                    
                    self.app.status_label.config(text=f"Configuration loaded from: {os.path.basename(file_path)}")
                else:
                    messagebox.showerror("Error", "Invalid configuration file")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load configuration: {str(e)}")
    
    def save_all_page_markers(self):
        """
        Save all page markers and manual data to a JSON file for future use.
        """
        if not self.app.page_markers:
            messagebox.showwarning("Warning", "No page markers to save")
            return
        
        # Create a configuration dictionary
        config = {
            'page_markers': {str(k): v for k, v in self.app.page_markers.items()},  # Convert keys to strings for JSON
            'manual_data': {},
            'created_date': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
            'description': 'Multi-page markers for PDF Table Extractor',
            'filename': os.path.basename(self.app.pdf_document.name) if self.app.pdf_document else "Unknown"
        }
        
        # Add manual data if available
        if hasattr(self.app, 'manual_input_manager') and hasattr(self.app.manual_input_manager, 'all_pages_manual_data'):
            if self.app.manual_input_manager.all_pages_manual_data:
                config['manual_data'] = {str(k): v for k, v in self.app.manual_input_manager.all_pages_manual_data.items()}
        
        # Ask for a file to save to
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save All Page Markers")
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(config, f, indent=4)
                self.app.status_label.config(text=f"All page markers saved to: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save page markers: {str(e)}")
    
    def load_all_page_markers(self):
        """
        Load all page markers and manual data from a JSON file.
        """
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load All Page Markers")
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    config = json.load(f)
                
                # Check if the current PDF filename matches the saved one
                current_filename = os.path.basename(self.app.pdf_document.name) if self.app.pdf_document else "Unknown"
                saved_filename = config.get('filename', "Unknown")
                
                if current_filename != saved_filename:
                    if not messagebox.askyesno("Warning", 
                                            f"This configuration was created for a different file: '{saved_filename}'\n\n"
                                            f"Your current file is: '{current_filename}'\n\n"
                                            "Load anyway? This might cause alignment issues."):
                        return
                
                # Extract the page markers from the configuration
                if 'page_markers' in config:
                    # Convert string keys back to integers
                    page_markers = {int(k): v for k, v in config['page_markers'].items()}
                    self.app.page_markers = page_markers
                    
                    # Update the current page display if it's one of the marked pages
                    if self.app.current_page in self.app.page_markers:
                        self.app.marker_manager.load_markers_for_current_page()
                        self.app.marker_manager.redraw_markers()
                    
                    num_pages = len(page_markers)
                    self.app.status_label.config(text=f"Loaded {num_pages} page markers from: {os.path.basename(file_path)}")
                
                # Load manual data if available
                if 'manual_data' in config and config['manual_data']:
                    if hasattr(self.app, 'manual_input_manager'):
                        # Convert string keys back to integers
                        manual_data = {int(k): v for k, v in config['manual_data'].items()}
                        self.app.manual_input_manager.all_pages_manual_data = manual_data
                        
                        # Notify user about loaded manual data
                        manual_pages = len(manual_data)
                        self.app.status_label.config(text=f"Loaded {num_pages} page markers and {manual_pages} pages of manual data")
                    
                else:
                    messagebox.showerror("Error", "Invalid page markers file")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load page markers: {str(e)}")