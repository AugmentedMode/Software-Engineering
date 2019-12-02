from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from OOZero.model import db
import OOZero.user_model as user
import enum
import secrets
import datetime
import json
from cryptography.fernet import Fernet, InvalidToken
import hashlib
import base64

class EventType(enum.Enum):
    """Marks the type of the event and the attributes it can be expected to have
    Note: No times
    EVENT: Start and End dates, has duration
    REMINDER: Has only start time, is an instantaneous event
    ENCRYPTED: Like note, has no times. Discripion is encrypted with a password seperate from the user's password
    """
    NOTE = 1
    EVENT = 2
    REMINDER = 3
    ENCRYPTED = 4

class Page(db.Model):
    __tablename__ = 'page'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=False, nullable=False)
    owner = db.relationship("User", foreign_keys=[owner_id], backref=db.backref("pages", uselist=True), uselist=False)
    name = db.Column(db.String(60), unique=False, nullable=False)
    description = db.Column(db.Text, unique=False, nullable=True)

class Event(db.Model):
    __tablename__ = 'event'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=False, nullable=False)
    owner = db.relationship("User", foreign_keys=[owner_id], backref=db.backref("events", uselist=True), uselist=False)
    name = db.Column(db.String(60), unique=False, nullable=False)
    description = db.Column(db.Text, unique=False, nullable=True)
    timestamp = db.Column(db.DateTime, unique=False, nullable=False, default=datetime.datetime.utcnow)
    start_time = db.Column(db.DateTime, unique=False, nullable=True)
    end_time = db.Column(db.DateTime, unique=False, nullable=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("event.id"), unique=False, nullable=True)
    parent = db.relationship("Event", remote_side=[id], backref=db.backref("children", uselist=True), uselist=False)
    event_type = db.Column(db.Enum(EventType), unique=False, nullable=False)
    page_id = db.Column(db.Integer, db.ForeignKey("page.id"), unique=False, nullable=True)
    page = db.relationship("Page", backref=db.backref("events", uselist=True), foreign_keys=[page_id], uselist=False)
    position_x = db.Column(db.Integer, unique=False, nullable=True)
    position_y = db.Column(db.Integer, unique=False, nullable=True)

    def __repr__(self):
        return str(self.id) + ', ' + str(self.name) + ', ' + str(self.owner_id) + ', ' + str(self.description)  + ', ' + str(self.timestamp)  + "\n" 

def createPage(name, owner, description=None):
    """Creates a page and returns it

    Args:
        name (str): 0 < length <= 60, title of page
        owner (int | User): id of user or User who this event belongs to
    Kwargs:
        description (str, Optional): Extra text about the page

    Returns:
        (Page): newly created page
    """
    if len(name) <= 0 or len(name) > 60:
        raise ValueError("Events page name of ilegal length")
    if type(owner) == user.User:
        owner = owner.id
    db.session.add(Page(name=name, owner_id=owner, description=description))
    db.session.commit()
    return Page.query.filter_by(name=name, owner_id=owner, description=description).first()

def getPageById(page):
    """Gets a page by id

    Args:
        page (int): page id

    Returns:
        (Page | None): the page or None if the page doesn't exist
    """
    return Page.query.filter_by(id=page).first()

def getPagesByOwner(owner):
    """Gets a list of pages by owner

    Args:
        owner (User | Int): owner User object or id

    Returns:
        ([Page]): the pages
    """
    if type(owner) == int:
        owner = user.getUser(owner)
    return owner.pages

def deletePage(page, cascadeEvents=True):
    """Deletes a page

    Args:
        page (Page | int): Page object or id of page to delete
        cascadeEvents (bool, Optional): delete all events belonging to this page, defaults to true
    """
    if type(page) == int:
        page = getPageById(page)
    if cascadeEvents:
        for event in page.events:
            removeEvent(event)
    db.session.delete(page)
    db.session.commit()

