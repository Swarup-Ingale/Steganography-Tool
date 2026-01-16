import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from detector.model import SteganoDetector
import threading

class DetectorGUI:
    """Dedicated GUI for steganography detection"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Steganography Detector")
        self.root.geometry("600x400")
        
        self.detector = SteganoDetector()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # Image selection
        ttk.Label(main_frame, text="Select Image:").grid(row=0, column=0, sticky='w', pady=5)
        self.image_path = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.image_path, width=50).grid(row=0, column=1, pady=5, padx=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_image).grid(row=0, column=2, pady=5)
        
        # Analyze button
        ttk.Button(main_frame, text="Analyze for Steganography", 
                  command=self.analyze_image).grid(row=1, column=1, pady=10)
        
        # Results area
        ttk.Label(main_frame, text="Analysis Results:").grid(row=2, column=0, sticky='w', pady=5)
        self.results_text = tk.Text(main_frame, width=70, height=15, state='disabled')
        self.results_text.grid(row=3, column=0, columnspan=3, pady=5)
        
        # Scrollbar for results
        scrollbar = ttk.Scrollbar(main_frame, orient='vertical', command=self.results_text.yview)
        scrollbar.grid(row=3, column=3, sticky='ns')
        self.results_text.configure(yscrollcommand=scrollbar.set)
    
    def browse_image(self):
        """Browse for image file"""
        filename = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff")]
        )
        if filename:
            self.image_path.set(filename)
    
    def analyze_image(self):
        """Analyze selected image"""
        if not self.image_path.get():
            messagebox.showerror("Error", "Please select an image file")
            return
        
        # Disable button during analysis
        self.root.config(cursor="watch")
        
        def analysis_thread():
            try:
                result = self.detector.detect(self.image_path.get())
                self.root.after(0, lambda: self.display_results(result))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Analysis failed: {e}"))
            finally:
                self.root.after(0, lambda: self.root.config(cursor=""))
        
        threading.Thread(target=analysis_thread, daemon=True).start()
    
    def display_results(self, result):
        """Display analysis results"""
        self.results_text.config(state='normal')
        self.results_text.delete('1.0', tk.END)
        
        if 'error' in result:
            self.results_text.insert(tk.END, f"Error during analysis:\n{result['error']}")
        else:
            self.results_text.insert(tk.END, "STEGANOGRAPHY ANALYSIS RESULTS\n")
            self.results_text.insert(tk.END, "=" * 40 + "\n\n")
            
            self.results_text.insert(tk.END, f"Detection: {result['prediction']}\n")
            self.results_text.insert(tk.END, f"Confidence: {result['confidence']:.2%}\n\n")
            
            self.results_text.insert(tk.END, "Detailed Probabilities:\n")
            for technique, probability in result['probabilities'].items():
                self.results_text.insert(tk.END, f"  {technique}: {probability:.2%}\n")
            
            # Interpretation
            self.results_text.insert(tk.END, "\nInterpretation:\n")
            if result['prediction'] == 'Clean':
                self.results_text.insert(tk.END, "The image appears to be clean with no steganography detected.\n")
            else:
                self.results_text.insert(tk.END, 
                    f"The image likely contains {result['prediction']} steganography.\n")
        
        self.results_text.config(state='disabled')

def main():
    root = tk.Tk()
    app = DetectorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()