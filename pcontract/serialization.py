import datetime
from json import JSONDecoder, JSONEncoder
from typing import Any

from pcontract.data import Branch, Collection

BRANCH_TYPE = "pcontract.branch"
COLLECTION_TYPE = "pcontract.collection"


class Encoder(JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, datetime.datetime):
            return o.isoformat()

        if isinstance(o, Branch):
            return self.decode_branch(o)

        if isinstance(o, Collection):
            return self.decode_collection(o)

    def decode_branch(self, branch: Branch) -> dict:  # noqa
        return {
            "type": BRANCH_TYPE,
            "uuid": branch.uuid,
            "start_at": branch.start_at,
            "end_at": branch.end_at,
            "created_at": branch.created_at,
            "replaced_by": branch.replaced_by,
            "data": branch.data,
        }

    def decode_collection(self, collection: Collection) -> dict:  # noqa
        return {
            "type": COLLECTION_TYPE,
            "uuid": collection.uuid,
            "created_at": collection.created_at,
            "meta": collection.meta,
            "items": collection.items,
        }


def object_hook(obj: dict) -> dict | Branch | Collection:
    kind = obj.get("type")
    isodate = datetime.datetime.fromisoformat

    if kind == BRANCH_TYPE:
        branch = Branch(
            data=obj["data"],
            start_at=isodate(obj["start_at"]),
            end_at=isodate(obj["end_at"]),
        )
        branch.created_at = isodate(obj["created_at"])
        branch.uuid = obj["uuid"]
        branch.replaced_by = obj["replaced_by"]
        return branch

    if kind == COLLECTION_TYPE:
        collection = Collection(items=obj["items"], meta=obj["meta"])
        collection.uuid = obj["uuid"]
        collection.created_at = isodate(obj["created_at"])
        return collection

    return obj


def to_json(collection: Collection) -> str:
    encoder = Encoder()
    return encoder.encode(collection)


def from_json(s: str) -> Collection:
    decoder = JSONDecoder(object_hook=object_hook)
    return decoder.decode(s)
