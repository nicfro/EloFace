from flask import Flask, flash, redirect, render_template, request, session, abort, Response
import os
import json
from validate_email import validate_email
from databaseScripts import connect, getRandomImages, getContesters, reportImage, ratePictures, userLogin, userExists, CreateNewUser
from datetime import datetime

app = Flask(__name__)
cursor = connect()

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    if userLogin(username, password):
        session['logged_in'] = True
        session['username'] = request.form['username']
        return Response(home(),mimetype = "text/html")
    else:
        errors = {}
        errors["fault"] = "Username or password does not match"
        json_data = json.dumps(errors)
        return Response(json_data ,mimetype = "application/json")

@app.route("/logout")
def logout():
    session['logged_in'] = False
    return home()

@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        username = session.get('username')
        images = list(getContesters(username, "female"))
        images = ["https://s3-eu-west-1.amazonaws.com/ratemegirl/"+s for s in images]
        return render_template('home.html', images=images)

@app.route('/vote', methods = ['POST'])
def vote():
    choice = request.form['choice']
    pic1 = request.form['pic1'][46:]
    pic2 = request.form['pic2'][46:]
    username = session.get('username')
    ratePictures(username, pic1, pic2, choice)
    return redirect('/')

@app.route('/report', methods = ['POST'])
def report():
    imagePath = request.form['CastReport'][46:]
    username = session.get('username')
    reportImage(username, imagePath)
    return redirect('/')

@app.route('/about/')
def about():
	return render_template('about.html')

@app.route('/newUser/')
def newUser():
    return render_template('newUser.html')

@app.route('/createNewUser', methods = ['POST'])
def createNewUser():
    username = request.form['username']
    password = request.form['password']
    country = request.form['country']
    email = request.form['email']
    gender = request.form['gender']
    bday = request.form['bday']

    print(username, password, country, email, gender, bday)
    errors = {}
    
    try:
        bday = datetime.strptime(bday, "%Y-%m-%d")
    except:
        errors["bday"] = "Please enter your birthday"

    if username.isalnum() != True:
        errors["usernameAlphanumeric"] = "Username can only contain alphanumeric characters"
    if userExists(username):
        errors["usernameExists"] = "Username is taken, please choose another"
    if len(password) < 6:
        errors["passwordLength"] = "Password must be 6 characters or longer"
    if not validate_email(email):
        errors["validEmail"] = "Please enter valid email"

    if len(errors) == 0:
        print("creating user with: ", username, password, country, email, gender, bday)
        CreateNewUser(username, password, country, email, gender, bday)
        session['logged_in'] = True
        session['username'] = username
        return Response(home(),mimetype = "text/html")
    else:
        json_data = json.dumps(errors)
        return Response(json_data ,mimetype = "application/json") 
        
    
if __name__ == '__main__':
    app.secret_key = os.urandom(12)
    app.run(debug=True)