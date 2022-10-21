import pickle
from pathlib import Path
from typing import TypeVar

from pcontract.data import Contract

T = TypeVar("T", bound="FileBackend")


class FileBackend:
    def __init__(self, filename: str | Path = None) -> None:
        if isinstance(filename, str):
            filename = Path(filename)

        self._filename = filename
        self._file = None
        self._contract = None

    def init(self, *args, **kwargs) -> None:
        if self._contract:
            raise ValueError("The contract is already initialized.")

        self._contract = Contract.init(*args, **kwargs)
        self._filename = self._contract.uuid
        self._dump()

    def branch(self, *args, **kwargs) -> None:
        self._contract.branch(*args, **kwargs)
        self._dump()

    def explain(self):
        return self._contract.explain()

    def gantt(self):
        return self._contract.gantt()

    def __enter__(self: T) -> T:
        if self._filename is not None:
            with open(self._filename, "rb") as f:
                self._contract = pickle.load(f)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._file is not None:
            self._file.close()

    def _dump(self):
        if self._file is None:
            self._file = open(self._filename, "wb")
        pickle.dump(self._contract, self._file)


def file(filename: str | Path = None) -> FileBackend:
    return FileBackend(filename)
