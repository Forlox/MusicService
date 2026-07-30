import os
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, HTTPBasic, HTTPBasicCredentials
from keycloak import KeycloakAdmin, KeycloakOpenID
from keycloak.exceptions import KeycloakAuthenticationError, KeycloakGetError

# -------------------------------------------------------------------
# Конфигурация из переменных окружения
# -------------------------------------------------------------------
KEYCLOAK_SERVER_URL = os.getenv("KEYCLOAK_SERVER_URL", "http://localhost:8080/")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "master")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "admin-cli")
KEYCLOAK_CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET", None)

# -------------------------------------------------------------------
# Клиенты Keycloak
# -------------------------------------------------------------------
keycloak_openid = KeycloakOpenID(
    server_url=KEYCLOAK_SERVER_URL,
    client_id=KEYCLOAK_CLIENT_ID,
    realm_name=KEYCLOAK_REALM,
    client_secret_key=KEYCLOAK_CLIENT_SECRET,
)

keycloak_admin = KeycloakAdmin(
    server_url=KEYCLOAK_SERVER_URL,
    username=os.getenv("KEYCLOAK_ADMIN_USERNAME"),
    password=os.getenv("KEYCLOAK_ADMIN_PASSWORD"),
    realm_name=KEYCLOAK_REALM,
    client_id=KEYCLOAK_CLIENT_ID,
    client_secret_key=KEYCLOAK_CLIENT_SECRET,
    verify=True,
)

# -------------------------------------------------------------------
# Схемы извлечения учётных данных
# -------------------------------------------------------------------
bearer_scheme = HTTPBearer()          # Authorization: Bearer <token>
basic_scheme = HTTPBasic()            # Authorization: Basic <base64>

# -------------------------------------------------------------------
# Зависимости FastAPI (без лишних запросов к Keycloak)
# -------------------------------------------------------------------

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    token = credentials.credentials
    try:
        # decode_token() автоматически проверяет подпись, issuer, expiration
        decoded = keycloak_openid.decode_token(token)
        return dict(decoded)
    except KeycloakAuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}",
        )


async def get_current_user_from_basic(
    credentials: HTTPBasicCredentials = Depends(basic_scheme),
) -> dict:
    """
    Аутентификация по логину/паролю (HTTP Basic).
    Получает токен и возвращает его claims через decode_token (без userinfo).
    """
    try:
        token = keycloak_openid.token(
            username=credentials.username,
            password=credentials.password,
            scope="openid",           # ← обязательно добавляем openid, чтобы работало и с userinfo при желании
        )
        return keycloak_openid.decode_token(token["access_token"])
    except KeycloakAuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Basic"},
        )


async def get_admin_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """
    Только для администраторов. Проверяет токен и наличие роли 'admin'.
    """
    token_data = await get_current_user(credentials)
    roles = token_data.get("realm_access", {}).get("roles", [])
    if "admin" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Admin role required.",
        )
    return token_data


# -------------------------------------------------------------------
# Вспомогательные административные функции (через Admin API)
# -------------------------------------------------------------------

def create_user(username: str, email: str, password: str,
                first_name: str = "", last_name: str = "") -> dict:
    """Создаёт нового пользователя в Keycloak."""
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
    """Получает пользователя по username."""
    try:
        users = keycloak_admin.get_users({"username": username, "exact": True})
        return users[0] if users else None
    except KeycloakGetError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user: {str(e)}",
        )


def update_user(user_id: str, user_data: dict) -> None:
    """Обновляет данные пользователя."""
    try:
        keycloak_admin.update_user(user_id=user_id, payload=user_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update user: {str(e)}",
        )


def delete_user(user_id: str) -> None:
    """Удаляет пользователя по ID."""
    try:
        keycloak_admin.delete_user(user_id=user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete user: {str(e)}",
        )


def get_all_users() -> list:
    """Возвращает список всех пользователей в realm."""
    try:
        return keycloak_admin.get_users()
    except KeycloakGetError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get users list: {str(e)}",
        )


def assign_admin_role(user_id: str) -> None:
    """Назначает пользователю роль 'admin' в realm."""
    try:
        realm_roles = keycloak_admin.get_realm_roles()
        admin_role = next((r for r in realm_roles if r["name"] == "admin"), None)
        if not admin_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin role not found in realm",
            )
        keycloak_admin.assign_realm_roles(user_id=user_id, roles=[admin_role])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to assign admin role: {str(e)}",
        )