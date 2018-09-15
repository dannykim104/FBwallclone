from flask import Flask, request, redirect, render_template, session, flash
from mysqlconnection import MySQLConnector
from datetime import datetime, timedelta
import os, binascii
import re 
import md5

DIG_REGEX = re.compile(r".*[0-9].*")
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$")

app = Flask(__name__)
app.secret_key="Keepthissecret"

mysql = MySQLConnector(app,'walldb')


@app.route('/')
def default():
    # Check if id is in session or not # 
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def validate():
    validate = True

    if valid:
        query = "SELECT id, password, salt FROM users WHERE email = :email"
        data = {"email": request.form["email"]}
        pw_info = mysql.query_db(query, data)
        if pw_info == []:
            flash("Email not registered!", "login")
            return redirect("/")
        elif md5.new(request.form["password"]+pw_info[0]["salt"]).hexdigest() == pw_info[0]["password"]:
            session["id"]=pw_info[0]["id"]
            flash("Successfully logged in!")
            return redirect("/thewall")
        else:
            flash("Email and password do not match!", "login")

    return redirect("/")



@app.route('/registration', methods=['POST'])
def valid():
    valid = True 
    if len(request.form['first_name']) < 1:
       flash("First name cannot be empty")
       valid = False 

    elif len(request.form['first_name']) < 2:
       flash("First name must be at least 2 chars")
       valid = False

    else:
        query = "SELECT email FROM users WHERE email = :email"
        data = {"email":request.form["email"]}
        if mysql.query_db(query, data) != []:
            flash("An account with that email is already registered!", "registration")
            valid = False

    if request.form["password"] != request.form["password_confirm"]:
        flash("Password confirmation must match password!", "registration")
        valid = False

    if valid:
        salt = binascii.b2a_hex(os.urandom(15))
        hashed_password = md5.new(request.form["password"] + salt).hexdigest()
        query = "INSERT INTO users (first_name, last_name, email, password, salt, created_at, updated_at) VALUES (:first_name, :last_name, :email, :password, :salt, NOW(), NOW())"
        data = {
            "first_name": request.form["first_name"],
            "last_name": request.form["last_name"],
            "email": request.form["email"],
            "password": hashed_password,
            "salt": salt
        }
        session["id"] = mysql.query_db(query, data)
        flash("Successfully registered and logged in!")
        return redirect("/thewall")
    else:
        return redirect("/")

    return redirect('/')


@app.route('/thewall')
def success():
    query = "SELECT first_name, last_name FROM users WHERE id = :id"
    data = {"id": session["id"]}
    namedic = mysql.query_db(query, data)
    name = namedic[0]["first_name"]+" "+namedic[0]["last_name"]
        # get name of logged in user for welcome

    # query for messages
    query = "SELECT users.id, users.first_name, users.last_name, posts.id as postid, posts.content, posts.created_at FROM users JOIN posts ON users.id = posts.users_id"
    posts = mysql.query_db(query)

    # query for comments
    query = "SELECT users.first_name, users.last_name, comments.content, comments.posts_id,comments.created_at FROM users JOIN comments ON users.id = comments.users_id"
    posts2 = mysql.query_db(query)

    return render_template("thewall.html", user=name, all_messages=posts, all_comments=posts2)



@app.route('/newpost', methods=['POST'])
def newmessage():
    query = "INSERT INTO posts (content, created_at, updated_at, users_id) VALUES (:content, NOW(), NOW(), :users_id)"
    data = {
        "users_id" : session["id"],
        "content" : request.form["message"]
    }
    mysql.query_db(query, data)
    return redirect("/thewall")

@app.route("/newcomment/<mesid>", methods=["POST"])
def newcomment(mesid):
    query = "INSERT INTO comments (posts_id, users_id, content, created_at, updated_at) VALUES (:posts_id, :users_id, :content, NOW(), NOW())"
    data = {
        "posts_id" : mesid,
        "users_id": session["id"],
        "content" : request.form["postid"]
    }
    mysql.query_db(query, data)
    return redirect("/thewall")

@app.route("/logout")
def logout():
    session.pop("id")
    return redirect("/")


app.run(debug=True)
