import hashlib
import os

import tkinter as tk
import customtkinter as ctk
import tkinter.simpledialog as simpledialog

try:
    from ..main import PALETTE as GLOBAL_PALETTE
except Exception:
    GLOBAL_PALETTE = {}

# Optional: import the Assembler class for GUI usage
try:
    import assembly as _assembly_module  # type: ignore

    _ASSEMBLER_CLASS = getattr(_assembly_module, "Assembler", None)
except Exception:
    _ASSEMBLER_CLASS = None


# ====================================#
#              Functions              #
# ====================================#
bin_box = None  # module-level reference to expose current binary textbox content


def get_bin_box_text():
    global bin_box
    try:
        if bin_box is not None:
            return bin_box.get("1.0", "end-1c")
    except Exception:
        pass
    return ""


def load_program(pc_bridge):
    # Load program directly from the content of the bin_box (hex bytes text)
    try:
        bin_text = get_bin_box_text()
    except Exception:
        bin_text = ""
    if not bin_text or not bin_text.strip():
        return

    # Treat bin_text as raw binary data (latin-1 encoding preserves byte values 0-255)
    data_bytes = None
    if bin_text:
        data_bytes = bin_text.encode("latin-1")
    if not data_bytes or len(data_bytes) == 0:
        return

    import tempfile, os

    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as tmp:
        tmp.write(data_bytes)
        tmp_path = tmp.name

    base_addr = 0
    try:
        addr = simpledialog.askinteger(
            "Base address", "Base address (default 0):", initialvalue=0
        )
        if addr is not None:
            base_addr = addr
    except Exception:
        base_addr = 0
    try:
        pc_bridge.load_program(tmp_path, base_addr=base_addr)
    except Exception:
        pass
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass


def build_code_tab(parent, pc_bridge=None):
    frame = parent

    # ====================================#
    #               Top Bar               #
    # ====================================#
    top_bar = ctk.CTkFrame(frame, height=30, corner_radius=0)
    top_bar.pack(side="top", fill="x")
    color02 = (
        GLOBAL_PALETTE.get("color02", "#252F3D")
        if isinstance(GLOBAL_PALETTE, dict)
        else "#252F3D"
    )
    top_bar.configure(fg_color=color02)

    # Local handlers capture asm_box/bin_box once created
    def on_assemble():
        asm_text = ""
        try:
            asm_text = asm_box.get("1.0", "end-1c")
        except Exception:
            asm_text = ""
        if _ASSEMBLER_CLASS is not None:
            assembler = _ASSEMBLER_CLASS()
            bin_lines = assembler.assemble_text_as_binary(asm_text)
            bin_box.configure(state="normal")
            bin_box.delete("1.0", "end")
            bin_box.insert("1.0", "\n".join(bin_lines))
            bin_box.configure(state="disabled")
        else:
            lines = [l.strip() for l in asm_text.splitlines() if l.strip()]
            results = [
                hashlib.sha256(line.encode("utf-8")).hexdigest()[:16].upper()
                for line in lines
            ]
            bin_box.configure(state="normal")
            bin_box.delete("1.0", "end")
            bin_box.insert("1.0", "\n".join(results))
            bin_box.configure(state="disabled")

    def on_load():
        load_program(pc_bridge)

    def on_assemble_load():
        on_assemble()
        on_load()

    btn_assm = ctk.CTkButton(top_bar, text="Assemble", command=on_assemble)
    btn_load = ctk.CTkButton(top_bar, text="Load File", command=on_load)
    btn_both = ctk.CTkButton(top_bar, text="Assemble & Load", command=on_assemble_load)
    btn_both.pack(side="right", padx=6, pady=6)
    btn_load.pack(side="right", padx=6, pady=6)
    btn_assm.pack(side="right", padx=6, pady=6)

    # ====================================#
    #             Main Content            #
    # ====================================#
    edit_frame = ctk.CTkFrame(frame, corner_radius=6)
    edit_frame.pack(side="left", fill="both", expand=True, padx=8, pady=8)
    bin_frame = ctk.CTkFrame(frame, corner_radius=6)
    bin_frame.pack(side="right", fill="both", expand=True, padx=8, pady=8)

    asm_box = ctk.CTkTextbox(edit_frame, width=580, height=520)
    asm_box.pack(fill="both", expand=True, padx=2, pady=2)
    asm_box.insert("1.0", "LDINT RA, 48\nLDINT RB, 18\nCOMP RA, RB \n")

    global bin_box
    bin_box = ctk.CTkTextbox(bin_frame, width=580, height=520)
    bin_box.pack(fill="both", expand=True, padx=2, pady=2)
    bin_box.configure(state="disabled")  # read-only by default
    bin_box.insert("1.0", "")

    return frame
