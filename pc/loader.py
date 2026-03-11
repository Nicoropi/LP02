WORD_SIZE = 64
CONTROL_WRITE = 1  # impar = write
OPCODE_BITS = 8
OPERAND_BITS = WORD_SIZE - OPCODE_BITS

ADDRESS_MASK = (1 << OPERAND_BITS) - 1

JUMP_OPCODES = {
    0x01,  # JMP
    0x02,  # JMPZ
    0x03,  # JMPNZ
    0x04,  # JMPN
    0x05,  # JMPNN
    0x06,  # JMPOVR
    0x07,  # JMPUND
    0x08,  # JMPNORZ
    0x09,  # JMPNANDZ
}

# ==== ERRORES ====

class LoaderError(Exception):
    pass


# ==== LOADER ====

class Loader:
    """
    Cargador de programas binarios con reubicación.
    """

    def __init__(self, start_address: int = 0):
        self.start_address = start_address
        self.entry_point = start_address
        self.end_address = start_address

    def _relocate(self, word: int) -> int:
        """
        Ajusta direcciones internas de la instrucción si es necesario.
        """
        opcode = (word >> OPERAND_BITS) & ((1 << OPCODE_BITS) - 1)

        if opcode in JUMP_OPCODES:
            addr = word & ADDRESS_MASK
            addr += self.start_address

            # reconstruir palabra
            word = (word & ~ADDRESS_MASK) | addr

        return word

    def load(self, filename: str, ram) -> int:
        """
        Carga el programa en RAM y retorna el entry point.
        """

        addr = self.start_address

        with open(filename, "r") as f:
            for line_number, line in enumerate(f, start=1):
                line = line.strip()

                # ignorar líneas vacías o comentarios
                if not line or line.startswith("#"):
                    continue

                # validaciones
                if len(line) != WORD_SIZE:
                    raise LoaderError(
                        f"Línea {line_number}: tamaño inválido ({len(line)} bits)"
                    )

                if any(c not in "01" for c in line):
                    raise LoaderError(
                        f"Línea {line_number}: carácter inválido"
                    )

                # convertir a entero
                word = int(line, 2)

                # reubicación
                word = self._relocate(word)

                # escritura en RAM vía bus
                ram.request(
                    data=word,
                    direction=addr,
                    control=CONTROL_WRITE
                )

                addr += 1

        self.entry_point = self.start_address
        self.end_address = addr

        return self.entry_point