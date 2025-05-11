"""
Dialog creation functions for the PDF Table Extractor.

This module defines functions for creating and configuring various dialog windows
used in the application, such as multi-page extraction options and progress indicators.
"""

import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from PIL import ImageTk

def create_multipage_options_dialog(app):
    """
    Create a dialog for configuring multi-page table extraction options.
    
    Args:
        app: The PDFTableExtractorApp instance
        
    Returns:
        dict: A dictionary containing the selected options if the user confirms,
              or None if the user cancels
    """
    # Check if there are marked pages
    if not app.page_markers:
        messagebox.showwarning("Warning", "No pages have been marked. Use 'Mark Current Page' to save markers for each page.")
        return None
    
    # Create dialog window
    options_dialog = tk.Toplevel(app.root)
    options_dialog.title("Marked Pages Extraction Options")
    options_dialog.geometry("400x250")  
    options_dialog.transient(app.root)  # Make dialog modal
    options_dialog.grab_set()
    
    # Create frame for the dialog content
    frame = tk.Frame(options_dialog, padx=20, pady=20)
    frame.pack(fill=tk.BOTH, expand=True)
    
    # Add descriptive label
    tk.Label(frame, text=f"Extract tables from {len(app.page_markers)} marked pages", 
             font=("Arial", 12, "bold")).pack(pady=5)
    
    # Merge mode selection
    tk.Label(frame, text="Merge mode:").pack(anchor=tk.W, pady=(10, 0))
    merge_mode_var = tk.StringVar(value="vertical")
    
    vertical_radio = tk.Radiobutton(frame, text="Vertical (append pages below each other)", 
                                   variable=merge_mode_var, value="vertical")
    vertical_radio.pack(anchor=tk.W)
    
    horizontal_radio = tk.Radiobutton(frame, text="Horizontal (append pages to the right)", 
                                     variable=merge_mode_var, value="horizontal")
    horizontal_radio.pack(anchor=tk.W)
    
    # Transpose option
    transpose_var = tk.BooleanVar(value=False)
    transpose_check = tk.Checkbutton(frame, text="Transpose final result (swap rows and columns)", 
                                   variable=transpose_var)
    transpose_check.pack(anchor=tk.W, pady=(10, 0))
    
    # Button frame at the bottom of the dialog
    button_frame = tk.Frame(options_dialog, padx=20, pady=10)
    button_frame.pack(side=tk.BOTTOM, fill=tk.X)
    
    # Dictionary to store the result
    result = {}
    
    # Function to collect options and close the dialog
    def on_confirm():
        result['merge_mode'] = merge_mode_var.get()
        result['transpose'] = transpose_var.get()
        options_dialog.destroy()
    
    # Add extract and cancel buttons
    extract_btn = tk.Button(button_frame, text="Extract Tables", command=on_confirm)
    extract_btn.pack(side=tk.RIGHT, padx=10, pady=5)
    
    cancel_btn = tk.Button(button_frame, text="Cancel", command=options_dialog.destroy)
    cancel_btn.pack(side=tk.RIGHT, padx=5, pady=5)
    
    # Wait for the dialog to be closed
    app.root.wait_window(options_dialog)
    
    # Return the result if it was set (i.e., user clicked Extract)
    return result if result else None

def create_progress_dialog(app, title, message):
    """
    Create a progress dialog for long-running operations.
    
    Args:
        app: The PDFTableExtractorApp instance
        title: The dialog title
        message: The initial message to display
        
    Returns:
        tuple: (dialog, progress_label, progress_bar) to be updated during the operation
    """
    progress_window = tk.Toplevel(app.root)
    progress_window.title(title)
    progress_window.geometry("300x100")
    progress_window.transient(app.root)
    
    progress_label = tk.Label(progress_window, text=message)
    progress_label.pack(pady=10)
    
    # Create a custom progress bar
    progress_frame = tk.Frame(progress_window, height=20, bd=1, relief=tk.SUNKEN)
    progress_frame.pack(fill=tk.X, padx=20, pady=10)
    
    progress_bar = tk.Canvas(progress_frame, height=20, bg="white", highlightthickness=0)
    progress_bar.pack(fill=tk.X, expand=True)
    
    return progress_window, progress_label, progress_bar

def update_progress(progress_bar, progress_label, message, progress_ratio):
    """
    Update the progress bar and message in a progress dialog.
    
    Args:
        progress_bar: The canvas progress bar
        progress_label: The label showing the progress message
        message: The new message to display
        progress_ratio: The progress ratio (0.0 to 1.0)
    """
    progress_bar.delete("progress")
    progress_bar.create_rectangle(
        0, 0, progress_bar.winfo_width() * progress_ratio, 20,
        fill="lightgreen", outline="", tags="progress"
    )
    progress_label.config(text=message)
    
    # Force update of the progress display
    progress_bar.update()
    progress_label.update()

