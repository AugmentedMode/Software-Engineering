from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from OOZero.model import db
import OOZero.event_model as event
import OOZero.user_model as user
import OOZero.group_model as group

class SharedEventUser(db.Model):
    __tablename__ = "shared_event_user"
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), primary_key=True, unique=False)
    event = db.relationship("Event", foreign_keys=[event_id], backref=db.backref("shared_events_user", uselist=True), uselist=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True, unique=False)
    user = db.relationship("User", foreign_keys=[user_id], backref=db.backref("shared_events", uselist=True), uselist=False)
    write = db.Column(db.Boolean, unique=False, nullable=False)

class SharedEventGroup(db.Model):
    __tablename__ = "shared_event_group"
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), primary_key=True, unique=False)
    event = db.relationship("Event", foreign_keys=[event_id], backref=db.backref("shared_events_group", uselist=True), uselist=False)
    group_id = db.Column(db.Integer, db.ForeignKey("group.id"), primary_key=True, unique=False)
    group = db.relationship("Group", foreign_keys=[group_id], backref=db.backref("shared_events", uselist=True), uselist=False)
    write = db.Column(db.Boolean, unique=False, nullable=False)