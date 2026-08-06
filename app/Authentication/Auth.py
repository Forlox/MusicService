import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, HTTPBasic, HTTPBasicCredentials
from keycloak import KeycloakAdmin, KeycloakOpenID
from keycloak.exceptions import KeycloakAuthenticationError, KeycloakGetError

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
bearer_scheme = HTTPBearer()          # Authorization: Bearer <token>
basic_scheme = HTTPBasic()            # Authorization: Basic <base64>

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),) -> dict:
    print(KEYCLOAK_CLIENT_ID)
    token = credentials.credentials
    try:
        decoded = keycloak_openid.decode_token(token) # decode_token() автоматически проверяет подпись, issuer, expiration
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


async def get_current_user_from_basic(credentials: HTTPBasicCredentials = Depends(basic_scheme),) -> dict:
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


async def get_admin_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),) -> dict:
    """Только для администраторов. Проверяет токен и наличие роли 'admin'."""
    token_data = await get_current_user(credentials)
    roles = token_data.get("realm_access", {}).get("roles", [])
    if "admin" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Admin role required.",
        )
    return token_data