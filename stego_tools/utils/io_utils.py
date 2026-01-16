from PIL import Image
import os

class IOUtils:
    """Utility functions for input/output operations"""
    
    @staticmethod
    def validate_image(image_path):
        """Validate if file is a supported image"""
        try:
            with Image.open(image_path) as img:
                return img.format in ['JPEG', 'PNG', 'BMP', 'TIFF']
        except:
            return False
    
    @staticmethod
    def get_image_info(image_path):
        """Get image dimensions and size"""
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                file_size = os.path.getsize(image_path)
                return {
                    'width': width,
                    'height': height,
                    'format': img.format,
                    'mode': img.mode,
                    'size_bytes': file_size
                }
        except Exception as e:
            return None
    
    @staticmethod
    def create_directory(path):
        """Create directory if it doesn't exist"""
        os.makedirs(path, exist_ok=True)