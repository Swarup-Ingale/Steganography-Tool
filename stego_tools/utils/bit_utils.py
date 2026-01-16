import numpy as np

class BitUtils:
    """Utility functions for bit manipulation"""
    
    @staticmethod
    def text_to_binary(text):
        """Convert text to binary string"""
        return ''.join(format(ord(char), '08b') for char in text)
    
    @staticmethod
    def binary_to_text(binary_str):
        """Convert binary string to text"""
        text = ""
        for i in range(0, len(binary_str), 8):
            byte = binary_str[i:i+8]
            if len(byte) == 8:
                text += chr(int(byte, 2))
        return text
    
    @staticmethod
    def file_to_binary(file_path):
        """Convert file to binary string"""
        with open(file_path, 'rb') as file:
            binary_data = file.read()
        return ''.join(format(byte, '08b') for byte in binary_data)
    
    @staticmethod
    def binary_to_file(binary_str, output_path):
        """Convert binary string to file"""
        bytes_data = bytearray()
        for i in range(0, len(binary_str), 8):
            byte = binary_str[i:i+8]
            if len(byte) == 8:
                bytes_data.append(int(byte, 2))
        
        with open(output_path, 'wb') as file:
            file.write(bytes_data)