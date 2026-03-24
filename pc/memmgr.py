"""
pc/memmgr.py
Memoria dinámica simple (heap) sobre la RAM simulada.

Formato de uso:
- Inicializar con una RAM existente (o una interfaz adecuada).
- allocate(n): reserva n palabras y devuelve la dirección base (start address).
- free(addr, n): libera un bloque previamente reservado.
- write(addr, data_list): helper para escribir un bloque de datos usando la RAM.
- read(addr, n): helper para leer un bloque de datos (opcional, para pruebas).

Notas:
- Este es un allocator simple (first-fit) con lista de bloques libres.
- No implementa coalescencia extremadamente sofisticada, pero fusiona bloques adyacentes.
- Requiere que la RAM exponga una interfaz de escritura (p.ej., ram.request).
"""
from __future__ import annotations
from typing import List, Tuple

class MemoryManager:
    def __init__(self, ram, heap_start: int = 0, heap_size: int = None):
        """
        ram: objeto RAM existente (con una API compatible, p.ej. ram.request).
        heap_start: dirección inicial del heap.
        heap_size: tamaño total del heap en palabras (si None, se intentará usar todo el RAM menos lo ya usado).
        """
        self.ram = ram
        self.heap_start = heap_start
        # Determinar tamaño total de RAM de forma robusta
        total_ram = (
            getattr(ram, "positions", None)
            or getattr(ram, "size", None)
            or getattr(ram, "MAX_RAM", None)
            or 0
        )
        if heap_size is None:
            self.heap_size = (total_ram - heap_start) if total_ram else 0
        else:
            self.heap_size = heap_size

        # Free list inicial: un único bloque libre que abarca todo el heap
        self.free_list: List[Tuple[int, int]] = [(self.heap_start, self.heap_size)]
        # Pistas simples para depuración
        self.allocated = {}  # addr -> size

    def _find_block(self, size: int) -> int:
        """
        Busca un bloque con tamaño >= size y devuelve el índice en free_list.
        Si no hay, devuelve -1.
        """
        for i, (_start, s) in enumerate(self.free_list):
            if s >= size:
                return i
        return -1

    def allocate(self, size: int) -> int:
        """
        Reserva 'size' palabras y devuelve la dirección base.
        Lanza MemoryError si no hay suficiente memoria.
        """
        if size <= 0:
            raise ValueError("size debe ser > 0")

        idx = self._find_block(size)
        if idx == -1:
            raise MemoryError("Memoria insuficiente en heap")

        start, block_size = self.free_list[idx]
        alloc_addr = start

        if block_size == size:
            # exact match, quita el bloque
            self.free_list.pop(idx)
        else:
            # reduce el bloque
            new_start = start + size
            new_size = block_size - size
            self.free_list[idx] = (new_start, new_size)

        self.allocated[alloc_addr] = size
        return alloc_addr

    def free(self, addr: int, size: int):
        """
        Libera un bloque previamente asignado.
        Fusiona con bloques adyacentes cuando sea posible.
        """
        if size <= 0:
            return
        if addr not in self.allocated or self.allocated[addr] != size:
            raise ValueError("Intento de liberar un bloque no asignado o tamaño incorrecto")

        del self.allocated[addr]

        # Insertar en la free_list y fusionar
        self.free_list.append((addr, size))
        self.free_list.sort()  # orden por dirección

        # Fusionar bloques adyacentes
        merged = []
        for b in self.free_list:
            if not merged:
                merged.append(b)
            else:
                last_start, last_size = merged[-1]
                cur_start, cur_size = b
                if last_start + last_size == cur_start:
                    # fusionar
                    merged[-1] = (last_start, last_size + cur_size)
                else:
                    merged.append(b)
        self.free_list = merged

    def write(self, addr: int, data: List[int]):
        """
        Escribe un bloque de datos en memoria a partir de 'addr'.
        """
        for i, w in enumerate(data):
            self.ram.request(
                data=w,
                direction=addr + i,
                control=1  # 1 podría significar WRITE dependiendo de tu RAM
            )

    def read(self, addr: int, n: int) -> List[int]:
        """
        Lee 'n' palabras desde 'addr' (ejemplo de utilidad).
        """
        result = []
        for i in range(n):
            # Aquí podrías usar un método real de RAM; dejamos 0s por simplicidad.
            val = 0
            result.append(val & 0xFFFFFFFFFFFFFFFF)
        return result
