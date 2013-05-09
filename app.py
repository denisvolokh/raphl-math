
import os
from flask import Flask, Response, request, redirect, render_template, send_from_directory, send_file
import csv
from urlparse import urlparse
from pymongo import MongoClient
from datetime import datetime
from flask import jsonify
from bson.json_util import dumps
from bson.objectid import ObjectId
import StringIO
import mimetypes
from dateutil import parser
from werkzeug.datastructures import Headers
import datetime
import hashlib

#----------------------------------------
# initialization
#----------------------------------------

app = Flask(__name__)

app.config.update(
    DEBUG = True,
)

ALLOWED_EXTENSIONS = set(['csv',])
PAGE_OFFSET = 20

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

# @app.route('/listfiles', methods=['GET', 'POST'])
# def list_files():
# 	files = db["files"].find()
# 	# print "[+] ", files.count()
# 	return dumps(list(files))

@app.route('/api/removefile', methods=['GET', 'POST'])
def removefile():
	id = request.args["file_id"]

	db["calculus"].remove({"file_id" : str(id)})
	db["records"].remove({"file_id": str(id)})
	db["files"].remove({"_id" : ObjectId(id)})

	files = db["files"].find()

	return dumps(list(files))

@app.route('/listrecords', methods=['GET', 'POST'])
def list_records():
	id = request.args["dataset_id"]
	page = int(request.args["page"])
	calc_hash = request.args["calc_hash"]
	file = db["files"].find_one({"_id": ObjectId(id)})

	if calc_hash != "":
		count_records = db["calculus"].find({"calc_hash" : calc_hash}).count()
		# count_records = db.command({
		# 		"count":"calculus",
		# 		"query": {
		# 			"calc_hash" : calc_hash
		# 		}
		# 	}
		# )
		records = db["calculus"].find({"calc_hash" : calc_hash}).skip((page-1)*PAGE_OFFSET).limit(PAGE_OFFSET)
		
	else:	
		count_records = db["records"].find({"file_id" : str(id)}).count()
		# count_records = db.command({
		# 		"count":"records",
		# 		"query": {
		# 			"file_id" : str(id)			
		# 		}
		# 	}
		# )
		records = db["records"].find({"file_id" : str(id)}).skip((page-1)*PAGE_OFFSET).limit(PAGE_OFFSET)
		

	# total_pages = int(count_records["n"]) / PAGE_OFFSET
	total_pages = int(count_records) / PAGE_OFFSET

	return dumps(dict(file=file, result=list(records), pages=total_pages))

@app.route("/api/export", methods=["GET", "POST"])
def export():
	id = request.args["dataset_id"]
	position = request.args["position"]

	file = db["files"].find_one({"_id": ObjectId(id)})
	records = db["records"].find({"file_id" : str(id)})
	
	marked = mark_records_buy_action(records, "SELL")
	marked = mark_records_buy_action(marked, "BUY")

	calculated = do_calc(marked, position)
	
	response = Response()
	response.status_code = 200

	output = StringIO.StringIO()

	summary_header = ["NUMBER OF TRADES","PnL","BPs","MIN","MAX"]
	output.write(",".join(summary_header))
	output.write("\n")
	sums = [str(calculated["trades_counter"]), calculated["sum_profit_loss"], calculated["sum_profit_bp"], calculated["min"], calculated["max"]]
	output.write(",".join(sums))
	output.write("\n")
	output.write("\n")

	table_header = ["DATE","OPEN","HIGH","LOW","LAST_PRICE","ACTION","VOL","STOP1","TARGET-1","TARGET-2","TRADES","EXIT 1","EXIT 2", "PROFIT (bp)","PROFIT (ccy)","BALANCE (ccy)"]
	output.write(",".join(table_header))
	output.write("\n")
	for item in calculated["result"]:
		row = []
		dt = parser.parse(item["date"])
		row.append(dt.strftime("%d/%m/%y %H:%M"))
		row.append(item["open"])	
		row.append(item["high"])
		row.append(item["low"])	
		row.append(item["last_price"])	
		row.append(item["action"])	
		row.append(item["vol"])	
		row.append(item["stop1"])	
		row.append(item["target1"])		
		row.append(item["target2"])		
		row.append(item["trades"])		
		row.append(item["exit1"])		
		row.append(item["exit2"])		
		row.append(item["profit_bp"])
		row.append(item["profit_ccy"])				
		row.append(item["balance"])
		output.write(",".join(row))						
		output.write("\n")
	response.data = output.getvalue()

	filename = "export.csv"
	mimetype_tuple = mimetypes.guess_type(filename)

	response_headers = Headers({
			'Pragma': "public",  # required,
			'Expires': '0',
			'Cache-Control': 'must-revalidate, post-check=0, pre-check=0',
			'Cache-Control': 'private',  # required for certain browsers,
			'Content-Type': mimetype_tuple[0],
			'Content-Disposition': 'attachment; filename=\"%s\";' % filename,
			'Content-Transfer-Encoding': 'binary',
			'Content-Length': len(response.data)
		})
 
 	if not mimetype_tuple[1] is None:
 		response.update({
			'Content-Encoding': mimetype_tuple[1]
 		})
 
	response.headers = response_headers
 
    #as per jquery.fileDownload.js requirements
	response.set_cookie('fileDownload', 'true', path='/')
 
    ################################
    # Return the response
    #################################
	return response


