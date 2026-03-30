import tkinter as tk
import customtkinter as ctk


def build_code_tab(parent):
    frame = parent

    # ====================================#
    #               Top Bar               #
    # ====================================#
    top_bar = ctk.CTkFrame(frame, height=30, corner_radius=0)
    top_bar.pack(side="top", fill="x")
    top_bar.configure(fg_color="#252F3D")

    # Create a simple assembly editor inside the given parent frame
    asm_box = ctk.CTkTextbox(frame, width=580, height=520)
    asm_box.pack(fill="both", expand=True, padx=8, pady=8)
    asm_box.insert("1.0", "# Enter assembly here (one instruction per line)\n")
    return frame


