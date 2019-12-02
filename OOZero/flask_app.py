from OOZero import create_app
from flask import Flask, render_template, request, redirect, url_for, session, flash
from OOZero.user_model import authenticateUser, addUser, hashPassword, getUser, editUser
from OOZero.user_session import login_required, user_login, user_logout
from OOZero.event_blueprint import events

app = create_app()
app.register_blueprint(events, url_prefix='/events')


@app.route('/')
#@login_required
def home():
    try:
        if session['username']:
            return render_template('home.html', username=session['username'])
        return render_template('home.html')
    except:
        session['username'] = None
        return render_template('home.html')


@app.route('/login/', methods=['POST', 'GET'])
def login():
    error = None
    if request.method == 'POST':
        # Authenticate the given user with this username and password
        username = request.form['username']
        password = request.form['password']
        user = authenticateUser(username, password)
        if user:
            user_login(user)
            session['username'] = username
            return redirect(url_for('home'))
        else:
            error = 'Incorrect username or password entered.'

    return render_template('login.html', error=error)

@app.route('/signup/', methods=['POST', 'GET'])
def signup():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        name = request.form['name']

        # Need to check if username is already taken here
        check = getUser(username) is not None
        if check:
            error = 'Username already taken.'
        else:
            try:
                addUser(username=username, password=password, name=name, email=email)
                session['username'] = username
                return redirect('/')
            except (ValueError, TypeError) as e:
                error = str(e)
    return render_template('signup.html', error=error)

@app.route('/manage_user/', methods=['POST', 'GET'])
@login_required
def manage_user():
    error = None
    user=getUser(session["username"])
    if request.method == 'POST':
        username, email, name, newPassword = (None,)*4

        if hashPassword(request.form['currentPassword'], user.salt) != user.password_hash:
            error = 'Password is incorrect.'
        if not request.form['username'] is None and request.form['username'] != '' and request.form['username'] != user.username:
            if getUser(request.form['username']) is not None:
                error = 'Username already taken.'
            username = request.form['username']
        if request.form['email'] != '' and request.form['email'] != user.email:
            email = request.form['email']
        if request.form['name'] != '' and request.form['name'] != user.name:
            name = request.form['name']
        if request.form['newPassword'] != '':
            if len(request.form['newPassword']) < 4:
                error = "Password must be at least 4 charactors"
            newPassword = request.form['newPassword']

        if error is None:
            user = editUser(user, username=username, password=newPassword, name=name, email=email)
            session['username'] = user.username
    return render_template('manage_user.html', error=error, user=user, username=user.username) #Redudent username is required for template to know user is logged in

@app.route('/logout/', methods=['POST', 'GET'])
def logout():
    session['username'] = None
    user_logout()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run()
