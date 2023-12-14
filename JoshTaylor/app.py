import os

from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
from datetime import datetime
from functools import wraps

secret = os.urandom(12)
app = Flask(__name__)

app.secret_key = secret
app.config["SESSION_PERMANENT"] = False

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def index():
    blog_entries = []
    blogs = fetch_blogs()
    for blog in blogs:
        blog_entries.append({"content": blog[0], "date": blog[1], "title": blog[2]})

    return render_template("index.html", blog_entries=blog_entries)

@app.route("/about")
def about():
    return render_template("about.html")

def fetch_blogs():
    db = sqlite3.connect("blogs.db")
    cursor = db.cursor()
    cursor.execute("select blog, datetime, title from blogs order by id desc;")
    blogs = cursor.fetchall()
    db.close()
    return blogs

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        if not request.form.get('username'):
            return redirect('/')

        if not request.form.get('password'):
            return redirect('/')
        if check_user():
            return redirect('/create')
        return redirect('/')

    else:
        return render_template("login.html")
    
@app.route("/create", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        print('test1really')
        create_post()
        return redirect('/')
    else:
        return render_template('create.html')


def check_user():
    db = sqlite3.connect('blogs.db')
    cursor = db.cursor()
    cursor.execute("select username from 'users';")
    user = cursor.fetchall()[0][0]
    if user != request.form.get('username'):
        db.close()
        print('not in users')
        return False
    
    cursor.execute('select hash from users where username= ?;', (request.form.get('username'),))
    hash = cursor.fetchall()[0][0]

    if check_password_hash(hash, request.form.get('password')):
        session["user_id"] = request.form.get('username')
        db.close()
        return True
    else: 
        print('password wrong')
        db.close()
        return False;

def create_post():
    db = sqlite3.connect("blogs.db")
    cursor = db.cursor()
    if not request.form.get("title"):
        db.close()
        print('test1')
        return redirect('/')
    if not request.form.get("content"):
        print('test2')
        db.close()
        return redirect('/')
    print('if those work...')
    print(request.form.get('content'))
    cursor.execute("insert into blogs(title, blog) values(?, ?);", (request.form.get('title'), request.form.get('content')))
    db.commit()
    db.close()
    print('success??')
    return redirect('/')
    