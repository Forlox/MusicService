from typing import Optional
from fastapi import HTTPException
from Users.UserManager import UserManager
import logging

logger = logging.getLogger(__name__)

user_manager = UserManager()

def get_current_user_info(current_user: dict) -> dict:
    try:
        return user_manager.get_user(current_user["sub"])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения данных пользователя {current_user.get('sub')}: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting user info: {str(e)}")


def update_user(user_id: str, current_user: dict,
                username: Optional[str] = None,
                email: Optional[str] = None,
                first_name: Optional[str] = None,
                last_name: Optional[str] = None,
                enabled: Optional[bool] = None) -> dict:
    """
    Обновляет данные пользователя. Если текущий пользователь не админ,
    он может обновлять только свой профиль (user_id должен совпадать с sub).
    """
    # Проверка прав
    if current_user.get("sub") != user_id:
        roles = current_user.get("realm_access", {}).get("roles", [])
        if "admin" not in roles:
            raise HTTPException(status_code=403, detail="Not enough permissions to update this user")

    # Собираем обновления
    updates = {}
    if username is not None:
        updates["username"] = username
    if email is not None:
        updates["email"] = email
    if first_name is not None:
        updates["firstName"] = first_name
    if last_name is not None:
        updates["lastName"] = last_name
    if enabled is not None:
        updates["enabled"] = enabled

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    try:
        return user_manager.update_user(user_id, **updates)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")

def set_active(keycloak_id: str, current_user: dict, active: bool):
    return update_user(keycloak_id, current_user, enabled=active)

def delete_user_by_id(user_id: str, current_user: dict) -> dict:
    roles = current_user.get("realm_access", {}).get("roles", [])
    if "admin" not in roles:
        raise HTTPException(status_code=403, detail="Admin role required")
    try:
        user_manager.delete_user(user_id)
        logger.info(f"Пользователь {user_id} удален администратором {current_user.get('sub')}")
        return {"status": "deleted", "user_id": user_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка удаления пользователя {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")


def get_user_by_id(user_id: str, current_user: dict) -> dict:
    """
    Возвращает данные пользователя по ID.
    Доступно самому пользователю или администратору.
    """
    if current_user.get("sub") != user_id:
        roles = current_user.get("realm_access", {}).get("roles", [])
        if "admin" not in roles:
            raise HTTPException(status_code=403, detail="Not enough permissions to view this user")

    try:
        return user_manager.get_user(user_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user: {str(e)}")


# - Операции для админов -
def create_new_user(username: str, password: str,
                    email: str = "", first_name: str = "", last_name: str = "",
                    admin_user: dict = None) -> dict:
    """
    Создаёт нового пользователя. Доступно только администраторам.
    Параметр admin_user передаётся из зависимости get_admin_user для проверки прав.
    """
    try:
        return user_manager.create_user(username, password, email, first_name, last_name)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка создания пользователя {username}: {e}")
        raise HTTPException(status_code=500, detail=f"User creation failed: {str(e)}")

def is_admin(user_id: str) -> bool:
    return user_manager.is_admin(user_id)

def assign_admin_role(user_id: str, admin_user: dict) -> dict:
    """Назначает пользователю роль admin"""
    try:
        if not is_admin(user_id):
            user_manager.assign_admin_role(user_id)
            return {"status": "admin assigned", "user_id": user_id}
        else: return {"status": "user is already an admin", "user_id": user_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Не удалось назначить роль admin пользователю {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to assign admin role: {str(e)}")

def remove_admin_role(user_id: str, admin_user: dict) -> dict:
    """Убирает у пользователя роль admin"""
    try:
        if is_admin(user_id):
            user_manager.remove_admin_role(user_id)
            return {"status": "admin removed", "user_id": user_id}
        else: return {"status": "user is already not admin", "user_id": user_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Не удалось снять роль admin у пользователя {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to remove admin role: {str(e)}")

def list_all_users(admin_user: dict) -> list:
    try:
        return user_manager.get_all_users()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get users list: {str(e)}")

def sync_all_users(admin_user: dict) -> dict:
    """Синхронизация локальной БД с Keycloak"""
    try:
        return user_manager.sync_all_users()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

def list_realm_roles(admin_user: dict) -> list:
    try:
        return user_manager.list_realm_roles()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get roles: {str(e)}")

def assign_realm_role(user_id: str, role: str, admin_user: dict) -> dict:
    try:
        status = user_manager.assign_role(user_id, role)
        return {"user_id": user_id, "role": role, "status": status}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to assign role: {str(e)}")

def remove_realm_role(user_id: str, role: str, admin_user: dict) -> dict:
    try:
        status = user_manager.remove_role(user_id, role)
        return {"user_id": user_id, "role": role, "status": status}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove role: {str(e)}")