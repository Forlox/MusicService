import logging
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status
from keycloak.exceptions import KeycloakAuthenticationError, KeycloakGetError, KeycloakError

# Импорты из ваших модулей
from Authentication.Auth import keycloak_admin, keycloak_openid
from Users.Users import Users

# Настройка логирования (можно вынести в конфиг)
logger = logging.getLogger(__name__)

class UserManager:
    """
    Единый менеджер для управления пользователями с синхронизацией Keycloak и локальной БД.
    Все операции с пользователями должны проходить через этот класс.
    """
    def __init__(self):
        self.keycloak = keycloak_admin
        self.local = Users()
        self.openid = keycloak_openid

    def _get_local_user_by_keycloak_id(self, keycloak_id: str) -> Optional[Dict]:
        """Возвращает локального пользователя как словарь или None."""
        row = self.local.get_user_by_keycloak_id(keycloak_id)
        if not row:
            return None
        columns = ['id', 'keycloak_id', 'login', 'created_at', 'last_login', 'is_admin', 'is_active']
        return dict(zip(columns, row))

    def _get_keycloak_user(self, keycloak_id: str) -> Optional[Dict]:
        try:
            return self.keycloak.get_user(keycloak_id)
        except KeycloakGetError as e:
            logger.error(f"Keycloak get_user failed for {keycloak_id}: {e}")
            return None

    def _sync_single_user(self, keycloak_id: str) -> bool:
        """
        Синхронизирует пользователя: обновляет локальную запись по данным из Keycloak.
        Если пользователь отсутствует в Keycloak – удаляет локально.
        """
        kc_user = self._get_keycloak_user(keycloak_id)
        local_user = self._get_local_user_by_keycloak_id(keycloak_id)

        if not kc_user:
            if local_user:
                self.local.delete_local_user(keycloak_id)
                logger.info(f"Deleted local user {keycloak_id} (not found in Keycloak)")
            return True

        # Проверяем, есть ли роль admin в realm
        realm_roles = kc_user.get("realmRoles", [])
        is_admin = "admin" in realm_roles
        is_active = kc_user.get("enabled", True)
        username = kc_user.get("username")

        if local_user:
            self.local.update_local_user(
                keycloak_id,
                login=username,
                is_admin=is_admin,
                is_active=is_active
            )
            logger.info(f"Updated local user {keycloak_id}")
        else:
            self.local.create_local_user(
                keycloak_id=keycloak_id,
                login=username,
                is_admin=is_admin,
                is_active=is_active
            )
            logger.info(f"Created local user {keycloak_id}")
        return True

    def create_user(self, username: str, email: str, password: str,first_name: str = "", last_name: str = "") -> Dict:
        """
        Создаёт пользователя в Keycloak и локальной БД.
        Выбрасывает HTTPException при ошибке.
        """
        if not username or not email or not password:
            raise HTTPException(status_code=400, detail="Username, email and password are required")
        if len(password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

        try:
            existing = self.keycloak.get_users({"username": username, "exact": True})
            if existing:
                raise HTTPException(status_code=400, detail="Username already exists")
        except KeycloakGetError as e:
            logger.error(f"Keycloak get_users failed: {e}")
            raise HTTPException(status_code=500, detail="Keycloak error")

        # 1 - Создаём в Keycloak
        try:
            new_user = self.keycloak.create_user({
                "username": username,
                "email": email,
                "enabled": True,
                "firstName": first_name,
                "lastName": last_name,
                "emailVerified": False,   # можно настроить
            }, exist_ok=False)
            keycloak_id = new_user["id"]
            self.keycloak.set_user_password(keycloak_id, password, temporary=False)
            logger.info(f"Created Keycloak user {username} (ID: {keycloak_id})")
        except KeycloakError as e:
            logger.error(f"Keycloak create_user failed: {e}")
            raise HTTPException(status_code=400, detail=f"Keycloak error: {str(e)}")

        # 2 - Создаём локальную запись
        try:
            self.local.create_local_user(
                keycloak_id=keycloak_id,
                login=username,
                is_admin=False,
                is_active=True
            )
            logger.info(f"Created local user for {username}")
        except Exception as e: # Откат: удаляем пользователя из Keycloak
            try:
                self.keycloak.delete_user(keycloak_id)
                logger.warning(f"Rolled back Keycloak user {username} due to local DB error")
            except Exception as rollback_error:
                logger.error(f"Rollback failed: {rollback_error}")
            raise HTTPException(status_code=500, detail=f"Local database error: {str(e)}")

        return { # Возвращаем данные созданного пользователя
            "id": keycloak_id,
            "username": username,
            "email": email,
            "firstName": first_name,
            "lastName": last_name,
            "enabled": True,
            "roles": []
        }

    def update_user(self, keycloak_id: str, **kwargs) -> Dict:
        """
        Обновляет пользователя в Keycloak и локальной БД.
        Допустимые поля: username, email, firstName, lastName, enabled.
        """
        allowed_fields = {"username", "email", "firstName", "lastName", "enabled"} #Разрешаем только определённые поля для обновления
        payload = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not payload:
            raise HTTPException(status_code=400, detail="No valid fields to update")

        # Проверяем существование в Keycloak
        kc_user = self._get_keycloak_user(keycloak_id)
        if not kc_user:
            raise HTTPException(status_code=404, detail="User not found in Keycloak")

        # Обновляем в Keycloak
        try:
            self.keycloak.update_user(keycloak_id, payload)
            logger.info(f"Updated Keycloak user {keycloak_id}")
        except KeycloakError as e:
            logger.error(f"Keycloak update_user failed: {e}")
            raise HTTPException(status_code=400, detail=f"Keycloak error: {str(e)}")

        # Обновляем локально (поддерживаемые поля: login, is_admin, is_active)
        local_updates = {}
        if "username" in payload:
            local_updates["login"] = payload["username"]
        if "enabled" in payload:
            local_updates["is_active"] = payload["enabled"]
        # is_admin не обновляется через update_user, только через assign/remove role
        if local_updates:
            try:
                self.local.update_local_user(keycloak_id, **local_updates)
                logger.info(f"Updated local user {keycloak_id}")
            except Exception as e:
                # Не откатываем Keycloak, но логируем
                logger.error(f"Local update failed for {keycloak_id}: {e}")
                raise HTTPException(status_code=500, detail="Local database error")

        updated = self._get_keycloak_user(keycloak_id)
        return updated or {}

    def delete_user(self, keycloak_id: str) -> None:
        """Удаляет пользователя из Keycloak и БД."""
        kc_user = self._get_keycloak_user(keycloak_id)
        if not kc_user:
            raise HTTPException(status_code=404, detail="User not found in Keycloak")

        # Удаляем из Keycloak
        try:
            self.keycloak.delete_user(keycloak_id)
            logger.info(f"Deleted Keycloak user {keycloak_id}")
        except KeycloakError as e:
            logger.error(f"Keycloak delete_user failed: {e}")
            raise HTTPException(status_code=400, detail=f"Keycloak error: {str(e)}")

        # Удаляем локально
        try:
            self.local.delete_local_user(keycloak_id)
            logger.info(f"Deleted local user {keycloak_id}")
        except Exception as e:
            logger.error(f"Local delete failed for {keycloak_id}: {e}")# Логируем, но не откатываем Keycloak (уже удалён)
            # Можно выбросить исключение, но лучше просто предупредить
            # raise HTTPException(status_code=500, detail="Local database error")

    def assign_admin_role(self, keycloak_id: str) -> None:
        """Назначает пользователю роль admin в Keycloak и обновляет локальный is_admin."""
        try:
            realm_roles = self.keycloak.get_realm_roles()
            admin_role = next((r for r in realm_roles if r["name"] == "admin"), None)
            if not admin_role:
                raise HTTPException(status_code=404, detail="Admin role not found in realm")
        except KeycloakError as e:
            logger.error(f"Keycloak get_realm_roles failed: {e}")
            raise HTTPException(status_code=500, detail="Keycloak error")

        # Назначаем роль
        try:
            self.keycloak.assign_realm_roles(user_id=keycloak_id, roles=[admin_role])
            logger.info(f"Assigned admin role to {keycloak_id}")
        except KeycloakError as e:
            logger.error(f"Keycloak assign_realm_roles failed: {e}")
            raise HTTPException(status_code=400, detail=f"Keycloak error: {str(e)}")

        # Обновляем локально
        try:
            self.local.update_local_user(keycloak_id, is_admin=True)
            logger.info(f"Updated local admin flag for {keycloak_id}")
        except Exception as e:
            logger.error(f"Local update admin flag failed: {e}")
            # Не откатываем Keycloak, но логируем

    def remove_admin_role(self, keycloak_id: str) -> None:
        """Снимает с пользователя роль admin в Keycloak и обновляет локальный is_admin."""
        try:
            # Получаем роли пользователя
            user_roles = self.keycloak.get_realm_roles_of_user(keycloak_id)
            admin_role = next((r for r in user_roles if r["name"] == "admin"), None)
            if not admin_role:
                # Роль уже снята
                return
            self.keycloak.delete_realm_roles_of_user(user_id=keycloak_id, roles=[admin_role])
            logger.info(f"Removed admin role from {keycloak_id}")
        except KeycloakError as e:
            logger.error(f"Keycloak remove admin role failed: {e}")
            raise HTTPException(status_code=400, detail=f"Keycloak error: {str(e)}")

        # Обновляем локально
        try:
            self.local.update_local_user(keycloak_id, is_admin=False)
            logger.info(f"Updated local admin flag for {keycloak_id}")
        except Exception as e:
            logger.error(f"Local update admin flag failed: {e}")

    def get_user(self, keycloak_id: str) -> Dict:
        """Возвращает пользователя из Keycloak (может быть дополнен локальными данными)."""
        kc_user = self._get_keycloak_user(keycloak_id)
        if not kc_user:
            raise HTTPException(status_code=404, detail="User not found")
        # Дополняем локальными данными, если нужно (например, created_at, last_login)
        local_user = self._get_local_user_by_keycloak_id(keycloak_id)
        if local_user:
            kc_user["local_created_at"] = local_user.get("created_at")
            kc_user["local_last_login"] = local_user.get("last_login")
        return kc_user

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Ищет пользователя по username в Keycloak."""
        try:
            users = self.keycloak.get_users({"username": username, "exact": True})
            if not users:
                return None
            return users[0]
        except KeycloakGetError as e:
            logger.error(f"Keycloak get_users failed: {e}")
            raise HTTPException(status_code=500, detail="Keycloak error")

    def get_all_users(self) -> List[Dict]:
        """Возвращает всех пользователей из Keycloak."""
        try:
            return self.keycloak.get_users()
        except KeycloakGetError as e:
            logger.error(f"Keycloak get_users failed: {e}")
            raise HTTPException(status_code=500, detail="Keycloak error")

    def sync_user(self, keycloak_id: str) -> bool:
        return self._sync_single_user(keycloak_id)

    def sync_all_users(self) -> Dict[str, int]:
        """
        Полная синхронизация всех пользователей из Keycloak с локальной БД.
        Возвращает статистику: {'created': n, 'updated': n, 'deleted': n}
        """
        stats = {"created": 0, "updated": 0, "deleted": 0}
        try:
            kc_users = self.keycloak.get_users()
            kc_ids = {u["id"] for u in kc_users}
        except KeycloakGetError as e:
            logger.error(f"Keycloak get_users failed: {e}")
            raise HTTPException(status_code=500, detail="Keycloak error")

        # Получаем всех локальных пользователей
        local_rows = self.local.get_all_local_users()
        local_ids = {row[1] for row in local_rows}  # keycloak_id на позиции 1

        # Синхронизируем каждого пользователя из Keycloak
        for kc_user in kc_users:
            keycloak_id = kc_user["id"]
            local_user = self._get_local_user_by_keycloak_id(keycloak_id)
            # Определяем роль admin
            realm_roles = kc_user.get("realmRoles", [])
            is_admin = "admin" in realm_roles
            is_active = kc_user.get("enabled", True)
            username = kc_user.get("username")

            if local_user:
                # Обновляем, если данные изменились (можно сравнить, но для простоты обновляем всегда)
                self.local.update_local_user(
                    keycloak_id,
                    login=username,
                    is_admin=is_admin,
                    is_active=is_active
                )
                stats["updated"] += 1
            else:
                self.local.create_local_user(
                    keycloak_id=keycloak_id,
                    login=username,
                    is_admin=is_admin,
                    is_active=is_active
                )
                stats["created"] += 1

        # Удаляем локальных пользователей, отсутствующих в Keycloak
        for local_id in local_ids:
            if local_id not in kc_ids:
                self.local.delete_local_user(local_id)
                stats["deleted"] += 1

        logger.info(f"Sync complete: {stats}")
        return stats

    def update_last_login(self, keycloak_id: str) -> None:
        """Обновляет время последнего входа в локальной БД."""
        try:
            self.local.update_last_login(keycloak_id)
        except Exception as e:
            logger.error(f"Failed to update last_login for {keycloak_id}: {e}")