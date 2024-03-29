from __future__ import annotations

import typing
import uuid
import warnings
import zoneinfo
from datetime import datetime, timedelta
from typing import Any, Type, cast

__version__ = "1.0.0"
__all__ = ["Branch", "Contract"]

zero = timedelta()
utc = zoneinfo.ZoneInfo("UTC")


def is_aware(dt: datetime, /) -> bool:
    return dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None


def validate_tz(
    start_at: datetime, end_at: datetime | None = None, /
) -> tuple[datetime, datetime | None]:
    if not is_aware(start_at):
        warnings.warn(
            "Received naive datetime for start_at, assuming UTC.",
            stacklevel=3,
        )
        start_at = start_at.replace(tzinfo=utc)

    if end_at and not is_aware(end_at):
        warnings.warn(
            "Received naive datetime for end_at, assuming UTC.",
            stacklevel=3,
        )
        end_at = end_at.replace(tzinfo=utc)

    return start_at, end_at


class Branch:
    def __init__(
        self,
        *,
        data: dict[str, Any] | None = None,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> None:
        now: datetime = datetime.now(tz=utc)
        self.start_at: datetime = start_at or now
        self.end_at: datetime | None = end_at

        self.start_at, self.end_at = validate_tz(self.start_at, self.end_at)
        self.created_at: datetime = now
        self.updated_at: datetime = now
        self.replaced_by: list[str] = []

        self.uuid: str = uuid.uuid4().hex
        self.data: dict[str, Any] = data or {}

    def __repr__(self) -> str:
        return (
            "<%s %s start_at=%-26s end_at=%-26s span=%-26s data=%s"
            " replaced_by=%s>"
            % (
                self.__class__.__name__,
                self.uuid[-8:],
                self.start_at,
                self.end_at,
                self.span,
                self.data,
                [uid[-8:] for uid in self.replaced_by],
            )
        )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Branch):
            return NotImplemented
        return self.uuid == other.uuid

    @property
    def span(self) -> timedelta:
        assert isinstance(self.end_at, datetime)
        return self.end_at - self.start_at


class Contract:
    def __init__(
        self,
        *,
        items: list[Branch],
        meta: dict[str, Any] | None = None,
        klass: Type[Branch] = Branch,
    ) -> None:
        self.items: list[Branch] = items
        self.klass: Type[Branch] = klass
        self.uuid: str = uuid.uuid4().hex
        self.meta: dict[str, Any] = meta or {}
        self.created_at = datetime.now(tz=utc)

    def __repr__(self) -> str:
        return "<%s %s>" % (self.__class__.__name__, repr(self.items))

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, item: int) -> Branch:
        return self.items[item]

    @classmethod
    def init(
        cls,
        *,
        start_at: datetime | None = None,
        end_at: datetime,
        data: dict[str, Any],
        meta: dict[str, Any] | None = None,
    ) -> Contract:
        initial_branch = Branch(start_at=start_at, end_at=end_at, data=data)
        if (not initial_branch.span) or (zero > initial_branch.span):
            raise ValueError("%s spans nothing." % initial_branch)
        return cls(items=[initial_branch], meta=meta)

    def branch(
        self,
        data: dict[str, Any],
        *,
        start_at: datetime,
        end_at: datetime | None = None,
    ) -> Branch:
        start_at, end_at = validate_tz(start_at, end_at)
        items: list[Branch] = [item for item in self.items if not item.replaced_by]

        max_end: datetime = max(cast(datetime, item.end_at) for item in items)
        min_start: datetime = min(item.start_at for item in items)

        if (start_at > max_end) or (start_at < min_start):
            raise ValueError(
                "Given start date (%s) is out of the boundary, the "
                "valid boundary is between %s and %s (inclusively)."
                % (start_at, min_start, max_end)
            )

        end_at = end_at or max_end
        branch = self.klass(data=data, start_at=start_at, end_at=end_at)

        if (not branch.span) or (zero > branch.span):
            raise ValueError("%s spans nothing." % branch)

        for item in items:
            assert item.start_at is not None
            assert item.end_at is not None

            latest_start = max(item.start_at, start_at)
            earliest_end = min(item.end_at, end_at)
            delta = earliest_end - latest_start
            overlap = max(zero, delta)
            is_extension = (not overlap) and (start_at == item.end_at)

            if not (overlap or is_extension):
                continue

            ldelta = max(zero, start_at - item.start_at)
            rdelta = max(zero, item.end_at - end_at)
            dataref = None

            if ldelta and ldelta != item.span:
                dataref = self._resolve_data_ref(item)
                left = self.klass(
                    start_at=item.start_at,
                    end_at=item.start_at + ldelta,
                    data=dataref,
                )
                self._shift(item, left)

            self._shift(item, branch, replace=not is_extension)

            if rdelta:
                if dataref is None:
                    dataref = self._resolve_data_ref(item)

                right = self.klass(
                    start_at=end_at,
                    end_at=item.end_at,
                    data=dataref,
                )
                self._shift(item, right)
        return branch

    def _shift(self, old: Branch, new: Branch, /, *, replace: bool = True) -> None:
        if not self.contains(new):
            self.items.append(new)

        if replace:
            old.replaced_by.append(new.uuid)

    def _resolve_data_ref(self, item: Branch) -> dict[str, Any]:
        if "_ref" in item.data:
            ref = item.data["_ref"]
            branch = next(b for b in self.items if b.uuid == ref)
            return self._resolve_data_ref(branch)
        return {"_ref": item.uuid}

    def contains(self, branch: Branch) -> bool:
        for item in self.items:
            if item.uuid == branch.uuid:
                return True
        return False

    def explain(self) -> None:
        span = timedelta()

        print("\tAll branches:")
        for item in self.items:
            if not item.replaced_by:
                span += item.span
            print(item)

        print("\tActive branches:")
        for aitem in self.items:
            if not aitem.replaced_by:
                print(aitem)

        print("span=%s,count=%s" % (span, len(self.items)))

    def get_branch(self, *, at: datetime) -> Branch | None:
        at, _ = validate_tz(at)
        candidates = [
            b
            for b in self.items
            if not b.replaced_by and b.start_at <= at < cast(datetime, b.end_at)
        ]

        if not candidates:
            return None

        (branch,) = candidates
        return branch

    @typing.no_type_check
    def gantt(self) -> None:
        import matplotlib.dates
        import matplotlib.pyplot as plt
        import pandas as pd

        matplotlib.use("TkAgg")

        df_list = [
            {
                "uuid": item.uuid[-8:],
                "start_at": item.start_at,
                "end_at": item.end_at,
                "color": "#f53214" if bool(item.replaced_by) else "#05bbed",
                "span": item.span,
            }
            for item in self.items
        ]
        df = pd.DataFrame.from_records(df_list)

        fig, ax = plt.subplots(1, figsize=(16, 16), dpi=80)
        ax.xaxis.set_minor_locator(matplotlib.dates.DayLocator(interval=1))
        ax.xaxis.set_major_locator(matplotlib.dates.DayLocator(interval=30))
        ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%Y-%m-%d"))
        plt.xticks(rotation=90)
        plt.hlines(
            df.uuid,
            df.start_at,
            df.end_at,
            colors=df.color,
            linewidth=100,
            label=df.color,
        )

        for item in df_list:
            startx = matplotlib.dates.date2num(item["start_at"])
            endx = matplotlib.dates.date2num(item["end_at"])
            y = item["uuid"]
            ax.annotate(
                item["span"],
                (endx, y),
                xytext=(startx - 100, y),
                arrowprops={"arrowstyle": "->"},
                backgroundcolor="black",
                color="white",
            )
        plt.show()
