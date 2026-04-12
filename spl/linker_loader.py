import ply.lex as lex
from pc.ram import RAM
import sys
import os
import re

tokens = ("STRING", "BINARY", "HEX", "NUMBER")

t_ignore = " \t\n"


def t_STRING(t):
    r'"[^"]*"'
    t.value = t.value.strip('"')
    return t


def t_BINARY(t):
    r"0b[01]+"
    t.value = int(t.value[2:], 2)
    return t


def t_HEX(t):
    r"0x[0-9a-fA-F]+"
    t.value = int(t.value[2:], 16)
    return t


def t_NUMBER(t):
    r"\d+"
    t.value = int(t.value)
    return t


def t_error(t):
    print(f"Token ilegal: {t.value[0]}")
    t.lexer.skip(1)


class LinkerLoader:
    def __init__(self):
        self.labels = {}
        self.dir_offset = 0
        self.text_dir_offset = self.dir_offset
        self.data_dir_offset = self.dir_offset
        self.text_dirs = {}
        self.text = []
        self.data = []
        self.data_replace = {}
        self.text_replace = {}

    def _skip_empty_strings(self, tokens, i):
        while (
            i < len(tokens)
            and tokens[i].type == "STRING"
            and tokens[i].value in ("", "\\0")
        ):
            i += 1
        return i

    def load_object(self, files: list[str]):
        lexer = lex.lex()
        for file in files:
            self.current_file = file
            try:
                with open(file) as f:
                    content = f.read()
            except FileNotFoundError:
                print(f"No se encontro el archivo {file}")

            lexer.input(content)

            tokens = []
            while tok := lexer.token():
                tokens.append(tok)

            self._parse(tokens)
            self.text_dir_offset = len(self.text) + self.dir_offset
            self.data_dir_offset = len(self.data) + self.dir_offset
            print(f"{self.text_dir_offset=}, {self.data_dir_offset=}")

    def _parse(self, tokens):
        i = 0

        # TEXT LABELS
        while (
            i < len(tokens) and tokens[i].type == "STRING" and tokens[i].value != "\\0"
        ):
            if i + 1 >= len(tokens):
                raise Exception("Formato inválido en labels")

            label = tokens[i].value
            addr = tokens[i + 1].value

            self.labels[label] = addr + self.text_dir_offset
            i += 2
        i += 1

        # DATA LABELS
        while (
            i < len(tokens) and tokens[i].type == "STRING" and tokens[i].value != "\\0"
        ):
            if i + 1 >= len(tokens):
                raise Exception("Formato inválido en labels")

            label = tokens[i].value
            addr = tokens[i + 1].value

            self.labels[label] = addr + self.data_dir_offset - self.dir_offset
            i += 2
        i += 1
        # TEXT REPLACE
        while (
            i < len(tokens) and tokens[i].type == "STRING" and tokens[i].value != "\\0"
        ):
            label = tokens[i].value
            i += 1

            if i >= len(tokens):
                raise Exception("Formato inválido en text_replace")

            count = tokens[i].value
            i += 1
            pos_info = []
            for _ in range(count):
                if i + 1 >= len(tokens):
                    raise Exception("Formato inválido en posiciones")
                start = tokens[i].value
                length = tokens[i + 1].value
                pos_info.append((start, length))
                i += 2
            self.text_replace[label] = pos_info
        i += 1

        # TEXT DIRECTIONS
        i = self._skip_empty_strings(tokens, i)
        if i >= len(tokens):
            raise Exception("Formato inválido: falta TEXT DIRS")

        i = self._skip_empty_strings(tokens, i)

        if i >= len(tokens) or tokens[i].type not in ("NUMBER", "BINARY", "HEX"):
            raise Exception(
                f"Se esperaba número en TEXT DIRS, encontrado {tokens[i].type}"
            )

        n_dirs = tokens[i].value
        i += 1

        for _ in range(n_dirs):
            if i + 1 >= len(tokens):
                raise Exception("Formato inválido en text_dirs")

            dir_val = tokens[i].value + self.text_dir_offset
            i += 1

            count = tokens[i].value
            i += 1

            positions = []
            for _ in range(count):
                if i + 1 >= len(tokens):
                    raise Exception("Formato inválido en posiciones")

                start = tokens[i].value
                length = tokens[i + 1].value
                positions.append(
                    (start + (self.text_dir_offset - self.dir_offset) * 64, length)
                )
                i += 2

            self.text_dirs[dir_val] = positions
        # TEXT SECTION
        if i >= len(tokens):
            raise Exception("Formato inválido: falta TEXT SECTION")

        i = self._skip_empty_strings(tokens, i)

        if tokens[i].type not in ("NUMBER", "BINARY", "HEX"):
            raise Exception("Se esperaba número en TEXT SECTION")

        n_text = tokens[i].value
        i += 1

        for _ in range(n_text):
            if i >= len(tokens):
                break

            if tokens[i].type not in ("NUMBER", "BINARY", "HEX"):
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
                            raise Exception(
                                "Formato inválido en data_replace posiciones"
                            )
                        positions.append(
                            tokens[i].value + self.data_dir_offset - self.dir_offset
                        )
                        i += 1

                    self.data_replace[label] = positions

                    i = self._skip_empty_strings(tokens, i)

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
                raise Exception(
                    "DATA inconsistente: tamaño mayor que tokens disponibles"
                )

            for _ in range(n_data):
                if i >= len(tokens):
                    raise Exception("Formato inválido en DATA")

                self.data.append(tokens[i].value)
                i += 1

    def resolve(self, base=0):
        for addr, positions in self.text_dirs.items():
            for bit_pos, bit_len in positions:
                instr_index = bit_pos // 64
                offset = bit_pos % 64

                mask = (1 << bit_len) - 1

                self.text[instr_index] |= (addr & mask) << offset

    def resolve_data(self):
        text_offset = self.text_dir_offset - self.dir_offset
        data_offset = self.data_dir_offset - self.dir_offset

        for label, positions in self.data_replace.items():
            if label not in self.labels:
                raise Exception(f"Label no definido: {label}")
            addr = self.labels[label] + data_offset
            for pos in positions:
                self.data[pos] = addr

        for label, positions in self.text_replace.items():
            if label not in self.labels:
                raise Exception(f"Label no definido: {label}")
            addr = self.labels[label] + text_offset
            for start, length in positions:
                index = start // 64
                start_bit = start % 64
                length = min(length, 64 - start_bit)
                mask = (1 << length) - 1
                trunk = addr & mask
                shift = 64 - start_bit - length
                self.text[index] &= ~(mask << shift)
                self.text[index] |= trunk << shift

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

        # LOAD DATA
        for word in self.data:
            ram.request(data=word, direction=addr, control=1)
            addr += 1

        return self.labels.get("main", start)

    def load_to_file(self, output_file):
        with open(output_file, "w") as file:
            file.write("#TEXT SECTION\n")
            for word in self.text:
                file.write(f"0x{word:016X}\n")
            file.write("#DATA SECTION\n")
            for word in self.data:
                file.write(f"0x{word:016X}\n")


