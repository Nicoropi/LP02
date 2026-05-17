import hashlib

import tkinter as tk
import customtkinter as ctk
import tkinter.simpledialog as simpledialog

try:
    from ..main import PALETTE as GLOBAL_PALETTE
except Exception:
    GLOBAL_PALETTE = {}

from spl.assembly import Assembler 


bin_box = None  # module-level reference to expose current binary textbox content
asm_box_ref = None


def get_bin_box_text():
    global bin_box
    try:
        if bin_box is not None:
            return bin_box.get("1.0", "end-1c")
    except Exception:
        pass
    return ""


def set_asm_box_text(text: str):
    global asm_box_ref
    if asm_box_ref is None:
        return
    try:
        asm_box_ref.delete("1.0", "end")
        asm_box_ref.insert("1.0", text or "")
    except Exception:
        pass


def get_asm_box_text() -> str:
    global asm_box_ref
    try:
        if asm_box_ref is not None:
            return asm_box_ref.get("1.0", "end-1c")
    except Exception:
        pass
    return ""

def load_program(pc_bridge):
    if pc_bridge is None:
        return

    # Obtener contenido del bin_box (salida del assembler)
    try:
        bin_text = get_bin_box_text()
    except Exception:
        bin_text = ""

    if not bin_text or not bin_text.strip():
        return

    # Dirección base
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
        pc_bridge.load_object_text(bin_text, base_addr=base_addr)
    except Exception as e:
        print(f"Error loading program:\n{e}")


def build_asm_tab(parent, pc_bridge=None):
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

        if pc_bridge is not None:
            try:
                obj_text = pc_bridge.assemble_asm_to_object_text(asm_text)
                bin_lines = obj_text.splitlines()
            except Exception as e:
                print(f"Error assembling:\n{e}")
                bin_lines = []
        else:
            assembler = Assembler()
            bin_lines = assembler.assemble_text_as_binary(asm_text)
        bin_box.configure(state="normal")
        bin_box.delete("1.0", "end")
        bin_box.insert("1.0", "\n".join(bin_lines))
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

    global asm_box_ref
    asm_box_ref = asm_box

    global bin_box
    bin_box = ctk.CTkTextbox(bin_frame, width=580, height=520)
    bin_box.pack(fill="both", expand=True, padx=2, pady=2)
    bin_box.configure(state="disabled")  # read-only by default
    bin_box.insert("1.0", "")

    return frame
