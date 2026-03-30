import hashlib
from tkinter import filedialog

import tkinter as tk
import customtkinter as ctk

try:
    from ..main import PALETTE as GLOBAL_PALETTE 
except Exception:
    GLOBAL_PALETTE = {}


def build_code_tab(parent):
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

    btn_assm = ctk.CTkButton(top_bar, text="Assemble", command=on_assemble)
    btn_load = ctk.CTkButton(top_bar, text="Load File", command=on_load)
    btn_both = ctk.CTkButton(top_bar, text="Assemble & Load", command=on_assemble_load)
    btn_assm.pack(side="right", padx=6, pady=6)
    btn_load.pack(side="right", padx=6, pady=6)
    btn_both.pack(side="right", padx=6, pady=6)

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

    bin_box = ctk.CTkTextbox(bin_frame, width=580, height=520)
    bin_box.pack(fill="both", expand=True, padx=2, pady=2)
    bin_box.configure(state="disabled")  # read-only by default
    bin_box.insert("1.0", "")

    # ====================================#
    #              Functions              #
    # ====================================#
    def on_assemble():
        pass

    def on_load():
        pass

    def on_assemble_load():
        on_assemble()
        on_load()

    return frame
