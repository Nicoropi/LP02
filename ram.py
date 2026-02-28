import numpy as np
from numpy.typing import NDArray
from typing import Literal

class RAM:
    def __init__(
        self,
        word_size: Literal["8", "16", "32", "64"] = "64",
        positions: int = 2**16
    ):
        """Object to simulate the RAM

        Args:
            word_size (str, optional): word size (Minimum ammount of bits to fetch and displace by). Defaults to "64".
            positions (int, optional): ammount of available positions. Defaults to 2**16.
        """
        
        #relate chosen word size with numpy type and maximum unsigned integer
        word_s_info = {
            "8":  (np.int8, 2**8 - 1),
            "16": (np.int16, 2**16 - 1),
            "32": (np.int32, 2**32 - 1),
            "64": (np.uint64, 2**64 - 1)
        }
        T, max_uint = word_s_info.get(word_size, np.int64)
        self._num_pos = positions
        self._max_uint = max_uint
        #The actual ram, it's initalized with zeros
        self._memo: NDArray = np.zeros(positions, dtype=T)
    
    def request(self, data: int, direction: int, control: int) -> int | None:
        """Function call for writing/accessing data in the RAM

        Args:
            data (int): Current value in data bus, used in case of writing
            direction (int): Current value in direction bus, direction in which to operate
            control (int): Current value in control bus, write if odd read if even

        Returns:
            int | None: Returns an int in case of a read operation, else returns None
        """
        #If a direction outside the scope of the ram is asked for return the last address
        if direction >= self._num_pos:
            direction = self._num_pos - 1
        if (control & 1) == 0: #read operation
            return self._memo[direction]
        else: #write operation
            self._memo[direction] = data & (self._max_uint)
