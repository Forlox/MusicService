import os, time
from keycloak.exceptions import KeycloakConnectionError
from Authentication.Auth import keycloak_admin, KEYCLOAK_CLIENT_ID

def configure_basic_scope():
    scopes = keycloak_admin.get_client_scopes()

    basic_scope = next(
        (scope for scope in scopes if scope["name"] == "basic"),
        None
    )

    if not basic_scope:
        return

    scope_id = basic_scope["id"]

    scope = keycloak_admin.get_client_scope(scope_id)
    attributes = scope.get("attributes", {})

    if attributes.get("include.in.token.scope") != "true":
        attributes["include.in.token.scope"] = "true"

        keycloak_admin.update_client_scope(
            scope_id,
            {
                **scope,
                "attributes": attributes
            }
        )

    mappers = keycloak_admin.get_mappers_from_client_scope(scope_id)

    for mapper in mappers:
        if mapper["name"] == "sub":
            config = mapper.get("config", {})

            if config.get("lightweight.claim") != "true":
                config["lightweight.claim"] = "true"

                keycloak_admin.update_mapper_in_client_scope(
                    scope_id,
                    mapper["id"],
                    {
                        **mapper,
                        "config": config
                    }
                )
            break

def configure_token_settings():
    realm_name = os.getenv("KEYCLOAK_REALM", "master")

    realm = keycloak_admin.get_realm(realm_name)

    if realm.get("accessTokenLifespan") != 300:
        keycloak_admin.update_realm(
            realm_name,
            {
                "accessTokenLifespan": 300
            }
        )

def configure_lightweight_tokens():
    """Отключает lightweight access tokens для клиента приложения.

    Начиная с Keycloak 26 сервисные клиенты (например admin-cli) по умолчанию
    выпускают "лёгкие" access-токены, в которые не попадают роли (realm_access)
    и другие claims. Без полноценного токена проверка админов не работает.
    """
    client_id = keycloak_admin.get_client_id(KEYCLOAK_CLIENT_ID)
    client = keycloak_admin.get_client(client_id)

    attributes = client.get("attributes", {})
    attributes["client.use.lightweight.access.token.enabled"] = "false"

    keycloak_admin.update_client(
        client_id,
        {
            **client,
            "attributes": attributes,
        }
    )

def wait_for_keycloak():
    while True:
        try:
            keycloak_admin.get_realm("master")
            return

        except KeycloakConnectionError:
            print("Keycloak недоступен. Попытка повторного подключения")
            time.sleep(3)


def configure_keycloak():
    wait_for_keycloak()
    configure_basic_scope()
    configure_lightweight_tokens()
    configure_token_settings()
