import torch
import torch.nn as nn
from models.tri_tool_minimal import TriToolSteganoDetector

class SteganoDetector:
    """Steganography detection wrapper"""
    
    def __init__(self, model_path=None, device='cpu'):
        self.device = device
        self.model = TriToolSteganoDetector()
        
        if model_path:
            self.load_model(model_path)
        else:
            self.model.to(device)
    
    def load_model(self, model_path):
        """Load trained model"""
        try:
            checkpoint = torch.load(model_path, map_location=self.device)
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.model.to(self.device)
            self.model.eval()
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
    
    def preprocess_image(self, image_path):
        """Preprocess image for model input"""
        from PIL import Image
        import torchvision.transforms as transforms
        
        transform = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
        
        image = Image.open(image_path).convert('RGB')
        return transform(image).unsqueeze(0)
    
    def detect(self, image_path):
        """Detect steganography in image"""
        try:
            # Preprocess image
            input_tensor = self.preprocess_image(image_path)
            input_tensor = input_tensor.to(self.device)
            
            # Run inference
            with torch.no_grad():
                outputs = self.model(input_tensor)
                probabilities = torch.softmax(outputs, dim=1)
                predicted_class = torch.argmax(outputs, dim=1).item()
            
            # Class mapping
            classes = ['Clean', 'LSB', 'DCT', 'DWT']
            confidence = probabilities[0][predicted_class].item()
            
            return {
                'prediction': classes[predicted_class],
                'confidence': confidence,
                'probabilities': {
                    cls: prob.item() for cls, prob in zip(classes, probabilities[0])
                }
            }
            
        except Exception as e:
            return {'error': str(e)}