import sys

from pc.ram      import RAM
from pc.register import Registers
from pc.alu_2    import Alu
from pc.cpu      import CPU
from pc.loader   import Loader
from pc.linker   import SimpleBinLinker, write_bin

MAX_RAM = 2 ** 16

def main():
    """Punto de entrada: carga y ejecuta binarios.
    Uso:
      - Enlazar estáticamente varios bins: python environment.py --link-static bin1.bin bin2.bin ...
      - Ejecutar un único bin:         python environment.py bin.bin
    """
    if len(sys.argv) < 2:
        print("Uso: python environment.py <archivo.bin> [--link bin1.bin bin2.bin ...]")
        sys.exit(1)

    ram  = RAM(word_size="64", positions=MAX_RAM)
    reg  = Registers()
    alu  = Alu(reg)
    cpu  = CPU(ram, reg, alu)

    # Enlazado estático entre varios .bin
    if sys.argv[1] == "--link":
        bin_paths = sys.argv[2:]
        if not bin_paths:
            print("Especifica al menos un bin para enlazar.")
            sys.exit(1)

        linker = SimpleBinLinker()
        final_words, entry = linker.link(bin_paths, base_start=0)
        final_bin = "program_final.bin"
        write_bin(final_bin, final_words)
        print(f"Bin final generado: {final_bin} (entry={entry})")

        # Cargar y ejecutar el binario final
        loader = Loader(start_address=0)
        entry_point = loader.load(final_bin, ram)

        reg.PC = entry_point
        reg.SP = MAX_RAM - 1

        cpu.run()

        print(f"Detenida tras {cpu.cycle_count} ciclos")
        cpu.dump_registers()
        return

    # Flujo simple: cargar un único bin
    filename  = sys.argv[1]
    base_addr = 0  # para este flujo simple, cargamos desde 0

    loader = Loader(start_address=base_addr)
    entry_point = loader.load(filename, ram)

    reg.PC = entry_point
    reg.SP = MAX_RAM - 1

    print(f"  Programa: {filename}")
    print(f"  PC: {entry_point}  |  SP: {reg.SP}")

    cpu.run()

    print(f"  Detenida tras {cpu.cycle_count} ciclos")
    cpu.dump_registers()

if __name__ == "__main__":
    main()
