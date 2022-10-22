import json

from pymongo.collection import Collection

from pcontract.backends.base import Backend
from pcontract.serialization import from_json, to_json


class MongoBackend(Backend):
    def __init__(self, collection: Collection) -> None:
        super().__init__()
        self.collection: Collection = collection

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
