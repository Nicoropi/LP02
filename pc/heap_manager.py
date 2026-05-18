class VirtualHeap:
    def __init__(self, ram_reference, start_address=20000, end_address=40000):
        """
        Gestiona el espacio dinámico (Heap) de la RAM simulada de forma segura
        sin colisionar con el Stack (zona alta) ni el Código objeto (zona baja).
        """
        self.ram = ram_reference
        self.start = start_address
        self.end = end_address
        
        # Diccionario de control: { dirección_inicio: tamaño_en_words }
        self.allocated_blocks = {}
        
        # Puntero para asignaciones secuenciales (Free Pointer)
        self.free_ptr = start_address

    def allocate(self, size_in_words, cpu_reference):
        """
        Reserva espacio en el Heap. Si excede el límite asignado,
        invoca al Garbage Collector.
        """
        if self.free_ptr + size_in_words > self.end:
            print(f"\n[HEAP] ¡Límite alcanzado! Intentando recolectar memoria para {size_in_words} celdas...")
            self.run_garbage_collector(cpu_reference)
            
            # Verificar si se liberó espacio contiguo suficiente después del ciclo de GC
            if self.free_ptr + size_in_words > self.end:
                print("[HEAP CRITICAL ERROR] Out of Memory: Espacio de Heap totalmente agotado.")
                cpu_reference.running = False
                return 0
        
        address = self.free_ptr
        self.allocated_blocks[address] = size_in_words
        self.free_ptr += size_in_words
        print(f"[HEAP] Bloque asignado en RAM[{address}] con tamaño {size_in_words}")
        return address

    def run_garbage_collector(self, cpu):
        """
        Algoritmo Tracing Mark-Sweep integrado con la arquitectura nativa.
        Identifica el Root Set leyendo 'cpu.reg.general' y el stack dinámico.
        """
        print("\n=======================================================")
        print("   INICIANDO RECOLECCIÓN DE BASURA (MARK & SWEEP)   ")
        print("=======================================================")
        
        root_set = set()
        
        # 1. ESCANEAR REGISTROS GENERALES (cpu.reg.general)
        for reg_name, reg_val in cpu.reg.general.items():
            if self.start <= reg_val < self.end:
                root_set.add(reg_val)
                
        # 2. ESCANEAR REGISTROS ESPECIALES
        for spec_reg in ['PC', 'SP', 'BP', 'MAR', 'MDR', 'IR']:
            reg_val = getattr(cpu.reg, spec_reg, 0)
            if self.start <= reg_val < self.end:
                root_set.add(reg_val)
                
        # 3. ESCANEAR EL STACK DINÁMICO EN LA RAM
        # El SP empieza en MAX_RAM - 1 y el BP marca la base del marco actual.
        sp_val = cpu.reg.SP
        bp_val = cpu.reg.BP
        
        # Escaneamos todas las celdas del stack utilizando llamadas de lectura (control=0)
        # Nota: El stack en tu entorno se mueve en la zona alta (ej. entre BP y SP)
        stack_start = min(sp_val, bp_val)
        stack_end = max(sp_val, bp_val)
        
        for stack_addr in range(stack_start, stack_end + 1):
            # Leemos mediante el bus (control=0 -> MemRead)
            stack_content = self.ram.request(data=0, direction=stack_addr, control=0)
            if self.start <= stack_content < self.end:
                root_set.add(stack_content)

        print(f"[GC - ROOT SET] Raíces vivas encontradas: {list(root_set)}")

        # 4. FASE DE MARCADO (Recursión en grafos de objetos)
        marked_addresses = set()
        for root in root_set:
            self._mark_recursive(root, marked_addresses)

        print(f"[GC - MARK] Bloques accesibles/vivos: {list(marked_addresses)}")

        # 5. FASE DE BARRIDO (Sweep)
        dead_blocks = []
        for addr in list(self.allocated_blocks.keys()):
            if addr not in marked_addresses:
                dead_blocks.append(addr)

        # Liberar bloques huérfanos reescribiendo la RAM con ceros
        for dead_addr in dead_blocks:
            size = self.allocated_blocks.pop(dead_addr)
            print(f"[GC - SWEEP] Liberando celdas muertas en RAM[{dead_addr}] ({size} celdas)")
            for offset in range(size):
                # Escribimos ceros mediante el bus (control=1 -> MemWrite)
                self.ram.request(data=0, direction=dead_addr + offset, control=1)

        # 6. COMPACTACIÓN BÁSICA DEL PUNTERO LIBRE
        if marked_addresses:
            last_alive_addr = max(marked_addresses)
            last_alive_size = self.allocated_blocks[last_alive_addr]
            self.free_ptr = last_alive_addr + last_alive_size
        else:
            self.free_ptr = self.start
            
        print(f"[GC] Compactación lista. Próxima ranura libre del Heap: RAM[{self.free_ptr}]")
        print("=======================================================\n")

    def _mark_recursive(self, addr, marked):
        """ Rastrea si un bloque del heap contiene punteros a otros bloques """
        if addr in marked or addr not in self.allocated_blocks:
            return
            
        marked.add(addr)
        block_size = self.allocated_blocks[addr]
        
        # Escanea el contenido del struct en busca de referencias internas
        for offset in range(block_size):
            cell_content = self.ram.request(data=0, direction=addr + offset, control=0)
            if self.start <= cell_content < self.end:
                self._mark_recursive(cell_content, marked)