def editPage(page, owner=None, name=None, discription=None):
    """Edits a page

    Args:
        page (int | Page): id of page or Page to edit
    Kwargs:
        name (str, Optional): 0 < length <= 60, title of page
        owner (User | int, Optional): new owner
        description (str, Optional): Extra text about the page
    """
    if type(page) == int:
        page = getPageById(page)
    if not name is None:
        page.name = name
    if not owner is None:
        if type(owner) == user.User:
            owner = owner.id
        page.owner_id = owner
    if not discription is None:
        page.discription = discription
    db.session.commit()
    return getPageById(page.id)
    

def getPageEvents(page):
    """Get all of the events belonging to a page

    Args:
        page (int | Page): id of page or Page to get events of

    Returns:
        list of events
    """
    if type(page) == int:
        page = getPageById(page)
    return page.events

def generateKey(value):
    """Generates a 256 bit encryption key off of the given string

    Args:
        value (str): string to derive key from

    Returns:
        (base64): 256 bit base64 string encryption key
    """
    hashFunct = hashlib.sha3_256()
    hashFunct.update(value.encode('utf-8'))
    return base64.urlsafe_b64encode(hashFunct.digest())

def encrypt(value, key):
    """Encryptes the value based on the key

    Args:
        value (str): value to encrypt
        key (str): password to generate key from

    Returns:
        (base64): base64 string of ciphertext
    """
    encryptionSuite = Fernet(generateKey(key))
    return encryptionSuite.encrypt(value.encode())

def decrypt(value, key):
    """Atempts to decrypt the value based on the key

    Args:
        value (base64): base64 string of ciphertext
        key (str): password to generate key from

    Returns:
        (str): plain text if successful
        (None): None if unsucessful
    """
    encryptionSuite = Fernet(generateKey(key))
    try:
        return encryptionSuite.decrypt(value).decode('utf-8')
    except InvalidToken:
        return None

def checkEventAttributes(event):
    """Checks the values of event attributes to ensure they are valid
    """
    if event.name is None or 60 < len(event.name) or len(event.name) <= 0:
        raise ValueError("Name length out of range")
    if event.owner_id is None:
        raise ValueError("Must have a valid owner")
    if not type(event.event_type) is EventType:
        raise ValueError("Must have a valid event type")
    
    if (event.event_type == EventType.NOTE or event.event_type == EventType.ENCRYPTED) and (not event.start_time is None or not event.end_time is None):
        raise ValueError("Note / encrypted note types do not have start or end times")
    elif event.event_type == EventType.REMINDER and (event.start_time is None or not event.end_time is None):
        raise ValueError("Reminder types have a start time and no end times")
    elif event.event_type == EventType.EVENT and (event.start_time is None or event.end_time is None):
        raise ValueError("Event types have start and end times")

    return True

def createEvent(name, owner, event_type, description=None, start_time=None, end_time=None, parent=None, password=None, page=None, position_x=None, position_y=None):
    """Creates an event, addes it to the database, and returns it

    Args:
        name (str): 0 < length <= 60, title of event, is not encrypted for encrypted notes
        owner (int): id of user who this event belongs to
        event_type (EventType): type of this event, refer to EventType for more infomation
    Kwargs:
        description (str, Optional): Extra text about the event, is encrypted and required for encrypted notes
        start_time (datetime, Optional): Start time of event, only used in some EventTypes
        end_time (datetime, Optional): End time of event, only used in some EventTypes
        parent (int, Optional): id of event this is a child of if any
        password (str): Used only on enrypted EventType, required in this case. Used to encrypt discription
        page (Page | int, Optional): Page this event belongs to
        position_x (int, Optional): used to determin where event is placed when displaying a Page
        position_y (int, Optional): used to determin where event is placed when displaying a Page

    Returns:
        (Event): newly created event
    """
    if not parent is None and Event.query.filter_by(id=parent).first() is None:
        raise ValueError("Parent, if used, must be a valid event")
    if event_type == EventType.ENCRYPTED:
        if description is None:
            raise TypeError("Encrypted notes must have a discription")
        if password is None:
            raise TypeError("Encrypted notes must have a password")
    elif not password is None:
        raise TypeError("Only encrypted notes can have a password")
    if type(owner) == user.User:
        owner = owner.id
    elif type(owner) != int:
        raise TypeError("Owner must be a user id or a User")
    if type(page) == Page:
        page = page.id

    if event_type == EventType.ENCRYPTED:
        description = encrypt(description, password)

    newEvent = Event(owner_id=owner, name=name, event_type=event_type, description=description, start_time=start_time, end_time=end_time, parent_id=parent, page_id=page, position_x=position_x, position_y=position_y)    
    if checkEventAttributes(newEvent):
        db.session.add(newEvent)
        db.session.commit()
        return Event.query.filter_by(owner_id=owner, name=name, event_type=event_type, description=description, start_time=start_time, end_time=end_time, parent_id=parent, page_id=page, position_x=position_x, position_y=position_y).first()

