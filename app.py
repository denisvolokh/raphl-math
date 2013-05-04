import os
from flask import Flask, request, redirect, render_template, send_from_directory
import csv
from urlparse import urlparse
from pymongo import MongoClient
from datetime import datetime
from flask import jsonify
from bson.json_util import dumps

#----------------------------------------
# initialization
#----------------------------------------

app = Flask(__name__)

app.config.update(
    DEBUG = True,
)

ALLOWED_EXTENSIONS = set(['csv',])

# mongodb://localhost/raphl-math
database = os.environ.get("MONGOHQ_URL", "")
if os.environ.get("MONGOHQ_URL") == None:
	database = "mongodb://root:admin@linus.mongohq.com:10061/app15435588"
print "[+] ", database

# client = MongoClient("mongodb://heroku:859c8a4107b78276aa47ee214977a061@linus.mongohq.com:10061/app15435588")
client = MongoClient(database)
# client = MongoClient("mongodb://root:admin@linus.mongohq.com:10061/app15435588")
db = client['app15435588']
print db.collection_names()

#----------------------------------------
# controllers
#----------------------------------------

@app.route('/listrecords', methods=['GET', 'POST'])
def list_records():
	id = request.args["dataset_id"]
	position = request.args["position"]

	records = db["records"].find({"file_id" : str(id)})
	
	marked = mark_records_buy_action(records, "SELL")
	marked = mark_records_buy_action(marked, "BUY")

	calculated = do_calc(marked, position) 

	return dumps(list(calculated))

@app.route('/listfiles', methods=['GET', 'POST'])
def list_files():
	files = db["files"].find()
	# print "[+] ", files.count()
	return dumps(list(files))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
	print "[+] Uploading file..."
	if request.method == 'POST':
		print "[+] Files: ", request.files
		file = request.files['file']
		print "[+] Files: ", file
		if "name" in request.form:
			given_name = request.form["name"]
		else:
			given_name = file.filename	
    	print "[+] Custom name: ", given_name
    	if file and allowed_file(file.filename):
        	_file = {
        		"name": given_name
        	}
        	file_id = db["files"].insert(_file)
        	for row in csv.DictReader(file.stream):
    				if row["Date/Time"] != "":
    					record = {
    						"file_id": str(file_id),
    						"date" : row["Date/Time"],
    						"open" : row["OPEN"],
    						"high" : row["HIGH"],
    						"low" : row["LOW"],
    						"last_price" : row["LAST_PRICE"],
    						"action" : row["Action"],
    						"vol" : row["Vol"],
    						"stop1" : row["STOP1"],
    						"target1" : row["Target 1"],
    						"target2" : row["Target 2"],
    						"profit_bp": "",
    						"profit_ccy": ""
    					}
    					db["records"].insert(record)
	return ""

@app.route("/")
def index():
    return render_template('index.html')

def mark_records_buy_action(collection, action="SELL"):
	opp_action = "BUY"
	if action == "BUY":
		opp_action = "SELL"

	skip_subsequent_flag = False			
	_coll = []

	for idx, item in enumerate(collection):
		if idx != 0:
			prev = _coll[idx-1]
			if not skip_subsequent_flag:
				if item["action"] == action and prev["action"] == action:
					# prev["highlight"] = True
					item["marked"] = True
					skip_subsequent_flag = True

			if item["action"] == "" or item["action"] == opp_action: 
				skip_subsequent_flag = False		

		_coll.append(item)		

	return _coll

def do_calc(coll, position=1000000):
	entry = ""
	entry_stop = ""		
	entry_target1 = ""
	entry_target2 = ""	
	for idx, item in enumerate(coll):
		if entry:
			if float(item["high"]) >= float(entry_stop):
				print "[+] STOPPED OUT @ ", float(item["high"])
				print "[+] PROFIT(bp) ", float(entry) - float(entry_stop)
				item["profit_bp"] = "{0:.4f}".format(float(entry) - float(entry_stop)) 
				print "[+] PROFIT(ccy) ", (float(entry) - float(entry_stop)) * float(position)
				item["profit_ccy"] = "{0:.4f}".format((float(entry) - float(entry_stop)) * float(position))
				entry = ""
				item["highlight"] = "error"
			# print item["low"], entry_target1	
			# if float(entry_target1) >= float(item["low"]) or float(entry_target2) >= float(item["low"]):
			# 	if float(entry_target1) >= float(item["low"]) and float(entry_target2) >= float(item["low"]):
			# 		print "[+] REACHED ALL TARGETS @ ", float(item["low"]) 

			# 	if float(entry_target1) >= float(item["low"]):
			# 		print "[+] REACHED TARGET-1 @ ", float(item["low"]) 
			# 		print "[+] PROFIT ", str(2500000 * (float(entry) - float(entry_target1)))

			# 	if float(entry_target2) >= float(item["low"]):
			# 		print "[+] REACHED TARGET-2 @ ", float(item["low"]) 

		else:
			if "marked" in item and item["marked"]:
				item["highlight"] = "success"
				entry = item["last_price"]
				entry_stop = item["stop1"]
				entry_target1 = item["target1"]
				entry_target2 = item["target2"]
				print "[+] Entry: ", entry_stop

	return coll				

#----------------------------------------
# launch
#----------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)