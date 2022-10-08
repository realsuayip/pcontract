import pickle
from pathlib import Path
from typing import TypeVar

from pcontract.data import Collection

T = TypeVar("T", bound="FileBackend")


class FileBackend:
    def __init__(self, filename: str | Path = None) -> None:
        if isinstance(filename, str):
            filename = Path(filename)

        self._filename = filename
        self._file = None
        self._collection = None

    def init(self, *args, **kwargs) -> None:
        if self._collection:
            raise ValueError("The collection is already initialized.")

        self._collection = Collection.init(*args, **kwargs)
        self._filename = self._collection.uuid
        self._dump()

    def branch(self, *args, **kwargs) -> None:
        self._collection.branch(*args, **kwargs)
        self._dump()

    def explain(self):
        return self._collection.explain()

    def gantt(self):
        return self._collection.gantt()

    def __enter__(self: T) -> T:
        if self._filename is not None:
            with open(self._filename, "rb") as f:
                self._collection = pickle.load(f)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._file is not None:
            self._file.close()

    def _dump(self):
        if self._file is None:
            self._file = open(self._filename, "wb")
        pickle.dump(self._collection, self._file)


def file(filename: str | Path = None) -> FileBackend:
    return FileBackend(filename)
