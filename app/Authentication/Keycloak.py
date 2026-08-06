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