@app.route("/api/calc", methods=["GET", "POST"])
def calc():
	id = request.args["dataset_id"]
	position = request.args["position"]
	strategy = request.args["strategy"]
	print "[+] STRATEGY: ", strategy

	calc_hash = request.args["calc_hash"]
	if calc_hash != "":
		print "[+] CLEANING BEFORE NEW CALC"
		db["calculus"].remove({"calc_hash":calc_hash})

	file = db["files"].find_one({"_id": ObjectId(id)})
	records = db["records"].find({"file_id" : str(id)})
	
	marked = mark_records_buy_action(records, "SELL")
	marked = mark_records_buy_action(marked, "BUY")

	calculated = do_calc(marked, position, strategy)

	print "[+] FILE ID", str(file["_id"])

	calc_hash = hashlib.sha512(str(datetime.datetime.utcnow())).hexdigest()[:11]
	calculus = []
	for item in calculated["result"]:
		calc_item = {
			"file_id" : str(file["_id"]),
			"trades_counter" : calculated["trades_counter"],
			"max" : calculated["max"],
			"min" : calculated["min"],
			"sum_profit_bp" : calculated["sum_profit_bp"],
			"sum_profit_loss" : calculated["sum_profit_loss"],
			"calc_hash" : calc_hash,
			"date" : item["date"],
			"open" : item["open"],
			"high" : item["high"],
			"low" : item["low"],
			"last_price" : item["last_price"],
			"action" : item["action"],
			"vol" : item["vol"],
			"stop1" : item["stop1"],
			"target1" : item["target1"],
			"target2" : item["target2"],
			"profit_bp": item["profit_bp"],
			"profit_ccy": item["profit_ccy"],
			"trades": item["trades"],
			"exit1": item["exit1"],
			"exit2": item["exit2"],
			"balance": item["balance"]
		}
		if "highlight" in item:
			calc_item["highlight"] = item["highlight"]
		calculus.append(calc_item)
		# item["file_id"] = str(file["_id"])
		# item["trades_counter"] = calculated["trades_counter"]
		# item["max"] = calculated["max"]
		# item["min"] = calculated["min"]
		# item["sum_profit_bp"] = calculated["sum_profit_bp"]
		# item["sum_profit_loss"] = calculated["sum_profit_loss"]
		# item["calc_hash"] = calc_hash
		# db["calculus"].insert(item)	

	print calculated["result"][0]	
	db["calculus"].insert(calculus)	
	total_pages = len(calculus) / PAGE_OFFSET
	
	first_page = db["calculus"].find({"calc_hash" : calc_hash}).skip(0).limit(PAGE_OFFSET)
	
	return dumps(dict(file=file, 
						result=list(first_page), 
						trades_counter=calculated["trades_counter"],
						max=calculated["max"],
						min=calculated["min"],
						sum_profit_bp=calculated["sum_profit_bp"],
						sum_profit_loss=calculated["sum_profit_loss"],
						calc_hash=calc_hash,
						pages=total_pages))	


