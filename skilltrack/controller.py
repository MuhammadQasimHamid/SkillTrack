from typing import List, Optional
import os
import sqlite3
from logic import (
    Entity,
    Session,
    loadEntitiesFromFile,
    appendEntityToFile,
    saveEntitesToFile,
    loadStartedSessionsFromFile,
    appendStartedSessionToFile,
    saveStartedSessionsToFile,
    appendSessionToFile,
    loadSessionsFromFile,
    GenerateReport,
    create_user,
    authenticate_user,
    loadUsersFromFile,
    Goal,
    loadGoalsFromFile,
    appendGoalToFile,
    saveGoalsToFile,
    startSession,
    endSession,
    get_db_connection,
    delete_session as logic_delete_session,
    recover_session as logic_recover_session,
    update_session as logic_update_session
)

# Simple in-memory auth state for the running application
_current_user: Optional[str] = None

import os

# Helper for any remaining user-specific files (not database)
def _user_file(base: str, username: Optional[str]) -> str:
    if not username:
        return f"{base}.txt"
    safe = username.replace(' ', '_')
    userdir = os.path.join('data', safe)
    # ensure directory exists
    try:
        os.makedirs(userdir, exist_ok=True)
    except Exception:
        pass
    return os.path.join(userdir, f"{base}.txt")


# Controller functions used by UI

def get_entities() -> List[Entity]:
    return loadEntitiesFromFile(username=current_user())


def create_entity(name: str, type_: str, description: str) -> Entity:
    ent = Entity(id=0, name=name, type=type_, description=description)
    appendEntityToFile(ent, username=current_user())
    return ent


def delete_entity(entity_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM entities WHERE id = ? AND username = ?", (entity_id, current_user()))
    rows = cursor.rowcount
    conn.commit()
    conn.close()
    return rows > 0


def update_entity(entity_id: int, name: str, type_: str, description: str, filename: str = None) -> bool:
    ent = Entity(id=entity_id, name=name, type=type_, description=description)
    saveEntitesToFile([ent], username=current_user())
    return True


def get_started_sessions():
    return loadStartedSessionsFromFile(username=current_user())


def start_entity_session(entity: Entity):
    return startSession(entity)


def stop_session(session):
    return endSession(session)


def get_completed_sessions(include_deleted: bool = False):
    return loadSessionsFromFile(username=current_user(), include_deleted=include_deleted)


def add_manual_session(entity_id: int, start_dt, end_dt):
    from logic import Session, appendSessionToFile
    session = Session(id=0, startTime=start_dt, endTime=end_dt, entityId=entity_id)
    appendSessionToFile(session)
    return session


def delete_session(session_id: int):
    logic_delete_session(session_id)


def recover_session(session_id):
    logic_recover_session(session_id)


def update_session(session_id: int, entity_id: int, start_dt, end_dt):
    logic_update_session(session_id, entity_id, start_dt, end_dt)


def generate_report(entity: Entity, start, end):
    return GenerateReport(entity, start, end, username=current_user())


# --- Authentication API ---

def register_user(username: str, password: str) -> bool:
    """Create a new user. Returns False if username already exists."""
    return create_user(username, password)


def login_user(username: str, password: str) -> bool:
    """Attempt to log in. Returns True on success."""
    global _current_user
    ok = authenticate_user(username, password)
    if ok:
        _current_user = username
    return ok


def logout_user():
    global _current_user
    _current_user = None


def current_user() -> Optional[str]:
    return _current_user


def is_authenticated() -> bool:
    return _current_user is not None


def list_users() -> List[str]:
    return list(loadUsersFromFile().keys())


# --- Goals API ---

def get_goals(entity_id: Optional[int] = None) -> List[Goal]:
    return loadGoalsFromFile(username=current_user())


def add_goal(entity_id: int, name: str, target_hours: float) -> Goal:
    goal = Goal(id=0, entityId=entity_id, name=name, targetHours=target_hours, status='Incomplete')
    appendGoalToFile(goal)
    return goal


def update_goal(goal_id: int, name: str, target_hours: float, status: str) -> bool:
    goal = Goal(id=goal_id, entityId=0, name=name, targetHours=target_hours, status=status)
    saveGoalsToFile([goal])
    return True


def delete_goal(goal_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
    rows = cursor.rowcount
    conn.commit()
    conn.close()
    return rows > 0
