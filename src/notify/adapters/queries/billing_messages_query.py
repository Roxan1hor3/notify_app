from pypika import MySQLQuery, Table, functions


class MessageBillingQueryStorage:
    us = Table("users")
    ps = Table("pays")

    def get_messages(
        self,
        created_since_from: float,
        created_since_to: float,
        limit: int,
        offset: int,
    ):
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
                & ((self.ps.category == 491) | (self.ps.category == 492))
                & (self.ps.time > created_since_from)
                & (self.ps.time < created_since_to)
            )
            .limit(limit)
            .offset(offset)
            .distinct()
        )
        return query

    def get_messages_count(self, created_since_from: float, created_since_to: float):
        query = (
            MySQLQuery.from_(self.ps)
            .select(functions.Count("*").as_("count"))
            .inner_join(self.us)
            .on(self.ps.mid == self.us.id)
            .where(
                (self.ps.type == 30)
                & ((self.ps.category == 491) | (self.ps.category == 492))
                & (self.ps.time > created_since_from)
                & (self.ps.time < created_since_to)
            )
            .distinct()
        )
        return query
