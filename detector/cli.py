import argparse
import sys
import os
from detector.model import SteganoDetector

def main():
    parser = argparse.ArgumentParser(description='Steganography Detection Tool')
    parser.add_argument('image_path', help='Path to the image to analyze')
    parser.add_argument('--model', '-m', help='Path to trained model', default=None)
    
    args = parser.parse_args()
    
    if not os.path.exists(args.image_path):
        print(f"Error: Image file '{args.image_path}' not found")
        sys.exit(1)
    
    # Initialize detector
    detector = SteganoDetector(args.model)
    
    # Perform detection
    print(f"Analyzing image: {args.image_path}")
    result = detector.detect(args.image_path)
    
    if 'error' in result:
        print(f"Error: {result['error']}")
        sys.exit(1)
    
    # Display results
    print("\n" + "="*50)
    print("STEGANOGRAPHY DETECTION RESULTS")
    print("="*50)
    print(f"Prediction: {result['prediction']}")
    print(f"Confidence: {result['confidence']:.2%}")
    print("\nDetailed Probabilities:")
    for technique, probability in result['probabilities'].items():
        print(f"  {technique}: {probability:.2%}")

if __name__ == "__main__":
    main()