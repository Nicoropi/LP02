MAX_RAM = 2**16


class PCBridge:
    def __init__(self, base_addr: int = 0):
        # Lazy import to avoid heavy import during GUI startup if not used
        from pc.ram import RAM
        from pc.register import Registers
        from pc.alu_2 import Alu
        from pc.cpu import CPU
        from pc.loader import Loader

        self._loaded = False
        # Hardware modules
        self.ram = RAM(word_size="64", positions=MAX_RAM)
        self.reg = Registers()
        self.alu = Alu(self.reg)
        self.cpu = CPU(self.ram, self.reg, self.alu)
        self._base_addr = base_addr
        self.loader = Loader(start_address=base_addr)

    def load_program(self, path: str, base_addr: int = 0) -> int:
        """Load a program into RAM and initialize PC/SP. Returns entry point."""
        from pc.loader import Loader

        self.loader = Loader(start_address=base_addr)
        entry = self.loader.load(path, self.ram)
        self.reg.PC = entry
        self.reg.SP = MAX_RAM - 1
        self._loaded = True
        return entry

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

        # RAM dump (windowed, not dumping the entire 64K in the UI for perf)
        ram_dump = []
        ram_start = 0
        try:
            if hasattr(self.ram, "request"):
                # Determine a window around the program counter
                window = 256
                pc_val = regs.get("PC", 0)
                start = 0
                if isinstance(pc_val, int):
                    start = max(0, min(pc_val - window // 2, MAX_RAM - window))
                ram_start = start
                for i in range(start, start + window):
                    val = self.ram.request(0, i, 0)
                    ram_dump.append(val if isinstance(val, int) else 0)
        except Exception:
            ram_dump = []
            ram_start = 0

        # If for some reason we didn't fill ram_dump, provide a small placeholder window
        if not ram_dump:
            ram_dump = [0] * 256
            ram_start = 0

        # Flags: best-effort extraction from known attributes
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
        # Fallbacks from ALU/CPU if available
        for src in (self.alu, self.cpu):
            for k in ("ZERO", "CARRY", "NEG", "OVERFLOW", "ZERO_FLAG", "CARRY_FLAG"):
                if hasattr(src, k) and k not in flags:
                    try:
                        flags[k] = int(getattr(src, k))
                    except Exception:
                        pass
        # Normalize common keys to a small set
        normalized = {
            "ZERO": int(flags.get("ZERO", flags.get("ZERO_FLAG", 0))),
            "CARRY": int(flags.get("CARRY", flags.get("CARRY_FLAG", 0))),
            "NEG": int(flags.get("NEG", 0)),
            "OVERFLOW": int(flags.get("OVERFLOW", 0)),
        }
        return {
            "pc": pc,
            "sp": sp,
            "regs": regs,
            "ram": ram_dump,
            "ram_start": ram_start,
            "flags": normalized,
        }

    def step(self) -> None:
        # Try to perform a single instruction step if supported by CPU
        try:
            if hasattr(self.cpu, "step"):
                self.cpu.step()
            elif hasattr(self.cpu, "run"):
                # Run a single instruction if API supports it
                self.cpu.run(1)
        except Exception:
            pass
