import os
from tempfile import NamedTemporaryFile
from logic import create_user, authenticate_user, loadUsersFromFile


def test_create_and_authenticate_user(tmp_path):
    fn = tmp_path / "users.txt"
    # create new user
    assert create_user('alice', 'secr3t', filename=str(fn)) is True
    # duplicate create should fail
    assert create_user('alice', 'other', filename=str(fn)) is False
    # authenticate correct password
    assert authenticate_user('alice', 'secr3t', filename=str(fn)) is True
    # wrong password fails
    assert authenticate_user('alice', 'wrong', filename=str(fn)) is False
    # unknown user fails
    assert authenticate_user('bob', 'whatever', filename=str(fn)) is False


def test_users_file_format(tmp_path):
    fn = tmp_path / "users.txt"
    create_user('carol', 'mypwd', filename=str(fn))
    users = loadUsersFromFile(filename=str(fn))
    assert 'carol' in users
    u = users['carol']
    assert u.username == 'carol'
    assert u.salt and u.pwdhash and u.iterations
