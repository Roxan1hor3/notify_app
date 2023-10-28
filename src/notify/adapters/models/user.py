from pydantic import BaseModel


class User(BaseModel):
    id: int
    ip: str
    name: str
    passwd: str
    grp: int
    mid: int
    contract: str
    contract_date: int
    state: str
    auth: str
    balance: float
    money: float
    limit_balance: float
    block_if_limit: int
    sortip: int
    modify_time: int
    fio: str
    srvs: int
    paket: int
    next_paket: int
    paket3: int
    next_paket3: int
    start_day: int
    discount: int
    hops: int
    cstate: int
    cstate_time: int
    comment: str
    lstate: int
    detail_traf: int
