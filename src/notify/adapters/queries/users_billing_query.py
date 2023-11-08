from typing import Any

from pypika import Criterion, MySQLQuery, Table, functions
from pypika.queries import QueryBuilder

from src.notify.adapters.models.user_billing import UserBillingFilter


class UserBillingQueryStorage:
    us_trf = Table("users_trf")
    us = Table("users")
    dv = Table("dopvalues")
    pl = Table("plans2")
    grp = Table("user_grp")

    def _filter(self, _filter: UserBillingFilter) -> list[bool | Any]:
        _filters = []
        if _filter.ids is False:
            _filters.append((self.us.id.isin(_filter.ids)))
        if _filter.fio is not None:
            _filters.append((self.us.fio.like(f"{_filter.fio}%")))
        if _filter.is_auth is False:
            _filters.append((self.us.auth == "no"))
        elif _filter.is_auth is True:
            _filters.append((self.us.auth == "on"))
        if _filter.user_active is False:
            _filters.append((self.pl.name == "[1000]0."))
        elif _filter.user_active is True:
            _filters.append((self.pl.name != "[1000]0."))
        if _filter.group_ids is not None:
            _filters.append((self.grp.grp_id.isin(_filter.group_ids)))
        if _filter.packet_ids is not None:
            _filters.append((self.pl.id.isin(_filter.packet_ids)))
        if _filter.balance_gte is not None:
            _filters.append(
                (self.us.balance - self.us_trf.submoney >= _filter.balance_gte)
            )
        if _filter.balance_lte is not None:
            _filters.append(
                (self.us.balance - self.us_trf.submoney <= _filter.balance_lte)
            )
        if _filter.fee_more_than_balance is not None:
            _filters.append((self.us_trf.submoney >= self.us.balance))
        return _filters

    def get_subquery_sn_onu(self, _filter: UserBillingFilter) -> QueryBuilder:
        subquery = (
            MySQLQuery.from_(self.dv)
            .select(
                self.dv.parent_id,
                functions.Max(self.dv.time).as_("max_time"),
            )
            .where((self.dv.dopfield_id == 33))
            .groupby(self.dv.parent_id)
        )
        query = (
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
        if _filter.sn_onu_equipment_delivered is True:
            query = query.where((self.dv.field_value == ""))
        elif _filter.sn_onu_equipment_delivered is False:
            query = query.where((self.dv.field_value != ""))
        return query

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

    def get_users_count(self, _filter: UserBillingFilter):
        subquery_sn_onu = self.get_subquery_sn_onu(_filter=_filter)
        subquery_mac = self.get_subquery_mac(_filter=_filter)
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
            .inner_join(subquery_mac)
            .on(self.us.id == subquery_mac.parent_id)
            .where(Criterion.all(self._filter(_filter=_filter)))
            .distinct()
        )
        return query

    def get_users(self, _filter: UserBillingFilter, limit: int, offset: int):
        subquery_sn_onu = self.get_subquery_sn_onu(_filter=_filter)
        subquery_mac = self.get_subquery_mac(_filter=_filter)
        subquery_phone_number = self.get_subquery_phone_number()
        query = (
            MySQLQuery.from_(self.us_trf)
            .select(
                self.us.id.as_("id"),
                self.us.ip,
                self.us.passwd,
                self.us.fio,
                self.us_trf.submoney.as_("fee"),
                self.us.comment,
                (self.us.balance - self.us_trf.submoney).as_("balance"),
                self.pl.name.as_("packet_name"),
                subquery_phone_number.phone_number.as_("phone_number"),
                subquery_phone_number.max_time.as_("phone_number_time"),
                subquery_sn_onu.sn_onu.as_("sn_onu"),
                subquery_sn_onu.max_time.as_("sn_onu_time"),
                subquery_mac.mac.as_("mac"),
                subquery_mac.max_time.as_("mac_time"),
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
            .inner_join(subquery_mac)
            .on(self.us.id == subquery_mac.parent_id)
            .where(Criterion.all(self._filter(_filter=_filter)))
            .limit(limit)
            .offset(offset)
            .distinct()
        )
        return query

    def get_subquery_mac(self, _filter: UserBillingFilter) -> QueryBuilder:
        subquery = (
            MySQLQuery.from_(self.dv)
            .select(
                self.dv.parent_id,
                functions.Max(self.dv.time).as_("max_time"),
            )
            .where((self.dv.dopfield_id == 13))
            .groupby(self.dv.parent_id)
        )
        query = (
            MySQLQuery.from_(self.dv)
            .select(
                self.dv.parent_id,
                self.dv.field_value.as_("mac"),
                self.dv.time.as_("max_time"),
            )
            .inner_join(subquery)
            .on(
                (self.dv.time == subquery.max_time)
                & (self.dv.parent_id == subquery.parent_id)
            )
            .where((self.dv.dopfield_id == 13))
        )
        if _filter.mac_equipment_delivered is True:
            query = query.where((self.dv.field_value == ""))
        elif _filter.mac_equipment_delivered is False:
            query = query.where((self.dv.field_value != ""))
        return query

    def get_groups(self):
        query = MySQLQuery.from_(self.grp).select(
            self.grp.grp_id,
            self.grp.grp_name,
        )
        return query

    def get_packets(self):
        query = MySQLQuery.from_(self.pl).select(
            self.pl.id,
            self.pl.name,
        )
        return query
