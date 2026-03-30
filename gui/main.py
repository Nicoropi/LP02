import hashlib
from pathlib import Path
from tkinter import filedialog

import tkinter as tk
import tkinter.ttk as ttk
import customtkinter as ctk

from .tabs.code_tab import build_code_tab
from .tabs.memory_tab import build_memory_tab

PALETTE = {
    # Base color palette (custom theme)
    "color01": "#1C2736",
    "color02": "#252F3D",
    "color03": "#2F3744",
    "color04": "#39404B",
    "color05": "#424852",
    "color06": "#4C515A",
    "color07": "#565A61",
    "color08": "#616469",
    "color09": "#6B6D70",
    "color10": "#757678",
    "color11": "#808080",
}


class VIC_GUI(ctk.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("VIC (Virtual Computer)")
        self.geometry("1200x700")

        self.palette = PALETTE

        # ====================================#
        #               Tab Bar               #
        # ====================================#
        self._setup_notebook_style()
        self.notebook = ttk.Notebook(self, style="CustomNotebook.TNotebook")
        self.notebook.pack(fill="both", expand=True)

        self.code_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.code_tab, text=" Code ")
        build_code_tab(self.code_tab)

        self.ram_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.ram_tab, text="    PC    ")
        build_memory_tab(self.ram_tab)

    def _setup_notebook_style(self):
        style = ttk.Style()

        style.theme_create(
            "standard",
            settings={
                "TLabel": {
                    "configure": {
                        "foreground": "#FFFFFF",
                        "background": PALETTE["color02"],
                    }
                },
                "TFrame": {"configure": {"background": PALETTE["color05"]}},
                "TNotebook": {
                    "configure": {
                        "background": PALETTE["color01"],
                        "tabmargins": [0, 5, 5, 0],
                        "padding": [5, 5],
                    }
                },
                "TNotebook.Tab": {
                    "configure": {
                        "background": PALETTE["color01"],
                        "foreground": "#FFFFFF",
                        "padding": [7, 2],
                        "focuscolor": "clear",
                    },
                    "map": {"background": [("selected", PALETTE["color02"])]},
                },
            },
        )

        style.theme_use("standard")


def run_gui():
    app = VIC_GUI()
    app.mainloop()


# # Lightweight color palette persistence
# PALETTE_DEFAULT = {
#     "color1": "#0A2548",
#     "color2": "#1A2D4E",
#     "color3": "#263653",
#     "color4": "#323E59",
#     "color50": "#EEF1F6",
#     "color100": "#D1D8E6",
#     "color200": "#B3C0D6",
#     "color300": "#95A7C6",
#     "color400": "#778EB6",
#     "color500": "#5975A6",
#     "color600": "#496088",
#     "color700": "#394B6A",
#     "color800": "#29364C",
#     "color900": "#1A2230",
#     "color950": "#090C11",
# }

# class ComputerSimulatorGUI(ctk.CTk):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.title("Simple Computer Simulator GUI")
#         self.geometry("1200x700")

#         # Load palette (will apply after UI is built)
#         self.palette = load_palette()

#         # Top action bar with three buttons
#         self.top_bar = ctk.CTkFrame(self, height=60, corner_radius=0)
#         self.top_bar.pack(side="top", fill="x")

#         self.btn_assembler = ctk.CTkButton(
#             self.top_bar, text="Assembler", command=self.on_assemble
#         )
#         self.btn_load = ctk.CTkButton(self.top_bar, text="Load", command=self.on_load)
#         self.btn_both = ctk.CTkButton(
#             self.top_bar, text="Assembler & Load", command=self.on_assemble_load
#         )

#         self.btn_assembler.pack(side="left", padx=6, pady=12)
#         self.btn_load.pack(side="left", padx=6, pady=12)
#         self.btn_both.pack(side="left", padx=6, pady=12)

#         # Main content: two panels side-by-side
#         self.main = ctk.CTkFrame(self, corner_radius=0)
#         self.main.pack(fill="both", expand=True)

#         self.left_frame = ctk.CTkFrame(self.main, width=600, corner_radius=6)
#         self.right_frame = ctk.CTkFrame(self.main, width=600, corner_radius=6)
#         self.left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
#         self.right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

#         # Text areas
#         self.asm_box = ctk.CTkTextbox(self.left_frame, width=580, height=520)
#         self.asm_box.pack(fill="both", expand=True, padx=2, pady=2)

#         self.bin_box = ctk.CTkTextbox(self.right_frame, width=580, height=520)
#         self.bin_box.pack(fill="both", expand=True, padx=2, pady=2)

