import numpy as np
import cv2
from scipy import stats
import pywt

class FeatureExtractor:
    """Extract features for steganography detection"""
    
    @staticmethod
    def extract_lsb_features(image_path):
        """Extract LSB-specific features"""
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return None
        
        # LSB plane analysis
        lsb_plane = img & 1
        
        # Statistical features
        features = []
        
        # LSB distribution
        hist, _ = np.histogram(lsb_plane, bins=2, density=True)
        features.extend(hist)
        
        # Correlation features
        height, width = img.shape
        horizontal_corr = np.corrcoef(lsb_plane[:-1, :].flatten(), 
                                    lsb_plane[1:, :].flatten())[0,1]
        vertical_corr = np.corrcoef(lsb_plane[:, :-1].flatten(), 
                                  lsb_plane[:, 1:].flatten())[0,1]
        
        features.extend([horizontal_corr, vertical_corr])
        
        return np.nan_to_num(features)
    
    @staticmethod
    def extract_dct_features(image_path):
        """Extract DCT-specific features"""
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return None
        
        # DCT coefficient analysis
        from scipy.fftpack import dct
        features = []
        
        # Process in 8x8 blocks
        for i in range(0, img.shape[0]-7, 8):
            for j in range(0, img.shape[1]-7, 8):
                block = img[i:i+8, j:j+8].astype(np.float32)
                dct_block = dct(dct(block.T, norm='ortho').T, norm='ortho')
                
                # Extract mid-frequency coefficients
                mid_freq = [dct_block[3,4], dct_block[4,3], dct_block[4,4]]
                features.extend(mid_freq)
        
        # Statistical moments of DCT coefficients
        if len(features) > 0:
            stats_features = [
                np.mean(features),
                np.std(features),
                stats.skew(features),
                stats.kurtosis(features)
            ]
            return np.nan_to_num(stats_features)
        
        return None
    
    @staticmethod
    def extract_all_features(image_path):
        """Extract comprehensive feature set"""
        all_features = []
        
        # LSB features
        lsb_feats = FeatureExtractor.extract_lsb_features(image_path)
        if lsb_feats is not None:
            all_features.extend(lsb_feats)
        
        # DCT features
        dct_feats = FeatureExtractor.extract_dct_features(image_path)
        if dct_feats is not None:
            all_features.extend(dct_feats)
        
        return np.array(all_features) if all_features else None