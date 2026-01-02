import os
import time
import shutil
from pathlib import Path
import logic
import skilltrack.controller as controller


def test_per_user_files(tmp_path, monkeypatch):
    # use tmp dir as working dir so files are isolated
    monkeypatch.chdir(tmp_path)

    # create two users
    assert logic.create_user('alice', 'pw1', filename='users.txt') is True
    assert logic.create_user('bob', 'pw2', filename='users.txt') is True

    # login as alice
    controller._current_user = 'alice'

    # alice creates an entity and starts a session
    e = controller.create_entity('Study', 'Skill', 'Test')
    assert e.id == 1
    started = controller.start_entity_session(e)
    assert started is not None

    # files for alice should exist under data/alice
    assert Path('data/alice/entities.txt').exists()
    assert Path('data/alice/started_sessions.txt').exists()

    # bob should have no files yet
    assert not Path('data/bob/entities.txt').exists()
    assert not Path('data/bob/started_sessions.txt').exists()

    # stop alice's session
    ended = controller.stop_session(started)
    assert ended is not None
    assert Path('data/alice/complete_sessions.txt').exists()

    # now login as bob and ensure his lists are empty
    controller._current_user = 'bob'
    ents = controller.get_entities()
    assert len(ents) == 0

    # create an entity for bob
    be = controller.create_entity('Work', 'Project', 'Bob project')
    assert be.id == 1
    assert Path('data/bob/entities.txt').exists()

    # ensure alice files still present and unchanged
    assert Path('data/alice/entities.txt').exists()
    assert Path('data/alice/complete_sessions.txt').exists()