#         # Close handling to persist palette
#         self.protocol("WM_DELETE_WINDOW", self._on_close)
#         # Apply the color palette now that widgets exist
#         self._apply_palette()

#     # Initialize RAM view state (placeholder for a RAM model)
#     self._ram = [0] * 1024
#     self._ram_window = None
#     # Small control to open RAM view (optional helper window)
#     try:
#         self._ram_button = ctk.CTkButton(
#             self.main, text="RAM View", command=self._toggle_ram_window
#         )
#         self._ram_button.pack(side="top", anchor="ne", padx=8, pady=8)
#     except Exception:
#         pass

# def _apply_palette(self):
#     # Set global window background to color800 if available
#     try:
#         self.configure(bg=self.palette.get("color800", PALETTE["color800"]))
#     except Exception:
#         pass
#

# def _toggle_ram_window(self):
#     # Lazy RAM viewer window
#     if self._ram_window is None or not self._ram_window.winfo_exists():
#         self._ram_window = tk.Toplevel(self)
#         self._ram_window.title("RAM Viewer")
#         self._ram_box = ctk.CTkTextbox(self._ram_window, width=580, height=320)
#         self._ram_box.pack(fill="both", expand=True, padx=8, pady=8)
#         self._update_ram_view()
#     else:
#         self._ram_window.lift()

# def _update_ram_view(self):
#     if not hasattr(self, "_ram_box"):
#         return
#     lines = []
#     for i, val in enumerate(self._ram):
#         lines.append(f"0x{(i * 4):08X}: 0x{val:08X}")
#     self._ram_box.delete("1.0", "end")
#     self._ram_box.insert("1.0", "\n".join(lines))

#     def _apply_palette(self):
#         # Best-effort palette application for CTk widgets
#         try:
#             # Background of the main window uses color800 (800-series)
#             self.configure(
#                 bg_color=self.palette.get("color100", PALETTE_DEFAULT["color100"])
#             )
#         except Exception:
#             pass
#         try:
#             self.top_bar.configure(
#                 bg_color=self.palette.get("color2", PALETTE_DEFAULT["color2"])
#             )
#         except Exception:
#             pass
#         # Style buttons to use color2 as their fill color
#         try:
#             self.btn_assembler.configure(
#                 fg_color=self.palette.get("color2", PALETTE_DEFAULT["color2"])
#             )
#         except Exception:
#             pass
#         try:
#             self.btn_load.configure(
#                 fg_color=self.palette.get("color2", PALETTE_DEFAULT["color2"])
#             )
#         except Exception:
#             pass
#         try:
#             self.btn_both.configure(
#                 fg_color=self.palette.get("color2", PALETTE_DEFAULT["color2"])
#             )
#         except Exception:
#             pass
#         # Text areas: no outline, color1 background
#         try:
#             # Text areas use color1 as background with no outline
#             self.asm_box.configure(
#                 fg_color=self.palette.get("color1", PALETTE_DEFAULT["color1"]),
#                 border_width=0,
#             )
#         except Exception:
#             pass
#         try:
#             self.bin_box.configure(
#                 fg_color=self.palette.get("color1", PALETTE_DEFAULT["color1"]),
#                 border_width=0,
#             )
#         except Exception:
#             pass

#     def on_assemble(self):
#         text = self.asm_box.get("1.0", "end-1c")
#         self._assemble_text(text)

#     def _assemble_text(self, text):
#         lines = [l.strip() for l in text.splitlines() if l.strip()]
#         results = []
#         for line in lines:
#             digest = hashlib.sha256(line.encode("utf-8")).hexdigest()[:16].upper()
#             results.append(digest)
#         self.bin_box.delete("1.0", "end")
#         self.bin_box.insert("1.0", "\n".join(results))

#     def on_load(self):
#         path = filedialog.askopenfilename(
#             title="Load Binary",
#             filetypes=[
#                 ("Binary files", "*.bin"),
#                 ("All files", "*.*"),
#                 ("Hex", "*.hex"),
#             ],
#         )
#         if not path:
#             return
#         with open(path, "rb") as f:
#             b = f.read()
#         hexs = " ".join(f"{byte:02X}" for byte in b)
#         self.bin_box.delete("1.0", "end")
#         self.bin_box.insert("1.0", hexs)

#     def on_assemble_load(self):
#         self.on_assemble()
#         self.on_load()

#     def _on_close(self):
#         self.destroy()


# def run_gui():
#     app = ComputerSimulatorGUI()
#     app.mainloop()
