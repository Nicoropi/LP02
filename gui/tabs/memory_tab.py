import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk

MAX_RAM = 2**16
RAM_PAGE_SIZE = 256

_reg_box = None
_pc_sp_label = None
_ram_box = None
_bin_box = None
_flags_box = None
_last_state = None
_ram_page_start = 0
_page_entry = None
_pc_bridge = None


def _hex(n: int, width: int = 2) -> str:
    return f"{n:0{width}X}"


def build_memory_tab(parent, pc_bridge=None):
    global \
        _reg_box, \
        _pc_sp_label, \
        _ram_box, \
        _bin_box, \
        _flags_box, \
        _page_entry, \
        _pc_bridge
    _pc_bridge = pc_bridge
    frame = parent

    # ====================================#
    #             Functions               #
    # ====================================#
    def on_run():
        if pc_bridge._loaded:
            pc_bridge.cpu.run()
            pc_bridge._loaded = False

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

    top_bar = ctk.CTkFrame(right_col, fg_color="#2b2b2b")
    top_bar.pack(fill="x", padx=6, pady=(6, 0))

    def on_page_change(new_start: int):
        global _ram_page_start
        _ram_page_start = max(0, min(new_start, MAX_RAM - RAM_PAGE_SIZE))
        if pc_bridge:
            _refresh_ram_display()

    def on_page_input():
        global _ram_page_start
        try:
            page_num = int(_page_entry.get())
            _ram_page_start = page_num * RAM_PAGE_SIZE
            _ram_page_start = max(0, min(_ram_page_start, MAX_RAM - RAM_PAGE_SIZE))
            if pc_bridge:
                _refresh_ram_display()
        except ValueError:
            pass

    def _refresh_ram_display():
        global _ram_page_start
        if pc_bridge and _ram_box:
            ram_dump, actual_start = pc_bridge.get_ram_window(
                _ram_page_start, RAM_PAGE_SIZE
            )
            _ram_box.configure(state="normal")
            _ram_box.delete("1.0", "end")
            if ram_dump:
                lines = []
                for idx, word in enumerate(ram_dump):
                    abs_addr = actual_start + idx
                    lines.append(f"{abs_addr:04X}: {word & ((1 << 64) - 1):064b}")
                _ram_box.insert("1.0", "\n".join(lines))
            else:
                _ram_box.insert("1.0", "RAM view (placeholder)\n")
            _ram_box.configure(state="disabled")

    def go_to_pc_page(pc_val: int):
        global _ram_page_start
        if pc_val is not None:
            _ram_page_start = (pc_val // RAM_PAGE_SIZE) * RAM_PAGE_SIZE
            _ram_page_start = max(0, min(_ram_page_start, MAX_RAM - RAM_PAGE_SIZE))
            _page_entry.delete(0, "end")
            _page_entry.insert(0, str(pc_val // RAM_PAGE_SIZE))
            if pc_bridge:
                _refresh_ram_display()
            return True
        return False

    def get_current_pc() -> int:
        global _pc_bridge
        if _pc_bridge and hasattr(_pc_bridge, "reg") and hasattr(_pc_bridge.reg, "PC"):
            return _pc_bridge.reg.PC
        return None

    def on_prev_page():
        on_page_change(_ram_page_start - RAM_PAGE_SIZE)
        _page_entry.delete(0, "end")
        _page_entry.insert(0, str(_ram_page_start // RAM_PAGE_SIZE))

    def on_next_page():
        on_page_change(_ram_page_start + RAM_PAGE_SIZE)
        _page_entry.delete(0, "end")
        _page_entry.insert(0, str(_ram_page_start // RAM_PAGE_SIZE))

    top_bar.grid_columnconfigure(0, weight=1)
    top_bar.grid_columnconfigure(1, weight=0)
    top_bar.grid_columnconfigure(2, weight=0)
    top_bar.grid_columnconfigure(3, weight=0)
    top_bar.grid_columnconfigure(4, weight=0)

    pc_btn = ctk.CTkButton(
        top_bar,
        text="PC",
        width=40,
        command=lambda: go_to_pc_page(get_current_pc()),
    )
    pc_btn.grid(row=0, column=0, sticky="w", padx=(0, 4))

    prev_btn = ctk.CTkButton(top_bar, text="<", width=30, command=on_prev_page)
    prev_btn.grid(row=0, column=1, sticky="w")

    _page_entry = ctk.CTkEntry(top_bar, width=50, justify="center")
    _page_entry.insert(0, "0")
    _page_entry.grid(row=0, column=2, sticky="w", padx=4)
    _page_entry.bind("<Return>", lambda e: on_page_input())

    next_btn = ctk.CTkButton(top_bar, text=">", width=30, command=on_next_page)
    next_btn.grid(row=0, column=3, sticky="w", padx=(0, 8))

    _pc_sp_label = ctk.CTkLabel(top_bar, text="PC: 0  SP: 0", anchor="w")
    _pc_sp_label.grid(row=0, column=4, sticky="w")

    run_btn = ctk.CTkButton(top_bar, text="run", command=on_run)
    run_btn.grid(row=0, column=5, sticky="e")

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
    global \
        _reg_box, \
        _pc_sp_label, \
        _ram_box, \
        _flags_box, \
        _last_state, \
        _ram_page_start, \
        _pc_bridge, \
        _page_entry
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
    if _ram_box is not None:
        if _pc_bridge:
            ram_dump, actual_start = _pc_bridge.get_ram_window(
                _ram_page_start, RAM_PAGE_SIZE
            )
            _ram_box.configure(state="normal")
            if ram_dump:
                lines = []
                for idx, word in enumerate(ram_dump):
                    abs_addr = actual_start + idx
                    lines.append(f"{abs_addr:04X}: {word & ((1 << 64) - 1):064b}")
                _ram_box.delete("1.0", "end")
                _ram_box.insert("1.0", "\n".join(lines))
            else:
                _ram_box.delete("1.0", "end")
                _ram_box.insert("1.0", "RAM view (placeholder)\n")
            _ram_box.configure(state="disabled")
        else:
            _ram_box.delete("1.0", "end")
            _ram_box.insert("1.0", "RAM view (placeholder)\n")
        _ram_box.configure(state="disabled")
