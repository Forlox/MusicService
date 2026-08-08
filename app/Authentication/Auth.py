import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, HTTPBasic, HTTPBasicCredentials
from keycloak import KeycloakAdmin, KeycloakOpenID
from keycloak.exceptions import KeycloakAuthenticationError, KeycloakGetError

import logging
logger = logging.getLogger(__name__)

# Конфигурация из переменных окружения
KEYCLOAK_SERVER_URL = os.getenv("KEYCLOAK_SERVER_URL", "http://localhost:8080/")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "master")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "admin-cli")
KEYCLOAK_CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET", None)

# Клиенты Keycloak
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

# Схемы извлечения учётных данных
bearer_scheme = HTTPBearer()
basic_scheme = HTTPBasic()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), ) -> dict:
    token = credentials.credentials
    try:
        decoded = keycloak_openid.decode_token(token)
        logger.debug(f"Decoded token: {decoded.keys()}")
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


async def get_admin_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token_data = await get_current_user(credentials)
    if not has_role(token_data, "admin"):
        raise HTTPException(
            status_code=403,
            detail=f"Insufficient permissions. Admin role required. Current roles: {get_user_roles(token_data)}",
        )
    return token_data


def get_user_roles(token_data: dict) -> list:
    """Возвращает все роли пользователя из токена (realm + client)."""
    realm_roles = token_data.get("realm_access", {}).get("roles", [])
    client_roles = token_data.get("resource_access", {}).get(KEYCLOAK_CLIENT_ID, {}).get("roles", [])
    return list(set(realm_roles + client_roles))

def has_role(token_data: dict, role: str) -> bool:
    return role in get_user_roles(token_data)

def require_roles(*roles: str):
    """Фабрика зависимости: пропускает пользователей, имеющих хотя бы одну из указанных ролей."""
    async def checker(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
        token_data = await get_current_user(credentials)

        if "admin" in roles or has_role(token_data, "admin"):
            return token_data

        if any(has_role(token_data, role) for role in roles):
            return token_data

        raise HTTPException(
            status_code=403,
            detail=f"Insufficient permissions. Required roles: {', '.join(roles)}. Current roles: {get_user_roles(token_data)}",
        )

    return checker

def _is_user_activated(user_id: str) -> bool:
    from Users.Users import Users
    user = Users().get_user_by_keycloak_id(user_id)
    return bool(user and user["is_active"])

def require_active_user():
    """Фабрика зависимости: пропускает только активированных пользователей и админов."""
    async def checker(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
        token_data = await get_current_user(credentials)

        if has_role(token_data, "admin"):
            return token_data

        if not _is_user_activated(token_data.get("sub")):
            raise HTTPException(
                status_code=403,
                detail="Account is not activated.",
            )
        return token_data
    return checker

async def get_current_user_from_basic(credentials: HTTPBasicCredentials = Depends(basic_scheme), ) -> dict:
    """Аутентификация по логину/паролю (HTTP Basic)"""
    try:
        token = keycloak_openid.token(
            username=credentials.username,
            password=credentials.password,
            scope="openid roles profile email",  # Важно добавить roles в scope
        )
        return keycloak_openid.decode_token(token["access_token"])
    except KeycloakAuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Basic"},
        )