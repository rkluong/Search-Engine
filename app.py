import os.path
from pymongo import *
from pprint import pprint
from flask import Flask, render_template, request
from dbcontroller import search

app = Flask(__name__)
app.config.from_object(__name__)

@app.route('/')
def render_static():
	return render_template("index.html");

@app.route('/result', methods=['POST'])
def query():
	client = MongoClient()
	db = client.search;
	query = request.form['query'].lower();
	results = search(query, db)
	if(len(results) > 0):
		results = [link[0] for link in results];
	return render_template("results.html", data = results);

@app.route('/page/<string:webpage>/<int:pageid>/<int:docid>')
def loadpage(webpage, pageid, docid):
	path = webpage+ "/" + str(pageid) + "/" + str(docid);
	with open(path, "r", encoding="utf-8") as file:
		content = file.read()
	return render_template("page.html", content=content, pageTitle = path);

if __name__ == '__main__':
	app.run(debug=True, port=3000);
		
