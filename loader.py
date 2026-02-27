WORD_SIZE = 64
CONTROL_WRITE = 1  # impar = write


class LoaderError(Exception):
    pass


class Loader:
    def __init__(self, start_address: int = 0):
        """
        Loader de programas binarios.
        """
        self.start_address = start_address
        self.entry_point = start_address
        self.end_address = start_address

    def load(self, filename: str, ram) -> int:
        """
        Carga el programa en RAM y retorna el entry point.
        """

        addr = self.start_address

        with open(filename, "r") as f:
            for line_number, line in enumerate(f, start=1):
                line = line.strip()

                if not line or line.startswith("#"):
                    continue

                if len(line) != WORD_SIZE:
                    raise LoaderError(
                        f"Línea {line_number}: tamaño inválido"
                    )

                if any(c not in "01" for c in line):
                    raise LoaderError(
                        f"Línea {line_number}: carácter inválido"
                    )

                word = int(line, 2)

                ram.request(
                    data=word,
                    direction=addr,
                    control=CONTROL_WRITE
                )

                addr += 1

        self.entry_point = self.start_address
        self.end_address = addr

        return self.entry_point