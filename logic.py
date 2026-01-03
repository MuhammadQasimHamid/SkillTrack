# 'Skill Track' helps users track their learning time automatically and manually 
# across multiple skills or projects. The system provides analytics, progress 
# Skill Track – Personal Learning Time and Productivity Tracker
# 4
# reports, time summaries, and goal tracking. It aims to improve productivity, 
# help users understand their learning habits, and support consistent growth. 
# Typical users include students, self-learners, freelancers, and professionals 
# who need a simple way to measure the time they invest in skill development.
# Key capabilities include:
# • Automatic and manual time tracking
# • Categorization of skills and projects
# • Daily, weekly, and monthly reports
# • Goal-setting and reminders

import os
import csv
import tempfile
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List

class Session:
    def __init__(self,id,startTime,endTime,entityId,is_deleted=0):
        self.id = id
        self.startTime = startTime
        self.endTime = endTime
        self.entityId = entityId
        self.is_deleted = is_deleted
    
class Entity:
    def __init__(self,id,name,type,description):
        self.id = id
        self.name = name
        self.type = type
        self.description = description
class Report:
    def __init__(self,id,entityId,startDate,endDate,totalTimeSpent):
        self.id = id
        self.entityId = entityId
        self.startDate = startDate
        self.endDate = endDate
        self.totalTimeSpent = totalTimeSpent

class Goal:
    def __init__(self, id, entityId, name, targetHours, status):
        self.id = id
        self.entityId = entityId
        self.name = name
        self.targetHours = targetHours
        self.status = status # 'Incomplete', 'Completed'

def _ensure_file_exists(filename):
    # Make parent directory if needed (supports per-user data folders)
    try:
        dirpath = os.path.dirname(os.path.abspath(filename))
        if dirpath and not os.path.exists(dirpath):
            os.makedirs(dirpath, exist_ok=True)
    except Exception:
        pass
    if not os.path.exists(filename):
        # create an empty file so readers don't fail
        open(filename, 'a', encoding='utf-8').close()

def _parse_iso_datetime(value: str) -> Optional[datetime]:
    try:
        return datetime.fromisoformat(value) if value else None
    except Exception:
        return None

# --- SQLite Database Initialization ---
DB_FILE = 'skilltrack.db'

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            salt TEXT NOT NULL,
            pwdhash TEXT NOT NULL,
            iterations INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    
    # Entities table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            description TEXT,
            username TEXT NOT NULL,
            FOREIGN KEY (username) REFERENCES users (username)
        )
    ''')
    
    # Sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_id INTEGER NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT,
            is_deleted INTEGER DEFAULT 0,
            FOREIGN KEY (entity_id) REFERENCES entities (id)
        )
    ''')
    
    # Goals table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            target_hours REAL NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (entity_id) REFERENCES entities (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on module load
init_db()

# --- User auth helpers ---
class User:
    def __init__(self, username: str, salt: str, pwdhash: str, iterations: int, created: datetime):
        self.username = username
        self.salt = salt
        self.pwdhash = pwdhash
        self.iterations = iterations
        self.created = created

import hashlib
import hmac
import binascii


def _hash_password(password: str, salt: bytes = None, iterations: int = 100000):
    if salt is None:
        salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
    return binascii.hexlify(salt).decode('ascii'), binascii.hexlify(dk).decode('ascii'), iterations


def loadUsersFromFile(filename='users.txt'):
    """Return dict username -> User"""
    users = {}
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    for row in cursor.fetchall():
        users[row['username']] = User(
            row['username'], row['salt'], row['pwdhash'], 
            row['iterations'], _parse_iso_datetime(row['created_at'])
        )
    conn.close()
    return users


def create_user(username: str, password: str, filename='users.txt') -> bool:
    users = loadUsersFromFile()
    if username in users:
        return False
    salt_hex, hash_hex, iterations = _hash_password(password)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, salt, pwdhash, iterations, created_at) VALUES (?, ?, ?, ?, ?)",
        (username, salt_hex, hash_hex, iterations, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    return True


def authenticate_user(username: str, password: str, filename='users.txt') -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    u = cursor.fetchone()
    conn.close()
    
    if not u:
        return False
    try:
        salt = binascii.unhexlify(u['salt'])
        dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, u['iterations'])
        return hmac.compare_digest(binascii.hexlify(dk).decode('ascii'), u['pwdhash'])
    except Exception:
        return False

# Function to calculate total time spent in hours,mins,seconds for a list of sessions
def calculateTotalTime(sessions):
    totalSeconds = 0
    for session in sessions:
        totalSeconds += (session.endTime - session.startTime).total_seconds()
    
    hours = totalSeconds // 3600
    minutes = (totalSeconds % 3600) // 60
    seconds = totalSeconds % 60
    
    return int(hours), int(minutes), int(seconds)

def GenerateReport(entity, startDate, endDate, filename='complete_sessions.txt', username=None):
    allSessions = loadSessionsFromFile(username=username)
    filteredSessions = [s for s in allSessions if s.entityId == entity.id and s.startTime >= startDate and s.endTime <= endDate]
    hours, minutes, seconds = calculateTotalTime(filteredSessions)
    return Report(id=0, entityId=entity.id, startDate=startDate, endDate=endDate, totalTimeSpent=(hours, minutes, seconds))


def appendSessionToFile(session, filename='complete_sessions.txt'):
    """Append a completed session using SQLite."""
    conn = get_db_connection()
    cursor = conn.cursor()
    start = session.startTime.isoformat() if session.startTime else ''
    end = session.endTime.isoformat() if session.endTime else ''
    cursor.execute(
        "INSERT INTO sessions (entity_id, start_time, end_time) VALUES (?, ?, ?)",
        (session.entityId, start, end)
    )
    conn.commit()
    conn.close()


