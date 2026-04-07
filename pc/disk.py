import os


class Disk:
    """Simple disk image backed by a file.

    This is a very lightweight disk model with fixed-size sectors.
    It is intended for educational purposes and easy integration with
    a GUI-based simulator.
    """

    def __init__(
        self, path: str = "disk.img", sectors: int = 1024, sector_size: int = 512
    ):
        self.path = path
        self.sectors = sectors
        self.sector_size = sector_size
        self._ensure_disk_file()

    def _ensure_disk_file(self):
        if not os.path.exists(self.path):
            with open(self.path, "wb") as f:
                f.write(b"\x00" * (self.sectors * self.sector_size))
        else:
            # Ensure size matches expected sectors * size; if not, resize/truncate
            size = self.sectors * self.sector_size
            with open(self.path, "ab"):
                pass
            with open(self.path, "rb+") as f:
                f.seek(0, os.SEEK_END)
                current = f.tell()
                if current != size:
                    f.seek(0)
                    f.write(b"\x00" * size)

    def read_sector(self, index: int) -> bytes:
        if index < 0 or index >= self.sectors:
            raise IndexError("Sector out of bounds")
        with open(self.path, "rb") as f:
            f.seek(index * self.sector_size)
            return f.read(self.sector_size)

    def write_sector(self, index: int, data: bytes):
        if index < 0 or index >= self.sectors:
            raise IndexError("Sector out of bounds")
        if len(data) != self.sector_size:
            raise ValueError(f"Sector must be exactly {self.sector_size} bytes")
        with open(self.path, "rb+") as f:
            f.seek(index * self.sector_size)
            f.write(data)

    def format(self):
        with open(self.path, "wb") as f:
            f.write(b"\x00" * (self.sectors * self.sector_size))

    def load_from_bytes(self, data: bytes):
        # Load data into the disk from a bytes object. Data length must be <= total size
        total = self.sectors * self.sector_size
        if len(data) > total:
            raise ValueError("Data exceeds disk size")
        with open(self.path, "rb+") as f:
            f.write(data.ljust(total, b"\x00"))

    def save_to_bytes(self) -> bytes:
        with open(self.path, "rb") as f:
            return f.read()


#############################
# Lightweight, single-file PC disk extension (merged)
#############################
DISK_REGISTERS = {
    "STATUS": 0x00,
    "SECTOR": 0x04,
    "DATA": 0x08,
}


class DiskDevice:
    def __init__(self, disk: "Disk", start_sector: int = 0):
        self.disk = disk
        self._current_sector = start_sector
        self._last_error = None

    def set_sector(self, sector: int):
        self._current_sector = sector

    def read_sector(self) -> bytes:
        try:
            return self.disk.read_sector(self._current_sector)
        except Exception as e:
            self._last_error = str(e)
            raise

    def write_sector(self, data: bytes):
        if len(data) != self.disk.sector_size:
            raise ValueError("Data length does not match sector size")
        self.disk.write_sector(self._current_sector, data)
        self._last_error = None

    def format(self):
        self.disk.format()

    @property
    def last_error(self) -> str:
        return self._last_error
