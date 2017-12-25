from flask import Flask, render_template, request, redirect
from databaseScripts import connect, getRandomImages, getContesters

app = Flask(__name__)
cursor = connect()


@app.route('/')
def home():
	images = list(getContesters("nicolai", "female"))
	#images = list(getRandomImages("female"))
	images = ["https://s3-eu-west-1.amazonaws.com/ratemegirl/"+s for s in images]
	return render_template('home.html', images=images)

@app.route('/vote', methods = ['POST'])
def vote():
    #vote = request.form['CastVote']
    content = request.get_json()
  	#votes = request.getContes
    print("voted for: ",content)
    return redirect('/')

@app.route('/report', methods = ['POST'])
def report():
    report = request.form['CastReport']
    print("reported: ",report)
    return redirect('/')

@app.route('/about/')
def about():
	return render_template('about.html')
    
if __name__ == '__main__':
	app.run(debug=True)


  