def loadSessionsFromFile(filename='complete_sessions.txt', username=None, include_deleted=False):
    sessions = []
    conn = get_db_connection()
    cursor = conn.cursor()
    
    deleted_filter = "" if include_deleted else "AND s.is_deleted = 0"
    
    if username:
        # Join with entities to filter by user
        cursor.execute(f'''
            SELECT s.* FROM sessions s
            JOIN entities e ON s.entity_id = e.id
            WHERE e.username = ? AND s.end_time IS NOT NULL {deleted_filter}
        ''', (username,))
    else:
        where_clause = "WHERE end_time IS NOT NULL"
        if not include_deleted:
            where_clause += " AND is_deleted = 0"
        cursor.execute(f"SELECT * FROM sessions {where_clause}")
        
    for row in cursor.fetchall():
        start = _parse_iso_datetime(row['start_time'])
        end = _parse_iso_datetime(row['end_time'])
        if start and end:
            sessions.append(Session(row['id'], start, end, row['entity_id'], row['is_deleted']))
    conn.close()
    return sessions

def delete_session(session_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE sessions SET is_deleted = 1 WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()

def recover_session(session_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE sessions SET is_deleted = 0 WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()

def update_session(session_id, entity_id, start_time, end_time):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE sessions SET entity_id = ?, start_time = ?, end_time = ? WHERE id = ?",
        (entity_id, start_time.isoformat(), end_time.isoformat(), session_id)
    )
    conn.commit()
    conn.close()


def saveSessionsToFile(sessions, filename='complete_sessions.txt'):
    # In SQLite, we typically don't 'save all' unless migrating.
    pass


def appendStartedSessionToFile(session, filename='started_sessions.txt'):
    """Append a started session in SQLite and update its id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    start = session.startTime.isoformat() if session.startTime else ''
    cursor.execute(
        "INSERT INTO sessions (entity_id, start_time, end_time) VALUES (?, ?, ?)",
        (session.entityId, start, None)
    )
    session.id = cursor.lastrowid
    conn.commit()
    conn.close()
    return session.id

def loadStartedSessionsFromFile(filename='started_sessions.txt', username=None):
    sessions = []
    conn = get_db_connection()
    cursor = conn.cursor()
    if username:
        cursor.execute('''
            SELECT s.* FROM sessions s
            JOIN entities e ON s.entity_id = e.id
            WHERE e.username = ? AND s.end_time IS NULL
        ''', (username,))
    else:
        cursor.execute("SELECT * FROM sessions WHERE end_time IS NULL")
        
    for row in cursor.fetchall():
        start = _parse_iso_datetime(row['start_time'])
        if start:
            sessions.append(Session(row['id'], start, None, row['entity_id'], row['is_deleted']))
    conn.close()
    return sessions

def saveStartedSessionsToFile(sessions, filename='started_sessions.txt'):
    # Manual synchronization not needed for SQLite.
    pass

def appendEntityToFile(entity, filename='entities.txt', username=None):
    if not username:
        return None
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO entities (name, type, description, username) VALUES (?, ?, ?, ?)",
        (entity.name, entity.type, entity.description, username)
    )
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id

def loadEntitiesFromFile(filename='entities.txt', username=None):
    entities = []
    conn = get_db_connection()
    cursor = conn.cursor()
    if username:
        cursor.execute("SELECT * FROM entities WHERE username = ?", (username,))
    else:
        cursor.execute("SELECT * FROM entities")
        
    for row in cursor.fetchall():
        entities.append(Entity(row['id'], row['name'], row['type'], row['description']))
    conn.close()
    return entities

def saveEntitesToFile(entities, filename='entities.txt', username=None):
    """Update existing entities in SQLite."""
    if not username:
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    for e in entities:
        cursor.execute(
            "UPDATE entities SET name = ?, type = ?, description = ? WHERE id = ? AND username = ?",
            (e.name, e.type, e.description, e.id, username)
        )
    conn.commit()
    conn.close()


def startSession(entity):
    session = Session(id=0, startTime=datetime.now(), endTime=None, entityId=entity.id)
    new_id = appendStartedSessionToFile(session)
    session.id = new_id
    return session

def endSession(session):
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now()
    cursor.execute("UPDATE sessions SET end_time = ? WHERE id = ?", (now.isoformat(), session.id))
    conn.commit()
    conn.close()
    session.endTime = now
    return session

def appendGoalToFile(goal, filename='goals.txt'):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO goals (entity_id, name, target_hours, status) VALUES (?, ?, ?, ?)",
        (goal.entityId, goal.name, goal.targetHours, goal.status)
    )
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id

def loadGoalsFromFile(filename='goals.txt', username=None):
    goals = []
    conn = get_db_connection()
    cursor = conn.cursor()
    if username:
        cursor.execute('''
            SELECT g.* FROM goals g
            JOIN entities e ON g.entity_id = e.id
            WHERE e.username = ?
        ''', (username,))
    else:
        cursor.execute("SELECT * FROM goals")
        
    for row in cursor.fetchall():
        goals.append(Goal(row['id'], row['entity_id'], row['name'], row['target_hours'], row['status']))
    conn.close()
    return goals

def saveGoalsToFile(goals, filename='goals.txt'):
    conn = get_db_connection()
    cursor = conn.cursor()
    for g in goals:
        cursor.execute(
            "UPDATE goals SET name = ?, target_hours = ?, status = ? WHERE id = ?",
            (g.name, g.targetHours, g.status, g.id)
        )
    conn.commit()
    conn.close()

    
    
    

   