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
from datetime import datetime, timedelta

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
# Function to calculate total time spent in hours,mins,seconds for a list of sessions
def calculateTotalTime(sessions):
    totalSeconds = 0
    for session in sessions:
        totalSeconds += (session.endTime - session.startTime).total_seconds()
    
    hours = totalSeconds // 3600
    minutes = (totalSeconds % 3600) // 60
    seconds = totalSeconds % 60
    
    return int(hours), int(minutes), int(seconds)

def GenerateReport(entity, startDate, endDate):
    allSessions = loadSessionsFromFile()
    filteredSessions = [s for s in allSessions if s.entityId == entity.id and s.startTime >= startDate and s.endTime <= endDate]
    hours, minutes, seconds = calculateTotalTime(filteredSessions)
    return Report(id=len(loadSessionsFromFile()) + 1, entityId=entity.id, startDate=startDate, endDate=endDate, totalTimeSpent=(hours, minutes, seconds))

# Function to append Completed session to a file
def appendSessionToFile(session, filename='complete_sessions.txt'):
    with open(filename, 'a') as file:
        file.write(f"{session.id},{session.startTime},{session.endTime},{session.entityId}\n")


# load all sessions from file
def loadSessionsFromFile(filename='complete_sessions.txt'):
    sessions = []
    with open(filename, 'r') as file:
        for line in file:
            id, startTime, endTime, entityId = line.strip().split(',')
            session = Session(int(id), datetime.fromisoformat(startTime), datetime.fromisoformat(endTime), int(entityId))
            sessions.append(session)
    return sessions
def saveSessionsToFile(sessions, filename='complete_sessions.txt'):
    with open(filename, 'w') as file:
        for session in sessions:
            file.write(f"{session.id},{session.startTime},{session.endTime},{session.entityId}\n")

# Function to append Started session to a file
def appendStartedSessionToFile(session, filename='started_sessions.txt'):
    with open(filename, 'a') as file:
        file.write(f"{session.id},{session.startTime},{session.endTime},{session.entityId}\n")
def loadStartedSessionsFromFile(filename='started_sessions.txt'):
    sessions = []
    with open(filename, 'r') as file:
        for line in file:
            id, startTime, endTime, entityId = line.strip().split(',')
            session = Session(int(id), datetime.fromisoformat(startTime), None, int(entityId))
            sessions.append(session)
    return sessions
def saveStartedSessionsToFile(sessions, filename='started_sessions.txt'):
    with open(filename, 'w') as file:
        for session in sessions:
            file.write(f"{session.id},{session.startTime},{session.endTime},{session.entityId}\n")

# Entity management functions
def appendEntityToFile(entity, filename='entities.txt'):
    with open(filename, 'a') as file:
        file.write(f"{entity.id},{entity.name},{entity.type},{entity.description}\n")
def loadEntitiesFromFile(filename='entities.txt'):
    entities = []
    with open(filename, 'r') as file:
        for line in file:
            id, name, type, description = line.strip().split(',')
            entity = Entity(int(id), name, type, description)
            entities.append(entity)
    return entities
def saveEntitesToFile(entities,filename='entities.txt'):
    with open(filename,'w') as file:
        for entity in entities:
            file.write(f"{entity.id},{entity.name},{entity.type},{entity.description}\n")


def startSession(entity):
    from datetime import datetime
    session = Session(id=len(loadStartedSessionsFromFile()) + 1, startTime=datetime.now(), endTime=None, entityId=entity.id)
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

    
    
    

   