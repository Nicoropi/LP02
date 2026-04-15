MAX_RAM = 2**16
RAM_WINDOW_WORDS = 256

class PCBridge:
    def __init__(self, base_addr: int = 0):
        from pc.ram import RAM
        from pc.register import Registers
        from pc.alu import Alu
        from pc.fpu import FPU
        from pc.cpu import CPU
        from pc.loader import Loader
        from pc.disk import Disk, DiskDevice

        self._loaded = False
        # Hardware modules
        self.ram = RAM(word_size="64", positions=MAX_RAM)
        self.reg = Registers()
        self.fpu = FPU(self.reg)
        self.alu = Alu(self.reg, self.fpu)
        self.cpu = CPU(self.ram, self.reg, self.alu)

        self._base_addr = base_addr
        self.loader = Loader(start_address=base_addr)

        # Disk
        self.disk = Disk()
        self.disk_device = DiskDevice(self.disk)

    def load_program(self, path: str, base_addr: int = 0) -> int:
        """Load a program into RAM and initialize PC/SP. Returns entry point."""
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