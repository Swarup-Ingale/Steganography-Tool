import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
from PIL import Image, ImageTk
import threading

# Import steganography tools
from stego_tools.lsb.core import LSBSteganography
from stego_tools.dct.core import DCTSteganography
from stego_tools.dwt.core import DWTSteganography
from detector.model import SteganoDetector

class MultiToolGUI:
    """Main GUI application for steganography toolkit"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Steganography Toolkit")
        self.root.geometry("800x600")
        
        # Initialize detector
        self.detector = SteganoDetector()
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        
        # LSB Tab
        lsb_frame = ttk.Frame(notebook)
        self.setup_lsb_tab(lsb_frame)
        notebook.add(lsb_frame, text="LSB")
        
        # DCT Tab
        dct_frame = ttk.Frame(notebook)
        self.setup_dct_tab(dct_frame)
        notebook.add(dct_frame, text="DCT")
        
        # DWT Tab
        dwt_frame = ttk.Frame(notebook)
        self.setup_dwt_tab(dwt_frame)
        notebook.add(dwt_frame, text="DWT")
        
        # Detection Tab
        detect_frame = ttk.Frame(notebook)
        self.setup_detection_tab(detect_frame)
        notebook.add(detect_frame, text="Detection")
        
        notebook.pack(expand=True, fill='both')
        
    def setup_lsb_tab(self, parent):
        """Setup LSB steganography tab"""
        # Input image
        ttk.Label(parent, text="Cover Image:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.lsb_image_path = tk.StringVar()
        ttk.Entry(parent, textvariable=self.lsb_image_path, width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(parent, text="Browse", command=self.browse_lsb_image).grid(row=0, column=2, padx=5, pady=5)
        
        # Secret message
        ttk.Label(parent, text="Secret Message:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.lsb_secret_text = scrolledtext.ScrolledText(parent, width=50, height=5)
        self.lsb_secret_text.grid(row=1, column=1, columnspan=2, padx=5, pady=5)
        
        # Output path
        ttk.Label(parent, text="Output Image:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.lsb_output_path = tk.StringVar()
        ttk.Entry(parent, textvariable=self.lsb_output_path, width=50).grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(parent, text="Browse", command=self.browse_lsb_output).grid(row=2, column=2, padx=5, pady=5)
        
        # Buttons
        ttk.Button(parent, text="Encode", command=self.encode_lsb).grid(row=3, column=1, padx=5, pady=10)
        ttk.Button(parent, text="Decode", command=self.decode_lsb).grid(row=3, column=2, padx=5, pady=10)
        
        # Capacity info
        self.lsb_capacity_label = ttk.Label(parent, text="")
        self.lsb_capacity_label.grid(row=4, column=0, columnspan=3, padx=5, pady=5)
        
    def setup_dct_tab(self, parent):
        """Setup DCT steganography tab"""
        # Similar structure to LSB tab...
        ttk.Label(parent, text="DCT Steganography - Implementation similar to LSB").pack(pady=20)
        
    def setup_dwt_tab(self, parent):
        """Setup DWT steganography tab"""
        ttk.Label(parent, text="DWT Steganography - Implementation similar to LSB").pack(pady=20)
        
    def setup_detection_tab(self, parent):
        """Setup detection tab"""
        ttk.Label(parent, text="Image to Analyze:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.detect_image_path = tk.StringVar()
        ttk.Entry(parent, textvariable=self.detect_image_path, width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(parent, text="Browse", command=self.browse_detect_image).grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Button(parent, text="Analyze", command=self.analyze_image).grid(row=1, column=1, pady=10)
        
        # Results display
        self.detect_results = scrolledtext.ScrolledText(parent, width=70, height=15)
        self.detect_results.grid(row=2, column=0, columnspan=3, padx=5, pady=5)
        
    def browse_lsb_image(self):
        """Browse for cover image"""
        filename = filedialog.askopenfilename(
            title="Select Cover Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff")]
        )
        if filename:
            self.lsb_image_path.set(filename)
            # Calculate and display capacity
            capacity = LSBSteganography.get_capacity(filename)
            self.lsb_capacity_label.config(text=f"Maximum capacity: {capacity} bytes")
    
    def browse_lsb_output(self):
        """Browse for output location"""
        filename = filedialog.asksaveasfilename(
            title="Save Stego Image",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        if filename:
            self.lsb_output_path.set(filename)
    
    def encode_lsb(self):
        """Encode using LSB"""
        if not all([self.lsb_image_path.get(), self.lsb_output_path.get()]):
            messagebox.showerror("Error", "Please select input and output files")
            return
        
        secret_text = self.lsb_secret_text.get("1.0", tk.END).strip()
        if not secret_text:
            messagebox.showerror("Error", "Please enter secret message")
            return
        
        # Run encoding in thread
        def encode_thread():
            success = LSBSteganography.encode(
                self.lsb_image_path.get(),
                secret_text,
                self.lsb_output_path.get()
            )
            self.root.after(0, lambda: self.encoding_complete(success))
        
        threading.Thread(target=encode_thread, daemon=True).start()
        messagebox.showinfo("Encoding", "Encoding started...")
    
    def encoding_complete(self, success):
        """Callback when encoding completes"""
        if success:
            messagebox.showinfo("Success", "Message encoded successfully!")
        else:
            messagebox.showerror("Error", "Encoding failed!")
    
    def decode_lsb(self):
        """Decode using LSB"""
        filename = filedialog.askopenfilename(
            title="Select Stego Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff")]
        )
        if filename:
            decoded_text = LSBSteganography.decode(filename)
            messagebox.showinfo("Decoded Message", f"Decoded text: {decoded_text}")
    
    def browse_detect_image(self):
        """Browse for image to analyze"""
        filename = filedialog.askopenfilename(
            title="Select Image to Analyze",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff")]
        )
        if filename:
            self.detect_image_path.set(filename)
    
    def analyze_image(self):
        """Analyze image for steganography"""
        if not self.detect_image_path.get():
            messagebox.showerror("Error", "Please select an image to analyze")
            return
        
        def analyze_thread():
            try:
                result = self.detector.detect(self.detect_image_path.get())
                self.root.after(0, lambda: self.display_results(result))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Analysis failed: {e}"))
        
        threading.Thread(target=analyze_thread, daemon=True).start()
    
    def display_results(self, result):
        """Display detection results"""
        self.detect_results.delete('1.0', tk.END)
        
        if 'error' in result:
            self.detect_results.insert(tk.END, f"Error: {result['error']}")
        else:
            self.detect_results.insert(tk.END, f"Prediction: {result['prediction']}\n")
            self.detect_results.insert(tk.END, f"Confidence: {result['confidence']:.2%}\n\n")
            self.detect_results.insert(tk.END, "Probabilities:\n")
            for cls, prob in result['probabilities'].items():
                self.detect_results.insert(tk.END, f"  {cls}: {prob:.2%}\n")

def main():
    root = tk.Tk()
    app = MultiToolGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()