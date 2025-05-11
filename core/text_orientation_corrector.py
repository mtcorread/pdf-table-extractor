"""
Text orientation correction functionality for the PDF Table Extractor.

This module provides the TextOrientationCorrector class, which is responsible for
detecting and correcting the orientation of text extracted from PDF documents.
"""

import re
from tkinter import messagebox

class TextOrientationCorrector:
    """
    Detects and corrects text orientation in PDF documents.
    
    This class provides methods to analyze text extracted from PDF documents
    and correct orientation issues such as vertical text being extracted incorrectly.
    """
    
    def __init__(self, app):
        """
        Initialise the text orientation corrector.
        
        Args:
            app: The PDFTableExtractorApp instance
        """
        self.app = app
        self.original_table_data = None
        self.corrected_table_data = None
        
    def correct_text_orientation(self):
        """
        Analyze and correct the orientation of extracted text.
        
        This method examines the current table data and applies corrections
        if text appears to be in the wrong orientation.
        """
        if not hasattr(self.app, 'table_data') or not self.app.table_data:
            messagebox.showwarning("Warning", "No table data to correct. Please extract a table first.")
            return
            
        try:
            # Backup original data
            self.original_table_data = [row[:] for row in self.app.table_data]
            
            # Analyze the extracted text to determine if correction is needed
            needs_correction, correction_type = self._analyze_text_orientation()
            
            if not needs_correction:
                messagebox.showinfo("Information", "No text orientation issues detected.")
                return
                
            # Apply the appropriate correction
            if correction_type == "vertical":
                self._correct_vertical_text()
            elif correction_type == "rtl":
                self._correct_rtl_text()
            elif correction_type == "flipped":
                self._correct_flipped_text()
            
            # Display the corrected data
            csv_data = ""
            for row in self.app.table_data:
                csv_data += ",".join(f'"{cell}"' if cell else "" for cell in row) + "\n"
            
            # Display in the text output area
            self.app.text_output.delete(1.0, "end")
            self.app.text_output.insert("end", csv_data)
            
            self.app.status_label.config(text=f"Text orientation corrected")
            
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            messagebox.showerror("Error", f"Failed to correct text orientation: {str(e)}")
            
    def _analyze_text_orientation(self):
        """
        Analyze the extracted text to determine the type of orientation correction needed.
        
        Returns:
            tuple: (needs_correction, correction_type) where correction_type can be 
                  "vertical", "rtl", "flipped", or None
        """
        # Flatten the table data for easier analysis
        all_text = ' '.join([''.join([cell for cell in row if cell]) for row in self.app.table_data])
        
        # Check if text is too short to analyze
        if len(all_text) < 20:
            return False, None
            
        # Count patterns that indicate vertical text
        vertical_indicators = 0
        
        # Check for characteristic patterns in vertical text extraction
        # 1. Single characters separated by spaces (common in vertical extraction)
        single_char_pattern = re.compile(r'(?:\s[a-zA-Z]\s){3,}')  # 3+ single letters with spaces
        single_char_matches = single_char_pattern.findall(all_text)
        vertical_indicators += len(single_char_matches) * 2
        
        # 2. Words with reversed character order (e.g., "elbaT" instead of "Table")
        # Find common English words backward (simplified approach)
        common_reversed = ['eht', 'dna', 'rof', 'era', 'elbaT', 'egaP', 'txeT', 'ataD']
        for word in common_reversed:
            reversed_count = all_text.count(word)
            vertical_indicators += reversed_count * 3
            
        # 3. Check for unusual character frequency patterns seen in vertical text
        # In English, 'e' is most common, but in vertical scan of normal text, other patterns emerge
        char_count = {}
        for char in all_text.lower():
            if char.isalpha():
                char_count[char] = char_count.get(char, 0) + 1
                
        if char_count.get('n', 0) > char_count.get('e', 0) * 1.5:
            vertical_indicators += 5
        
        # 4. Check for new line characters mid-word (common in vertical extraction)
        newline_in_word = re.compile(r'[a-zA-Z]\n[a-zA-Z]')
        newline_matches = newline_in_word.findall(all_text)
        vertical_indicators += len(newline_matches)
        
        # 5. Try direct detection from PDF if available
        pdf_needs_correction, pdf_correction_type = self.detect_text_orientation_from_pdf()
        if pdf_needs_correction and pdf_correction_type == "vertical":
            vertical_indicators += 10
        
        # Determine if correction is needed and what type
        if vertical_indicators >= 5:
            return True, "vertical"
        
        return False, None
        
    def _correct_vertical_text(self):
        """
        Correct vertically extracted text by rearranging characters.
        This handles cases where text is printed horizontally but extracted vertically.
        """
        # For each cell, detect and correct vertical text
        for row_idx, row in enumerate(self.app.table_data):
            for col_idx, cell in enumerate(row):
                if not cell:
                    continue
                
                # Skip very short cells or those that are likely numbers
                if len(cell) < 3 or cell.isdigit():
                    continue
                    
                # Check if cell contains vertical text (multiple lines with 1-2 characters per line)
                lines = cell.split('\n')
                is_vertical = False
                
                # Check if most lines are 1-2 characters
                short_lines = [line for line in lines if len(line.strip()) <= 2 and len(line.strip()) > 0]
                
                if len(lines) >= 3 and len(short_lines) > len(lines) * 0.6:
                    is_vertical = True
                
                if is_vertical:
                    # Reconstruct the text by reading from bottom to top (reverse the lines)
                    # and join characters into words
                    corrected_text = ''.join(line.strip() for line in reversed(lines) if line.strip())
                    
                    # If the result looks meaningful (heuristic check)
                    if len(corrected_text) >= 3:
                        self.app.table_data[row_idx][col_idx] = corrected_text
                        
                # Alternative approach for non-newline vertical text
                elif '\n' not in cell and len(cell) >= 3:
                    # Check for alternating character-space pattern (e.g., "e k o t S")
                    if re.match(r'([a-zA-Z] ){2,}[a-zA-Z]', cell):
                        # Remove spaces and reverse (as vertical text is often read bottom-to-top)
                        corrected_text = ''.join(reversed(cell.replace(' ', '')))
                        self.app.table_data[row_idx][col_idx] = corrected_text
        
        self.corrected_table_data = self.app.table_data
                        
    def _correct_rtl_text(self):
        """
        Correct right-to-left text by reversing character order.
        """
        # For each cell, reverse the text to correct RTL issues
        for row_idx, row in enumerate(self.app.table_data):
            for col_idx, cell in enumerate(row):
                if not cell or len(cell) < 2:
                    continue
                    
                # Reverse the text
                self.app.table_data[row_idx][col_idx] = cell[::-1]
        
        self.corrected_table_data = self.app.table_data
    
    def _correct_flipped_text(self):
        """
        Correct upside-down text by rotating 180 degrees.
        """
        # For each cell, flip the text upside-down
        for row_idx, row in enumerate(self.app.table_data):
            for col_idx, cell in enumerate(row):
                if not cell or len(cell) < 2:
                    continue
                    
                # Flip the text upside-down (reverse the text and handle newlines)
                lines = cell.split('\n')
                flipped_lines = [line[::-1] for line in reversed(lines)]
                self.app.table_data[row_idx][col_idx] = '\n'.join(flipped_lines)
        
        self.corrected_table_data = self.app.table_data
                
    def restore_original_text(self):
        """
        Restore the original text before orientation correction.
        """
        if not self.original_table_data:
            messagebox.showinfo("Information", "No original data to restore.")
            return
            
        # Restore original data
        self.app.table_data = [row[:] for row in self.original_table_data]
        
        # Display the original data
        csv_data = ""
        for row in self.app.table_data:
            csv_data += ",".join(f'"{cell}"' if cell else "" for cell in row) + "\n"
        
        # Display in the text output area
        self.app.text_output.delete(1.0, "end")
        self.app.text_output.insert("end", csv_data)
        
        self.app.status_label.config(text="Restored original text orientation")
        
    def detect_text_orientation_from_pdf(self):
        """
        Attempt to detect text orientation directly from the PDF document.
        """
        if not self.app.pdf_document:
            return False, None
            
        try:
            # Get the current page
            page = self.app.pdf_document[self.app.current_page]
            
            # Extract text with direction information
            text_dict = page.get_text("dict")
            
            # Analyze text spans for direction flags
            vertical_spans = 0
            rtl_spans = 0
            total_spans = 0
            
            for block in text_dict["blocks"]:
                if block["type"] == 0:  # Text block
                    for line in block["lines"]:
                        for span in line["spans"]:
                            total_spans += 1
                            
                            # Check direction information
                            dir_flags = span.get("dir", [0, 0, 0])
                            if dir_flags[0] < 0:  # Negative x direction = RTL
                                rtl_spans += 1
                            if dir_flags[1] < 0:  # Negative y direction = TTB (top-to-bottom)
                                vertical_spans += 1
                                
                            # Also check for spans with unusual bbox dimensions
                            bbox = span.get("bbox", [0, 0, 0, 0])
                            if bbox:
                                width = bbox[2] - bbox[0]
                                height = bbox[3] - bbox[1]
                                # If significantly taller than wide, likely vertical text
                                if height > width * 3 and height > 20:  # Avoid tiny spans
                                    vertical_spans += 1
            
            # Calculate percentages
            if total_spans > 0:
                vertical_percent = vertical_spans / total_spans
                rtl_percent = rtl_spans / total_spans
                
                # Determine orientation based on percentages
                if vertical_percent > 0.3:  # More than 30% vertical spans
                    return True, "vertical"
                elif rtl_percent > 0.3:  # More than 30% RTL spans
                    return True, "rtl"
            
            return False, None
            
        except Exception as e:
            print(f"Error detecting text orientation from PDF: {str(e)}")
            return False, None