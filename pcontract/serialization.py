import datetime
from json import JSONDecoder, JSONEncoder
from typing import Any

from pcontract.data import Branch, Contract

BRANCH_TYPE = "pcontract.branch"
CONTRACT_TYPE = "pcontract.contract"


class Encoder(JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, datetime.datetime):
            return o.isoformat()

        if isinstance(o, Branch):
            return self.decode_branch(o)

        if isinstance(o, Contract):
            return self.decode_contract(o)

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

    def decode_contract(self, contract: Contract) -> dict:  # noqa
        return {
            "type": CONTRACT_TYPE,
            "uuid": contract.uuid,
            "created_at": contract.created_at,
            "meta": contract.meta,
            "items": contract.items,
        }


def object_hook(obj: dict) -> dict | Branch | Contract:
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

    if kind == CONTRACT_TYPE:
        contract = Contract(items=obj["items"], meta=obj["meta"])
        contract.uuid = obj["uuid"]
        contract.created_at = isodate(obj["created_at"])
        return contract

    return obj


def to_json(contract: Contract) -> str:
    encoder = Encoder()
    return encoder.encode(contract)


def from_json(s: str) -> Contract:
    decoder = JSONDecoder(object_hook=object_hook)
    return decoder.decode(s)
