# SkillTrack controller: thin UI-facing API that wraps logic.py
from typing import List, Optional
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
)

# Simple in-memory auth state for the running application
_current_user: Optional[str] = None

import os

# Helper to create per-user filenames under data/<username>/
def _user_file(base: str, username: Optional[str]) -> str:
    if not username:
        return f"{base}.txt"
    safe = username.replace(' ', '_')
    userdir = os.path.join('data', safe)
    # ensure directory exists when called from controller
    try:
        os.makedirs(userdir, exist_ok=True)
    except Exception:
        pass
    return os.path.join(userdir, f"{base}.txt")


# Controller functions used by UI

def get_entities() -> List[Entity]:
    fname = _user_file('entities', current_user())
    return loadEntitiesFromFile(filename=fname)


def create_entity(name: str, type_: str, description: str) -> Entity:
    fname = _user_file('entities', current_user())
    entities = loadEntitiesFromFile(filename=fname)
    next_id = max((e.id for e in entities), default=0) + 1
    ent = Entity(id=next_id, name=name, type=type_, description=description)
    appendEntityToFile(ent, filename=fname)
    return ent


def delete_entity(entity_id: int) -> bool:
    fname = _user_file('entities', current_user())
    entities = loadEntitiesFromFile(filename=fname)
    new_list = [e for e in entities if e.id != entity_id]
    if len(new_list) == len(entities):
        return False
    saveEntitesToFile(new_list, filename=fname)
    return True


def update_entity(entity_id: int, name: str, type_: str, description: str, filename: str = None) -> bool:
    fname = filename or _user_file('entities', current_user())
    entities = loadEntitiesFromFile(fname)
    updated = False
    for e in entities:
        if e.id == entity_id:
            e.name = name
            e.type = type_
            e.description = description
            updated = True
            break
    if updated:
        saveEntitesToFile(entities, filename=fname)
    return updated


def get_started_sessions():
    fname = _user_file('started_sessions', current_user())
    return loadStartedSessionsFromFile(filename=fname)


def start_entity_session(entity: Entity):
    # create a started session in the user's started sessions file
    fname = _user_file('started_sessions', current_user())
    started = loadStartedSessionsFromFile(filename=fname)
    next_id = max((s.id for s in started), default=0) + 1
    from datetime import datetime
    session = Session(id=next_id, startTime=datetime.now(), endTime=None, entityId=entity.id)
    appendStartedSessionToFile(session, filename=fname)
    return session


def stop_session(session):
    started_fname = _user_file('started_sessions', current_user())
    completed_fname = _user_file('complete_sessions', current_user())
    sessions = loadStartedSessionsFromFile(filename=started_fname)
    for s in sessions:
        if s.id == session.id:
            from datetime import datetime
            s.endTime = datetime.now()
            appendSessionToFile(s, filename=completed_fname)
            sessions.remove(s)
            saveStartedSessionsToFile(sessions, filename=started_fname)
            return s


def get_completed_sessions():
    fname = _user_file('complete_sessions', current_user())
    return loadSessionsFromFile(filename=fname)


def generate_report(entity: Entity, start, end):
    fname = _user_file('complete_sessions', current_user())
    return GenerateReport(entity, start, end, filename=fname)


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
    fname = _user_file('goals', current_user())
    all_goals = loadGoalsFromFile(filename=fname)
    if entity_id is not None:
        return [g for g in all_goals if g.entityId == entity_id]
    return all_goals


def add_goal(entity_id: int, name: str, target_hours: float) -> Goal:
    fname = _user_file('goals', current_user())
    all_goals = loadGoalsFromFile(filename=fname)
    next_id = max((g.id for g in all_goals), default=0) + 1
    goal = Goal(id=next_id, entityId=entity_id, name=name, targetHours=target_hours, status='Incomplete')
    appendGoalToFile(goal, filename=fname)
    return goal


def update_goal(goal_id: int, name: str, target_hours: float, status: str) -> bool:
    fname = _user_file('goals', current_user())
    all_goals = loadGoalsFromFile(filename=fname)
    updated = False
    for g in all_goals:
        if g.id == goal_id:
            g.name = name
            g.targetHours = target_hours
            g.status = status
            updated = True
            break
    if updated:
        saveGoalsToFile(all_goals, filename=fname)
    return updated


def delete_goal(goal_id: int) -> bool:
    fname = _user_file('goals', current_user())
    all_goals = loadGoalsFromFile(filename=fname)
    new_list = [g for g in all_goals if g.id != goal_id]
    if len(new_list) == len(all_goals):
        return False
    saveGoalsToFile(new_list, filename=fname)
    return True
