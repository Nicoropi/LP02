from __future__ import annotations

import os
import tempfile

MAX_RAM = 2**16
RAM_WINDOW_WORDS = 256

class PCBridge:
    def __init__(self, base_addr: int = 0):
        from pc.ram import RAM
        from pc.register import Registers
        from pc.alu import Alu
        from pc.fpu import FPU
        from pc.cpu import CPU
        from pc.disk import Disk, DiskDevice

        self._loaded = False
        # Hardware modules
        self.ram = RAM(word_size="64", positions=MAX_RAM)
        self.reg = Registers()
        self.fpu = FPU(self.reg)
        self.alu = Alu(self.reg, self.fpu)
        self.cpu = CPU(self.ram, self.reg, self.alu)

        self._base_addr = base_addr

        # Disk
        self.disk = Disk()
        self.disk_device = DiskDevice(self.disk)

    def compile_high_level_to_asm(self, source_text: str) -> dict:
        if source_text is None:
            source_text = ""

        from spl.preprocessor import preprocess
        from spl.lexic_analizer import Lexer

        try:
            from spl.compiler import Parser, CodeGenerator
        except Exception:
            from compiler import Parser, CodeGenerator

        preprocessed, loaded_files = preprocess(source_text)

        lexer = Lexer()
        tokens, symbol_table = lexer.analyze(preprocessed)

        parser = Parser()
        ast = parser.parse(preprocessed)
        generator = CodeGenerator()
        asm = generator.generate(ast)

        return {
            "preprocessed": preprocessed,
            "loaded_files": loaded_files,
            "tokens": tokens,
            "symbol_table": symbol_table,
            "ast": ast,
            "asm": asm,
        }

    def assemble_asm_to_object_text(self, asm_text: str) -> str:
        if asm_text is None:
            asm_text = ""
        from spl.assembly import Assembler

        assembler = Assembler()
        obj_lines = assembler.assemble_text_as_object(asm_text)
        return "\n".join(obj_lines)

    def load_object_text(self, obj_text: str, base_addr: int = 0) -> int:
        from spl.linker_loader import link, loader

        if obj_text is None or not obj_text.strip():
            raise ValueError("Object text is empty")

        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".o", mode="w") as tmp:
                tmp.write(obj_text)
                tmp_path = tmp.name

            linked = link([tmp_path])
            loader(linked, self.ram, base_addr=base_addr)
            entry = base_addr

            self.reg.PC = entry
            self.reg.SP = MAX_RAM - 1
            self._loaded = True
            return entry
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)

    def assemble_and_load(self, asm_text: str, base_addr: int = 0) -> int:
        obj_text = self.assemble_asm_to_object_text(asm_text)
        return self.load_object_text(obj_text, base_addr=base_addr)

    def get_state(self) -> dict:
        # PC and SP
        pc = getattr(self.reg, "PC", 0)
        sp = getattr(self.reg, "SP", 0)

        # Registers: gather from known attributes and the general dict
        regs = {}
        try:
            for name in ("PC", "SP", "BP", "IR", "MAR", "MDR"):
                if hasattr(self.reg, name):
                    val = getattr(self.reg, name)
                    if isinstance(val, int):
                        regs[name] = val
        except Exception:
            regs = {}
        # General purpose registers stored in self.reg.general
        try:
            if hasattr(self.reg, "general") and isinstance(self.reg.general, dict):
                regs.update(self.reg.general)
        except Exception:
            pass

        pc_val = regs.get("PC", 0)

        if isinstance(pc_val, int):
            start = max(0, min(pc_val - RAM_WINDOW_WORDS // 2, MAX_RAM - RAM_WINDOW_WORDS))
        else:
            start = 0

        ram_dump, ram_start = self.get_ram_window(start, RAM_WINDOW_WORDS)

        # If for some reason we didn't fill ram_dump, provide a small placeholder window
        if not ram_dump:
            ram_dump = [0] * 256
            ram_start = 0

        # Flags
        flags = {}
        try:
            # Try common places for flag bits
            for candidate in ("FLAGS", "FLAG", "FLAGS_BITS", "FLAGS_REG"):
                if hasattr(self.reg, candidate):
                    val = getattr(self.reg, candidate)
                    if isinstance(val, dict):
                        flags.update(val)
                    elif isinstance(val, int):
                        flags[candidate] = int(val)
        except Exception:
            pass
        
        try:
            if hasattr(self.reg, "flags") and isinstance(self.reg.flags, dict):
                flags.update(self.reg.flags)
        except Exception:
            pass

        normalized = {
            "ZERO": int(flags.get("ZERO", flags.get("ZERO_FLAG", flags.get("Z", 0)))),
            "CARRY": int(flags.get("CARRY", flags.get("CARRY_FLAG", 0))),
            "NEG": int(flags.get("NEG", flags.get("N", 0))),
            "OVERFLOW": int(flags.get("OVERFLOW", flags.get("D", 0))),
            "UNDERFLOW": int(flags.get("UNDERFLOW", flags.get("U", 0))),
        }
        return {
            "pc": pc,
            "sp": sp,
            "regs": regs,
            "ram": ram_dump,
            "ram_start": ram_start,
            "flags": normalized,
        }

    def get_ram_window(self, start: int, length: int = 256) -> tuple[list[int], int]:
        start = max(0, min(start, MAX_RAM - 1))
        length = min(length, MAX_RAM - start)

        dump = []

        if not hasattr(self.ram, "request"):
            return [0] * length, start

        for i in range(start, start + length):
            try:
                val = self.ram.request(0, i, 0)
                dump.append(val if isinstance(val, int) else 0)
            except Exception:
                dump.append(0)

        return dump, start
