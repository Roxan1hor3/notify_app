from pypika import MySQLQuery, Table, functions


class MessageBillingQueryStorage:
    us = Table("users")
    ps = Table("pays")

    def get_messages(self, created_since: float, limit: int, offset: int):
        query = (
            MySQLQuery.from_(self.ps)
            .select(
                self.ps.reason,
                self.ps.id.as_("reason_id"),
                self.ps.mid.as_("id"),
                self.ps.time,
                self.us.fio,
            )
            .inner_join(self.us)
            .on(self.ps.mid == self.us.id)
            .where(
                (self.ps.type == 30)
                & (self.ps.category == 491)
                & (self.ps.time > created_since)
            )
            .limit(limit)
            .offset(offset)
            .distinct()
        )
        return query

    def get_messages_count(self, created_since: float):
        query = (
            MySQLQuery.from_(self.ps)
            .select(functions.Count("*").as_("count"))
            .inner_join(self.us)
            .on(self.ps.mid == self.us.id)
            .where(
                (self.ps.type == 30)
                & (self.ps.category == 491)
                & (self.ps.time > created_since)
            )
            .distinct()
        )
        return query
