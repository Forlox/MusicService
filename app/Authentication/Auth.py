# TODO ниже все - вайбкод. Надо все понять и править :)

import os
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from keycloak import KeycloakAdmin, KeycloakOpenID
from keycloak.exceptions import KeycloakAuthenticationError, KeycloakGetError

# --- Конфигурация ---

# Настройки Keycloak загружаются из переменных окружения
KEYCLOAK_SERVER_URL = os.getenv("KEYCLOAK_SERVER_URL", "http://localhost:8080/")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "master")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "admin-cli")
KEYCLOAK_CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET", None)

# --- Инициализация клиентов ---

# Клиент для OpenID Connect (аутентификация пользователей)
keycloak_openid = KeycloakOpenID(
    server_url=KEYCLOAK_SERVER_URL,
    client_id=KEYCLOAK_CLIENT_ID,
    realm_name=KEYCLOAK_REALM,
    client_secret_key=KEYCLOAK_CLIENT_SECRET,  # может быть None для public клиентов
)

# Клиент для Admin API (административные задачи)
# Требует учетных данных администратора
keycloak_admin = KeycloakAdmin(
    server_url=KEYCLOAK_SERVER_URL,
    username=os.getenv("KEYCLOAK_ADMIN_USERNAME"),
    password=os.getenv("KEYCLOAK_ADMIN_PASSWORD"),
    realm_name=KEYCLOAK_REALM,
    client_id=KEYCLOAK_CLIENT_ID,
    client_secret_key=KEYCLOAK_CLIENT_SECRET,
    verify=True,
)

# --- Вспомогательные зависимости FastAPI ---

security = HTTPBasic()


async def get_current_user(
    credentials: HTTPBasicCredentials = Depends(security),
) -> dict:
    """
    Dependency для FastAPI. Аутентифицирует пользователя по логину и паролю.
    Возвращает словарь с данными пользователя (access_token, refresh_token, userinfo).
    """
    try:
        # 1. Получаем токены по логину и паролю (Resource Owner Password Flow)[reference:0][reference:1]
        token = keycloak_openid.token(
            username=credentials.username,
            password=credentials.password,
        )

        # 2. Получаем информацию о пользователе по access_token[reference:2]
        userinfo = keycloak_openid.userinfo(token["access_token"])

        # 3. Возвращаем данные пользователя вместе с токенами
        return {
            "access_token": token["access_token"],
            "refresh_token": token["refresh_token"],
            "userinfo": userinfo,
        }

    except KeycloakAuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}",
        )


async def get_admin_user(
    credentials: HTTPBasicCredentials = Depends(security),
) -> dict:
    """
    Dependency для FastAPI. Аутентифицирует администратора.
    Использует те же механизмы, что и get_current_user, но с дополнительной
    проверкой роли администратора.
    """
    user_data = await get_current_user(credentials)

    # Проверяем, есть ли у пользователя роль администратора
    # (название роли может отличаться в вашем Keycloak)
    roles = user_data["userinfo"].get("realm_access", {}).get("roles", [])
    if "admin" not in roles and "offline_access" not in roles:  # пример проверки
        # Более надежная проверка: запросить пользователя через Admin API
        try:
            # Ищем пользователя по username через Admin API
            users = keycloak_admin.get_users(
                {"username": credentials.username, "exact": True}
            )
            if not users:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin user not found",
                )
            user_id = users[0]["id"]
            # Получаем роли пользователя через Admin API
            user_roles = keycloak_admin.get_realm_roles_of_user(user_id)
            role_names = [role["name"] for role in user_roles]
            if "admin" not in role_names:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions. Admin role required.",
                )
        except KeycloakGetError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error checking admin role: {str(e)}",
            )

    return user_data


# --- Административные методы ---

def create_user(username: str, email: str, password: str, first_name: str = "", last_name: str = ""):
    """
    Создает нового пользователя в Keycloak.[reference:3]
    """
    try:
        new_user = keycloak_admin.create_user(
            {
                "username": username,
                "email": email,
                "enabled": True,
                "firstName": first_name,
                "lastName": last_name,
            },
            exist_ok=False,
        )
        # Устанавливаем пароль пользователю
        keycloak_admin.set_user_password(
            user_id=new_user["id"],
            password=password,
            temporary=False,
        )
        return new_user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create user: {str(e)}",
        )


def get_user_by_username(username: str) -> Optional[dict]:
    """
    Получает пользователя по имени пользователя через Admin API.
    """
    try:
        users = keycloak_admin.get_users({"username": username, "exact": True})
        return users[0] if users else None
    except KeycloakGetError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user: {str(e)}",
        )


def update_user(user_id: str, user_data: dict):
    """
    Обновляет данные пользователя.
    """
    try:
        keycloak_admin.update_user(user_id=user_id, payload=user_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update user: {str(e)}",
        )


def delete_user(user_id: str):
    """
    Удаляет пользователя по ID.
    """
    try:
        keycloak_admin.delete_user(user_id=user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete user: {str(e)}",
        )


def get_all_users() -> list:
    """
    Возвращает список всех пользователей в реалме.
    """
    try:
        return keycloak_admin.get_users()
    except KeycloakGetError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get users list: {str(e)}",
        )


def assign_admin_role(user_id: str):
    """
    Назначает пользователю роль администратора в текущем реалме.
    """
    try:
        # Получаем все роли реалма
        realm_roles = keycloak_admin.get_realm_roles()
        admin_role = next((r for r in realm_roles if r["name"] == "admin"), None)
        if not admin_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin role not found in realm",
            )
        # Назначаем роль пользователю
        keycloak_admin.assign_realm_roles(
            user_id=user_id,
            roles=[admin_role],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to assign admin role: {str(e)}",
        )


