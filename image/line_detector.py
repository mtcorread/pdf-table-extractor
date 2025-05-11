"""
Line detection algorithms for the PDF Table Extractor.

This module provides the LineDetector class, which implements algorithms for
detecting horizontal and vertical lines in images of PDF content.
"""

import numpy as np
from PIL import ImageDraw

class LineDetector:
    """
    Detects horizontal and vertical lines in images.
    
    This class implements algorithms to analyze images and detect line patterns
    that represent table structures, using image processing techniques.
    """
    
    def __init__(self):
        """
        Initialise the line detector.
        """
        # Results storage
        self.vertical_lines = []
        self.horizontal_lines = []
        self.line_detection_image = None
    
    def analyze_image_borders(self, image):
        """
        Analyze the borders of an image to detect table lines.
        
        This function examines the edges and full-line segments of the image
        to find significant colour changes that may indicate table lines.
        
        Args:
            image: A PIL Image object containing the area to analyze
        """
        # Convert to numpy array for easier processing
        img_array = np.array(image)
        height, width, _ = img_array.shape
        
        # Lists to store detected line positions
        vertical_lines = []  # x-coordinates
        horizontal_lines = []  # y-coordinates
        
        # Create a copy of the image for visualization
        vis_image = image.copy()
        draw = ImageDraw.Draw(vis_image)
        
        # Check if the image is large enough for reliable line detection
        min_dimension = min(width, height)
        if min_dimension < 200:  # If image is too small, give warning in console
            print(f"Warning: Image size {width}x{height} may be too small for reliable line detection")
            print("Consider using a higher zoom factor for better results")
            
        # Adjust clustering distance threshold based on image size
        # For larger images (from higher zoom), we can use a larger threshold
        cluster_threshold = max(5, min(20, int(min_dimension * 0.03)))
        print(f"Using cluster threshold of {cluster_threshold} pixels based on image size")
        
        # Define thresholds for line detection
        line_intensity_threshold = 160  # Higher value to catch lighter lines (was 150)
        line_percentage_threshold = 0.35  # Lower percentage to be more forgiving (was 0.40)
        
        # Function to calculate grayscale intensity of a pixel
        def pixel_intensity(pixel):
            return 0.299 * pixel[0] + 0.587 * pixel[1] + 0.114 * pixel[2]
            
        # ===== COMPREHENSIVE METHOD FOR DETECTING VERTICAL LINES =====
        # Create a projection by summing pixel values along rows to detect vertical lines
        print("Creating vertical projection to detect lines...")
        vertical_projection = []
        for x in range(width):
            # Sample the column at regular intervals
            column_samples = [img_array[y, x] for y in range(0, height, max(1, height // 200))]
            # Calculate average darkness
            darkness_sum = sum(255 - pixel_intensity(pixel) for pixel in column_samples)
            vertical_projection.append(darkness_sum)
        
        # Normalize the projection
        max_darkness = max(vertical_projection) if vertical_projection else 1
        normalized_vproj = [val / max_darkness for val in vertical_projection]
        
        # Find local maxima in the projection (where darkness peaks)
        vertical_candidates = []
        for x in range(1, width - 1):
            if normalized_vproj[x] > 0.3:  # Only consider reasonably dark positions
                # Check if it's a local maximum or part of a plateau
                if (normalized_vproj[x] > normalized_vproj[x-1] or 
                    normalized_vproj[x] == normalized_vproj[x-1] > normalized_vproj[x-2]) and \
                   (normalized_vproj[x] > normalized_vproj[x+1] or 
                    normalized_vproj[x] == normalized_vproj[x+1] > normalized_vproj[x+2]):
                    vertical_candidates.append(x)
                    
        # ===== COMPREHENSIVE METHOD FOR DETECTING HORIZONTAL LINES =====
        # Create a projection by summing pixel values along columns to detect horizontal lines
        print("Creating horizontal projection to detect lines...")
        horizontal_projection = []
        for y in range(height):
            # Sample the row at regular intervals
            row_samples = [img_array[y, x] for x in range(0, width, max(1, width // 200))]
            # Calculate average darkness
            darkness_sum = sum(255 - pixel_intensity(pixel) for pixel in row_samples)
            horizontal_projection.append(darkness_sum)
        
        # Normalize the projection
        max_darkness = max(horizontal_projection) if horizontal_projection else 1
        normalized_hproj = [val / max_darkness for val in horizontal_projection]
        
        # Find local maxima in the projection (where darkness peaks)
        horizontal_candidates = []
        for y in range(1, height - 1):
            if normalized_hproj[y] > 0.3:  # Only consider reasonably dark positions
                # Check if it's a local maximum or part of a plateau
                if (normalized_hproj[y] > normalized_hproj[y-1] or 
                    normalized_hproj[y] == normalized_hproj[y-1] > normalized_hproj[y-2]) and \
                   (normalized_hproj[y] > normalized_hproj[y+1] or 
                    normalized_hproj[y] == normalized_hproj[y+1] > normalized_hproj[y+2]):
                    horizontal_candidates.append(y)
                    
        # Use traditional edge-based detection as a supplement
        # Find edges in multiple slices for more robustness
        slice_positions = [
            0,                     # Top edge
            height // 4,           # Quarter down
            height // 2,           # Middle
            (height * 3) // 4,     # Three quarters down
            height - 1             # Bottom edge
        ]
        
        # Function to check if a pixel might be part of a line
        def is_line_pixel(pixel):
            # Calculate intensity (grayscale equivalent)
            intensity = pixel_intensity(pixel)
            # Higher threshold to catch more potential lines
            return intensity < line_intensity_threshold  # Assuming lines are darker than background
        
        for y_pos in slice_positions:
            horizontal_slice = [img_array[y_pos, x] for x in range(width)]
            for x in range(1, width - 1):
                # Quick edge detection by looking at consecutive pixels
                prev_intensity = pixel_intensity(horizontal_slice[x-1])
                curr_intensity = pixel_intensity(horizontal_slice[x])
                next_intensity = pixel_intensity(horizontal_slice[x+1])
                
                # Check for significant darkening
                if (prev_intensity - curr_intensity > 30 and curr_intensity < line_intensity_threshold) or \
                   (next_intensity - curr_intensity > 30 and curr_intensity < line_intensity_threshold):
                    vertical_candidates.append(x)
        
        # Same for horizontal lines
        slice_positions = [
            0,                    # Left edge
            width // 4,           # Quarter across
            width // 2,           # Middle
            (width * 3) // 4,     # Three quarters across
            width - 1             # Right edge
        ]
        
        for x_pos in slice_positions:
            vertical_slice = [img_array[y, x_pos] for y in range(height)]
            for y in range(1, height - 1):
                # Quick edge detection by looking at consecutive pixels
                prev_intensity = pixel_intensity(vertical_slice[y-1])
                curr_intensity = pixel_intensity(vertical_slice[y])
                next_intensity = pixel_intensity(vertical_slice[y+1])
                
                # Check for significant darkening
                if (prev_intensity - curr_intensity > 30 and curr_intensity < line_intensity_threshold) or \
                   (next_intensity - curr_intensity > 30 and curr_intensity < line_intensity_threshold):
                    horizontal_candidates.append(y)
                
        # Function to verify if a complete vertical line is valid by checking the entire line
        def is_valid_vertical_line(x):
            # Create multiple sampling paths for thick lines - main line and offsets
            sampling_paths = [x]  # Start with the center
            
            # Add more sampling paths to better handle thick lines
            for offset in range(1, 6):  # Check up to 5 pixels in each direction
                if x - offset >= 0:  # Check within bounds
                    sampling_paths.append(x - offset)
                if x + offset < width:  # Check within bounds
                    sampling_paths.append(x + offset)
            
            # For each sampling path, check if it's a valid line
            for path_x in sampling_paths:
                # Sample pixels along the entire line (more samples)
                samples = [img_array[y, path_x] for y in range(0, height, max(1, height // 200))]
                # Count dark pixels
                dark_pixels = sum(1 for pixel in samples if pixel_intensity(pixel) < line_intensity_threshold)
                # Calculate percentage of dark pixels
                dark_percentage = dark_pixels / len(samples)
                
                # If any path is valid, consider the line valid
                if dark_percentage >= line_percentage_threshold:
                    return True
                    
            return False
            
        # Function to verify if a complete horizontal line is valid by checking the entire line
        def is_valid_horizontal_line(y):
            # Create multiple sampling paths for thick lines - main line and offsets
            sampling_paths = [y]  # Start with the center
            
            # Add more sampling paths to better handle thick lines
            for offset in range(1, 6):  # Check up to 5 pixels in each direction
                if y - offset >= 0:  # Check within bounds
                    sampling_paths.append(y - offset)
                if y + offset < height:  # Check within bounds
                    sampling_paths.append(y + offset)
                
            # For each sampling path, check if it's a valid line
            for path_y in sampling_paths:
                # Sample pixels along the entire line (more samples)
                samples = [img_array[path_y, x] for x in range(0, width, max(1, width // 200))]
                # Count dark pixels
                dark_pixels = sum(1 for pixel in samples if pixel_intensity(pixel) < line_intensity_threshold)
                # Calculate percentage of dark pixels
                dark_percentage = dark_pixels / len(samples)
                
                # If any path is valid, consider the line valid
                if dark_percentage >= line_percentage_threshold:
                    return True
                    
            return False
            
        # Function to cluster nearby lines and select a representative from each cluster
        def cluster_lines(lines, distance_threshold=10):
            if not lines:
                return []
                
            # Sort the lines
            sorted_lines = sorted(lines)
            
            # Initialize clusters with the first line
            clusters = [[sorted_lines[0]]]
            
            # Group lines into clusters based on proximity
            for line in sorted_lines[1:]:
                # If close to the previous cluster, add to it
                if line - clusters[-1][-1] <= distance_threshold:
                    clusters[-1].append(line)
                else:
                    # Start a new cluster
                    clusters.append([line])
            
            # Choose a representative line from each cluster (the median)
            representative_lines = []
            for cluster in clusters:
                # Use the median as the representative
                rep = cluster[len(cluster) // 2]
                representative_lines.append(rep)
                
            return representative_lines
            
        # Cluster the vertical line candidates
        v_tolerance = max(3, int(width * 0.01))  # 1% of width or at least 3 pixels
        clustered_vertical_candidates = cluster_lines(vertical_candidates, distance_threshold=v_tolerance)
        
        # Verify each vertical line candidate by checking along its length
        verified_vertical_lines = []
        for x in clustered_vertical_candidates:
            if 0 <= x < width and is_valid_vertical_line(x):  # Ensure x is within image bounds
                verified_vertical_lines.append(x)
                # Draw the verified vertical line
                draw.line([(x, 0), (x, height-1)], fill=(255, 0, 0), width=2)
        
        # Cluster the horizontal line candidates
        h_tolerance = max(3, int(height * 0.01))  # 1% of height or at least 3 pixels
        clustered_horizontal_candidates = cluster_lines(horizontal_candidates, distance_threshold=h_tolerance)
        
        # Verify each horizontal line candidate by checking along its length
        verified_horizontal_lines = []
        for y in clustered_horizontal_candidates:
            if 0 <= y < height and is_valid_horizontal_line(y):  # Ensure y is within image bounds
                verified_horizontal_lines.append(y)
                # Draw the verified horizontal line
                draw.line([(0, y), (width-1, y)], fill=(0, 0, 255), width=2)
                
        # Draw outer boundary lines that represent the original selection borders
        # These correspond to the edges of the cropped image
        draw.line([(0, 0), (width-1, 0)], fill=(0, 255, 0), width=2)  # Top (green)
        draw.line([(0, height-1), (width-1, height-1)], fill=(0, 255, 0), width=2)  # Bottom (green)
        draw.line([(0, 0), (0, height-1)], fill=(0, 255, 0), width=2)  # Left (green)
        draw.line([(width-1, 0), (width-1, height-1)], fill=(0, 255, 0), width=2)  # Right (green)
        
        # Sort the detected lines
        verified_vertical_lines.sort()
        verified_horizontal_lines.sort()
        
        # Store the detected lines and the visualization
        self.vertical_lines = verified_vertical_lines
        self.horizontal_lines = verified_horizontal_lines
        self.line_detection_image = vis_image
        
        # Log the number of detected lines
        print(f"Detected {len(verified_vertical_lines)} vertical lines and {len(verified_horizontal_lines)} horizontal lines")