@app.route('/listfiles', methods=['GET', 'POST'])
def list_files():
	"""Print all records from collection FILES"""
	files = db["files"].find()
	
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
			rows = []
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
							"exit2": "",
							"balance": 0
						}
						rows.append(record)
			db["records"].insert(rows)			

	return ""

@app.route("/")
def index():
    return render_template('index.html')

def mark_records_buy_action(collection, action="SELL"):
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


def do_calc(coll, position, strategy):
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
	balance = 0
	just_closed = False
	trades_counter = 0
	min_balance = 0
	max_balance = 0
	sum_profit_bp = 0
	sum_profit_loss = 0
	for idx, item in enumerate(coll):
		print idx, item["date"], entry
		if entry:
			just_closed = False		
			# STOPPED OUT, NO TARGETS
			if entry_action == "SELL":
				if float(item["high"]) >= float(entry_stop):
					# print "[+] STOPPED OUT @ ", float(item["high"])
					# print "[+] PROFIT(bp) ", float(entry) - float(entry_stop)
					item["profit_bp"] = "{0:.4f}".format(float(entry) - float(entry_stop)) 
					sum_profit_bp += float(entry) - float(entry_stop)
					# print "[+] PROFIT(ccy) ", (float(entry) - float(entry_stop)) * float(position)
					pl = (float(entry) - float(entry_stop)) * float(position)
					item["profit_ccy"] = "{0:.4f}".format(pl)
					sum_profit_loss += pl
					balance += pl
					if balance >= max_balance:
						max_balance = balance
					if balance <= min_balance:
						min_balance = balance	
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
					# print "[+] STOPPED OUT @ ", float(item["low"])
					# print "[+] PROFIT(bp) ", float(entry) - float(entry_stop)
					item["profit_bp"] = "{0:.4f}".format(float(entry_stop) - float(entry)) 
					sum_profit_bp += float(entry_stop) - float(entry) 
					# print "[+] PROFIT(ccy) ", (float(entry_stop) - float(entry)) * float(position)
					pl = (float(entry_stop) - float(entry)) * float(position)
					item["profit_ccy"] = "{0:.4f}".format(pl)
					sum_profit_loss += pl
					balance += pl
					if balance >= max_balance:
						max_balance = balance
					if balance <= min_balance:
						min_balance = balance	
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
						profit_bp = float(trade) - float(exit1)
						sum_profit_bp += profit_bp
						_total_profit = profit_bp * (float(position)/2)
						item["exit2"] = exit2
						profit_bp = float(trade) - float(exit2)
						sum_profit_bp += profit_bp
						_total_profit += profit_bp * (float(position)/2)
						item["profit_ccy"] = "{0:.4f}".format(_total_profit)
						balance += _total_profit
						sum_profit_loss += _total_profit
						if balance >= max_balance:
							max_balance = balance
						if balance <= min_balance:
							min_balance = balance	
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
									sum_profit_bp += profit_bp
									item["profit_ccy"] = "{0:.4f}".format(profit_bp * (float(position)/2))
									balance += profit_bp * (float(position)/2)
									sum_profit_loss += profit_bp * (float(position)/2)
									if balance >= max_balance:
										max_balance = balance
									if balance <= min_balance:
										min_balance = balance	
								elif exit2 == "":
									exit2 = entry_target2	
									item["exit2"] = exit2
									profit_bp = float(trade) - float(exit2)
									item["profit_bp"] = "{0:.4f}".format(profit_bp) 
									sum_profit_bp += profit_bp
									item["profit_ccy"] = "{0:.4f}".format(profit_bp * (float(position)/2))
									balance += profit_bp * (float(position)/2)
									sum_profit_loss += profit_bp * (float(position)/2)
									if balance >= max_balance:
										max_balance = balance
									if balance <= min_balance:
										min_balance = balance	
								print "[+] EXIT 1 @ ", exit1
								print "[+] EXIT 2 @ ", exit2
								closed_target1 = True
								if strategy == "2":
									print "[+] SKIP TARGET-2s"
									closed_target2 = True
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
									sum_profit_bp += profit_bp
									item["profit_ccy"] = "{0:.4f}".format(profit_bp * (float(position)/2))
									balance += profit_bp * (float(position)/2)
									sum_profit_loss += profit_bp * (float(position)/2)
									if balance >= max_balance:
										max_balance = balance
									if balance <= min_balance:
										min_balance = balance	
								elif exit2 == "":
									exit2 = entry_target2	
									item["exit2"] = exit2
									profit_bp = float(trade) - float(exit2)
									item["profit_bp"] = "{0:.4f}".format(profit_bp) 
									sum_profit_bp += profit_bp
									item["profit_ccy"] = "{0:.4f}".format(profit_bp * (float(position)/2))
									balance += profit_bp * (float(position)/2)
									sum_profit_loss += profit_bp * (float(position)/2)
									if balance >= max_balance:
										max_balance = balance
									if balance <= min_balance:
										min_balance = balance	
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
					sum_profit_bp += profit_bp
					_total_profit = profit_bp * (float(position)/2)
					item["exit2"] = exit2
					profit_bp = float(exit2) - float(trade)
					sum_profit_bp += profit_bp
					_total_profit += profit_bp * (float(position)/2)
					item["profit_ccy"] = "{0:.4f}".format(_total_profit)
					balance += _total_profit
					sum_profit_loss += _total_profit
					if balance >= max_balance:
						max_balance = balance
					if balance <= min_balance:
						min_balance = balance	
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
									sum_profit_bp += profit_bp
									item["profit_ccy"] = "{0:.4f}".format(profit_bp * (float(position)/2))
									balance += profit_bp * (float(position)/2)
									sum_profit_loss += profit_bp * (float(position)/2)
									if balance >= max_balance:
										max_balance = balance
									if balance <= min_balance:
										min_balance = balance	
								elif exit2 == "":
									exit2 = entry_target2	
									item["exit2"] = exit2
									profit_bp = float(exit2) - float(trade)
									item["profit_bp"] = "{0:.4f}".format(profit_bp) 
									sum_profit_bp += profit_bp
									item["profit_ccy"] = "{0:.4f}".format(profit_bp * (float(position)/2))
									balance += profit_bp * (float(position)/2)
									sum_profit_loss += profit_bp * (float(position)/2)
									if balance >= max_balance:
										max_balance = balance
									if balance <= min_balance:
										min_balance = balance	
								print "[+] EXIT 1 @ ", exit1
								print "[+] EXIT 2 @ ", exit2
								closed_target1 = True
								if strategy == "2":
									print "[+] SKIP TARGET-2"
									closed_target2 = True
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
									sum_profit_bp += profit_bp
									item["profit_ccy"] = "{0:.4f}".format(profit_bp * (float(position)/2))
									balance += profit_bp * (float(position)/2)
									sum_profit_loss += profit_bp * (float(position)/2)
									if balance >= max_balance:
										max_balance = balance
									if balance <= min_balance:
										min_balance = balance	
								elif exit2 == "":
									exit2 = entry_target2	
									item["exit2"] = exit2
									profit_bp = float(exit2) - float(trade)
									item["profit_bp"] = "{0:.4f}".format(profit_bp) 
									sum_profit_bp += profit_bp
									item["profit_ccy"] = "{0:.4f}".format(profit_bp * (float(position)/2))
									balance += profit_bp * (float(position)/2)
									sum_profit_loss += profit_bp * (float(position)/2)
									if balance >= max_balance:
										max_balance = balance
									if balance <= min_balance:
										min_balance = balance	
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
						trades_counter += 1
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
					trades_counter += 1
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
				trades_counter += 1
				trade = entry
				print "[+] Entry: ", entry_stop

		item["balance"] = str(balance)		
	
	return dict(result=coll, 
				trades_counter=trades_counter,
				min="{0:.2f}".format(min_balance),
				max="{0:.2f}".format(max_balance),
				sum_profit_bp="{0:.4f}".format(sum_profit_bp),
				sum_profit_loss="{0:.2f}".format(sum_profit_loss))


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