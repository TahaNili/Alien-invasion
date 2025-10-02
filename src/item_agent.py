"""
Item agent: pickup & use logic for enemies
- API:
    - should_pickup(entity, item) -> bool
    - on_pickup(entity, item)
    - should_use(entity, item) -> bool
    - on_use(entity, item)

Simple rule-based implementation to start with.
"""
from typing import Any


def should_pickup(entity: Any, item: Any) -> bool:
    # Example rules: pickup heart if hp < 40%, pickup shield if no shield
    try:
        itype = getattr(item, "type", None) or item
        hp = getattr(entity, "health", None)
        if itype == "heart":
            return hp is not None and hp < getattr(entity, "max_health", 100) * 0.4
        if itype == "shield":
            return not getattr(entity, "has_shield", False)
    except Exception:
        return False
    return False


def on_pickup(entity: Any, item: Any) -> None:
    itype = getattr(item, "type", None) or item
    if itype == "heart":
        entity.health = min(getattr(entity, "max_health", 100), getattr(entity, "health", 0) + getattr(item, "value", 25))
    if itype == "shield":
        entity.has_shield = True
        entity.shield_expires_at = None  # caller should set a timer if needed


def should_use(entity: Any, item_type: str) -> bool:
    # Use heart if hp < 40%; use shield if taking heavy fire (simplified)
    if item_type == "heart":
        return getattr(entity, "health", 0) < getattr(entity, "max_health", 100) * 0.4
    if item_type == "shield":
        return not getattr(entity, "has_shield", False)
    return False


def on_use(entity: Any, item_type: str) -> None:
    if item_type == "heart":
        entity.health = min(getattr(entity, "max_health", 100), getattr(entity, "health", 0) + 50)
    if item_type == "shield":
        entity.has_shield = True
        # set duration if entity supports it
        entity.shield_expires_at = None

