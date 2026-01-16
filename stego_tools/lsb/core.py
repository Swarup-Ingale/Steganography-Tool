import numpy as np
from PIL import Image
import cv2

class LSBSteganography:
    """
    LSB (Least Significant Bit) Steganography implementation
    """
    
    @staticmethod
    def encode(image_path, secret_data, output_path):
        """
        Encode secret data into image using LSB
        
        Args:
            image_path (str): Path to cover image
            secret_data (str): Secret message to hide
            output_path (str): Path to save stego image
            
        Returns:
            bool: Success status
        """
        try:
            # Read image
            img = Image.open(image_path)
            img_array = np.array(img)
            
            # Convert secret data to binary
            binary_secret = ''.join(format(ord(i), '08b') for i in secret_data)
            binary_secret += '1111111111111110'  # End delimiter
            
            # Get image dimensions
            h, w = img_array.shape[:2]
            if len(img_array.shape) == 3:
                c = img_array.shape[2]
            else:
                c = 1
                img_array = img_array.reshape(h, w, 1)
            
            # Check capacity
            total_pixels = h * w * c
            if len(binary_secret) > total_pixels:
                raise ValueError("Secret data too large for image")
            
            # Embed data
            data_index = 0
            for i in range(h):
                for j in range(w):
                    for k in range(c):
                        if data_index < len(binary_secret):
                            # Clear LSB and set to secret bit
                            pixel = img_array[i, j, k]
                            pixel_bin = format(pixel, '08b')
                            new_pixel_bin = pixel_bin[:-1] + binary_secret[data_index]
                            img_array[i, j, k] = int(new_pixel_bin, 2)
                            data_index += 1
            
            # Save stego image
            stego_img = Image.fromarray(img_array.astype('uint8'))
            stego_img.save(output_path)
            return True
            
        except Exception as e:
            print(f"LSB Encoding Error: {e}")
            return False
    
    @staticmethod
    def decode(image_path):
        """
        Decode secret data from LSB stego image
        
        Args:
            image_path (str): Path to stego image
            
        Returns:
            str: Decoded secret message
        """
        try:
            # Read image
            img = Image.open(image_path)
            img_array = np.array(img)
            
            # Get image dimensions
            h, w = img_array.shape[:2]
            if len(img_array.shape) == 3:
                c = img_array.shape[2]
            else:
                c = 1
                img_array = img_array.reshape(h, w, 1)
            
            # Extract LSBs
            binary_data = ""
            for i in range(h):
                for j in range(w):
                    for k in range(c):
                        pixel = img_array[i, j, k]
                        binary_data += format(pixel, '08b')[-1]
            
            # Find end delimiter and extract message
            delimiter = '1111111111111110'
            if delimiter in binary_data:
                binary_data = binary_data[:binary_data.index(delimiter)]
            
            # Convert binary to string
            secret_text = ""
            for i in range(0, len(binary_data), 8):
                byte = binary_data[i:i+8]
                if len(byte) == 8:
                    secret_text += chr(int(byte, 2))
            
            return secret_text
            
        except Exception as e:
            print(f"LSB Decoding Error: {e}")
            return ""
    
    @staticmethod
    def get_capacity(image_path):
        """
        Calculate maximum capacity of image for LSB steganography
        
        Args:
            image_path (str): Path to image
            
        Returns:
            int: Maximum bytes that can be hidden
        """
        img = Image.open(image_path)
        img_array = np.array(img)
        h, w = img_array.shape[:2]
        if len(img_array.shape) == 3:
            c = img_array.shape[2]
        else:
            c = 1
        return (h * w * c) // 8 - 2  # Reserve 2 bytes for delimiter