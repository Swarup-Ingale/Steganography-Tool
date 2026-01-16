import numpy as np
from PIL import Image
import cv2
from scipy.fftpack import dct, idct

class DCTSteganography:
    """
    DCT (Discrete Cosine Transform) based Steganography
    """
    
    @staticmethod
    def encode(image_path, secret_data, output_path, quality=0.1):
        """
        Encode secret data using DCT coefficients
        
        Args:
            image_path (str): Path to cover image
            secret_data (str): Secret message to hide
            output_path (str): Path to save stego image
            quality (float): Embedding strength (0-1)
            
        Returns:
            bool: Success status
        """
        try:
            # Read and convert to YCbCr
            img = cv2.imread(image_path)
            img_yuv = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)
            
            # Convert secret to binary
            binary_secret = ''.join(format(ord(i), '08b') for i in secret_data)
            binary_secret += '1111111111111110'  # End delimiter
            
            # Process Y channel (luminance)
            y_channel = img_yuv[:,:,0].astype(np.float32)
            h, w = y_channel.shape
            
            # Embed in 8x8 blocks
            data_index = 0
            for i in range(0, h-7, 8):
                for j in range(0, w-7, 8):
                    if data_index >= len(binary_secret):
                        break
                    
                    # Extract 8x8 block
                    block = y_channel[i:i+8, j:j+8]
                    
                    # Apply DCT
                    dct_block = dct(dct(block.T, norm='ortho').T, norm='ortho')
                    
                    # Embed bit in mid-frequency coefficient
                    if data_index < len(binary_secret):
                        bit = int(binary_secret[data_index])
                        # Modify a mid-frequency coefficient
                        dct_block[4,4] = dct_block[4,4] * (1 - quality) + bit * quality * 10
                        data_index += 1
                    
                    # Inverse DCT
                    idct_block = idct(idct(dct_block.T, norm='ortho').T, norm='ortho')
                    y_channel[i:i+8, j:j+8] = idct_block
            
            # Convert back to BGR
            img_yuv[:,:,0] = np.clip(y_channel, 0, 255)
            stego_img = cv2.cvtColor(img_yuv, cv2.COLOR_YUV2BGR)
            
            # Save image
            cv2.imwrite(output_path, stego_img)
            return True
            
        except Exception as e:
            print(f"DCT Encoding Error: {e}")
            return False
    
    @staticmethod
    def decode(image_path, quality=0.1):
        """
        Decode secret data from DCT stego image
        
        Args:
            image_path (str): Path to stego image
            quality (float): Embedding strength used during encoding
            
        Returns:
            str: Decoded secret message
        """
        try:
            # Read and convert to YCbCr
            img = cv2.imread(image_path)
            img_yuv = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)
            y_channel = img_yuv[:,:,0].astype(np.float32)
            h, w = y_channel.shape
            
            binary_data = ""
            
            # Extract from 8x8 blocks
            for i in range(0, h-7, 8):
                for j in range(0, w-7, 8):
                    # Extract 8x8 block
                    block = y_channel[i:i+8, j:j+8]
                    
                    # Apply DCT
                    dct_block = dct(dct(block.T, norm='ortho').T, norm='ortho')
                    
                    # Extract bit from mid-frequency coefficient
                    coefficient = dct_block[4,4]
                    bit = '1' if coefficient > 5 else '0'
                    binary_data += bit
            
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
            print(f"DCT Decoding Error: {e}")
            return ""