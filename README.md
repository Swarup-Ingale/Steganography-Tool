# Steganography Toolkit

A comprehensive steganography tool with multiple embedding techniques and detection capabilities.

## Features
- LSB (Least Significant Bit) Steganography
- DCT (Discrete Cosine Transform) based Steganography  
- DWT (Discrete Wavelet Transform) based Steganography
- AI-powered Steganography Detection
- User-friendly GUI

## Installation

    ```bash
    # Clone the repository
    git clone <repository-url>
    cd steganography-toolkit

    # Install required dependencies
    pip install -r requirements.txt

## How to run

    ```bash
    python models/tri_tool_minimal.py

## Usage Instructions

    Launch the tool using the command above.

1. Select the steganography technique: LSB, DCT, or DWT.

2. Choose an image and enter the text you want to hide.

3. Save the output image containing the hidden message.

4. To decrypt, select the same technique and choose the stego-image to extract and read the hidden text.
