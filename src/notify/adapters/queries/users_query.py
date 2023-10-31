from pprint import pprint

from pypika import MySQLQuery, Table, functions
from pypika.queries import QueryBuilder

from src.notify.adapters.models.user import UserFilter


class UserQueryStorage:
    us_trf = Table("users_trf")
    us = Table("users")
    dv = Table("dopvalues")
    pl = Table("plans2")
    grp = Table("user_grp")

    def _filter_and(self, _filter: UserFilter) -> bool:
        if _filter.user_active:
            _filter_query = self.pl.name == "[1000]0."
        if _filter.group_ids:
            _filter_query = _filter_query & self.grp.grp_id.isin(_filter.group_ids)
        if _filter.balance_gte:
            _filter_query = _filter_query & (self.us.balance >= _filter.balance_gte)
        if _filter.balance_lte:
            _filter_query = _filter_query & (self.us.balance <= _filter.balance_lte)
        if _filter.fee_more_than_balance:
            _filter_query = _filter_query & (self.us_trf.submoney >= self.us.balance)
        return _filter_query

    def get_subquery_sn_onu(self) -> QueryBuilder:
        subquery = (
            MySQLQuery.from_(self.dv)
            .select(
                self.dv.parent_id,
                functions.Max(self.dv.time).as_("max_time"),
            )
            .where((self.dv.dopfield_id == 33))
            .groupby(self.dv.parent_id)
        )
        return (
            MySQLQuery.from_(self.dv)
            .select(
                self.dv.parent_id,
                self.dv.field_value.as_("sn_onu"),
                self.dv.time.as_("max_time"),
            )
            .inner_join(subquery)
            .on(
                (self.dv.time == subquery.max_time)
                & (self.dv.parent_id == subquery.parent_id)
            )
            .where((self.dv.dopfield_id == 33))
        )

    def get_subquery_phone_number(self) -> QueryBuilder:
        subquery = (
            MySQLQuery.from_(self.dv)
            .select(
                self.dv.parent_id,
                functions.Max(self.dv.time).as_("max_time"),
            )
            .where((self.dv.dopfield_id == 8))
            .groupby(self.dv.parent_id)
        )
        return (
            MySQLQuery.from_(self.dv)
            .select(
                self.dv.parent_id,
                self.dv.field_value.as_("phone_number"),
                self.dv.time.as_("max_time"),
            )
            .inner_join(subquery)
            .on(
                (self.dv.time == subquery.max_time)
                & (self.dv.parent_id == subquery.parent_id)
            )
            .where((self.dv.dopfield_id == 8))
        )

    def get_users_count(self, _filter: UserFilter):
        subquery_sn_onu = self.get_subquery_sn_onu()
        subquery_phone_number = self.get_subquery_phone_number()
        query = (
            MySQLQuery.from_(self.us_trf)
            .select(functions.Count("*").as_("count"))
            .inner_join(self.us)
            .on(self.us_trf.uid == self.us.id)
            .inner_join(self.pl)
            .on(self.us_trf.packet == self.pl.id)
            .inner_join(self.grp)
            .on(self.us.grp == self.grp.grp_id)
            .inner_join(subquery_sn_onu)
            .on(self.us.id == subquery_sn_onu.parent_id)
            .inner_join(subquery_phone_number)
            .on(self.us.id == subquery_phone_number.parent_id)
            .distinct()
            # .where(self._filter_and(_filter=_filter))
        )
        return query

    def get_users(self, _filter: UserFilter, limit: int, offset: int, ordering: str):
        subquery_sn_onu = self.get_subquery_sn_onu()
        subquery_phone_number = self.get_subquery_phone_number()
        query = (
            MySQLQuery.from_(self.us_trf)
            .select(
                self.us.id.as_("id"),
                self.us.ip,
                self.us.fio,
                self.us_trf.submoney.as_("fee"),
                self.us.comment,
                self.us_trf.startmoney.as_("balance"),
                self.pl.name.as_("packet_name"),
                subquery_phone_number.phone_number.as_("phone_number"),
                subquery_phone_number.max_time.as_("phone_number_time"),
                subquery_sn_onu.sn_onu.as_("sn_onu"),
                subquery_sn_onu.max_time.as_("sn_onu_time"),
                self.grp.grp_name,
                self.us.grp.as_("grp_id"),
            )
            .inner_join(self.us)
            .on(self.us_trf.uid == self.us.id)
            .inner_join(self.pl)
            .on(self.us_trf.packet == self.pl.id)
            .inner_join(self.grp)
            .on(self.us.grp == self.grp.grp_id)
            .inner_join(subquery_sn_onu)
            .on(self.us.id == subquery_sn_onu.parent_id)
            .inner_join(subquery_phone_number)
            .on(self.us.id == subquery_phone_number.parent_id)
            # .where(self._filter_and(_filter=_filter))
            .limit(limit)
            .offset(offset)
            .distinct()
            # .orderby(subquery_phone_number.max_time.as_("phone_number_time"), order=Order.desc)
            # .orderby(subquery_phone_number.max_time.as_("sn_onu_time"), order=Order.desc)
            # .order_by(self.get_ordering(ordering=ordering))
        )
        return query

    def get_ordering(self, ordering: str):
        if ordering == "id":
            return self.us.id
        elif ordering == "-id":
            return self.us.id.desc()
        return self.us.id
