import os, time
from keycloak.exceptions import KeycloakConnectionError
from Authentication.Auth import keycloak_admin

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

def wait_for_keycloak():
    while True:
        try:
            keycloak_admin.get_realm("master")
            return

        except KeycloakConnectionError:
            print("Keycloak недоступен. Попытка повторного подключения через 3 сек")
            time.sleep(3)


def configure_keycloak():
    wait_for_keycloak()
    configure_basic_scope()
    configure_token_settings()
