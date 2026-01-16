import os
import numpy as np
from PIL import Image
import torch
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as transforms

class SteganoDataset(Dataset):
    """Dataset for steganography detection"""
    
    def __init__(self, image_dir, transform=None, is_train=True):
        self.image_dir = image_dir
        self.transform = transform
        self.is_train = is_train
        
        # Collect image paths and labels
        self.image_paths = []
        self.labels = []
        
        # Expected structure: image_dir/class_name/*.jpg
        for class_name in ['clean', 'lsb', 'dct', 'dwt']:
            class_dir = os.path.join(image_dir, class_name)
            if os.path.exists(class_dir):
                for img_file in os.listdir(class_dir):
                    if img_file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                        self.image_paths.append(os.path.join(class_dir, img_file))
                        self.labels.append(self.class_to_label(class_name))
    
    def class_to_label(self, class_name):
        """Convert class name to numerical label"""
        class_map = {'clean': 0, 'lsb': 1, 'dct': 2, 'dwt': 3}
        return class_map.get(class_name, 0)
    
    def __len__(self):
        return len(self.image_paths)
    
    def __getitem__(self, idx):
        img_path = self.image_paths[idx]
        label = self.labels[idx]
        
        # Load image
        image = Image.open(img_path).convert('RGB')
        
        if self.transform:
            image = self.transform(image)
        
        return image, label

def get_transforms():
    """Get data transforms for training and validation"""
    train_transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(10),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                           std=[0.229, 0.224, 0.225])
    ])
    
    val_transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                           std=[0.229, 0.224, 0.225])
    ])
    
    return train_transform, val_transform

def create_data_loaders(data_dir, batch_size=32, num_workers=4):
    """Create data loaders for training and validation"""
    train_transform, val_transform = get_transforms()
    
    train_dataset = SteganoDataset(
        os.path.join(data_dir, 'train'),
        transform=train_transform
    )
    
    val_dataset = SteganoDataset(
        os.path.join(data_dir, 'val'),
        transform=val_transform
    )
    
    train_loader = DataLoader(
        train_dataset, batch_size=batch_size, 
        shuffle=True, num_workers=num_workers
    )
    
    val_loader = DataLoader(
        val_dataset, batch_size=batch_size, 
        shuffle=False, num_workers=num_workers
    )
    
    return train_loader, val_loader