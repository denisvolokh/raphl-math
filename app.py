
import os
from flask import Flask, request, redirect, render_template, send_from_directory
import csv
from urlparse import urlparse
from pymongo import MongoClient
from datetime import datetime
from flask import jsonify
from bson.json_util import dumps
from bson.objectid import ObjectId

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

	file = db["files"].find_one({"_id": ObjectId(id)})
	records = db["records"].find({"file_id" : str(id)})
	
	marked = mark_records_buy_action(records, "SELL")
	marked = mark_records_buy_action(marked, "BUY")

	print marked

	return dumps(dict(file=file, result=list(marked)))


@app.route("/api/calc", methods=["GET", "POST"])
def calc():
	id = request.args["dataset_id"]
	position = request.args["position"]

	file = db["files"].find_one({"_id": ObjectId(id)})
	records = db["records"].find({"file_id" : str(id)})
	
	marked = mark_records_buy_action(records, "SELL")
	marked = mark_records_buy_action(marked, "BUY")

	calculated = do_calc(marked, position)
	
	return dumps(dict(file=file, result=list(marked)))	


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
    						"profit_ccy": "",
    						"trades": "",
    						"exit1": "",
    						"exit2": ""
    					}
    					print record
    					db["records"].insert(record)
	return ""

@app.route("/")
def index():
    return render_template('index.html')

def mark_records_buy_action(collection, action="SELL"):
	# opp_action = "BUY"
	# if action == "BUY":
	# 	opp_action = "SELL"

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

			if item["action"] == "" or item["action"] == get_opposite_action(item["action"]): 
				skip_subsequent_flag = False		

		_coll.append(item)		

	return _coll


