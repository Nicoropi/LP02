# Máscara de 64 bits: se usa para truncar cualquier valor al rango [0, 2^64-1]
WORD_MASK_64 = (1 << 64) - 1


class RAM:
    """Emula la memoria principal (RAM) de palabra configurable.

    Internamente almacena enteros sin signo de 64 bits en una lista de Python.
    La interfaz pública es el método ``request()``, que simula el Bus de Datos,
    el Bus de Direcciones y el Bus de Control en una sola llamada.
    """

    def __init__(
        self,
        word_size: str = "64",
        positions: int = 2 ** 16
    ):
        """Inicializa la RAM.

        Args:
            word_size (str): tamaño de palabra en bits ("8", "16", "32", "64").
                             Determina la máscara de truncamiento al escribir.
            positions (int): cantidad de posiciones (celdas) disponibles.
                             Por defecto 2^16 = 65 536.
        """
        # Mapa de tamaño de palabra → máscara máxima sin signo
        word_s_info = {
            "8":  (1 << 8)  - 1,   # 0xFF
            "16": (1 << 16) - 1,   # 0xFFFF
            "32": (1 << 32) - 1,   # 0xFFFF_FFFF
            "64": (1 << 64) - 1,   # 0xFFFF_FFFF_FFFF_FFFF
        }

        self._num_pos  = positions
        self._max_uint = word_s_info.get(word_size, WORD_MASK_64)

        # Arreglo interno: lista inicializada en ceros.
        # Cada posición almacena un entero Python ,
        # se trunca a ``_max_uint`` en cada escritura.
        self._memo = [0] * positions

    # Interfaz pública, simula los tres buses
    def request(self, data: int, direction: int, control: int):
        """Acceso a la RAM mediante buses simulados.

        Args:
            data      (int): valor presente en el Bus de Datos (se usa solo
                             en operaciones de escritura).
            direction (int): dirección presente en el Bus de Direcciones.
            control   (int): señal del Bus de Control:
                             - par  (bit 0 = 0) → lectura  (MemRead)
                             - impar (bit 0 = 1) → escritura (MemWrite)

        Returns:
            int | None: el dato leído (lectura), o ``None`` (escritura).
        """
        # Protección: si la dirección excede el rango, se ajusta al último
        if direction >= self._num_pos:
            direction = self._num_pos - 1

        if (control & 1) == 0:
            # LECTURA (MemRead)
            return self._memo[direction]
        else:
            # ESCRITURA (MemWrite)
            self._memo[direction] = data & self._max_uint
