import customtkinter as ctk

from .asm_tab import set_asm_box_text


def build_high_level_tab(parent, pc_bridge=None):
    frame = parent

    top_bar = ctk.CTkFrame(frame, height=30, corner_radius=0)
    top_bar.pack(side="top", fill="x")

    editor_frame = ctk.CTkFrame(frame, corner_radius=6)
    editor_frame.pack(fill="both", expand=True, padx=8, pady=8)

    high_level_box = ctk.CTkTextbox(editor_frame, width=1160, height=520)
    high_level_box.pack(fill="both", expand=True, padx=2, pady=2)

    def on_compile_to_asm():
        if pc_bridge is None:
            return
        try:
            src = high_level_box.get("1.0", "end-1c")
        except Exception:
            src = ""
        if not src.strip():
            return

        try:
            result = pc_bridge.compile_high_level_to_asm(src)
            asm = result.get("asm", "")
            set_asm_box_text(asm)
        except Exception as e:
            print(f"Error compiling high level:\n{e}")

    compile_btn = ctk.CTkButton(
        top_bar,
        text="Compile (HL -> ASM)",
        command=on_compile_to_asm,
    )
    compile_btn.pack(side="right", padx=6, pady=6)

    return frame