def removeEvent(event):
    """Removes event from database, if event doesn't exist don't do anything. Also delete child events

    Args:
        event (int | User): Removes event by id or event object
    """
    if type(event) == int:
        event = Event.query.filter_by(id=event).first()
    elif type(event) != Event:
        raise TypeError("Event was not an int or Event")
    if event is None:
        return
    for child in Event.query.filter_by(parent_id=event.id):
        removeEvent(child)
    db.session.delete(event)
    db.session.commit()

def getEventById(id):
    """Get single event by id
    """
    return Event.query.filter_by(id=id).first()

def getEventsByOwner(owner, search=None, event_type=None):
    """Get list of events by their owner
    Args:
        owner (int | User): User object or user id
        search (str): Search string to limit results
        event_type (EventType): Event type to further limit results
    """
    if type(owner) is user.User:
        owner = owner.id
    events = Event.query.filter_by(owner_id=owner)
    if search:
        search = '%' + search + '%'
        events = events.filter(Event.name.like(search)
                               | Event.description.like(search))
    # Sort by event
    if event_type:
        events = events.filter_by(event_type=event_type)
    return events.all()

def editEvent(event, name=None, owner=None, event_type=None, description=None, start_time=None, end_time=None, password=None, page=None, position_x=None, position_y=None):
    """Modifies an event, and returns it

    Args:
        event (int | Event): id of event or Event object to modify

    Kwargs:
        name (str, Optional): 0 < length <= 60, title of event, is not encrypted for encrypted notes
        owner (int, Optional): id of user who this event belongs to
        event_type (EventType, Optional): type of this event, refer to EventType for more infomation
        description (str, Optional): Extra text about the event, is encrypted and required for encrypted notes
        start_time (datetime, Optional): Start time of event, only used in some EventTypes
        end_time (datetime, Optional): End time of event, only used in some EventTypes
        parent (int, Optional): id of event this is a child of if any
        password (str, Optional): Used only on enrypted EventType, required in this case. Used to encrypt discription

    Returns:
        (Event): the newly modifed event
    """
    if type(event) is int:
        event = getEventById(event)
    if not name is None:
        event.name = name
    if not owner is None:
        event.owner_id = owner
    if not event_type is None:
        event.event_type = event_type
    if not start_time is None:
        event.start_time = start_time
    if not end_time is None:
        event.end_time = end_time
    if not position_x is None:
        event.position_x = position_x
    if not position_y is None:
        event.position_y = position_y
    if not page is None:
        event.page = page
    if not description is None:
        if event.event_type is EventType.ENCRYPTED:
            if password is None:
                raise TypeError("Changing the discription on an encrypted note requires a password")
            event.description = encrypt(description, password)
        else:
            event.description = description

    try:
        checkEventAttributes(event)
        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        raise e
    return getEventById(event.id)

def removeEventFromPage(event):
    """Removes an event from the page its on if any

    Args:
        event (int | Event): id of event or Event object to remove from its page

    Returns:
        (Event): the newly modifed event
    """
    if type(event) == int:
        event = Event.query.filter_by(id=event).first()
    event.page_id = None
    db.session.commit()
    return getEventById(event.id)

def getAllEvents(search):
    """Returns a list of all events
    Args:
        search (str, Optional): return events that contain this string in their name or discription
    """
    search = '%' + search + '%'
    return Event.query.filter(Event.name.like(search) | Event.description.like(search)).all()
