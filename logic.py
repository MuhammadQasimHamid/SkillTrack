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
from datetime import datetime, timedelta
from typing import Optional

class Session:
    def __init__(self,id,startTime,endTime,entityId):
        self.id = id
        self.startTime = startTime
        self.endTime = endTime
        self.entityId = entityId
    
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
    if not os.path.exists(filename):
        return users
    with open(filename, 'r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            if not row or len(row) < 5:
                continue
            try:
                username = row[0]
                salt = row[1]
                pwdhash = row[2]
                iterations = int(row[3])
                created = _parse_iso_datetime(row[4]) or datetime.now()
                users[username] = User(username, salt, pwdhash, iterations, created)
            except Exception:
                continue
    return users


def saveUsersToFile(users: dict, filename='users.txt'):
    _ensure_file_exists(filename)
    dirpath = os.path.dirname(os.path.abspath(filename)) or '.'
    tmpfd, tmpname = tempfile.mkstemp(dir=dirpath)
    try:
        with os.fdopen(tmpfd, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            for u in users.values():
                writer.writerow([u.username, u.salt, u.pwdhash, u.iterations, u.created.isoformat()])
        os.replace(tmpname, filename)
    except Exception:
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            for u in users.values():
                writer.writerow([u.username, u.salt, u.pwdhash, u.iterations, u.created.isoformat()])
        try:
            if os.path.exists(tmpname):
                os.remove(tmpname)
        except Exception:
            pass


def create_user(username: str, password: str, filename='users.txt') -> bool:
    users = loadUsersFromFile(filename)
    if username in users:
        return False
    salt_hex, hash_hex, iterations = _hash_password(password)
    users[username] = User(username, salt_hex, hash_hex, iterations, datetime.now())
    saveUsersToFile(users, filename)
    return True


def authenticate_user(username: str, password: str, filename='users.txt') -> bool:
    users = loadUsersFromFile(filename)
    u = users.get(username)
    if not u:
        return False
    try:
        salt = binascii.unhexlify(u.salt)
        dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, u.iterations)
        return hmac.compare_digest(binascii.hexlify(dk).decode('ascii'), u.pwdhash)
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

def GenerateReport(entity, startDate, endDate, filename='complete_sessions.txt'):
    allSessions = loadSessionsFromFile(filename=filename)
    filteredSessions = [s for s in allSessions if s.entityId == entity.id and s.startTime >= startDate and s.endTime <= endDate]
    hours, minutes, seconds = calculateTotalTime(filteredSessions)
    return Report(id=len(allSessions) + 1, entityId=entity.id, startDate=startDate, endDate=endDate, totalTimeSpent=(hours, minutes, seconds))

# Function to append Completed session to a file
def appendSessionToFile(session, filename='complete_sessions.txt'):
    """Append a completed session using CSV and ISO timestamps."""
    _ensure_file_exists(filename)
    with open(filename, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        start = session.startTime.isoformat() if session.startTime else ''
        end = session.endTime.isoformat() if session.endTime else ''
        writer.writerow([session.id, start, end, session.entityId])


# load all sessions from file
def loadSessionsFromFile(filename='complete_sessions.txt'):
    sessions = []
    if not os.path.exists(filename):
        return sessions
    with open(filename, 'r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            if not row or len(row) < 4:
                continue
            try:
                id = int(row[0])
                start = _parse_iso_datetime(row[1])
                end = _parse_iso_datetime(row[2])
                entityId = int(row[3])
                if start and end:
                    sessions.append(Session(id, start, end, entityId))
            except Exception:
                # skip malformed rows
                continue
    return sessions
def saveSessionsToFile(sessions, filename='complete_sessions.txt'):
    _ensure_file_exists(filename)
    dirpath = os.path.dirname(os.path.abspath(filename)) or '.'
    tmpfd, tmpname = tempfile.mkstemp(dir=dirpath)
    try:
        with os.fdopen(tmpfd, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            for session in sessions:
                start = session.startTime.isoformat() if session.startTime else ''
                end = session.endTime.isoformat() if session.endTime else ''
                writer.writerow([session.id, start, end, session.entityId])
        os.replace(tmpname, filename)
    except Exception:
        # Fallback: attempt direct write to target (non-atomic)
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            for session in sessions:
                start = session.startTime.isoformat() if session.startTime else ''
                end = session.endTime.isoformat() if session.endTime else ''
                writer.writerow([session.id, start, end, session.entityId])
        try:
            if os.path.exists(tmpname):
                os.remove(tmpname)
        except Exception:
            pass

# Function to append Started session to a file
def appendStartedSessionToFile(session, filename='started_sessions.txt'):
    """Append a started session (end time is blank until ended)."""
    _ensure_file_exists(filename)
    with open(filename, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        start = session.startTime.isoformat() if session.startTime else ''
        writer.writerow([session.id, start, '', session.entityId])
def loadStartedSessionsFromFile(filename='started_sessions.txt'):
    sessions = []
    if not os.path.exists(filename):
        return sessions
    with open(filename, 'r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            if not row or len(row) < 4:
                continue
            try:
                id = int(row[0])
                start = _parse_iso_datetime(row[1])
                entityId = int(row[3])
                if start:
                    sessions.append(Session(id, start, None, entityId))
            except Exception:
                continue
    return sessions
def saveStartedSessionsToFile(sessions, filename='started_sessions.txt'):
    _ensure_file_exists(filename)
    dirpath = os.path.dirname(os.path.abspath(filename)) or '.'
    tmpfd, tmpname = tempfile.mkstemp(dir=dirpath)
    try:
        with os.fdopen(tmpfd, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            for session in sessions:
                start = session.startTime.isoformat() if session.startTime else ''
                writer.writerow([session.id, start, '', session.entityId])
        os.replace(tmpname, filename)
    except Exception:
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            for session in sessions:
                start = session.startTime.isoformat() if session.startTime else ''
                writer.writerow([session.id, start, '', session.entityId])
        try:
            if os.path.exists(tmpname):
                os.remove(tmpname)
        except Exception:
            pass

# Entity management functions
def appendEntityToFile(entity, filename='entities.txt'):
    _ensure_file_exists(filename)
    with open(filename, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([entity.id, entity.name, entity.type, entity.description])
def loadEntitiesFromFile(filename='entities.txt'):
    entities = []
    if not os.path.exists(filename):
        return entities
    with open(filename, 'r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            if not row or len(row) < 4:
                continue
            try:
                id = int(row[0])
                name, type_, description = row[1], row[2], row[3]
                entities.append(Entity(id, name, type_, description))
            except Exception:
                continue
    return entities
def saveEntitesToFile(entities,filename='entities.txt'):
    _ensure_file_exists(filename)
    dirpath = os.path.dirname(os.path.abspath(filename)) or '.'
    tmpfd, tmpname = tempfile.mkstemp(dir=dirpath)
    try:
        with os.fdopen(tmpfd, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            for entity in entities:
                writer.writerow([entity.id, entity.name, entity.type, entity.description])
        os.replace(tmpname, filename)
    except Exception:
        with open(filename,'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            for entity in entities:
                writer.writerow([entity.id, entity.name, entity.type, entity.description])
        try:
            if os.path.exists(tmpname):
                os.remove(tmpname)
        except Exception:
            pass


def startSession(entity):
    from datetime import datetime
    started = loadStartedSessionsFromFile()
    next_id = max((s.id for s in started), default=0) + 1
    session = Session(id=next_id, startTime=datetime.now(), endTime=None, entityId=entity.id)
    appendStartedSessionToFile(session)
    return session

def endSession(session):
    sessions = loadStartedSessionsFromFile()
    for s in sessions:
        if s.id == session.id:
            s.endTime = datetime.now()
            appendSessionToFile(s) # Move to completed sessions
            sessions.remove(s)
            saveStartedSessionsToFile(sessions) # Update started sessions file
            return s

# Goal management functions
def appendGoalToFile(goal, filename='goals.txt'):
    _ensure_file_exists(filename)
    with open(filename, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([goal.id, goal.entityId, goal.name, goal.targetHours, goal.status])

def loadGoalsFromFile(filename='goals.txt'):
    goals = []
    if not os.path.exists(filename):
        return goals
    with open(filename, 'r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            if not row or len(row) < 5:
                continue
            try:
                id = int(row[0])
                entityId = int(row[1])
                name = row[2]
                targetHours = float(row[3])
                status = row[4]
                goals.append(Goal(id, entityId, name, targetHours, status))
            except Exception:
                continue
    return goals

def saveGoalsToFile(goals, filename='goals.txt'):
    _ensure_file_exists(filename)
    dirpath = os.path.dirname(os.path.abspath(filename)) or '.'
    tmpfd, tmpname = tempfile.mkstemp(dir=dirpath)
    try:
        with os.fdopen(tmpfd, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            for g in goals:
                writer.writerow([g.id, g.entityId, g.name, g.targetHours, g.status])
        os.replace(tmpname, filename)
    except Exception:
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            for g in goals:
                writer.writerow([g.id, g.entityId, g.name, g.targetHours, g.status])
        try:
            if os.path.exists(tmpname):
                os.remove(tmpname)
        except Exception:
            pass

    
    
    

   