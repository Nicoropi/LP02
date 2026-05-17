import hashlib
from pathlib import Path
from tkinter import filedialog

import tkinter as tk
import tkinter.ttk as ttk
import customtkinter as ctk

from .tabs.asm_tab import build_asm_tab
from .tabs.high_level_tab import build_high_level_tab
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
        self.pc_bridge = PCBridge()

        # ====================================#
        #               Tab Bar               #
        # ====================================#
        self._setup_notebook_style()
        self.notebook = ttk.Notebook(self, style="CustomNotebook.TNotebook")
        self.notebook.pack(fill="both", expand=True)

        self.asm_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.asm_tab, text="Assembly")
        build_asm_tab(self.asm_tab, pc_bridge=self.pc_bridge)

        self.high_level_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.high_level_tab, text="High Level")
        build_high_level_tab(self.high_level_tab, pc_bridge=self.pc_bridge)

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

    # ====================================#
    #             Tab Style               #
    # ====================================#
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
