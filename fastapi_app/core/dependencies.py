from fastapi import Request
from storage import user_repo


def load_logged_in_user(request: Request):
    user_id = request.session.get('user_id')
    if user_id is None:
        return None

    return user_repo.get_by_id(user_id)
