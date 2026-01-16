# File: steg_project/tri_tool_minimal.py
# One-file LSB + DCT-QIM + DWT-QIM GUI with auto-detect decode.
# Deps: pip install opencv-python numpy pywavelets

import os, sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import numpy as np
import cv2

# Try PyWavelets for DWT. If missing, we disable DWT in the GUI.
try:
    import pywt
    HAS_PYWT = True
except Exception:
    HAS_PYWT = False

DEBUG = True
def dprint(*a):
    if DEBUG:
        print(*a)

# ---------------- Bits + IO helpers ----------------
def bytes_to_bits(data: bytes):
    for b in data:
        for i in range(7, -1, -1):
            yield (b >> i) & 1

def bits_to_bytes(bits):
    out = bytearray()
    acc = 0
    n = 0
    for bit in bits:
        acc = (acc << 1) | (bit & 1)
        n += 1
        if n == 8:
            out.append(acc); acc = 0; n = 0
    return bytes(out)

def load_bgr(path: str):
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"Failed to read image: {path}")
    return img

def imread_gray(path: str):
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"Failed to read image: {path}")
    return img

def cv_imwrite(path: str, img) -> bool:
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    root, ext = os.path.splitext(path)
    if not ext:
        ext = ".png"
        path = root + ext
    try:
        if cv2.imwrite(path, img):
            return True
    except Exception:
        pass
    try:
        ok, buf = cv2.imencode(ext, img)
        if not ok:
            return False
        buf.tofile(path)
        return True
    except Exception:
        return False

# ---------------- LSB ----------------
MAGIC_LSB = b"LSB1"
HEADER_BITS = 64