def create_image_view_dialog(app, image, title="Processed Image", has_detection=False, detection_image=None):
    """
    Create a dialog to display a processed image with tabs for original and line detection.
    
    Args:
        app: The PDFTableExtractorApp instance
        image: The PIL image to display (original processed image)
        title: The dialog title
        has_detection: Whether to show line detection tab and controls
        detection_image: The line detection visualization image (if any)
    """
    if not image:
        return None
        
    # Create a new top-level window
    img_window = tk.Toplevel(app.root)
    img_window.title(title)
    img_window.transient(app.root)  # Make it a child of the main window
    
    # Get screen dimensions for proper window sizing
    screen_width = img_window.winfo_screenwidth()
    screen_height = img_window.winfo_screenheight()
    
    # Create notebook with tabs
    notebook = ttk.Notebook(img_window)
    notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Tab 1: Original cropped image
    original_tab = tk.Frame(notebook)
    notebook.add(original_tab, text="Original")
    
    # Original image tab content
    original_content_frame = tk.Frame(original_tab)
    original_content_frame.pack(fill=tk.BOTH, expand=True)
    
    # Info label
    if hasattr(app.area_processor, 'crop_x') and hasattr(app.area_processor, 'crop_y'):
        crop_info = f"(Cropped inward by {app.area_processor.crop_x:.1f}pt horizontally, {app.area_processor.crop_y:.1f}pt vertically)"
    else:
        crop_info = "(Cropped inward from original selection)"
        
    width, height = image.size
    info_text = f"Processed image size: {width}x{height} pixels\n{crop_info}"
    
    info_label = tk.Label(original_content_frame, text=info_text, justify=tk.LEFT, anchor=tk.W)
    info_label.pack(side=tk.TOP, fill=tk.X, pady=5)
    
    # Create scrollable canvas for the original image
    h_scrollbar = tk.Scrollbar(original_content_frame, orient=tk.HORIZONTAL)
    v_scrollbar = tk.Scrollbar(original_content_frame)
    
    h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
    v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    canvas = tk.Canvas(original_content_frame, 
                     xscrollcommand=h_scrollbar.set,
                     yscrollcommand=v_scrollbar.set)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    h_scrollbar.config(command=canvas.xview)
    v_scrollbar.config(command=canvas.yview)
    
    # Convert PIL image to PhotoImage
    photo = ImageTk.PhotoImage(image)
    
    # Add image to canvas
    canvas.create_image(0, 0, anchor=tk.NW, image=photo)
    canvas.config(scrollregion=(0, 0, width, height))
    canvas.image = photo  # Keep reference
    
    # Tab 2: Line detection visualization (if applicable)
    if has_detection and detection_image:
        detection_tab = tk.Frame(notebook)
        notebook.add(detection_tab, text="Line Detection")
        
        # Detection tab content
        detection_content_frame = tk.Frame(detection_tab)
        detection_content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Detection results info
        v_lines = len(app.area_processor.detected_vertical_lines) if hasattr(app.area_processor, 'detected_vertical_lines') else 0
        h_lines = len(app.area_processor.detected_horizontal_lines) if hasattr(app.area_processor, 'detected_horizontal_lines') else 0
        
        detection_info = f"Detected {v_lines} vertical lines and {h_lines} horizontal lines\n"
        detection_info += "Red = vertical lines, Blue = horizontal lines, Green = table boundaries\n"
        detection_info += "\nClick 'Apply Detected Lines as Markers' to use these lines for table extraction"
        
        detection_label = tk.Label(detection_content_frame, text=detection_info, justify=tk.LEFT, anchor=tk.W)
        detection_label.pack(side=tk.TOP, fill=tk.X, pady=5)
        
        # Button at top for visibility
        buttons_top_frame = tk.Frame(detection_content_frame)
        buttons_top_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        
        apply_button = tk.Button(buttons_top_frame, text="Apply Detected Lines as Markers", 
                               command=lambda: app.area_processor.apply_detected_lines(), 
                               bg="#98FB98")
        apply_button.pack(pady=5)
        
        # Scrollable area for the detection image
        h_scrollbar2 = tk.Scrollbar(detection_content_frame, orient=tk.HORIZONTAL)
        v_scrollbar2 = tk.Scrollbar(detection_content_frame)
        
        h_scrollbar2.pack(side=tk.BOTTOM, fill=tk.X)
        v_scrollbar2.pack(side=tk.RIGHT, fill=tk.Y)
        
        detection_canvas = tk.Canvas(detection_content_frame, 
                                   xscrollcommand=h_scrollbar2.set,
                                   yscrollcommand=v_scrollbar2.set)
        detection_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        h_scrollbar2.config(command=detection_canvas.xview)
        v_scrollbar2.config(command=detection_canvas.yview)
        
        # Convert detection image to PhotoImage
        detection_photo = ImageTk.PhotoImage(detection_image)
        
        # Add image to canvas
        detection_canvas.create_image(0, 0, anchor=tk.NW, image=detection_photo)
        detection_canvas.config(scrollregion=(0, 0, width, height))
        detection_canvas.image = detection_photo  # Keep reference
    
    # Bottom button frame
    button_frame = tk.Frame(img_window)
    button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
    
    # Apply button
    if has_detection:
        apply_btn = tk.Button(button_frame, text="Apply Detected Lines", 
                            command=lambda: app.area_processor.apply_detected_lines(), 
                            bg="#98FB98")
        apply_btn.pack(side=tk.LEFT, padx=5)
    
    # Save image button
    def save_processed_image():
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
            title="Save Processed Image")
            
        if file_path:
            try:
                # Find which tab is active to determine which image to save
                tab_id = notebook.index(notebook.select())
                if tab_id == 0:
                    image.save(file_path)
                else:  # Line detection tab
                    detection_image.save(file_path)
                    
                messagebox.showinfo("Info", f"Image saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save image: {str(e)}")
    
    save_btn = tk.Button(button_frame, text="Save Image", command=save_processed_image)
    save_btn.pack(side=tk.RIGHT, padx=5)
    
    # Close button
    close_btn = tk.Button(button_frame, text="Close", command=img_window.destroy)
    close_btn.pack(side=tk.RIGHT, padx=5)
    
    # Set window size
    window_width = min(width + 50, int(screen_width * 0.8))
    window_height = min(height + 150, int(screen_height * 0.8))
    
    # Center the window
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    
    img_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    return img_window