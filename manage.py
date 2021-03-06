﻿#!flask/bin/python
"""
Author: StackFocus
File: manage.py
Purpose: Manages the app
"""

import os
import fileinput
import flask_migrate
from re import sub
from flask_script import Manager
from postmaster import app, db, models
from postmaster.utils import add_default_configuration_settings, clear_lockout_fields_on_user, reset_admin_password

migrate = flask_migrate.Migrate(app, db)

manager = Manager(app)
manager.add_command('db', flask_migrate.MigrateCommand)


@manager.command
def upgradedb():
    """Upgrades the existing database to the latest schema and adds the
    default configuration items if they are missing"""
    alembic_version_table_exists = db.engine.dialect.has_table(db.session.connection(), 'alembic_version')

    if not alembic_version_table_exists:
        virtual_domains_table_exists = db.engine.dialect.has_table(db.session.connection(), 'virtual_domains')
        virtual_users_table_exists = db.engine.dialect.has_table(db.session.connection(), 'virtual_users')
        virtual_aliases_table_exists = db.engine.dialect.has_table(db.session.connection(), 'virtual_aliases')

        # If the alembic_version table doesn't exist and the virtual_* tables exist, that means the database is
        # in the default state after following the mail server guide on Linode or DigitalOcean.
        if virtual_domains_table_exists and virtual_users_table_exists and virtual_aliases_table_exists:
            # This marks the first revision as complete, which is the revision that creates the virtual_* tables
            flask_migrate.stamp(revision='bcc85aaa7896')

    flask_migrate.upgrade()
    add_default_configuration_settings()


@manager.shell
def make_shell_context():
    """Returns app, db, models to the shell"""
    return dict(app=app, db=db, models=models)


@manager.command
def clean():
    """Cleans the codebase, including database migration scripts"""
    if os.name == 'nt':
        commands = ["powershell.exe -Command \"@('*.pyc', '*.pyo', '*~', '__pycache__') |  Foreach-Object { Get-ChildItem -Filter $_ -Recurse | Remove-Item -Recurse -Force }\"",  # pylint: disable=anomalous-backslash-in-string, line-too-long
                    "powershell.exe -Command \"@('postmaster.log') |  Foreach-Object { Get-ChildItem -Filter $_ | Remove-Item -Recurse -Force }\""]  # pylint: disable=anomalous-backslash-in-string, line-too-long
    else:
        commands = ["find . -name '*.pyc' -exec rm -f {} \;",  # pylint: disable=anomalous-backslash-in-string
                    "find . -name '*.pyo' -exec rm -f {} \;",  # pylint: disable=anomalous-backslash-in-string
                    "find . -name '*~' -exec rm -f {} \;",  # pylint: disable=anomalous-backslash-in-string
                    "find . -name '__pycache__' -exec rmdir {} \;",  # pylint: disable=anomalous-backslash-in-string
                    "rm -f postmaster.log"]
    for command in commands:
        os.system(command)


@manager.command
def generatekey():
    """Replaces the SECRET_KEY in config.py with a new random one"""
    for line in fileinput.input('config.py', inplace=True):
        print(sub(r'(?<=SECRET_KEY = \')(.+)(?=\')', os.urandom(24).encode('hex'), line.rstrip()))


@manager.command
def setdburi(uri):
    """Replaces the BaseConfiguration SQLALCHEMY_DATABASE_URI in config.py with one supplied"""
    base_config_set = False
    for line in fileinput.input('config.py', inplace=True, backup='.bak'):
        if not base_config_set and 'SQLALCHEMY_DATABASE_URI' in line:
            print(sub(r'(?<=SQLALCHEMY_DATABASE_URI = \')(.+)(?=\')', uri, line.rstrip()))
            base_config_set = True
        else:
            print(line.rstrip())


@manager.command
def setlogfile(filepath):
    """Replaces the BaseConfiguration LOG_LOCATION in config.py with one supplied"""
    base_config_set = False
    for line in fileinput.input('config.py', inplace=True, backup='.bak'):
        if not base_config_set and 'LOG_LOCATION' in line:
            print(sub(r'(?<=LOG_LOCATION = \')(.+)(?=\')', filepath, line.rstrip()))
            base_config_set = True
        else:
            print(line.rstrip())


@manager.command
def unlockadmin(username):
    """Unlocks a locked out administrator"""
    clear_lockout_fields_on_user(username)


@manager.command
def resetadminpassword(username, new_password):
    """Resets an administrator's password with one supplied"""
    reset_admin_password(username, new_password)


if __name__ == "__main__":
    manager.run()
