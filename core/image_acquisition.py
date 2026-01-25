
import os
import cv2
import numpy as np
from datetime import datetime
from pathlib import Path

class ImageAcquisitionService:
    """Handle image acquisition from webcam, file, or a dummy default"""
    
    def __init__(self, config):
        self.config = config
    
    def acquire(self, source='ask', selected_item=None):
        """Acquire image based on source type"""

        if source == 'webcam':
            return self.capture_webcam()
        elif source == 'file':
            return self.load_from_file()
        elif source == 'default':
            return self.create_test_pattern(selected_item)
        else:
            return self._interactive_select(selected_item)
    
    def capture_webcam_image(self):
        """Capture single frame from webcam"""

        color_mode = self.config.acquisition_colors
        mode_str = "COLOR" if color_mode else "GRAYSCALE"
        
        print("\nOpening webcam... Press SPACE to capture, ESC to cancel")
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("✗ Failed to open webcam")
            return None
        
        # Set resolution if configured
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.image_width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.image_height)
        
        image = None

        while True:
            ret, frame = cap.read()

            if not ret:
                print("✗ Failed to read from webcam")
                break
            
            # Resize to target dimensions
            frame_resized = cv2.resize(frame, (self.config.image_width, self.config.image_height))
            
            # Add overlay info
            info_text = f"Modality: {self.config.modality_type} | Station: {self.config.station_name}"
            cv2.putText(frame_resized, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.6, (0, 255, 0), 2)
            cv2.putText(frame_resized, "SPACE: Capture | ESC: Cancel", (10, frame_resized.shape[0] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            cv2.imshow('DICOM Modality Simulator', frame_resized)
            key = cv2.waitKey(1)
            
            if key == 32:  # SPACE
                if color_mode:
                    image = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
                    print("✓ Color image captured from webcam")
                else:
                    image = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)
                    print("✓ Grayscale image captured from webcam")
                break
            elif key == 27:  # ESC
                print("Capture cancelled")
                break
        
        cap.release()
        cv2.destroyAllWindows()

        return image
    
    def load_from_file(self):
        """Load image from file"""

        color_mode = self.config.acquisition_colors

        print("\nEnter image file path (or drag and drop):")
        file_path = input("> ").strip().strip('"').strip("'")
        
        if not os.path.exists(file_path):
            print(f"✗ File not found: {file_path}")
            return None
        
        try:
            # Load image
            if color_mode:
                image = cv2.imread(file_path, cv2.IMREAD_COLOR)
                if image is not None:
                    # Convert BGR to RGB (swap red and blue channels)
                    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    mode_str = "color"
            else:
                image = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
                mode_str = "grayscale"

            if image is None:
                print("✗ Failed to load image")
                return None
            
            # Resize to target dimensions
            image = cv2.resize(image, (self.config.image_width, self.config.image_height))
            print(f"✓ {mode_str.capitalize()} Image loaded from file: {Path(file_path).name}")
            return image

        except Exception as e:
            print(f"✗ Error loading image: {e}")
            return None
    
    def create_test_image(self, selected_item):
        """Create a default test pattern image"""

        color_mode = self.config.acquisition_colors

        print(f"\nGenerating default test pattern ({'color' if color_mode else 'grayscale'})...")
        
        # Create checkerboard pattern
        square_size = 64
        
        if color_mode:
            # Create colorful checkerboard pattern
            image = np.zeros((self.config.image_height, self.config.image_width, 3), dtype=np.uint8)
            colors = [
                (255, 0, 0),    # Red
                (0, 255, 0),    # Green
                (0, 0, 255),    # Blue
                (255, 255, 0),  # Yellow
                (255, 0, 255),  # Magenta
                (0, 255, 255),  # Cyan
            ]
            
            for i in range(0, self.config.image_height, square_size):
                for j in range(0, self.config.image_width, square_size):
                    color_idx = ((i // square_size) + (j // square_size)) % len(colors)
                    image[i:i+square_size, j:j+square_size] = colors[color_idx]
            
            text_color = (255, 255, 255)  # White text
        else:
            # Create grayscale checkerboard pattern
            image = np.zeros((self.config.image_height, self.config.image_width), dtype=np.uint8)
            
            for i in range(0, self.config.image_height, square_size):
                for j in range(0, self.config.image_width, square_size):
                    if (i // square_size + j // square_size) % 2 == 0:
                        image[i:i+square_size, j:j+square_size] = 255
            
            text_color = 128  # Gray text

        # Add text overlay
        patient_name = getattr(selected_item, 'PatientName', 'TEST') if selected_item else 'TEST'
        cv2.putText(image, f"Patient: {patient_name}", (20, 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, 128, 2)
        cv2.putText(image, f"Modality: {self.config.modality_type}", (20, 80), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, 128, 2)
        cv2.putText(image, f"Station: {self.config.station_name}", (20, 120), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, 128, 2)
        cv2.putText(image, f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", (20, 160), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, 128, 2)
        cv2.putText(image, f"Mode: {'COLOR' if color_mode else 'GRAYSCALE'}", (20, 200), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color, 2)
        
        print("✓ Default test pattern generated")

        return image
    
    def _interactive_select(self, selected_item):
        """Interactive source selection"""

        print("\n=== Image Acquisition ===")
        print("1. Webcam")
        print("2. File")
        print("3. Default Test Pattern")
        choice = input("Select source: ").strip()
        
        if choice == '1':
            return self.capture_webcam_image()
        elif choice == '2':
            return self.load_from_file()
        elif choice == '3':
            return self.create_test_image(selected_item)
        else:
            print("Invalid choice")
            return None
