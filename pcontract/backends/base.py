import typing

if typing.TYPE_CHECKING:
    from pcontract.data import Contract


class Backend:
    def __init__(self, *args, **kwargs) -> None:
        self._contract: Contract | None = None

    def init(self, *args, **kwargs) -> None:
        if self._contract is not None:
            raise ValueError(
                "You are already working on an initialized contract (%s)."
                % self._contract.uuid
            )

        from pcontract.data import Contract

        self._contract = Contract.init(*args, **kwargs)

    def branch(self, *args, **kwargs) -> None:
        assert self._contract
        self._contract.branch(*args, **kwargs)

    def explain(self) -> None:
        assert self._contract
        self._contract.explain()

    def gantt(self) -> None:
        assert self._contract
        self._contract.gantt()