def lsb_capacity_bytes(image_path: str) -> int:
    img = load_bgr(image_path)
    flat = img.flatten()
    return max(0, (flat.size - HEADER_BITS)//8)

def lsb_hide(cover_path: str, out_path: str, text: str, encoding="utf-8"):
    data = text.encode(encoding)
    img = load_bgr(cover_path).copy()
    flat = img.flatten()
    payload = MAGIC_LSB + len(data).to_bytes(4, "big") + data
    needed = len(payload)*8
    if needed > flat.size:
        raise ValueError(f"Not enough capacity (need {len(data)} bytes).")
    i = 0
    for bit in bytes_to_bits(payload):
        flat[i] = (flat[i] & 0xFE) | bit
        i += 1
    out_img = flat.reshape(img.shape)
    if not cv_imwrite(out_path, out_img):
        raise ValueError(f"Failed to write: {out_path}")

def lsb_reveal(stego_path: str, encoding="utf-8", errors="replace") -> str:
    img = load_bgr(stego_path)
    flat = img.flatten()
    if flat.size < HEADER_BITS:
        raise ValueError("Image too small for header.")
    header = bits_to_bytes([flat[i] & 1 for i in range(HEADER_BITS)])
    if len(header) < 8 or header[:4] != MAGIC_LSB:
        raise ValueError("No valid LSB payload (bad header).")
    length = int.from_bytes(header[4:8], "big")
    total = HEADER_BITS + length*8
    if total > flat.size:
        raise ValueError("Truncated LSB payload.")
    data_bits = [flat[i] & 1 for i in range(HEADER_BITS, HEADER_BITS + length*8)]
    return bits_to_bytes(data_bits).decode(encoding, errors=errors)

# ---------------- DCT-QIM ----------------
MAGIC_DCT = b"DCT1"
COEFF_POSITIONS = [(3,3), (4,3), (3,4), (2,3), (3,2), (4,4)]
DELTA = 12.0

def dct_capacity_bytes(image_path: str) -> int:
    img = load_bgr(image_path)
    h, w = img.shape[:2]
    H8, W8 = (h//8)*8, (w//8)*8
    if H8 == 0 or W8 == 0: return 0
    blocks = (H8//8)*(W8//8)
    cap_bits = blocks*len(COEFF_POSITIONS) - HEADER_BITS
    return max(0, cap_bits//8)

def dct_hide(cover_path: str, out_path: str, text: str, encoding="utf-8"):
    data = text.encode(encoding)
    img = load_bgr(cover_path)
    ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    Y = ycrcb[:,:,0].astype(np.float32)
    h, w = Y.shape
    H8, W8 = (h//8)*8, (w//8)*8
    if H8 == 0 or W8 == 0:
        raise ValueError("Image must be at least 8x8.")
    blocks = (H8//8)*(W8//8)
    capacity_bits = blocks*len(COEFF_POSITIONS)
    payload = MAGIC_DCT + len(data).to_bytes(4,"big") + data
    needed = len(payload)*8
    if needed > capacity_bits:
        raise ValueError(f"Not enough capacity (need {len(data)} bytes).")
    bit_it = bytes_to_bits(payload)
    Yw = Y.copy()
    done = False
    for i in range(0, H8, 8):
        for j in range(0, W8, 8):
            dct = cv2.dct(Yw[i:i+8, j:j+8] - 128.0)
            for (r,c) in COEFF_POSITIONS:
                try:
                    bit = next(bit_it)
                except StopIteration:
                    done = True; break
                coeff = dct[r,c]
                q = int(np.rint(coeff/DELTA))
                if (q & 1) != bit:
                    q += 1 if coeff >= 0 else -1
                if q == 0 and bit == 1:
                    q = 1 if coeff >= 0 else -1
                dct[r,c] = float(q*DELTA)
            Yw[i:i+8, j:j+8] = cv2.idct(dct) + 128.0
            if done: break
        if done: break
    ycrcb[:,:,0] = np.clip(Yw, 0, 255).astype(np.uint8)
    out_img = cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)
    if not cv_imwrite(out_path, out_img):
        raise ValueError(f"Failed to write: {out_path}")

def dct_reveal(stego_path: str, encoding="utf-8", errors="replace") -> str:
    img = load_bgr(stego_path)
    ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    Y = ycrcb[:,:,0].astype(np.float32)
    h, w = Y.shape
    H8, W8 = (h//8)*8, (w//8)*8
    if H8 == 0 or W8 == 0:
        raise ValueError("Image must be at least 8x8.")
    def iter_bits():
        for i in range(0, H8, 8):
            for j in range(0, W8, 8):
                dct = cv2.dct(Y[i:i+8, j:j+8] - 128.0)
                for (r,c) in COEFF_POSITIONS:
                    q = int(np.rint(dct[r,c]/DELTA))
                    yield (q & 1) if q != 0 else 0
    bits = iter_bits()
    # header
    header_bits = []
    try:
        for _ in range(HEADER_BITS):
            header_bits.append(next(bits))
    except StopIteration:
        raise ValueError("Image too small for header.")
    header = bits_to_bytes(header_bits)
    if len(header) < 8 or header[:4] != MAGIC_DCT:
        raise ValueError("No valid DCT payload (bad header).")
    length = int.from_bytes(header[4:8], "big")
    data_bits = []
    try:
        for _ in range(length*8):
            data_bits.append(next(bits))
    except StopIteration:
        raise ValueError("Truncated DCT payload.")
    return bits_to_bytes(data_bits).decode(encoding, errors=errors)

# ---------------- DWT-QIM ----------------
MAGIC_DWT = b"DWT1"
WAVELET = "haar"
Q = 14.0  # QIM step

def dwt_capacity_bytes(image_path: str) -> int:
    if not HAS_PYWT: return 0
    img = imread_gray(image_path).astype(np.float32)
    cA,(cH,cV,cD) = pywt.dwt2(img, wavelet=WAVELET, mode="symmetric")
    coeffs = cH.size + cV.size
    return max(0, (coeffs - HEADER_BITS)//8)

def dwt_hide(cover_path: str, out_path: str, text: str, encoding="utf-8"):
    if not HAS_PYWT:
        raise RuntimeError("PyWavelets not installed. Use Python 3.12 or install pywavelets.")
    data = text.encode(encoding)
    img = imread_gray(cover_path).astype(np.float32)
    H,W = img.shape
    payload = MAGIC_DWT + len(data).to_bytes(4,"big") + data
    needed = len(payload)*8
    cA,(cH,cV,cD) = pywt.dwt2(img, wavelet=WAVELET, mode="symmetric")
    coeffs = cH.size + cV.size
    if needed > coeffs:
        raise ValueError(f"Not enough capacity (need {len(data)} bytes).")
    bit_it = bytes_to_bits(payload)
    def embed(arr, written):
        flat = arr.ravel()
        for i in range(flat.size):
            if written >= needed: break
            try:
                bit = next(bit_it)
            except StopIteration:
                break
            cval = flat[i]
            q = int(np.rint(cval/Q))
            if (q & 1) != bit:
                q += 1 if cval >= 0 else -1
            if q == 0 and bit == 1:
                q = 1 if cval >= 0 else -1
            flat[i] = float(q*Q)
            written += 1
        return written
    written = 0
    written = embed(cH, written)
    written = embed(cV, written)
    if written < needed:
        raise RuntimeError("Internal error: ran out of coefficients.")
    rec = pywt.idwt2((cA,(cH,cV,cD)), wavelet=WAVELET, mode="symmetric")
    rec = rec[:H,:W]
    rec = np.clip(rec, 0, 255).astype(np.uint8)
    if not cv_imwrite(out_path, rec):
        raise ValueError(f"Failed to write: {out_path}")

def dwt_reveal(stego_path: str, encoding="utf-8", errors="replace") -> str:
    if not HAS_PYWT:
        raise RuntimeError("PyWavelets not installed.")
    img = imread_gray(stego_path).astype(np.float32)
    cA,(cH,cV,cD) = pywt.dwt2(img, wavelet=WAVELET, mode="symmetric")
    def iter_bits():
        for cval in cH.ravel():
            q = int(np.rint(cval/Q)); yield (q & 1) if q != 0 else 0
        for cval in cV.ravel():
            q = int(np.rint(cval/Q)); yield (q & 1) if q != 0 else 0
    bits = iter_bits()
    header_bits = []
    try:
        for _ in range(HEADER_BITS):
            header_bits.append(next(bits))
    except StopIteration:
        raise ValueError("Image too small for header.")
    header = bits_to_bytes(header_bits)
    if len(header) < 8 or header[:4] != MAGIC_DWT:
        raise ValueError("No valid DWT payload (bad header).")
    length = int.from_bytes(header[4:8], "big")
    data_bits = []
    try:
        for _ in range(length*8):
            data_bits.append(next(bits))
    except StopIteration:
        raise ValueError("Truncated DWT payload.")
    return bits_to_bytes(data_bits).decode(encoding, errors=errors)

# ---------------- GUI ----------------
TECHS = ["LSB", "DCT"] + (["DWT"] if HAS_PYWT else [])

def try_decode_all(stego_path: str):
    errors = {}
    # Try LSB, then DCT, then DWT (if available)
    order = TECHS
    for name in order:
        try:
            if name == "LSB":
                return "LSB", lsb_reveal(stego_path)
            elif name == "DCT":
                return "DCT", dct_reveal(stego_path)
            elif name == "DWT" and HAS_PYWT:
                return "DWT", dwt_reveal(stego_path)
        except Exception as e:
            errors[name] = str(e)
    raise RuntimeError(f"No valid payload found with any technique.\nErrors: {errors}")

class MultiStegoGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tri-Tool Stego (LSB / DCT / DWT)")
        self.geometry("780x580"); self.minsize(740, 540)

        top = ttk.Frame(self, padding=10); top.pack(fill="both", expand=True)

        row1 = ttk.Frame(top); row1.pack(fill="x", pady=(0,8))
        ttk.Label(row1, text="Technique:").pack(side="left")
        self.tech_var = tk.StringVar(value=TECHS[0])
        self.tech_combo = ttk.Combobox(row1, values=TECHS, textvariable=self.tech_var, state="readonly", width=10)
        self.tech_combo.pack(side="left", padx=6)
        self.tech_combo.bind("<<ComboboxSelected>>", self.update_capacity)

        lf = ttk.LabelFrame(top, text="Paths"); lf.pack(fill="x", pady=6)
        self.cover_var = tk.StringVar(); self.out_var = tk.StringVar(); self.stego_var = tk.StringVar()

        ttk.Label(lf, text="Cover (encode):").grid(row=0, column=0, sticky="w", padx=6, pady=4)
        ttk.Entry(lf, textvariable=self.cover_var).grid(row=0, column=1, sticky="ew", padx=6, pady=4)
        ttk.Button(lf, text="Browse...", command=self.pick_cover).grid(row=0, column=2, padx=6, pady=4)

        ttk.Label(lf, text="Output (encode):").grid(row=1, column=0, sticky="w", padx=6, pady=4)
        ttk.Entry(lf, textvariable=self.out_var).grid(row=1, column=1, sticky="ew", padx=6, pady=4)
        ttk.Button(lf, text="Save As...", command=self.pick_out).grid(row=1, column=2, padx=6, pady=4)

        ttk.Label(lf, text="Stego (decode):").grid(row=2, column=0, sticky="w", padx=6, pady=4)
        ttk.Entry(lf, textvariable=self.stego_var).grid(row=2, column=1, sticky="ew", padx=6, pady=4)
        ttk.Button(lf, text="Browse...", command=self.pick_stego).grid(row=2, column=2, padx=6, pady=4)
        lf.columnconfigure(1, weight=1)

        info = ttk.Frame(top); info.pack(fill="x", pady=(0,6))
        self.capacity_lbl = ttk.Label(info, text="Capacity: —"); self.capacity_lbl.pack(side="left", padx=6)
        self.msglen_lbl = ttk.Label(info, text="Message length: 0 bytes"); self.msglen_lbl.pack(side="left", padx=12)

        lf_msg = ttk.LabelFrame(top, text="Message (UTF-8)"); lf_msg.pack(fill="both", expand=True)
        self.msg_text = tk.Text(lf_msg, height=14, wrap="word"); self.msg_text.pack(fill="both", expand=True, padx=8, pady=8)
        self.msg_text.bind("<KeyRelease>", self.update_msglen)

        btns = ttk.Frame(top); btns.pack(fill="x", pady=6)
        ttk.Button(btns, text="Encode", command=self.do_encode).pack(side="left", padx=6)
        ttk.Button(btns, text="Decode", command=self.do_decode).pack(side="left", padx=6)

        tip_text = "Tip: Use PNG/BMP; JPEG is lossy and can break DCT/DWT. DWT requires PyWavelets."
        if not HAS_PYWT: tip_text += " (DWT disabled: PyWavelets not detected)"
        ttk.Label(top, foreground="#666", text=tip_text).pack(anchor="w", pady=(4,0))

    def update_msglen(self, *_):
        text = self.msg_text.get("1.0", "end-1c").encode("utf-8")
        self.msglen_lbl.config(text=f"Message length: {len(text)} bytes")

    def pick_cover(self):
        p = filedialog.askopenfilename(title="Select cover image",
            filetypes=[("Images","*.png *.bmp *.tif *.tiff *.webp *.gif *.jpg *.jpeg"), ("All files","*.*")])
        if p:
            self.cover_var.set(p)
            root, _ = os.path.splitext(p)
            self.out_var.set(root + "_stego.png")
            self.update_capacity()

    def pick_out(self):
        p = filedialog.asksaveasfilename(title="Save stego as", defaultextension=".png",
            filetypes=[("PNG","*.png"), ("BMP","*.bmp"), ("All files","*.*")])
        if p: self.out_var.set(p)

    def pick_stego(self):
        p = filedialog.askopenfilename(title="Select stego image",
            filetypes=[("Images","*.png *.bmp *.tif *.tiff *.webp *.gif *.jpg *.jpeg"), ("All files","*.*")])
        if p: self.stego_var.set(p)

    def update_capacity(self, *_):
        path = self.cover_var.get().strip()
        if not path or not os.path.exists(path):
            self.capacity_lbl.config(text="Capacity: —"); return
        tech = self.tech_var.get()
        try:
            if tech == "LSB":
                cap = lsb_capacity_bytes(path)
            elif tech == "DCT":
                cap = dct_capacity_bytes(path)
            elif tech == "DWT" and HAS_PYWT:
                cap = dwt_capacity_bytes(path)
            else:
                cap = 0
        except Exception:
            cap = 0
        self.capacity_lbl.config(text=f"Capacity: {cap} bytes")

    def do_encode(self):
        cover = self.cover_var.get().strip()
        outp = self.out_var.get().strip()
        msg = self.msg_text.get("1.0","end-1c")
        tech = self.tech_var.get()

        if not cover or not os.path.exists(cover):
            messagebox.showwarning("Encode", "Select a valid cover image."); return
        if not outp:
            root, _ = os.path.splitext(cover); outp = root + "_stego.png"; self.out_var.set(outp)
        if outp.lower().endswith((".jpg",".jpeg")):
            if not messagebox.askyesno("Warning","JPEG is lossy and may break DCT/DWT. Continue?"): return

        dprint(f"[ENC] tech={tech} cover={cover} out={outp} len={len(msg.encode('utf-8'))}")
        try:
            if tech == "LSB":
                lsb_hide(cover, outp, msg)
            elif tech == "DCT":
                dct_hide(cover, outp, msg)
            elif tech == "DWT":
                dwt_hide(cover, outp, msg)
            else:
                raise RuntimeError("Unknown technique")
            messagebox.showinfo("Encode", f"Saved stego to:\n{outp}")
        except Exception as e:
            messagebox.showerror("Encode", f"Failed to encode:\n{e}")

    def do_decode(self):
        stego = self.stego_var.get().strip()
        if not stego or not os.path.exists(stego):
            messagebox.showwarning("Decode", "Select a valid stego image."); return
        tech = self.tech_var.get()
        dprint(f"[DEC] try={tech} stego={stego}")
        try:
            if tech == "LSB":
                msg = lsb_reveal(stego)
            elif tech == "DCT":
                msg = dct_reveal(stego)
            elif tech == "DWT":
                msg = dwt_reveal(stego)
            else:
                raise RuntimeError("Unknown technique")
            self.msg_text.delete("1.0","end"); self.msg_text.insert("1.0", msg)
            messagebox.showinfo("Decode", f"Message revealed using {tech}.")
            return
        except Exception as e:
            dprint(f"[DEC] {tech} failed: {e}")

        # Auto-detect
        try:
            name, msg = try_decode_all(stego)
            self.tech_var.set(name)
            self.msg_text.delete("1.0","end"); self.msg_text.insert("1.0", msg)
            messagebox.showinfo("Decode", f"Message revealed (auto-detected: {name}).")
        except Exception as e:
            messagebox.showerror("Decode", f"Failed to decode with any technique:\n{e}")

if __name__ == "__main__":
    app = MultiStegoGUI()
    app.mainloop()