def do_calc(coll, position=1000000):
	entry_action = ""
	entry = ""
	entry_stop = ""		
	entry_target1 = ""
	entry_target2 = ""
	exit1 = ""
	exit2 = ""
	balance= ""	
	trade = ""
	closed_target1 = False
	closed_target2 = False
	profit_bp = ""
	just_closed = False
	for idx, item in enumerate(coll):
		print idx, item["date"], entry
		if entry:
			just_closed = False		
			# STOPPED OUT, NO TARGETS
			if entry_action == "SELL":
				if float(item["high"]) >= float(entry_stop):
					print "[+] STOPPED OUT @ ", float(item["high"])
					print "[+] PROFIT(bp) ", float(entry) - float(entry_stop)
					item["profit_bp"] = "{0:.4f}".format(float(entry) - float(entry_stop)) 
					print "[+] PROFIT(ccy) ", (float(entry) - float(entry_stop)) * float(position)
					item["profit_ccy"] = "{0:.4f}".format((float(entry) - float(entry_stop)) * float(position))
					entry = ""
					item["highlight"] = "error"
					if exit1 == "":
						exit1 = entry_stop	
						item["exit1"] = exit1
					elif exit2 == "":
						exit2 = entry_stop	
						item["exit2"] = exit2
					print "[+] EXIT 1 @ ", exit1
					print "[+] EXIT 2 @ ", exit2
					closed_target1 = True
					closed_target2 = True	
					just_closed = True
			elif entry_action == "BUY":
				if float(item["low"]) <= float(entry_stop):
					print "[+] STOPPED OUT @ ", float(item["low"])
					print "[+] PROFIT(bp) ", float(entry) - float(entry_stop)
					item["profit_bp"] = "{0:.4f}".format(float(entry) - float(entry_stop)) 
					print "[+] PROFIT(ccy) ", (float(entry) - float(entry_stop)) * float(position)
					item["profit_ccy"] = "{0:.4f}".format((float(entry) - float(entry_stop)) * float(position))
					entry = ""
					item["highlight"] = "error"
					if exit1 == "":
						exit1 = entry_stop	
						item["exit1"] = exit1
					elif exit2 == "":
						exit2 = entry_stop	
						item["exit2"] = exit2
					print "[+] EXIT 1 @ ", exit1
					print "[+] EXIT 2 @ ", exit2
					closed_target1 = True
					closed_target2 = True	
					just_closed = True		

			if entry_action == "SELL":		
				if float(entry_target1) >= float(item["low"]) and float(entry_target2) >= float(item["low"]) and not closed_target1 and not closed_target2:
						print "[+] REACHED ALL TARGETS IN ONE LINE ", float(item["low"]) 
						exit1 = entry_target1	
						item["exit1"] = exit1
						exit2 = entry_target2	
						profit_bp = float(exit1) - float(trade)
						_total_profit = profit_bp * (float(position)/2)
						item["exit2"] = exit2
						profit_bp = float(exit1) - float(trade)
						_total_profit += profit_bp * (float(position)/2)
						item["profit_ccy"] = "{0:.4f}".format(_total_profit)
						closed_target1 = True
						closed_target2 = True
						item["highlight"] = "warning"
				else:		
					if float(entry_target1) >= float(item["low"]) or float(entry_target2) >= float(item["low"]):
						if not closed_target1:
							if float(entry_target1) >= float(item["low"]):
								print "[+] REACHED TARGET-1 @ ", float(item["low"]) 
								print "[+] PROFIT ", str(2500000 * (float(entry) - float(entry_target1)))
								entry_stop = entry
								print "[+] NEW STOP ", entry_stop
								if exit1 == "":
									exit1 = entry_target1	
									item["exit1"] = exit1
									profit_bp = float(trade) - float(exit1)
									item["profit_bp"] = "{0:.4f}".format(profit_bp) 
									item["profit_ccy"] = "{0:.4f}".format(profit_bp * (float(position)/2))
								elif exit2 == "":
									exit2 = entry_target2	
									item["exit2"] = exit2
									profit_bp = float(trade) - float(exit2)
									item["profit_bp"] = "{0:.4f}".format(profit_bp) 
									item["profit_ccy"] = "{0:.4f}".format(profit_bp * (float(position)/2))
								print "[+] EXIT 1 @ ", exit1
								print "[+] EXIT 2 @ ", exit2
								closed_target1 = True
								item["highlight"] = "warning"

						if not closed_target2:
							if float(entry_target2) >= float(item["low"]):
								print "[+] REACHED TARGET-2 @ ", float(item["low"]) 
								print "[+] CHECK DATA:", entry, entry_target2
								print "[+] PROFIT ", str(float(position)/2 * (float(entry) - float(entry_target2)))
								entry_stop = entry
								print "[+] NEW STOP ", entry_stop
								if exit1 == "":
									exit1 = entry_target1	
									item["exit1"] = exit1
									profit_bp = float(trade) - float(exit1)
									item["profit_bp"] = "{0:.4f}".format(profit_bp) 
									item["profit_ccy"] = "{0:.4f}".format(profit_bp * (float(position)/2))
								elif exit2 == "":
									exit2 = entry_target2	
									item["exit2"] = exit2
									profit_bp = float(trade) - float(exit2)
									item["profit_bp"] = "{0:.4f}".format(profit_bp) 
									item["profit_ccy"] = "{0:.4f}".format(profit_bp * (float(position)/2))
								print "[+] EXIT 1 @ ", exit1
								print "[+] EXIT 2 @ ", exit2
								closed_target2 = True
								item["highlight"] = "warning"
								just_closed = closed_target1 and closed_target2					

			elif entry_action == "BUY":
				if float(entry_target1) <= float(item["high"]) and float(entry_target2) <= float(item["high"]) and not closed_target1 and not closed_target2:
					print "[+] REACHED ALL TARGETS IN ONE LINE ", float(item["high"]) 
					exit1 = entry_target1	
					item["exit1"] = exit1
					exit2 = entry_target2	
					profit_bp = float(exit1) - float(trade)
					_total_profit = profit_bp * (float(position)/2)
					item["exit2"] = exit2
					profit_bp = float(exit1) - float(trade)
					_total_profit += profit_bp * (float(position)/2)
					item["profit_ccy"] = "{0:.4f}".format(_total_profit)
					closed_target1 = True
					closed_target2 = True
					item["highlight"] = "warning"
				else:	
					if float(entry_target1) <= float(item["high"]) or float(entry_target2) <= float(item["high"]):
						if not closed_target1:
							if float(entry_target1) <= float(item["high"]):
								print "[+] REACHED TARGET-1 @ ", float(item["high"]) 
								print "[+] PROFIT ", str(2500000 * (float(entry) - float(entry_target1)))
								entry_stop = entry
								print "[+] NEW STOP ", entry_stop
								if exit1 == "":
									exit1 = entry_target1	
									item["exit1"] = exit1
									profit_bp = float(exit1) - float(trade)
									item["profit_bp"] = "{0:.4f}".format(profit_bp) 
									item["profit_ccy"] = "{0:.4f}".format(profit_bp * (float(position)/2))
								elif exit2 == "":
									exit2 = entry_target2	
									item["exit2"] = exit2
									profit_bp = float(exit2) - float(trade)
									item["profit_bp"] = "{0:.4f}".format(profit_bp) 
									item["profit_ccy"] = "{0:.4f}".format(profit_bp * (float(position)/2))
								print "[+] EXIT 1 @ ", exit1
								print "[+] EXIT 2 @ ", exit2
								closed_target1 = True
								item["highlight"] = "warning"

						if not closed_target2:
							if float(entry_target2) <= float(item["high"]):
								print "[+] REACHED TARGET-2 @ ", float(item["high"]) 
								print "[+] CHECK DATA:", entry, entry_target2
								print "[+] PROFIT ", str(float(position)/2 * (float(entry) - float(entry_target2)))
								entry_stop = entry
								print "[+] NEW STOP ", entry_stop
								if exit1 == "":
									exit1 = entry_target1	
									item["exit1"] = exit1
									profit_bp = float(exit1) - float(trade)
									item["profit_bp"] = "{0:.4f}".format(profit_bp) 
									item["profit_ccy"] = "{0:.4f}".format(profit_bp * (float(position)/2))
								elif exit2 == "":
									exit2 = entry_target2	
									item["exit2"] = exit2
									profit_bp = float(exit2) - float(trade)
									item["profit_bp"] = "{0:.4f}".format(profit_bp) 
									item["profit_ccy"] = "{0:.4f}".format(profit_bp * (float(position)/2))
								print "[+] EXIT 1 @ ", exit1
								print "[+] EXIT 2 @ ", exit2
								closed_target2 = True
								item["highlight"] = "warning"
								just_closed = closed_target1 and closed_target2					

			if closed_target1 and closed_target2:
				print "[+] ALL CLOSED"
				closed_target1 = False
				closed_target2 = False
				entry = ""
				entry_stop = ""
				entry_target1 = ""
				entry_target2 = ""
				exit1 = ""
				exit2 = ""
				entry_action = ""
				just_closed = True		

				if item["action"] == get_opposite_action(item["action"]):
					if coll[idx - 1]["action"] == get_opposite_action(item["action"]):
						"""#case 3: opened at SELL, closed at BUY and prev is BUY as well -> open in the same closed"""
						item["highlight"] = "success"	
						entry = item["last_price"]
						entry_stop = item["stop1"]
						entry_target1 = item["target1"]
						entry_target2 = item["target2"]
						item["trades"] = entry
						trade = entry
						print "[+] Entry: ", entry_stop	

		else:
			if just_closed:
				print "[+] JUST CLOSED"
				just_closed = False		
				print "[+] JUST CLOSED: ", item["action"], coll[idx-1]["action"] 
				if item["action"] != "" and item["action"] == coll[idx-1]["action"]: 
					"""case 2: closed at SELL and next is SELL as well -> open at next"""
					item["highlight"] = "success"	
					entry_action = item["action"]
					entry = item["last_price"]
					entry_stop = item["stop1"]
					entry_target1 = item["target1"]
					entry_target2 = item["target2"]
					item["trades"] = entry
					trade = entry
					print "[+] Entry Stop: ", entry_stop
					print "[+]: ", idx, len(coll)
					print "[+] Entry: ", entry

			if entry == "" and  "marked" in item and item["marked"]:
				entry_action = item["action"]
				item["highlight"] = "success"
				entry = item["last_price"]
				entry_stop = item["stop1"]
				entry_target1 = item["target1"]
				entry_target2 = item["target2"]
				item["trades"] = entry
				trade = entry
				print "[+] Entry: ", entry_stop
	
	return coll				


def get_opposite_action(action):
	if action == "SELL":
		return "BUY"
	if action == "BUY":	
		return "SELL"

#----------------------------------------
# launch
#----------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)