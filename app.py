
from flask import Flask,  render_template, url_for, request, g, redirect, session
from database import connect_to_database, getDatabase
from werkzeug.security import generate_password_hash, check_password_hash
import os



app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)# Also  note that when u want to hash a password or anything, u have to have a variable configured in ur system for that and thats what this line of code does
# This "app.config['SECRET_KEY'] = os.urandom(24)" generates a secret of 24 character

@app.teardown_appcontext
# This function is created to disconnect the database whenever a response-request cycle is completed or ended
def close_database(error):
    if hasattr(g, 'quizapp_db'):
        g.quizapp_db.close()


# this function fetches the current user of the application
def get_current_user(): # this function gives us the current user 
    user_result = None  # initially this is the state of the current user i.e no user
    # the "if 'user' in session: " checks if user is in session
    if 'user' in session: # session is used to persist information across multiple requests made by aa user when interacting with a web applicatiion
        # sessions are commonly used in web development to store user-specific data, such as login info, preferences, or other custom data, btw difft HTTP request
        user = session['user'] # we store the user in a variable user as seen in this line of code session['user']
        db = getDatabase() # we connect to the database
        user_cursor = db.execute("select * from users where name = ?", [user]) # This line of code checks if the user is already present in the database
        user_result = user_cursor.fetchone() # This gets the person or user with that specific name "name"
    return user_result


@app.route('/')
def index():
    user = get_current_user()
    db = getDatabase()

    questions_cursor = db.execute("select questions.id, questions.question_text, askers.name as asker_name, teachers.name as teacher_name from questions join users as askers on askers.id = questions.asked_by_id join users as teachers on teachers.id = questions.teacher_id where questions.answer_text is not null")
    question_result = questions_cursor.fetchall()
    return render_template('home.html', user=user, questions = question_result)


@app.route('/login', methods = ["POST", "GET"])
def login():
    user = get_current_user()
    error = None # This is the initial state b4 inputing ur details
    if request.method == "POST":
        db = getDatabase() # connecting to the database
        name = request.form['name'] # Geting the name from the form input box from the login page
        password = request.form['password'] # # Geting the password from the form input box login page 
        
        fetchedperson_cursor = db.execute("select * from users where name = ?", [name]) # fetching name(this name on line 44) of user 
        personfromdatabase = fetchedperson_cursor.fetchone() # the fetched persons details from database

        if personfromdatabase: # this means that this person's username exists in the database
            if check_password_hash(personfromdatabase['password'], password): # This is checking if the password entered on the login page is the as the one in the database i.e comparing line 45 and line 49
                session['user'] = personfromdatabase['name'] # This persist in the name in the web application so that all the other pages can get the current user whois using the current application 
                return redirect(url_for('index')) # This returns it to the homepage i.e function 'index' when the passwords are the same
            else:
                error = "Username or password did not match. Try again." # This will be the message rendered on the screen if the passwords do not match
                # return render_template('login.html', error = error) # Then this remains in the login page. U can also use the redirect function here
            
        else: 
            error = "Username or password did not match, Try again." # this is when the name entered in the username does not match
            # return redirect(url_for('login')) # This redirects to the login page

    return render_template('login.html', user=user, error = error)


@app.route('/register', methods = ["POST", "GET"])
def register():  # This function is for registering a user
    user = get_current_user()
    error = None
    if request.method == "POST": 
        db = getDatabase() # we have to get connected to the database
        name = request.form['name']  # Geting the name from the form input box from the register page
        password = request.form['password'] # Geting the password from the form input box from the register page

        # the line of code below checks if username already exist
        user_fetching_cursor = db.execute("select * from users where name = ?", [name]) # the name is the one entered by the user on the 4th line code
        existing_user = user_fetching_cursor.fetchone()

        if existing_user:
            error = "Username already taken, please choose a different username."
            return render_template("register.html", error = error)

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256') # this generates "#" passwords which makes the password in the backend database encoded
        db.execute("insert into users (name, password, teacher, admin) values (?,?,?,?)", 
        [name, hashed_password, '0', '0'])
        db.commit() # The registration ends here
        session['user'] = name # This name by the right hand side is the one typed by the user and also rept the current user of the app 

        return redirect(url_for('index'))  # This returns u back to the homepage when the user successfully registers.

    return render_template('register.html', user=user)


@app.route('/askquestions', methods = ["POST", "GET"])
def askquestions():
    user = get_current_user()
    db = getDatabase()
    # getting the question and teacher input from the form 
    if request.method == "POST":
        question = request.form['question']
        teacher = request.form['teacher']
        db.execute("insert into questions (question_text, asked_by_id, teacher_id) values (?,?,?)", [question, user['id'], teacher]) #here we get the questions column from the sqlite
        db.commit()
        return redirect(url_for('index'))
    # from here we down are getting the names of the teachers from the database table from the sqlite
    teacher_cursor = db.execute("select * from users where teacher = 1") # '*' is used to select all
    allteachers = teacher_cursor.fetchall() 

    return render_template("askquestions.html", user = user, allteachers = allteachers)

@app.route('/unansweredquestions')
def unansweredquestions():
    user = get_current_user()
    db = getDatabase()

    question_cursor = db.execute("select questions.id, questions.question_text, users.name from questions join users on users.id = questions.asked_by_id where questions.answer_text is null and questions.teacher_id = ?", [user['id']])
    allquestions = question_cursor.fetchall()
    return render_template("unansweredquestions.html", user = user, allquestions = allquestions )


@app.route('/answerquestion/<question_id>', methods = ["POST", "GET"])
def answerquestion(question_id):
    user = get_current_user()
    db = getDatabase()

    if request.method == "POST":
        db.execute('update questions set answer_text = ? where id = ?', [request.form['answer'], question_id])
        db.commit()
        return redirect('unansweredquestions')

    question_cursor = db.execute("select id, question_text from questions where id =?", [question_id])
    question = question_cursor.fetchone()
    return render_template("answerquestion.html", user = user, question = question)


@app.route('/allusers', methods = ["POST", "GET"])
def allusers(): 
    user = get_current_user() # calling the get_current_user function to get current user of the application
    db = getDatabase() # connecting to database
    user_cursor = db.execute("select * from users") # This selects from exixting users
    allusers = user_cursor.fetchall() # gets all users of the application
 
    return render_template('allusers.html', user = user, allusers = allusers)


@app.route('/promote/<int:id>', methods =  ["POST", "GET"]) # whenever u r passing any parameters from a link, u will use the GET method but when u r getting a parameter from a form,u use POST
def promote(id):
    user = get_current_user # getting the current user of the application
    if request.method == "GET": # we are passing parameters to a link
        db = getDatabase()
        db.execute("update users set teacher = 1 where id = ?", [id])
        db.commit()
        return redirect(url_for('allusers'))

    return render_template("allusers.html", user = user)


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug = True)
