import tkinter as tk
import customtkinter as ctk


def build_memory_tab(parent):
    frame = parent
    # RAM dump area (read-only view placeholder)
    ram_box = ctk.CTkTextbox(frame, width=580, height=260)
    ram_box.pack(fill="both", expand=True, padx=8, pady=8)
    ram_box.insert("1.0", "RAM view (placeholder)\n")

    # Binary view area
    bin_box = ctk.CTkTextbox(frame, width=580, height=260)
    bin_box.pack(fill="both", expand=True, padx=8, pady=8)
    bin_box.insert("1.0", "Binary view (placeholder)\n")
    return frame
