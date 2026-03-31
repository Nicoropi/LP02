import hashlib
from pathlib import Path
from tkinter import filedialog

import tkinter as tk
import tkinter.ttk as ttk
import customtkinter as ctk

from .tabs.code_tab import build_code_tab
from .tabs.memory_tab import build_memory_tab, update_memory_tab
from .pc_bridge import PCBridge

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

        # Initialize PC bridge for GUI interaction with the PC emulation
        self.pc_bridge = PCBridge()

        # ====================================#
        #               Tab Bar               #
        # ====================================#
        self._setup_notebook_style()
        self.notebook = ttk.Notebook(self, style="CustomNotebook.TNotebook")
        self.notebook.pack(fill="both", expand=True)

        self.code_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.code_tab, text=" Code ")
        build_code_tab(self.code_tab, pc_bridge=self.pc_bridge)

        self.ram_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.ram_tab, text="    PC    ")
        build_memory_tab(self.ram_tab, pc_bridge=self.pc_bridge)

        # Start periodic refresh loop to push PC state to the memory tab
        self.after(50, self._refresh_loop)

    # Load program moved to memory tab; no inline method here
    def _refresh_loop(self):
        state = self.pc_bridge.get_state()
        update_memory_tab(state)
        self.after(50, self._refresh_loop)

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
                "TFrame": {"configure": {"background": PALETTE["color02"]}},
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
