import numpy as np
from PIL import Image
import pywt
import cv2

class DWTSteganography:
    """
    DWT (Discrete Wavelet Transform) based Steganography
    """
    
    @staticmethod
    def encode(image_path, secret_data, output_path, wavelet='haar', level=1):
        """
        Encode secret data using DWT coefficients
        
        Args:
            image_path (str): Path to cover image
            secret_data (str): Secret message to hide
            output_path (str): Path to save stego image
            wavelet (str): Wavelet type
            level (int): Decomposition level
            
        Returns:
            bool: Success status
        """
        try:
            # Read image
            img = cv2.imread(image_path)
            img_yuv = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)
            y_channel = img_yuv[:,:,0].astype(np.float32)
            
            # Convert secret to binary
            binary_secret = ''.join(format(ord(i), '08b') for i in secret_data)
            binary_secret += '1111111111111110'  # End delimiter
            
            # Apply DWT
            coeffs = pywt.wavedec2(y_channel, wavelet, level=level)
            cA = coeffs[0]  # Approximation coefficients
            cHVs = coeffs[1:]  # Detail coefficients
            
            # Embed in detail coefficients (cH - horizontal details)
            cH = cHVs[0][0]
            data_index = 0
            
            # Flatten and embed
            cH_flat = cH.flatten()
            for i in range(len(cH_flat)):
                if data_index >= len(binary_secret):
                    break
                if abs(cH_flat[i]) > 1.0:  # Only modify significant coefficients
                    bit = int(binary_secret[data_index])
                    cH_flat[i] = cH_flat[i] * 0.99 + bit * 0.1
                    data_index += 1
            
            cH_modified = cH_flat.reshape(cH.shape)
            cHVs_modified = [(cH_modified, cHVs[0][1], cHVs[0][2])] + cHVs[1:]
            
            # Inverse DWT
            coeffs_modified = [cA] + cHVs_modified
            y_channel_modified = pywt.waverec2(coeffs_modified, wavelet)
            
            # Ensure same shape
            y_channel_modified = y_channel_modified[:y_channel.shape[0], :y_channel.shape[1]]
            
            # Convert back
            img_yuv[:,:,0] = np.clip(y_channel_modified, 0, 255)
            stego_img = cv2.cvtColor(img_yuv, cv2.COLOR_YUV2BGR)
            
            cv2.imwrite(output_path, stego_img)
            return True
            
        except Exception as e:
            print(f"DWT Encoding Error: {e}")
            return False
    
    @staticmethod
    def decode(image_path, wavelet='haar', level=1):
        """
        Decode secret data from DWT stego image
        
        Args:
            image_path (str): Path to stego image
            wavelet (str): Wavelet type used during encoding
            level (int): Decomposition level used during encoding
            
        Returns:
            str: Decoded secret message
        """
        try:
            # Read image
            img = cv2.imread(image_path)
            img_yuv = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)
            y_channel = img_yuv[:,:,0].astype(np.float32)
            
            # Apply DWT
            coeffs = pywt.wavedec2(y_channel, wavelet, level=level)
            cH = coeffs[1][0]  # Horizontal detail coefficients
            
            binary_data = ""
            cH_flat = cH.flatten()
            
            # Extract bits from significant coefficients
            for i in range(len(cH_flat)):
                if abs(cH_flat[i]) > 1.0:
                    bit = '1' if cH_flat[i] > 0.05 else '0'
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
            print(f"DWT Decoding Error: {e}")
            return ""