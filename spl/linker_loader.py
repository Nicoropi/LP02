import ply.lex as lex
from pc.ram import RAM
import sys
import os

tokens = ("STRING", "BINARY", "NUMBER")

t_ignore = " \t\n"

def t_STRING(t):
    r'"[^"]*"'
    t.value = t.value.strip('"')
    return t

def t_BINARY(t):
    r'0b[01]+'
    t.value = int(t.value[2:], 2)
    return t

def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_error(t):
    print(f"Token ilegal: {t.value[0]}")
    t.lexer.skip(1)

class LinkerLoader:

    def __init__(self):
        self.labels = {}
        self.text_dirs = {}
        self.text = []
        self.data = []
        self.data_replace = {}

    def _skip_empty_strings(self, tokens, i):
        while (
            i < len(tokens)
            and tokens[i].type == "STRING"
            and tokens[i].value in ("", "\\0")
        ):
            i += 1
        return i

    def load_object(self, filename):
        lexer = lex.lex()

        with open(filename) as f:
            content = f.read()

        lexer.input(content)

        tokens = []
        while tok := lexer.token():
            tokens.append(tok)

        self._parse(tokens)
    
    def _parse(self, tokens):
        i = 0
        # LABELS
        while i < len(tokens) and tokens[i].type == "STRING" and tokens[i].value == "":

            i = self._skip_empty_strings(tokens, i)

            if i + 1 >= len(tokens):
                raise Exception("Formato inválido en labels")

            label = tokens[i].value
            addr = tokens[i + 1].value

            self.labels[label] = addr
            i += 2
        
        # TEXT REPLACE 
        while i < len(tokens) and tokens[i].type == "STRING" and tokens[i].value == "":
            i += 1

            i = self._skip_empty_strings(tokens, i)
            label = tokens[i].value
            i += 1

            if i >= len(tokens):
                raise Exception("Formato inválido en text_replace")

            count = tokens[i].value
            i += 1
            # saltar pares
            i += count * 2

        # TEXT DIRECTIONS
        i = self._skip_empty_strings(tokens, i)
        if i >= len(tokens):
            raise Exception("Formato inválido: falta TEXT DIRS")

        i = self._skip_empty_strings(tokens, i)

        if i >= len(tokens) or tokens[i].type not in ("NUMBER", "BINARY"):
            raise Exception(f"Se esperaba número en TEXT DIRS, encontrado {tokens[i].type}")

        n_dirs = tokens[i].value
        i += 1

        for _ in range(n_dirs):
            if i + 1 >= len(tokens):
                raise Exception("Formato inválido en text_dirs")

            dir_val = tokens[i].value
            i += 1

            count = tokens[i].value
            i += 1

            positions = []
            for _ in range(count):
                if i + 1 >= len(tokens):
                    raise Exception("Formato inválido en posiciones")

                start = tokens[i].value
                length = tokens[i + 1].value
                positions.append((start, length))
                i += 2

            self.text_dirs[dir_val] = positions
        # TEXT SECTION
        if i >= len(tokens):
            raise Exception("Formato inválido: falta TEXT SECTION")

        i = self._skip_empty_strings(tokens, i)

        if tokens[i].type not in ("NUMBER", "BINARY"):
            raise Exception("Se esperaba número en TEXT SECTION")

        n_text = tokens[i].value
        i += 1

        for _ in range(n_text):
            if i >= len(tokens):
                break

            if tokens[i].type not in ("NUMBER", "BINARY"):
                break

            self.text.append(tokens[i].value)
            i += 1

            # DATA REPLACE 
            i = self._skip_empty_strings(tokens, i)

            if i < len(tokens) and tokens[i].type == "STRING":
                while i < len(tokens) and tokens[i].type == "STRING":
                    label = tokens[i].value
                    i += 1

                    if i >= len(tokens):
                        raise Exception("Formato inválido en data_replace")

                    count = tokens[i].value
                    i += 1

                    positions = []
                    for _ in range(count):
                        if i >= len(tokens):
                            raise Exception("Formato inválido en data_replace posiciones")
                        positions.append(tokens[i].value)
                        i += 1

                    self.data_replace[label] = positions

                    i = self._skip_empty_strings(tokens, i)

        print(">> i:", i, "token:", tokens[i] if i < len(tokens) else "EOF")

        i = self._skip_empty_strings(tokens, i)

        if i >= len(tokens):
            return  # No DATA SECTION
        
        # DATA SECTION
        n_data = 0
        i = self._skip_empty_strings(tokens, i)
        if i < len(tokens) and tokens[i].type in ("NUMBER", "BINARY"):

            n_data = tokens[i].value
            i += 1

            if n_data > (len(tokens) - i):
                raise Exception("DATA inconsistente: tamaño mayor que tokens disponibles")

            for _ in range(n_data):
                if i >= len(tokens):
                    raise Exception("Formato inválido en DATA")

                self.data.append(tokens[i].value)
                i += 1

    def resolve(self, base=0):
        for addr, positions in self.text_dirs.items():
            for (bit_pos, bit_len) in positions:

                instr_index = bit_pos // 64
                offset = bit_pos % 64

                mask = (1 << bit_len) - 1

                self.text[instr_index] |= (addr & mask) << offset

    def resolve_data(self):
        for label, positions in self.data_replace.items():
            if label not in self.labels:
                raise Exception(f"Label no definido: {label}")

            addr = self.labels[label]

            for pos in positions:
                self.data[pos] = addr

    def load_to_ram(self, ram, start=0):
        addr = start

        # LOAD TEXT
        for word in self.text:
            ram.request(data=word, direction=addr, control=1)
            addr += 1

        # TEMPORAL
        if not self.text or self.text[-1] != 0xFFFFFFFFFFFFFFFF:
            ram.request(data=0xFFFFFFFFFFFFFFFF, direction=addr, control=1)
            addr += 1
        # ---
        
        data_start = addr
        new_labels = {}
        for label, addr_label in self.labels.items():
            if addr_label >= len(self.text):
                new_labels[label] = addr_label + data_start
            else:
                new_labels[label] = addr_label

        self.labels = new_labels

        # LOAD DATA
        for word in self.data:
            ram.request(data=word, direction=addr, control=1)
            addr += 1

        return self.labels.get("main", start)

def main():

    # Formato:  py linker_loader.py <nombre_archivo.o> <direccion>

    if len(sys.argv) < 2:
        print("Uso: python linker_loader.py <archivo_objeto> [direccion]")
        sys.exit(1)

    obj_file = sys.argv[1]


    base = int(sys.argv[2]) if len(sys.argv) > 2 else 0

    ram = RAM()
    linker = LinkerLoader()

    try:
        linker.load_object(obj_file)
        linker.resolve(base)
        linker.resolve_data()
        entry = linker.load_to_ram(ram, start=base)
    except Exception as e:
        print(f"Error durante linking/loading: {e}")
        sys.exit(1)

    print(f"Programa cargado desde dirección {entry}")

    print("\nContenido en RAM:")
    for i in range(base, base + 10):
        val = ram.request(0, i, 0)
        print(f"RAM[{i}] = {val:#018x}")

if __name__ == "__main__":
    main()
