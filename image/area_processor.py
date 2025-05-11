"""
Area selection processing functionality for the PDF Table Extractor.

This module provides the AreaProcessor class, which is responsible for processing
selected areas of PDF pages to extract table structure information.
"""
import fitz  # PyMuPDF
from PIL import Image
from tkinter import messagebox
import traceback
from .line_detector import LineDetector
from gui.dialogs import create_progress_dialog, update_progress

class AreaProcessor:
    """
    Processes selected areas of PDF pages.
    
    This class handles the selection, processing, and analysis of areas within
    PDF pages to identify table structures and convert them to markers.
    """
    
    def __init__(self, app):
        """
        Initialise the area processor.
        
        Args:
            app: The PDFTableExtractorApp instance
        """
        self.app = app
        self.line_detector = LineDetector()
        
        # Image processing variables
        self.selection_image = None
        self.processed_image = None
        self.line_detection_image = None
        self.detected_vertical_lines = []
        self.detected_horizontal_lines = []
        self.original_selection = None
        self.crop_x = None
        self.crop_y = None
        self.x1_cropped = None
        self.y1_cropped = None
        self.x2_cropped = None
        self.y2_cropped = None
        self.image_scaling_factor = None
        self.processing_zoom_factor = None
    
    def process_selected_area(self):
        """
        Process the selected area as an image, detect table lines, and apply them directly.
        """
        if not self.app.pdf_document or not self.app.selection_start or not self.app.selection_end:
            messagebox.showwarning("Warning", "Please select an area first using the 'Select Area' tool")
            return
        
        try:
            # Create progress window
            progress_window, progress_label, progress_bar = create_progress_dialog(
                self.app, 
                "Processing Area...", 
                "Detecting table lines from selection..."
            )
            
            # Update progress
            update_progress(progress_bar, progress_label, "Extracting selection...", 0.1)
            
            # Get the coordinates of the selection
            x1, y1 = self.app.selection_start
            x2, y2 = self.app.selection_end
            
            # Make sure we have the correct order (start is top-left, end is bottom-right)
            if x1 > x2:
                x1, x2 = x2, x1
            if y1 > y2:
                y1, y2 = y2, y1
                
            self.app.selection_start = (x1, y1)
            self.app.selection_end = (x2, y2)
            
            # Store original selection for table boundaries
            self.original_selection = (x1, y1, x2, y2)
            
            # Get the current page
            page = self.app.pdf_document[self.app.current_page]
            
            update_progress(progress_bar, progress_label, "Preparing image...", 0.2)
            
            # Calculate a fixed crop based on typical table line thickness (approx 3pt)
            # 1 point = 1/72 inch, PDF coordinates are typically in points
            table_line_thickness = 3  # typical line thickness in points
            padding_factor = 1  # multiply by line thickness for adequate padding
            fixed_crop = table_line_thickness * padding_factor
            
            # Ensure the crop isn't too extreme for very small selections
            selection_width = x2 - x1
            selection_height = y2 - y1
            max_crop_percent = 0.05  # cap at 5% of selection dimension
            max_crop_x = selection_width * max_crop_percent
            max_crop_y = selection_height * max_crop_percent
            
            # Use the smaller of fixed crop or max percentage
            crop_x = min(fixed_crop, max_crop_x)
            crop_y = min(fixed_crop, max_crop_y)
            
            # Store crop values for later use
            self.crop_x = crop_x
            self.crop_y = crop_y
            
            # Store the current user zoom factor to restore it later
            self.processing_zoom_factor = self.app.zoom_factor
            
            # Use a higher zoom factor for processing to improve line detection
            # This temporary zoom is only used for the processing, not for display
            processing_zoom = max(8.0, self.app.zoom_factor)
            
            # Calculate coordinates for the cropped region in document space
            x1_cropped = x1 + crop_x
            y1_cropped = y1 + crop_y
            x2_cropped = x2 - crop_x
            y2_cropped = y2 - crop_y
            
            # Store the cropped coordinates for debugging and later use
            self.x1_cropped = x1_cropped
            self.y1_cropped = y1_cropped
            self.x2_cropped = x2_cropped
            self.y2_cropped = y2_cropped
            
            update_progress(progress_bar, progress_label, "Rendering selection...", 0.3)
            
            # Render the page at the higher processing zoom level
            mat = fitz.Matrix(processing_zoom, processing_zoom)
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to PIL Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Convert document coordinates to scaled values for the actual image
            # Use the processing zoom factor for this conversion
            x1_scaled = int(x1 * processing_zoom)
            y1_scaled = int(y1 * processing_zoom)
            x2_scaled = int(x2 * processing_zoom)
            y2_scaled = int(y2 * processing_zoom)
            
            # Store the scaling factor between document and image coordinates
            self.image_scaling_factor = processing_zoom
            
            # Calculate scaled crop values
            crop_x_scaled = int(crop_x * processing_zoom)
            crop_y_scaled = int(crop_y * processing_zoom)
            
            # Crop the image to the selection
            selection_img = img.crop((x1_scaled, y1_scaled, x2_scaled, y2_scaled))
            
            # Store original selection image before cropping
            self.selection_image = selection_img
            
            # Crop inward by the calculated amounts
            width, height = selection_img.size
            cropped_img = selection_img.crop((crop_x_scaled, crop_y_scaled, width - crop_x_scaled, height - crop_y_scaled))
            
            # Store the processed image
            self.processed_image = cropped_img
            
            update_progress(progress_bar, progress_label, "Analyzing image for table lines...", 0.5)
            
            # Analyze the image for table lines
            self.line_detector.analyze_image_borders(cropped_img)
            
            # Get detected lines from line detector
            self.detected_vertical_lines = self.line_detector.vertical_lines
            self.detected_horizontal_lines = self.line_detector.horizontal_lines
            self.line_detection_image = self.line_detector.line_detection_image
            
            update_progress(progress_bar, progress_label, "Applying detected lines...", 0.8)
            
            # Apply the detected lines directly
            self.apply_detected_lines()
            
            update_progress(progress_bar, progress_label, "Complete!", 1.0)
            progress_window.destroy()
            
        except Exception as e:
            if 'progress_window' in locals():
                progress_window.destroy()
            print(traceback.format_exc())
            messagebox.showerror("Error", f"Failed to process selected area: {str(e)}")
    
    
    def apply_detected_lines(self):
        """
        Apply the detected lines as markers in the main application.
        Based on the original implementation to ensure coordinate mapping works correctly.
        """
        if not hasattr(self, 'detected_vertical_lines') or not hasattr(self, 'detected_horizontal_lines'):
            messagebox.showwarning("Warning", "No lines detected to apply")
            return
            
        try:
            # Check if we have all needed references
            if not hasattr(self, 'x1_cropped') or not hasattr(self, 'y1_cropped'):
                messagebox.showwarning("Warning", "Missing coordinate references. Please reprocess the selection.")
                return
            
            # Get the original selection coordinates
            orig_x1, orig_y1 = self.app.selection_start
            
            # Get the stored cropped coordinates in document space
            x1_cropped = self.x1_cropped
            y1_cropped = self.y1_cropped
            
            # Get the crop adjustments (in document space)
            crop_x = self.crop_x
            crop_y = self.crop_y
            
            # Use the processed image to calculate the scaling factor
            if hasattr(self, 'processed_image') and self.processed_image:
                # Original selected area width in document coordinates
                doc_width = self.x2_cropped - self.x1_cropped
                # Processed image width in pixels
                img_width = self.processed_image.width
                # This gives us document units per pixel
                scale_factor = doc_width / img_width
                
                print(f"Original doc width: {doc_width}, Image width: {img_width}")
                print(f"Scale factor: {scale_factor} doc units per pixel")
            else:
                # Fallback if we can't calculate precisely
                scale_factor = 1.0 / self.image_scaling_factor
                print(f"Using fallback scale factor from processing zoom: {scale_factor}")
            
            # Debug information
            print(f"Original selection starts at: ({orig_x1}, {orig_y1})")
            print(f"Cropped region starts at: ({x1_cropped}, {y1_cropped})")
            print(f"Detected vertical lines: {self.detected_vertical_lines}")
            print(f"Detected horizontal lines: {self.detected_horizontal_lines}")
            print(f"Scale factor: {scale_factor}")
            
            # Clear existing markers (optional - could add this as a checkbox option)
            if messagebox.askyesno("Confirm", "Clear existing markers before applying detected lines?"):
                self.app.column_markers = []
                self.app.row_markers = []
                self.app.marker_history = []
                
            # Add the original selection boundaries as markers
            # If we have the original selection coordinates
            if hasattr(self, 'original_selection'):
                x1, y1, x2, y2 = self.original_selection
                
                # Add the outer bounds as markers
                if x1 not in self.app.column_markers:
                    self.app.column_markers.append(x1)
                    self.app.marker_history.append({'type': 'column', 'value': x1})
                    
                if x2 not in self.app.column_markers:
                    self.app.column_markers.append(x2)
                    self.app.marker_history.append({'type': 'column', 'value': x2})
                    
                if y1 not in self.app.row_markers:
                    self.app.row_markers.append(y1)
                    self.app.marker_history.append({'type': 'row', 'value': y1})
                    
                if y2 not in self.app.row_markers:
                    self.app.row_markers.append(y2)
                    self.app.marker_history.append({'type': 'row', 'value': y2})
            
            # Add detected vertical lines as column markers
            for x_rel in self.detected_vertical_lines:
                # Convert from pixels in processed image to PDF coordinates
                # Need to scale the pixel coordinate to document units and then
                # add the offset of the cropped region
                x_pdf = int(x1_cropped + (x_rel * scale_factor))
                print(f"Mapping detected x={x_rel} to PDF x={x_pdf} (orig + {x_rel * scale_factor})")
                
                if x_pdf not in self.app.column_markers:
                    self.app.column_markers.append(x_pdf)
                    # Add to history for undo
                    self.app.marker_history.append({'type': 'column', 'value': x_pdf})
            
            # Add detected horizontal lines as row markers
            for y_rel in self.detected_horizontal_lines:
                # Convert from pixels in processed image to PDF coordinates
                y_pdf = int(y1_cropped + (y_rel * scale_factor))
                print(f"Mapping detected y={y_rel} to PDF y={y_pdf} (orig + {y_rel * scale_factor})")
                
                if y_pdf not in self.app.row_markers:
                    self.app.row_markers.append(y_pdf)
                    # Add to history for undo
                    self.app.marker_history.append({'type': 'row', 'value': y_pdf})
            
            # Sort markers
            self.app.column_markers.sort()
            self.app.row_markers.sort()
            
            # Redraw markers
            self.app.marker_manager.redraw_markers()
            
            # Update status
            v_lines = len(self.detected_vertical_lines)
            h_lines = len(self.detected_horizontal_lines)
            self.app.status_label.config(text=f"Applied {v_lines} vertical and {h_lines} horizontal detected lines as markers")
            
        except Exception as e:
            print(traceback.format_exc())
            messagebox.showerror("Error", f"Failed to apply detected lines: {str(e)}")