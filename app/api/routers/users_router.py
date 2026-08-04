from fastapi import APIRouter, Depends

from Authentication.Auth import get_current_user, get_admin_user
import Users.interface as users

user_router = APIRouter(prefix="/users", tags=["Users"])

@user_router.get("/me")
async def me(current_user: dict = Depends(get_current_user)):
    return users.get_current_user_info(current_user)

@user_router.get("/{user_id}")
async def get_user(user_id: str, current_user: dict = Depends(get_current_user)):
    return users.get_user_by_id(user_id, current_user)

@user_router.put("/{user_id}")
async def update_user(
    user_id: str,
    username: str | None = None,
    email: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    enabled: bool | None = None,
    current_user: dict = Depends(get_current_user),
):
    return users.update_user(
        user_id,
        current_user,
        username,
        email,
        first_name,
        last_name,
        enabled,
    )

@user_router.delete("/{user_id}")
async def delete_user(user_id: str, admin: dict = Depends(get_admin_user)):
    return users.delete_user_by_id(user_id, admin)

@user_router.post("/")
async def create_user(
    username: str,
    password: str,
    email: str = "",
    first_name: str = "",
    last_name: str = "",
    admin: dict = Depends(get_admin_user),
):
    return users.create_new_user(
        username,
        password,
        email,
        first_name,
        last_name,
        admin,
    )

@user_router.post("/{user_id}/admin")
async def assign_admin(user_id: str, admin: dict = Depends(get_admin_user)):
    return users.assign_admin_role(user_id, admin)

@user_router.delete("/{user_id}/admin")
async def remove_admin(user_id: str, admin: dict = Depends(get_admin_user)):
    return users.remove_admin_role(user_id, admin)

@user_router.get("/")
async def list_users(admin: dict = Depends(get_admin_user)):
    return users.list_all_users(admin)

@user_router.post("/sync")
async def sync_users(admin: dict = Depends(get_admin_user)):
    return users.sync_all_users(admin)