from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from OOZero.model import db
import OOZero.event_model as event
import hashlib
import secrets
import datetime
import struct

#Expiration of the remember user cookie
MAX_LENGTH_DAYS = 30

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    name = db.Column(db.String(60), unique=False, nullable=True)
    email = db.Column(db.String(60), unique=False, nullable=True)
    password_hash = db.Column(db.String(129), unique=False, nullable=False)
    salt = db.Column(db.String(128), unique=False, nullable=False)
    profile_picture = db.Column(db.LargeBinary, nullable=True)

    def __repr__(self):
        return str(self.id) + ', ' + str(self.username) + ', ' + str(self.name) + ', ' + str(self.email)  + ', ' + str(self.password_hash)  + ', ' + str(self.salt) + "\n"

class RememberUser(db.Model):
    __tablename__="remember_user"
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=False, nullable=False)
    user = db.relationship("User", backref=db.backref("user"), foreign_keys=[user_id], uselist=False)
    timestamp = db.Column(db.DateTime, unique=False, nullable=False, default=datetime.datetime.utcnow)
    cookie = db.Column(db.String(129), unique=False, nullable=False, primary_key=True)

def addRemember(user):
    """For the given user generate an entry in the RememberUser table and return a cookie that can be used to log the user in

    Args:
        user (User | int): User by id or User object

    Returns:
        (str): 128 byte hex hash to be used as temporary authentication token
    """
    if type(user) == User:
        user = user.id
    hashFunct = hashlib.sha3_512()
    token = None
    while True:
        hashFunct.update(struct.pack("d", secrets.SystemRandom().random()))
        token = hashFunct.hexdigest()
        if RememberUser.query.filter_by(cookie=token).first() == None:
            break
    db.session.add(RememberUser(user_id=user, cookie=token))
    db.session.commit()
    return token

def checkRemember(cookie):
    """For the given temporary authentication token find a matching entry that hasn't expired, if sucessful return the User

    Args:
        cookie (str): temporary authentication token from client cookie

    Returns:
        (User | None): The user or None if no valid entry is found
    """
    oldEntries = RememberUser.query.filter(RememberUser.timestamp < datetime.datetime.utcnow() - datetime.timedelta(days=MAX_LENGTH_DAYS)).all()
    for entry in oldEntries:
        db.session.delete(entry)
        db.session.commit()
    entry = RememberUser.query.filter_by(cookie=cookie).first()
    if entry is None:
        return None
    else:
        return entry.user

def hashPassword(password, salt):
    """Generates hash from given salt and password

    Args:
        password (str): password
        salt (str): 128 byte hex string

    Returns:
        (str): 128 byte hex hash
    """
    hashFunct = hashlib.sha3_512()
    hashFunct.update(password.encode('utf-8'))
    hashFunct.update(salt.encode('utf-8'))
    return hashFunct.hexdigest()

def getUser(user):
    """Gets user from database

    Args:
        user (str | int): Finds user by id or username

    Returns:
        on sucess - User: populated with the users infomation
        on failure - None: Null
    """
    if type(user) == str:
        return User.query.filter_by(username=user).first()
    elif type(user) == int:
        return User.query.filter_by(id=user).first()
    else:
        raise TypeError("User was not a string or int")

def addUser(username, password, name=None, email=None, profile_picture=None):
    """Make sure user parameters a valid and commit to database

    Args:
        username (str): must be unique, min length 1, max length 30
        password (str): password, min length 4

    Kwargs:
        name (str, optional): name of user, no criteria for format, max length 60
        email (str, optional): email of user, max length 60
        profile_picture (bytes, optioanl): to be determined

    Returns:
        on sucess - User: populated with the users infomation
        on failure - None: Null

    Raises:
        TypeError: If any required param is null
        ValueError: If any param out of expected range or username is not unique
    """
    if len(username) > 30 or len(username) < 1:
        raise ValueError("Username length out of range")
    if len(password) < 4:
        raise ValueError("Password too short")
    if not name is None and len(name) > 60:
        raise ValueError("Name too long")
    if not email is None and len(email) > 60:
        raise ValueError("Email too long")
    duplicateUser = getUser(username)
    if not duplicateUser is None:
        raise ValueError("Username alreay exists")
    salt = secrets.token_hex(64)
    db.session.add(User(username=username, name=name, email=email, password_hash = hashPassword(password, salt), salt=salt, profile_picture=profile_picture))
    db.session.commit()
    return getUser(username)


def authenticateUser(username, password):
    """Finds user with username and checks if hashed and salted password matches hash

    Args:
        username (str): username to search for. len < 30
        password (str): password to check

    Returns:
        on sucess - User: populated with the users infomation
        on failure - None: user doesn't exist or password is incorrect
    """
    challengedUser = getUser(username)
    if not challengedUser is None and hashPassword(password, challengedUser.salt) == challengedUser.password_hash:
        return challengedUser
    return None

def removeUser(user):
    """Removes user from database, if user doesn't exist don't do anything

    Args:
        user (str | int | User): Removes user by id, username, or User object
    """
    if type(user) == str:
        user = User.query.filter_by(username=user).first()
    elif type(user) == int:
        user = User.query.filter_by(id=user).first()
    elif type(user) != User:
        raise TypeError("User was not a string, int or User")
    if user is None:
        return
    event.Event.query.filter_by(owner_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()

def editUser(user, username=None, password=None, name=None, email=None, profile_picture=None):
    """Make sure user parameters are valid, modify, and commit to database

    Args:
        user (int, User): user id or User object

    Kwargs:
        username (str, optional): must be unique, min length 1, max length 30
        password (str, optional): password, min length 4
        name (str, optional): name of user, no criteria for format, max length 60
        email (str, optional): email of user, max length 60
        profile_picture (bytes, optioanl): to be determined

    Returns:
        The newly modifed user

    Raises:
        TypeError: If any required param is null
        ValueError: If any param out of expected range or username is not unique
    """
    if type(user) == int:
        user = getUser(user)
    try:
        if username is not None:
            if len(username) > 30 or len(username) < 1:
                raise ValueError("Username length out of range")
            elif not getUser(username) is None:
                raise ValueError("Username alreay exists")
            else:
                user.username = username
        if password is not None:
            if len(password) < 4:
                raise ValueError("Password too short")
            else:
                user.salt = secrets.token_hex(64)
                user.password_hash = hashPassword(password, user.salt)
        if not name is None:
            if len(name) > 60:
                raise ValueError("Name too long")
            else:
                user.name = name
        if not email is None:
            if len(email) > 60:
                raise ValueError("Email too long")
            else:
                user.email = email
        if not profile_picture is None:
            user.profile_picture = profile_picture
        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        raise e

    return getUser(user.id)