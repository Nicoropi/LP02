import sys

from pc.ram      import RAM
from pc.register import Registers
from pc.alu_2    import Alu
from pc.cpu      import CPU
from pc.loader   import Loader
from pc.memmgr   import MemoryManager

MAX_RAM = 2 ** 16

# Configuración mínima del heap dinámico
MEM_HEAP_START = 0x1000  # dirección donde empieza el heap (ajusta según tu RAM)
MEM_HEAP_SIZE  = MAX_RAM - MEM_HEAP_START

def count_lines_bin(path: str) -> int:
    """Cuenta cuántas líneas (palabras) tiene un bin .bin (la entrada a Loader espera palabras de 64 bits)."""
    count = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            count += 1
    return count

def spawn_bin(filename: str, ram, memmgr: MemoryManager) -> int:
    """
    Carga un binario .bin en el heap y retorna su entry point (su base).
    """
    n_words = count_lines_bin(filename)
    if n_words <= 0:
        raise RuntimeError(f"No se pudo determinar tamaño de palabras en {filename}")

    addr = memmgr.allocate(n_words)
    loader = Loader(start_address=addr)
    entry_point = loader.load(filename, ram)
    return entry_point

def main_spawn_multiple(filenames, ram, memmgr):
    """
    Carga múltiples bins en el heap y retorna una lista de (filename, entry, base).
    """
    results = []
    for fn in filenames:
        ep = spawn_bin(fn, ram, memmgr)
        results.append((fn, ep, MEM_HEAP_START))  # base fijo para este ejemplo
    return results

def main():
    """Punto de entrada: conecta los modulos, carga el programa y ejecuta.
    Uso: python environment.py <archivo.bin> [dir_base]
    O bien: python environment.py --spawn bin1.bin bin2.bin ...
    """
    if len(sys.argv) < 2:
        print("Uso: python environment.py <archivo.bin> [dir_base]")
        print("Opcional: --spawn bin1.bin bin2.bin ... para cargar varios en una misma sesión.")
        sys.exit(1)

    ram  = RAM(word_size="64", positions=MAX_RAM)
    reg  = Registers()
    alu  = Alu(reg)
    cpu  = CPU(ram, reg, alu)

    memmgr = MemoryManager(ram, heap_start=MEM_HEAP_START, heap_size=MEM_HEAP_SIZE)

    # Modo spawn múltiple
    if sys.argv[1] == "--spawn":
        files = sys.argv[2:]
        if not files:
            print("Especifica al menos un bin para spawnear.")
            sys.exit(1)
        spawned = main_spawn_multiple(files, ram, memmgr)
        print("Spawn realizados:")
        for fn, ep, base in spawned:
            print(f" - {fn}: entry={ep}, base={base}")
        if not spawned:
            sys.exit(0)
        # Ejecuta el primer módulo
        first_ep = spawned[0][1]
        reg.PC = first_ep
        reg.SP = MAX_RAM - 1
        cpu.run()
        print(f"Detenida tras {cpu.cycle_count} ciclos")
        cpu.dump_registers()
        return

    # Flujo normal (un único bin ya preparado .bin)
    filename  = sys.argv[1]
    base_addr = int(sys.argv[2]) if len(sys.argv) > 2 else 0

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
