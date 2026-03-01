import sys

from ram      import RAM
from register import Registers
from alu_2    import Alu
from cpu      import CPU
from loader   import Loader

MAX_RAM = 2 ** 16


def main():
    """Punto de entrada: conecta los modulos, carga el programa y ejecuta.
    Uso: python environment.py <archivo.bin> [dir_base]
    """
    if len(sys.argv) < 2:
        print("Uso: python environment.py <archivo.bin> [dir_base]")
        sys.exit(1)

    filename  = sys.argv[1]
    base_addr = int(sys.argv[2]) if len(sys.argv) > 2 else 0

    #Instanciar los modulos de hardware
    ram  = RAM(word_size="64", positions=MAX_RAM)
    reg  = Registers()
    alu  = Alu(reg)
    cpu  = CPU(ram, reg, alu)

    #Cargar programa con el Loader (ANTES del ciclo run)
    loader = Loader(start_address=base_addr)
    entry_point = loader.load(filename, ram)

    # Inicializar PC y SP
    reg.PC = entry_point
    reg.SP = MAX_RAM - 1

    print(f"  Programa: {filename}")
    print(f"  PC: {entry_point}  |  SP: {reg.SP}")

    #Ejecutar
    cpu.run()

    print(f"  Detenida tras {cpu.cycle_count} ciclos")
    cpu.dump_registers()


if __name__ == "__main__":
    main()
