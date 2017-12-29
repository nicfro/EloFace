from flask import Flask
from flask import Flask, flash, redirect, render_template, request, session, abort
import os

#from databaseScripts import connect, getRandomImages, getContesters
#from databaseScripts import getRandomImages, getContesters
app = Flask(__name__)
#cursor = connect()

@app.route('/login', methods=['POST'])
def login():
    if request.form['password'] == 'password' and request.form['username'] == 'admin':
        session['logged_in'] = True
        session['username'] = request.form['username']
    else:
        flash('wrong password!')
    return home()

@app.route("/logout")
def logout():
    session['logged_in'] = False
    return home()

@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        #return "Hello Boss!  <a href='/logout'>Logout</a>"
        #images = list(getContesters("nicolai", "female"))
        images = ["all/1.jpg", "all/101.jpg"]
        images = ["https://s3-eu-west-1.amazonaws.com/ratemegirl/"+s for s in images]
        return render_template('home.html', images=images)

@app.route('/vote', methods = ['POST'])
def vote():
    choice = request.form['choice']
    pic1 = request.form['pic1'][46:]
    pic2 = request.form['pic2'][46:]
    username = session.get('username')
    #vote(username, pic1, pic2, choice)
    print(choice, pic1, pic2, username)
    print("voted for: ",choice)
    return redirect('/')

@app.route('/report', methods = ['POST'])
def report():
    report = request.form['CastReport']
    imagePath = report[46:]
    username = session.get('username')
    #reportImage(username, ImagePath)
    print("reported: ",imagePath)
    return redirect('/')

@app.route('/about/')
def about():
	return render_template('about.html')
    
if __name__ == '__main__':
    app.secret_key = os.urandom(12)
    app.run(debug=True)