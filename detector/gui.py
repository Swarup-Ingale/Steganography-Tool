import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
from detector.dataset import build_dataset_from_folders
from detector.model import StegoLogReg, domain_contributions
from detector.features import extract_features

class DetectorGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Stego Detector (LSB + DCT + DWT)")
        self.geometry("720x540")
        self.minsize(700, 520)
        self.model = None
        self.model_path = os.path.join(os.getcwd(), "data", "models", "stego_model.json")

        nb = ttk.Notebook(self); nb.pack(fill="both", expand=True, padx=10, pady=10)
        self.train_tab = ttk.Frame(nb); self.detect_tab = ttk.Frame(nb)
        nb.add(self.train_tab, text="Train"); nb.add(self.detect_tab, text="Detect")

        self._build_train(); self._build_detect()

    def _build_train(self):
        pad = {"padx":8, "pady":6}
        lf = ttk.LabelFrame(self.train_tab, text="Folders")
        lf.pack(fill="x", **pad)
        self.covers_var = tk.StringVar(); self.lsb_var = tk.StringVar(); self.dct_var = tk.StringVar(); self.dwt_var = tk.StringVar()
        def row(r, label, var, cmd):
            ttk.Label(lf, text=label).grid(row=r, column=0, sticky="w", padx=6, pady=4)
            ttk.Entry(lf, textvariable=var).grid(row=r, column=1, sticky="ew", padx=6, pady=4)
            ttk.Button(lf, text="Browse...", command=cmd).grid(row=r, column=2, padx=6, pady=4)
        row(0, "Covers:", self.covers_var, self.pick_covers)
        row(1, "LSB stego:", self.lsb_var, lambda: self.pick_folder(self.lsb_var))
        row(2, "DCT stego:", self.dct_var, lambda: self.pick_folder(self.dct_var))
        row(3, "DWT stego:", self.dwt_var, lambda: self.pick_folder(self.dwt_var))
        lf.columnconfigure(1, weight=1)

        path_row = ttk.Frame(self.train_tab); path_row.pack(fill="x", **pad)
        ttk.Label(path_row, text="Model file:").pack(side="left")
        self.model_path_var = tk.StringVar(value=self.model_path)
        ttk.Entry(path_row, textvariable=self.model_path_var).pack(side="left", fill="x", expand=True, padx=(6,4))
        ttk.Button(path_row, text="Browse...", command=self.pick_model_save).pack(side="left")

        btns = ttk.Frame(self.train_tab); btns.pack(fill="x", **pad)
        ttk.Button(btns, text="Train", command=self.do_train).pack(side="left", padx=6)
        ttk.Button(btns, text="Load Model", command=self.do_load_model).pack(side="left", padx=6)

        self.train_status = ttk.Label(self.train_tab, text="Status: Ready")
        self.train_status.pack(fill="x", padx=12, pady=(4,8))

    def _build_detect(self):
        pad = {"padx":8,"pady":6}
        lf = ttk.LabelFrame(self.detect_tab, text="Image")
        lf.pack(fill="x", **pad)
        self.image_var = tk.StringVar()
        ttk.Entry(lf, textvariable=self.image_var).pack(side="left", fill="x", expand=True, padx=(8,4), pady=8)
        ttk.Button(lf, text="Browse...", command=self.pick_image).pack(side="left", padx=(4,8), pady=8)

        ttk.Button(self.detect_tab, text="Analyze", command=self.do_predict).pack(anchor="w", padx=12, pady=6)

        self.result_txt = tk.Text(self.detect_tab, height=15, wrap="word")
        self.result_txt.pack(fill="both", expand=True, padx=10, pady=8)

    # Handlers
    def pick_folder(self, var):
        p = filedialog.askdirectory(title="Select folder")
        if p: var.set(p)

    def pick_covers(self):
        self.pick_folder(self.covers_var)

    def pick_model_save(self):
        p = filedialog.asksaveasfilename(title="Save model as", defaultextension=".json",
                                         initialfile="stego_model.json",
                                         filetypes=[("JSON","*.json"), ("All files","*.*")])
        if p: self.model_path_var.set(p)

    def pick_image(self):
        p = filedialog.askopenfilename(title="Select image",
                                       filetypes=[("Images","*.png *.bmp *.jpg *.jpeg *.tif *.tiff *.webp *.gif"),
                                                  ("All files","*.*")])
        if p: self.image_var.set(p)

    def do_train(self):
        covers = self.covers_var.get().strip()
        dirs = [self.lsb_var.get().strip(), self.dct_var.get().strip(), self.dwt_var.get().strip()]
        stego_dirs = [d for d in dirs if d]
        if not covers or not stego_dirs:
            messagebox.showwarning("Train", "Select covers and at least one stego folder.")
            return
        try:
            X,y,names = build_dataset_from_folders(covers, stego_dirs)
            model = StegoLogReg(); model.names = names
            model.fit(X,y, lr=0.1, epochs=1000, reg=1e-2)
            model.save(self.model_path_var.get().strip())
            self.model = model
            prob = model.predict_proba(X); acc = float(((prob>=0.5).astype(int)==y).mean())
            self.train_status.config(text=f"Trained. Acc: {acc:.3f}. Saved: {self.model_path_var.get().strip()}")
            messagebox.showinfo("Train", f"Done. Acc: {acc:.3f}")
        except Exception as e:
            messagebox.showerror("Train", f"Failed: {e}")

    def do_load_model(self):
        p = filedialog.askopenfilename(title="Select model .json", filetypes=[("JSON","*.json"),("All files","*.*")])
        if not p: return
        try:
            self.model = StegoLogReg.load(p)
            self.model_path_var.set(p)
            messagebox.showinfo("Model", "Model loaded.")
        except Exception as e:
            messagebox.showerror("Model", f"Failed to load: {e}")

    def do_predict(self):
        imgp = self.image_var.get().strip()
        if not imgp or not os.path.exists(imgp):
            messagebox.showwarning("Detect", "Pick an image.")
            return
        if self.model is None:
            if os.path.exists(self.model_path_var.get().strip()):
                self.model = StegoLogReg.load(self.model_path_var.get().strip())
            else:
                messagebox.showwarning("Model", "Load or train a model first.")
                return
        try:
            img = cv2.imread(imgp, cv2.IMREAD_COLOR)
            x, names = extract_features(img)
            self.model.names = names
            prob = float(self.model.predict_proba(x.reshape(1,-1))[0])
            contrib = domain_contributions(self.model, x, names)
            verdict = "LIKELY STEGO" if prob >= 0.5 else "LIKELY CLEAN"
            self.result_txt.delete("1.0", "end")
            self.result_txt.insert("1.0", f"Image: {imgp}\n")
            self.result_txt.insert("end", f"Stego probability: {prob:.4f}\n")
            self.result_txt.insert("end", f"Verdict: {verdict}\n")
            self.result_txt.insert("end", f"Contributions (logit): {contrib}\n")
        except Exception as e:
            messagebox.showerror("Detect", f"Failed: {e}")

if __name__ == "__main__":
    app = DetectorGUI()
    app.mainloop()