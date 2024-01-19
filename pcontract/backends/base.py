from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from pcontract.data import Contract


class Backend:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._contract: Contract | None = None

    def init(self, *args: Any, **kwargs: Any) -> None:
        if self._contract is not None:
            raise ValueError(
                "You are already working on an initialized contract (%s)."
                % self._contract.uuid
            )

        from pcontract.data import Contract

        self._contract = Contract.init(*args, **kwargs)

    def branch(self, *args: Any, **kwargs: Any) -> None:
        assert self._contract
        self._contract.branch(*args, **kwargs)

    def explain(self) -> None:
        assert self._contract
        self._contract.explain()

    def gantt(self) -> None:
        assert self._contract
        self._contract.gantt()
