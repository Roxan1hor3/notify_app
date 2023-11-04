from typing import Any

from backend.src.notify.adapters.models.user import UserFilter


class UserQueryStorage:
    @staticmethod
    def get_match_dict(user_filter: UserFilter) -> dict[str, Any]:
        match_params = {}
        if user_filter.session_uuid is not None:
            match_params["session_uuid"] = user_filter.session_uuid
        if user_filter.username is not None:
            match_params["user_name"] = user_filter.username
        if user_filter.expire_time_lt is not None:
            match_params["expire_time"] = {"$lt": user_filter.expire_time_lt}
        return match_params
