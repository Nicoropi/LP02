import hashlib

import tkinter as tk
import customtkinter as ctk
import tkinter.simpledialog as simpledialog

try:
    from ..main import PALETTE as GLOBAL_PALETTE
except Exception:
    GLOBAL_PALETTE = {}

# Optional: import the Assembler class for GUI usage
try:
    import spl.assembly as _assembly_module  # type: ignore

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
    # Load program directly from the content of the bin_box
    try:
        bin_text = get_bin_box_text()
    except Exception:
        bin_text = ""
    if not bin_text or not bin_text.strip():
        return

    bin_text = bin_text.strip()

    # Parse hex lines from bin_box (format: 0xXXXXXXXXXXXXXXXX)
    lines = [
        line.strip()
        for line in bin_text.splitlines()
        if line.strip() and not line.startswith("#")
    ]

    if not lines:
        return

    # Try to parse as hex values
    words = []
    for line in lines:
        try:
            # Handle hex format: 0x...
            if line.startswith("0x") or line.startswith("0X"):
                words.append(int(line, 16))
            # Handle binary format: 0b...
            elif line.startswith("0b") or line.startswith("0B"):
                words.append(int(line, 2))
            # Handle plain decimal
            elif line.isdigit():
                words.append(int(line))
            else:
                # Try to parse anyway
                words.append(int(line, 0))
        except ValueError:
            continue

    if not words:
        return

    # Get base address
    base_addr = 0
    try:
        addr = simpledialog.askinteger(
            "Base address", "Base address (default 0):", initialvalue=0
        )
        if addr is not None:
            base_addr = addr
    except Exception:
        base_addr = 0

    # Load directly to RAM using the same approach as linker_loader.load_to_ram
    addr = base_addr
    for word in words:
        pc_bridge.ram.request(data=word, direction=addr, control=1)
        addr += 1

    # Set PC and SP
    pc_bridge.reg.PC = base_addr
    pc_bridge.reg.SP = 2**16 - 1
    pc_bridge._loaded = True


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

    def on_save_disk():
        if pc_bridge is None or not hasattr(pc_bridge, "disk"):
            return

        asm_text = ""
        try:
            asm_text = asm_box.get("1.0", "end-1c")
        except Exception:
            asm_text = ""
        if not asm_text or not asm_text.strip():
            return

        path = simpledialog.askstring(
            "Save to Disk", "Path (e.g., programas/fibonacci):"
        )
        if not path:
            return

        try:
            pc_bridge.disk.write_file(path, asm_text)
        except Exception as e:
            simpledialog.showerror("Error", f"Could not save file: {e}")

    btn_assm = ctk.CTkButton(top_bar, text="Assemble", command=on_assemble)
    btn_load = ctk.CTkButton(top_bar, text="Load File", command=on_load)
    btn_both = ctk.CTkButton(top_bar, text="Assemble & Load", command=on_assemble_load)
    btn_save = ctk.CTkButton(top_bar, text="Save to Disk", command=on_save_disk)
    btn_save.pack(side="right", padx=6, pady=6)
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
