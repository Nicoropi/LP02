import sys

from pc.ram import RAM
from pc.register import Registers
from pc.alu import Alu
from pc.fpu import FPU
from pc.cpu import CPU
from pc.loader import Loader

import os
import sys as _sys

_sys.path.insert(0, os.path.dirname(__file__))

from spl.linker_loader import LinkerLoader

MAX_RAM = 2**16


def main():
    """Punto de entrada: carga y ejecuta binarios.
    Uso:
      - Enlazar estáticamente varios .o: python environment.py --link obj1.o obj2.o ...
      - Ejecutar un único .o o .bin: python environment.py archivo.o
    """
    if len(sys.argv) < 2:
        print("Uso: python environment.py <archivo.o o archivo.bin> [--dir=direccion]")
        print("     python environment.py --link obj1.o obj2.o ...")
        sys.exit(1)

    ram = RAM(word_size="64", positions=MAX_RAM)
    reg = Registers()
    fpu = FPU(reg)
    alu = Alu(reg, fpu)
    cpu = CPU(ram, reg, alu)

    # Enlazado estático entre varios .o usando spl/linker_loader
    if sys.argv[1] == "--link":
        obj_paths = sys.argv[2:]
        if not obj_paths:
            print("Especifica al menos un .o para enlazar.")
            sys.exit(1)

        linker = LinkerLoader()
        linker.load_object(obj_paths)
        linker.resolve(0)
        linker.resolve_data()
        entry = linker.load_to_ram(ram, start=0)

        print(f"Linked {len(obj_paths)} files, entry point: {entry}")

        reg.PC = entry
        reg.SP = MAX_RAM - 1

        # Limit cycles for safety
        original_run = cpu.run

        def limited_run():
            cpu.running = True
            cpu.cycle_count = 0
            while cpu.running and cpu.cycle_count < 1000:
                cpu.cycle_count += 1
                cpu.fetch()
                cpu.execute()
            print(f"Detenida tras {cpu.cycle_count} ciclos (max 1000)")

        limited_run()
        cpu.dump_registers()
        return

    # Flujo simple: cargar un único archivo (.o o .bin)
    filename = sys.argv[1]
    base_addr = 0

    # Parse --dir if provided
    for arg in sys.argv[2:]:
        if arg.startswith("--dir="):
            base_addr = int(arg.split("=")[1])
            break

    # Determine file type
    is_object = filename.lower().endswith(".o")

    if is_object:
        # Use spl/linker_loader for .o files
        linker = LinkerLoader()
        linker.load_object([filename])
        linker.resolve(base_addr)
        linker.resolve_data()
        entry_point = linker.load_to_ram(ram, start=base_addr)
        print(f"  Programa: {filename} (linked)")
    else:
        # Use pc/loader for .bin files
        loader = Loader(start_address=base_addr)
        entry_point = loader.load(filename, ram)
        print(f"  Programa: {filename}")

    reg.PC = entry_point
    reg.SP = MAX_RAM - 1

    print(f"  PC: {entry_point}  |  SP: {reg.SP}")

    # Limit cycles for safety
    original_run = cpu.run

    def limited_run():
        cpu.running = True
        cpu.cycle_count = 0
        while cpu.running and cpu.cycle_count < 1000:
            cpu.cycle_count += 1
            cpu.fetch()
            cpu.execute()
        print(f"  Detenida tras {cpu.cycle_count} ciclos (max 1000)")

    limited_run()
    cpu.dump_registers()


if __name__ == "__main__":
    main()
