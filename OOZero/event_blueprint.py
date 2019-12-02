from flask import Blueprint, render_template, abort, request, redirect, url_for, jsonify, session
import datetime

from OOZero.user_model import getUser
from OOZero.user_session import login_required, current_username
from OOZero.event_model import decrypt, getEventsByOwner, getEventById, createEvent, editEvent, removeEvent, EventType, getAllEvents

events = Blueprint('events', __name__, template_folder='templates')

def momentToPyDatetime(date):
    '''Parse datetime string from moment.js to datetime object'''
    return datetime.datetime.strptime(date, '%m/%d/%Y %H:%M %p')

def pyDatetimeToMoment(date):
    '''Format datetime object to moment.js string'''
    if date is None:
        return ""
    else:
        return datetime.datetime.strftime(date, '%m/%d/%Y %H:%M %p')

@login_required
def checkCachedEncrypted(event):
    if str(event.id) in session["Passes"]:
        value = decrypt(event.description, session["Passes"][str(event.id)])
        if value is None:
            del session['Passes'][str(event.id)]
            session.modified = True
            value = ""
        return value
    return ""

@events.route('/')
@login_required
def index():
    user = getUser(current_username())
    search = request.args.get('q')
    search = search if search else ''
    event_type = request.args.get('event_type')
    event_type = EventType(int(event_type)) if event_type else None
    return render_template('events.html', events=getEventsByOwner(user, search=search, event_type=event_type),
                           username=current_username, search=search, EventType=EventType, pyDatetimeToMoment=pyDatetimeToMoment, checkCachedEncrypted=checkCachedEncrypted)

@events.route('/create', methods=('POST', 'GET'))
@login_required
def create_or_edit():
    """Create or update an event. If id is passed as a a query parameter then update
       the event corresponding to that query parameter.
    """
    error = None
    if request.method == 'POST':
        id = request.form.get('id')
        id = int(id) if id else None
        # Edit or create the event based on whether we have an id and also
        # the type of event that we have.
        name = request.form.get('name')
        owner = getUser(current_username()).id
        event_type = EventType(int(request.form.get('event_type')))
        description = request.form['description']
        startTime = momentToPyDatetime(request.form['start_time']) if event_type == EventType.EVENT or event_type == EventType.REMINDER else None
        endTime = momentToPyDatetime(request.form['end_time']) if event_type == EventType.EVENT else None
        password = request.form['event_password'] if event_type == event_type.ENCRYPTED else None
        
        if id:
            editEvent(id, name=name, owner=owner, event_type=event_type, description=description, start_time=startTime, end_time=endTime, password=password)
        else:
            createEvent(name=name, owner=owner, event_type=event_type, description=description, start_time=startTime, end_time=endTime, password=password)
        return redirect(url_for('events.index'))

    # Get an event if we are editing an event
    id = request.args.get('id')
    event = None
    if id:
        event = getEventById(int(id))
        if event.event_type == EventType.ENCRYPTED and not checkCachedEncrypted(event):
            #If this encrypted event hasn't had its password entered already, then send back to event page
            return redirect(url_for('events.index'))

    return render_template('events_create.html', event=event,
                           username=current_username(), EventType=EventType,
                           error=error, checkCachedEncrypted=checkCachedEncrypted)


@events.route('/remove/<int:id>', methods=('POST',))
@login_required
def remove(id):
    """Remove an event with this id.
    """
    removeEvent(id)
    return redirect(url_for('events.index'))

@events.route('decryptReq/<int:id>', methods=('POST',))
@login_required
def decryptReq(id):
    """Checks ownership and uses provided password to decrypt message
    """
    event = getEventById(id)
    if not event is None and event.owner.username == current_username() and not request.form['event_password'] is None:
        description = decrypt(event.description, request.form['event_password'])
        res = {}
        res["sucess"] = not description is None
        if res["sucess"]:
            session['Passes'][str(id)] = request.form['event_password']
            session.modified = True
            res['data'] = description
        return jsonify(res)

@events.route('reEncryptReq/<int:id>', methods=('POST',))
@login_required
def reEncryptReq(id):
    """Checks ownership and removes encryption key from session
    """
    event = getEventById(id)
    if not event is None and event.owner.username == current_username():
        del session["Passes"][str(id)]
        session.modified = True
        return ""
