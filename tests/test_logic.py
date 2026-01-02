import os
import tempfile
from datetime import datetime, timedelta

from logic import Session, appendSessionToFile, loadSessionsFromFile, appendStartedSessionToFile, loadStartedSessionsFromFile, GenerateReport, Entity


def test_load_sessions_skips_malformed(tmp_path):
    f = tmp_path / "complete_sessions.txt"
    # good row
    start = datetime.now() - timedelta(hours=1)
    end = datetime.now()
    good = f"1,{start.isoformat()},{end.isoformat()},10\n"
    bad = "malformed,line,that,should,be,skipped\n"
    f.write_text(good + bad, encoding='utf-8')

    sessions = loadSessionsFromFile(str(f))
    assert len(sessions) == 1
    s = sessions[0]
    assert s.id == 1
    assert s.entityId == 10


def test_append_and_load_started_sessions(tmp_path):
    f = tmp_path / "started_sessions.txt"
    start = datetime.now()
    session = Session(5, start, None, 2)
    appendStartedSessionToFile(session, filename=str(f))

    loaded = loadStartedSessionsFromFile(filename=str(f))
    assert len(loaded) == 1
    s = loaded[0]
    assert s.id == 5
    assert s.entityId == 2


def test_generate_report_aggregation(tmp_path):
    f = tmp_path / "complete_sessions.txt"
    # two sessions for entity 7
    s1 = Session(1, datetime(2020,1,1,9,0,0), datetime(2020,1,1,10,0,0), 7)
    s2 = Session(2, datetime(2020,1,2,9,0,0), datetime(2020,1,2,11,30,0), 7)
    appendSessionToFile(s1, filename=str(f))
    appendSessionToFile(s2, filename=str(f))

    entity = Entity(7, 'Test', 'Skill', 'desc')
    report = GenerateReport(entity, datetime(2020,1,1,0,0,0), datetime(2020,1,3,0,0,0))
    hours, minutes, seconds = report.totalTimeSpent
    # total = 1h + 2.5h = 3.5h = 3 hours 30 minutes
    assert hours == 3
    assert minutes == 30


def test_update_entity(tmp_path):
    # use entities file in tmp path
    f = tmp_path / "entities.txt"
    # write an entity row
    f.write_text("1,OldName,Skill,old desc\n", encoding='utf-8')
    from skilltrack.controller import update_entity
    from logic import loadEntitiesFromFile
    updated = update_entity(1, 'NewName', 'Project', 'new desc', filename=str(f))
    assert updated is True
    ents = loadEntitiesFromFile(filename=str(f))
    assert len(ents) == 1
    assert ents[0].name == 'NewName'

