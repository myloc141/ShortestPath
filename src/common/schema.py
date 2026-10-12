from typing import TypedDict


class NetworkRecord(TypedDict):
    node_id: str
    edge_id: str
    u: str
    v: str
    distance: float
    date: str  # Ngày theo định dạng YYYY-MM-DD
    slot_id: int
    day_of_week: str