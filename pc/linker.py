"""
pc/linker_simple.py
Enlazador estático simple para unir varios bins (.bin) en un único programa.

Formato esperado de entrada:
- Archivos .bin: cada fila es una palabra de 64 bits en binario (0/1).

Funcionamiento:
- Lee cada bin y lo coloca en memoria contigua, calculando una base para cada uno.
- Proporciona (final_words, entry_addr) donde:
  - final_words: lista de palabras 64-bit que componen el binario final.
  - entry_addr: dirección de inicio del binario final.
- Es útil para pruebas rápidas o para un flujo estático simple.

Notas:
- No maneja símbolos entre bins ni relocaciones cruzadas en este simple enlazador.
- Puedes ampliar para soportar cabeceras o relocaciones más adelante si lo necesitas.
"""

from __future__ import annotations
from typing import List, Tuple

def read_bin_words(path: str) -> List[int]:
    """
    Lee un binario en formato texto (064 bits por línea) y devuelve una lista de enteros.
    Ignora líneas en blanco o comentarios que comiencen con '#'.
    """
    words: List[int] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            words.append(int(s, 2) & ((1 << 64) - 1))
    return words

class SimpleBinLinker:
    def __init__(self):
        self.bases: List[int] = []

    def link(self, bin_paths: List[str], base_start: int = 0) -> Tuple[List[int], int]:
        """
        Concatena los bins en memoria contigua, sin relocación entre bins.
        Retorna (final_words, entry_addr).
        - final_words: palabras 64-bit del binario final.
        - entry_addr: dirección de inicio del binario final.
        Nota: no maneja símbolos inter-bin; se asume que no hay dependencias cruzadas.
        """
        self.bases = []
        final_words: List[int] = []
        current_base = base_start

        for path in bin_paths:
            words = read_bin_words(path)
            self.bases.append(current_base)
            final_words.extend(words)
            current_base += len(words)
            
        entry_addr = base_start if bin_paths else 0
        return final_words, entry_addr

def write_bin(path: str, words: List[int]) -> None:
    """
    Escribe el binario final en formato texto (064 bits por línea).
    """
    with open(path, "w", encoding="utf-8") as f:
        for w in words:
            f.write(f"{w:064b}\n")

__all__ = ["SimpleBinLinker", "read_bin_words", "write_bin"]
