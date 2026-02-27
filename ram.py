import numpy as np
from numpy.typing import NDArray
from typing import Literal

class RAM:
    def __init__(
        self,
        word_size: Literal["8", "16", "32", "64"] = "64",
        positions: int = 2**16
    ):
        word_s_info = {
            "8":  (np.int8, 2**8 - 1),
            "16": (np.int16, 2**16 - 1),
            "32": (np.int32, 2**32 - 1),
            "64": (np.int64, 2**64 - 1)
        }
        T, max_uint = word_s_info.get(word_size, np.int64)
        self._num_pos = positions
        self._max_uint = max_uint
        self._memo: NDArray = np.zeros(positions, dtype=T)
    
    def request(self, data: int, direction: int, control: int) -> int | None:
        if direction >= self._num_pos:
            direction = self._num_pos - 1
        if (control & 1) == 0:
            return self._memo[direction]
        else:
            self._memo[direction] = data & (self._max_uint)
