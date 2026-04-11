import json
import os


class Disk:
    """Disk emulator using JSON file storage.

    Uses nested JSON objects for folder structure:
    {"root": {"folder": {"file": "content", "subfolder": {}}, "file": "data"}}
    """

    def __init__(self, path: str = "disk.json"):
        self.path = path
        self._data: dict = {"root": {}}
        self._load()

    def _load(self):
        """Load disk image from JSON file."""
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
                if "root" not in self._data:
                    self._data = {"root": {}}
            except (json.JSONDecodeError, IOError):
                self._data = {"root": {}}
        else:
            self._data = {"root": {}}

    def _save(self):
        """Save disk image to JSON file."""
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    def _get_folder(self, path: str) -> dict:
        """Get folder dict by path."""
        if not path or path == "root":
            return self._data["root"]

        path = path.strip("/")
        parts = path.split("/")

        current = self._data["root"]
        for part in parts:
            if not part:
                continue
            if part not in current:
                raise FileNotFoundError(f"Folder '{path}' not found")
            if not isinstance(current[part], dict):
                raise NotADirectoryError(f"'{part}' is not a folder")
            current = current[part]

        return current

    def _set_folder(self, path: str, content: dict):
        """Set folder dict by path."""
        if not path or path == "root":
            self._data["root"] = content
            return

        path = path.strip("/")
        parts = path.split("/")

        current = self._data["root"]
        for part in parts[:-1]:
            if not part:
                continue
            if part not in current:
                current[part] = {}
            current = current[part]

        current[parts[-1]] = content

    def exists(self, path: str) -> bool:
        """Check if file or folder exists."""
        path = path.strip("/")
        if not path:
            return True

        parts = path.split("/")
        try:
            current = self._data["root"]
            for part in parts[:-1]:
                if part not in current:
                    return False
                current = current[part]
            return parts[-1] in current
        except (KeyError, TypeError):
            return False

    def is_folder(self, path: str) -> bool:
        """Check if path is a folder."""
        path = path.strip("/")
        if not path:
            return True

        parts = path.split("/")
        try:
            current = self._data["root"]
            for part in parts:
                if part not in current:
                    return False
                current = current[part]
            return isinstance(current, dict)
        except (KeyError, TypeError):
            return False

    def create_folder(self, path: str):
        """Create a new folder."""
        folder = self._get_folder(path)
        folder_name = path.split("/")[-1]
        if folder_name in folder and isinstance(folder[folder_name], dict):
            raise FileExistsError(f"Folder '{path}' already exists")
        folder[folder_name] = {}
        self._save()

    def delete_folder(self, path: str):
        """Delete a folder and all its contents."""
        if not path or path == "root":
            raise ValueError("Cannot delete root folder")

        parent_path, folder_name = path.rsplit("/", 1)
        parent = self._get_folder(parent_path) if parent_path else self._data["root"]

        if folder_name not in parent:
            raise FileNotFoundError(f"Folder '{path}' not found")

        del parent[folder_name]
        self._save()

    def list_folder(self, path: str = "") -> list[str]:
        """List contents of a folder."""
        folder = self._get_folder(path)
        return list(folder.keys())

    def read_file(self, path: str) -> str:
        """Read file contents."""
        path = path.strip("/")
        if not path:
            raise ValueError("Cannot read root folder")

        parts = path.split("/")
        parent_path = "/".join(parts[:-1])
        filename = parts[-1]

        folder = self._get_folder(parent_path)

        if filename not in folder:
            raise FileNotFoundError(f"File '{path}' not found")

        if isinstance(folder[filename], dict):
            raise IsADirectoryError(f"'{path}' is a folder")

        return folder[filename]

    def write_file(self, path: str, content: str):
        """Write content to file (creates or overwrites). Creates intermediate folders."""
        path = path.strip("/")
        if not path:
            raise ValueError("Filename cannot be empty")
        
        parts = path.split("/")
        
        folder = self._data["root"]
        for part in parts[:-1]:
            if part not in folder:
                folder[part] = {}
            elif not isinstance(folder[part], dict):
                folder[part] = {}
            folder = folder[part]
        
        filename = parts[-1]
        folder[filename] = content
        self._save()

    def delete_file(self, path: str):
        """Delete a file."""
        path = path.strip("/")
        parts = path.split("/")
        parent_path = "/".join(parts[:-1])
        filename = parts[-1]

        folder = self._get_folder(parent_path)

        if filename not in folder:
            raise FileNotFoundError(f"File '{path}' not found")

        if isinstance(folder[filename], dict):
            raise IsADirectoryError(f"'{path}' is a folder, use delete_folder()")

        del folder[filename]
        self._save()

    def format(self):
        """Format disk (delete all contents)."""
        self._data = {"root": {}}
        self._save()


class DiskDevice:
    """Disk device interface for CPU interaction."""

    STATUS_OK = 0x00
    STATUS_NOT_FOUND = 0x01
    STATUS_ERROR = 0x02

    def __init__(self, disk: Disk):
        self.disk = disk
        self._current_sector = 0
        self._last_error = None

    def set_sector(self, sector: int):
        """Set current sector (simulated)."""
        self._current_sector = sector

    def read_sector(self) -> str:
        """Read sector as string."""
        try:
            files = self.disk.list_folder()
            if self._current_sector < len(files):
                filename = files[self._current_sector]
                return self.disk.read_file(f"root/{filename}")
            return ""
        except Exception as e:
            self._last_error = str(e)
            return ""

    def write_sector(self, data: str):
        """Write sector data."""
        try:
            files = self.disk.list_folder()
            if self._current_sector < len(files):
                filename = files[self._current_sector]
                self.disk.write_file(f"root/{filename}", data)
            self._last_error = None
        except Exception as e:
            self._last_error = str(e)

    def format(self):
        """Format disk."""
        self.disk.format()

    @property
    def last_error(self) -> str | None:
        return self._last_error
