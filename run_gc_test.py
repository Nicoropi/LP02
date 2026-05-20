import os
import sys
from spl.compiler import Parser, CodeGenerator
from spl.assembly import Assembler, Builder
from pc.ram import RAM
from pc.register import Registers
from pc.alu import Alu
from pc.fpu import FPU
from pc.cpu import CPU
from pc.heap_manager import VirtualHeap

def run_pipeline():
    ruta_archivo = "programs/data_structures/test_gc.spl"
    print(f"[1/4] Leyendo archivo de alto nivel {ruta_archivo}...")
    if not os.path.exists(ruta_archivo):
        print(f"Error: No se encontró el archivo en '{ruta_archivo}'")
        return
        
    with open(ruta_archivo, "r") as f: # Asegúrate de que use la variable con la ruta corregida
        spl_code = f.read()

    # --- FASE 1: COMPILACIÓN SPL -> ASM ---
    print("[2/4] Compilando SPL a Lenguaje Ensamblador...")
    parser = Parser()
    ast = parser.parse(spl_code)
    
    codegen = CodeGenerator()
    asm_code = codegen.generate(ast)
    
    # Guardamos el assembly generado para inspección visual
    with open("output_test_gc.asm", "w") as f:
        f.write(asm_code)
    print("      -> Assembly generado en 'output_test_gc.asm'")

    # --- FASE 2: ENSAMBLADO ASM -> OBJETO (LÍNEAS BINARIAS) ---
    print("[3/4] Ensamblando código máquina...")
    assembler = Assembler(readable="bin")
    builder_obj = assembler.assemble_text(asm_code)
    
    # --- FASE 3: CARGA EN COMPRENSION HARDWARE ---
    print("[4/4] Inicializando Hardware Simulado...")
    ram = RAM(word_size="64", positions=65536)
    reg = Registers()
    fpu = FPU(reg)
    alu = Alu(reg, fpu)
    
    # Rango del Heap de prueba: RAM[20000] a RAM[20005]
    heap = VirtualHeap(ram_reference=ram, start_address=20000, end_address=20005)
    cpu = CPU(ram, reg, alu, heap=heap)

    # Inyectar las instrucciones directamente en la RAM simulada desde la dirección 0
    addr = 0
    for elemento in builder_obj._textOutput:
        word_value = elemento
        
        # Si el ensamblador entrega strings binarios '0b...', los decodificamos a enteros
        if isinstance(word_value, str):
            clean_bin = word_value.replace("0b", "").replace("0x", "")
            base = 16 if "0x" in word_value else (2 if "0b" in word_value else 10)
            word_value = int(clean_bin, base)
            
        ram.request(data=word_value, direction=addr, control=1) # control=1 -> Escritura
        addr += 1

    # Inicializar punteros de la CPU
    reg.PC = 0
    reg.SP = 65535 # Stack inicia arriba del todo
    reg.BP = 65535

    print("\n🚀 --- EMPEZANDO EJECUCIÓN EN LA CPU --- 🚀")
    
    # Ejecutamos ciclo por ciclo para monitorear el Heap
    try:
        while cpu.running and cpu.cycle_count < 1000:
            cpu.fetch()
            
            # Capturar la Syscall personalizada
            if cpu.get_reg(0xE) == 9999:
                size_requested = cpu.get_reg(0xA) # R1 contiene el tamaño
                print(f"\n[SYS_ALLOC DETECTADA] CPU solicita {size_requested} celdas.")
                allocated_addr = heap.allocate(size_requested, cpu)
                cpu.set_reg(0xE, allocated_addr) # Retorna dirección en R5
                continue
                
            cpu.execute()
            cpu.cycle_count += 1
            
    except Exception as e:
        print(f"\n[ERROR DE EJECUCIÓN]: {e}")

    print("\n========== RESULTADO FINAL DEL HARDWARE ==========")
    print(f"Ciclos totales ejecutados: {cpu.cycle_count}")
    print(f"Bloques remanentes en el Registro del Heap: {heap.allocated_blocks}")
    print(f"Puntero de asignación libre final: RAM[{heap.free_ptr}]")
    print("==================================================")

if __name__ == "__main__":
    run_pipeline()
