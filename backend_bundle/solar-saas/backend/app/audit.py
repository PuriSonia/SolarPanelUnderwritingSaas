from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from .models import AuditLog, User

def log_event(
    db: Session,
    *,
    user: Optional[User],
    org_id: int,
    action: str,
    entity: Optional[str] = None,
    entity_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    entry = AuditLog(
        org_id=org_id,
        user_id=user.id if user else None,
        action=action,
        entity=entity,
        entity_id=entity_id,
        metadata=metadata or {},
    )
    db.add(entry)
    db.commit()
