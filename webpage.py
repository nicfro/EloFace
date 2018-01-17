from flask import Flask, flash, redirect, render_template, request, session, abort, Response
import os
import json
from validate_email import validate_email
import databaseScripts
from datetime import datetime
from io import BytesIO
import base64
import re

app = Flask(__name__)
cursor = databaseScripts.connect()

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    if databaseScripts.userLogin(username, password):
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
    return redirect('/')

@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        username = session.get('username')
        if username == "admin":
            return render_template('admin.html')
        else:
            images = list(databaseScripts.getContesters(username, "female"))
            images = ["https://s3-eu-west-1.amazonaws.com/ratemegirl/"+s for s in images]
            return render_template('home.html', images=images)

@app.route('/vote', methods = ['POST'])
def vote():
    choice = request.form['choice']
    pic1 = request.form['pic1'][46:]
    pic2 = request.form['pic2'][46:]
    username = session.get('username')
    databaseScripts.ratePictures(username, pic1, pic2, choice)
    return redirect('/')

@app.route('/report', methods = ['POST'])
def report():
    imagePath = request.form['CastReport'][46:]
    username = session.get('username')
    databaseScripts.reportImage(username, imagePath)
    return redirect('/')

@app.route('/howto/')
def howto():
    return render_template('howto.html')

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
    race = request.form['race']

    errors = {}
    
    try:
        bday = datetime.strptime(bday, "%Y-%m-%d")
    except:
        errors["bdayError"] = "Please enter your birthday"

    if username.isalnum() != True:
        errors["usernameAlphanumericError"] = "Username can only contain alphanumeric characters"
    if databaseScripts.userExists(username):
        errors["usernameExistsError"] = "Username is taken, please choose another"
    if len(password) < 6:
        errors["passwordLengthError"] = "Password must be 6 characters or longer"
    if not validate_email(email):
        errors["validEmailError"] = "Please enter valid email"
    if gender == "Please select your gender":
        errors["genderError"] = "Please select your gender"
    if country == "Please select your country":
        errors["countryError"] = "Please select your country"
    if race == "Please select your ethnicity":
        errors["ethnicityError"] = "Please select your ethnicity"

    if len(errors) == 0:
        databaseScripts.CreateNewUser(username, password, country, email, gender, bday, race)
        session['logged_in'] = True
        session['username'] = username
        return Response(home(),mimetype = "text/html")
    else:
        json_data = json.dumps(errors)
        return Response(json_data ,mimetype = "application/json") 
  
@app.route('/upload/')      
def upload():
    return render_template('upload.html')

@app.route('/uploadToS3', methods = ['POST'])
def uploadToS3():
    errors = {}

    username = session.get('username')
    try:
        image = request.form['upload']
    except:
        errors["imageError"] = "Please upload an image"

    gender = request.form['gender']
    race = request.form['race']
    ageGroup = request.form['ageGroup']

    print(gender, race)
    if not databaseScripts.userExists(username):
        errors["usernameError"] = "Username does not exist"
    if gender == "Please select image gender":
        errors["genderError"] = "Please select image gender"
    if race == "Please select image ethnicity":
        errors["ethnicityError"] = "Please select image ethnicity"
    if ageGroup == "Please select image age group":
        errors["ageError"] = "Please select image age group"
    if len(errors) == 0:
        fileName = databaseScripts.getNewFileName()
        image_data = re.sub('^data:image/.+;base64,', '', image)
        encoded = BytesIO(base64.b64decode(image_data.encode()))

        databaseScripts.uploadS3Image(encoded, fileName)
        databaseScripts.uploadImage(fileName, username, gender, race, ageGroup)
        resp = json.dumps({'success':True}), 200, {'ContentType':'application/json'}
        return resp    
    else:
        print(errors)
        json_data = json.dumps(errors)
        return Response(json_data ,mimetype = "application/json") 

@app.route('/highscores/')   
def highscores():
    highscores = databaseScripts.getHighscores("female")
    highscores = [["https://s3-eu-west-1.amazonaws.com/ratemegirl/"+x[0],x[1], i] for i, x in enumerate(highscores, 1)]
    return render_template('highscores.html', highscores = highscores)

@app.route('/adminReport/')
def adminReport():
    return render_template('adminReport.html')

@app.route('/adminUsers/')
def adminUsers():
    userImages = databaseScripts.getUserInfo("images")
    userVotes = databaseScripts.getUserInfo("vote")
    userReports = databaseScripts.getUserInfo("report")
    return render_template('adminUsers.html', userImages = userImages,
                            userVotes = userVotes, userReports = userReports)

if __name__ == '__main__':
    app.secret_key = os.urandom(12)
    app.run(debug=True)
    #app.run(host='0.0.0.0', port=80)