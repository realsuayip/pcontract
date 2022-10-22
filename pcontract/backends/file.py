import pickle
from pathlib import Path
from typing import Literal, TypeVar

from pcontract.backends.base import Backend
from pcontract.serialization import from_json, to_json

T = TypeVar("T", bound="FileBackend")


class FileBackend(Backend):
    def __init__(
        self,
        filename: str | Path | None = None,
        method: Literal["json", "pickle"] = "json",
    ) -> None:
        super().__init__()

        if isinstance(filename, str):
            filename = Path(filename)

        self._filename: str | Path | None = filename
        self._method = method

    def init(self, *args, **kwargs) -> None:
        super().init(*args, **kwargs)
        self._filename = self._contract.uuid

    def __enter__(self: T) -> T:
        if self._filename is not None:
            if self._method == "json":
                with open(self._filename, "r") as f:
                    self._contract = from_json(f.read())
            else:
                with open(self._filename, "rb") as f:
                    self._contract = pickle.load(f)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        contract = self._contract
        if contract is None:
            return

        assert self._filename
        mode: str = "w" if self._method == "json" else "wb"

        with open(self._filename, mode) as f:
            if self._method == "json":
                f.write(to_json(contract))
            else:
                pickle.dump(contract, f)


def file(
    filename: str | Path | None = None,
    method: Literal["json", "pickle"] = "json",
) -> FileBackend:
    return FileBackend(filename, method=method)
