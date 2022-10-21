import json
import typing

from pymongo.collection import Collection

from pcontract.serialization import from_json, to_json

if typing.TYPE_CHECKING:
    from pcontract.data import Contract


class MongoBackend:
    def __init__(self, collection: Collection) -> None:
        self.collection: Collection = collection
        self._contract: Contract | None = None

    def set_contract(self, uuid: str | None) -> None:
        if uuid is None:
            self._contract = None
        else:
            collection = self.collection.find_one(
                {"uuid": uuid}, {"_id": False}
            )
            collection = json.dumps(collection)
            self._contract = from_json(collection)

    def unset(self) -> None:
        self._contract = None

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

    def commit(self) -> None:
        assert self._contract
        contract_data = json.loads(to_json(self._contract))
        self.collection.replace_one(
            {"uuid": self._contract.uuid},
            contract_data,
            upsert=True,
        )


def mongo(collection: Collection) -> MongoBackend:
    return MongoBackend(collection)
