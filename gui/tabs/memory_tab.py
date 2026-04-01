import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk


# Memory tab: shows PC state, Registers and RAM dump.
#
# Public API:
# - build_memory_tab(parent) -> frame
# - update_memory_tab(state: dict) -> None
# +
# State shape (example):
# {
#   "pc": 1234,
#   "sp": 65530,
#   "regs": {"R0": 0x0, "R1": 0x1, ...},
#   "ram": [0x00, 0x01, ..., 0xFF]
# }

_reg_box = None
_pc_sp_label = None
_ram_box = None
_bin_box = None
_flags_box = None
_last_state = None


def _hex(n: int, width: int = 2) -> str:
    return f"{n:0{width}X}"


def build_memory_tab(parent, pc_bridge=None):
    global _reg_box, _pc_sp_label, _ram_box, _bin_box, _flags_box
    frame = parent

    # ====================================#
    #         Registers and Flags         #
    # ====================================#
    left_col = ctk.CTkFrame(frame)
    left_col.pack(side="left", fill="y", padx=8, pady=8)

    # Registers
    reg_frame = ctk.CTkFrame(left_col)
    reg_frame.pack(fill="both", expand=True)
    reg_label = ctk.CTkLabel(reg_frame, text="Registers", font=("Arial", 12, "bold"))
    reg_label.pack(anchor="w", padx=6, pady=(6, 0))
    _reg_box = ctk.CTkTextbox(reg_frame, width=300, height=260)
    _reg_box.pack(fill="both", expand=True, padx=6, pady=6)
    _reg_box.insert("1.0", "Registers view\n")
    _reg_box.configure(state="disabled")

    # Flags box (below registers)
    flags_box = ctk.CTkTextbox(left_col, width=400, height=120)
    flags_box.pack(fill="x", pady=(8, 8), padx=8)
    flags_box.insert("1.0", "FLAGS\n")
    flags_box.configure(state="disabled")
    _flags_box = flags_box

    # ====================================#
    #               RAM BOX               #
    # ====================================#
    right_col = ctk.CTkFrame(frame)
    right_col.pack(side="left", fill="both", expand=True, padx=8, pady=8)

    _pc_sp_label = ctk.CTkLabel(right_col, text="PC: 0  SP: 0", anchor="w")
    _pc_sp_label.pack(fill="x", padx=6, pady=(6, 0))

    # RAM: container with horizontal scrollbar for binary-like 64-bit words
    ram_frame = ctk.CTkFrame(right_col)
    ram_frame.pack(fill="both", expand=True, padx=6, pady=6)
    _ram_box = ctk.CTkTextbox(ram_frame, width=580, height=260)
    _ram_box.pack(fill="both", expand=True, padx=0, pady=0)
    _ram_box.insert("1.0", "RAM view (placeholder)\n")
    _ram_box.configure(state="disabled", wrap="none")

    return frame


def update_memory_tab(state: dict):
    """
    Update the memory tab views from an external PC state dictionary.
    Expected keys: pc, sp, regs (dict), ram (iterable of ints 0-255)
    """
    global _reg_box, _pc_sp_label, _ram_box, _flags_box, _last_state
    # Lazy update: skip if the state hasn't changed
    if _last_state is not None and state == _last_state:
        return
    _last_state = state
    if state is None:
        return

    # PC/SP
    pc = state.get("pc")
    sp = state.get("sp")
    if _pc_sp_label is not None and pc is not None and sp is not None:
        _pc_sp_label.configure(text=f"PC: {pc}  SP: {sp}")

    # FLAGS: update if available
    flags = state.get("flags", {})
    if _flags_box is not None:
        flag_parts = [
            f"{k}:{int(flags.get(k, 0))}" for k in ("ZERO", "CARRY", "NEG", "OVERFLOW")
        ]
        _flags_box.configure(state="normal")
        _flags_box.delete("1.0", "end")
        _flags_box.insert("1.0", "FLAGS  " + "  ".join(flag_parts))
        _flags_box.configure(state="disabled")

    # Registers
    regs = state.get("regs")
    if _reg_box is not None:
        if isinstance(regs, dict) and len(regs) > 0:
            _reg_box.configure(state="normal")
            lines = [f"{name:>6}: {val:#010x}" for name, val in regs.items()]
            _reg_box.delete("1.0", "end")
            _reg_box.insert("1.0", "\n".join(lines))
            _reg_box.configure(state="disabled")
        else:
            _reg_box.configure(state="normal")
            _reg_box.delete("1.0", "end")
            _reg_box.insert("1.0", "Registers view (placeholder)\n")
            _reg_box.configure(state="disabled")

    # RAM dump (display as 64-bit words, 64-bit binary per word)
    ram = state.get("ram")
    ram_start = state.get("ram_start", 0)
    if _ram_box is not None:
        _ram_box.configure(state="normal")
        if isinstance(ram, (list, tuple)) and len(ram) > 0:
            lines = []
            for idx, word in enumerate(ram):
                if isinstance(word, int):
                    abs_addr = ram_start + idx
                    lines.append(f"{abs_addr:04X}: {word & ((1 << 64) - 1):064b}")
            _ram_box.delete("1.0", "end")
            _ram_box.insert("1.0", "\n".join(lines))
        else:
            _ram_box.delete("1.0", "end")
            _ram_box.insert("1.0", "RAM view (placeholder)\n")
        _ram_box.configure(state="disabled")