def main():
    # Formato:  py linker_loader.py <nombre_archivo.o> <direccion>

    if len(sys.argv) < 2:
        print(
            "Uso: python linker_loader.py <archivo> [otros]... [-o resultado] [--dir=<direccion>]"
        )
        sys.exit(1)

    obj_files = []

    base = 0
    out_file = None
    arg_itr = iter(sys.argv[1:])
    for arg in arg_itr:
        match = re.match(r"--dir=(.+)", arg)

        if match is not None:
            num = match.group(1)
            if num.isdigit():
                base = int(num)
                continue
            if num[:2] == "0b":
                if re.match(r"[^0-1]", num[2:]) is not None:
                    print(
                        'Error: numero binario invalido despues de "--dir"',
                        file=sys.stderr,
                    )
                    return
                base = int(num[2:], 2)

            elif num[:2] == "0b":
                if re.match(r"[^0-1]", num[2:]) is not None:
                    print(
                        'Error: numero binario invalido despues de "--dir"',
                        file=sys.stderr,
                    )
                    return
                base = int(num[2:], 2)

        if arg == "-o":
            out_file = next(arg_itr, None)
            if out_file is None:
                print(
                    'Error: no se especifico archivo despues de "-o"', file=sys.stderr
                )
                return
            continue

        obj_files.append(arg.strip("\"'"))

    ram = RAM()
    linker = LinkerLoader()

    try:
        linker.load_object(obj_files)
        linker.resolve(base)
        linker.resolve_data()
        entry = linker.load_to_ram(ram, start=base)

        if out_file is not None:
            linker.load_to_file(out_file)
            return
    except Exception as e:
        print(f"Error durante linking/loading: {e}")
        sys.exit(1)

    print(f"Programa cargado desde dirección {entry}")

    # print("\nContenido en RAM:")
    # for i in range(base, base + 10):
    #     val = ram.request(0, i, 0)
    #     print(f"RAM[{i}] = {val:#018x}")

    from pc.register import Registers
    from pc.alu import Alu
    from pc.fpu import FPU
    from pc.cpu import CPU
    from pc.loader import Loader

    reg = Registers()
    fpu = FPU(reg)
    alu = Alu(reg, fpu)
    cpu = CPU(ram, reg, alu)

    MAX_RAM = 2**16

    # Inicializar PC y SP
    reg.PC = base
    reg.SP = MAX_RAM - 1

    # print(f"  Programa: {filename}")
    print(f"  PC: {base}  |  SP: {reg.SP}")

    # Ejecutar
    # return
    try:
        cpu.run()
    except KeyboardInterrupt:
        print(reg.PC, reg.SP)

    print(f"  Detenida tras {cpu.cycle_count} ciclos")
    cpu.dump_registers()


if __name__ == "__main__":
    main()
