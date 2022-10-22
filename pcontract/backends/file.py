import pickle
import typing
from pathlib import Path
from typing import Literal, TypeVar

from pcontract.serialization import from_json, to_json

if typing.TYPE_CHECKING:
    from pcontract.data import Contract

T = TypeVar("T", bound="FileBackend")


class FileBackend:
    def __init__(
        self,
        filename: str | Path | None = None,
        method: Literal["json", "pickle"] = "json",
    ) -> None:
        if isinstance(filename, str):
            filename = Path(filename)

        self._filename: str | Path | None = filename
        self._method = method
        self._contract: Contract | None = None

    def init(self, *args, **kwargs) -> None:
        if self._contract:
            raise ValueError("The contract is already initialized.")

        from pcontract.data import Contract

        self._contract = Contract.init(*args, **kwargs)
        self._filename = self._contract.uuid

    def branch(self, *args, **kwargs) -> None:
        assert self._contract
        self._contract.branch(*args, **kwargs)

    def explain(self) -> None:
        assert self._contract
        self._contract.explain()

    def gantt(self) -> None:
        assert self._contract
        self._contract.gantt()

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
