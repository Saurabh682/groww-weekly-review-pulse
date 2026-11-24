class StoreError(Exception):
    pass


class UnknownApp(StoreError):
    pass


class ActiveAppCapReached(StoreError):
    pass


class AppIdentityFrozen(StoreError):
    pass


class DuplicateStoreListing(StoreError):
    pass


class InvalidAppRecord(StoreError):
    pass


def translate_integrity_error(exc: Exception) -> StoreError:
    message = str(exc)
    if "active_app_cap_reached" in message:
        return ActiveAppCapReached("5 of 5 active app slots are used. Archive an app first.")
    if "app_identity_frozen" in message:
        return AppIdentityFrozen("app_key and store listing IDs cannot change. Use replace instead.")
    if "apps_play_live" in message or "apps.play_package_id" in message:
        return DuplicateStoreListing("This Play Store listing already belongs to an active app.")
    if "apps_ios_live" in message or "apps.app_store_id" in message:
        return DuplicateStoreListing("This App Store listing already belongs to an active app.")
    if "CHECK constraint" in message or "check constraint" in message or "violates check" in message:
        return InvalidAppRecord(message)
    if "UNIQUE constraint failed: apps.app_key" in message or "apps_pkey" in message:
        return InvalidAppRecord(f"app_key already exists: {message}")
    return StoreError(message)
