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

database = urlparse(os.environ.get("MONGOHQ_URL"))
print "[+] ", database

client = MongoClient(database)
db = client['raphl-math']
print db.collection_names()

# connect(database.path[1:],
# 		host=database.hostname,
# 		port=database.port,
# 		username=database.username,
# 		password=database.password)

# class DataSet(Document):
# 	name = StringField()
# 	created = DateTimeField()

# 	def to_dict(self):
# 		return mongo_to_dict_helper(self)

# class Record(Document):
# 	dataset_id = StringField()
# 	date = StringField()
# 	created = DateTimeField()
# 	open = FloatField()
# 	high = FloatField()
# 	low = FloatField()
# 	last_price=FloatField()
# 	action=StringField()
# 	vol=FloatField()
# 	stop1=FloatField()
# 	target1=FloatField()
# 	target2=FloatField()

# 	highlight=BooleanField(default=False)

# 	def to_dict(self):
# 		return mongo_to_dict_helper(self)

# def mongo_to_dict_helper(obj):
# 	return_data = []
# 	for field_name in obj._fields:
# 		if field_name in ("id",):
# 			continue

# 		data = obj._data[field_name]

# 		if isinstance(obj._fields[field_name], StringField):
# 			return_data.append((field_name, str(data)))
# 		elif isinstance(obj._fields[field_name], FloatField):
# 			return_data.append((field_name, float(data)))
# 		elif isinstance(obj._fields[field_name], BooleanField):
# 			return_data.append((field_name, bool(data)))
# 		# elif isinstance(obj._fields[field_name], ListField):
# 		# 	return_data.append((field_name, data))
# 		# else:
#             # You can define your logic for returning elements
# 	return dict(return_data)

#----------------------------------------
# controllers
#----------------------------------------

@app.route('/listrecords', methods=['GET', 'POST'])
def list_records():
	id = request.args["dataset_id"]
	records = db["records"].find({"file_id" : str(id)})
	
	marked = mark_records_buy_action(records, "SELL")
	marked = mark_records_buy_action(marked, "BUY")

	return dumps(list(marked))

	# for rec in marked:		
		# _marked.append(mongo_to_dict_helper(rec))
	
	# return json.dumps(_marked)

@app.route('/listfiles', methods=['GET', 'POST'])
def list_files():
	files = db["files"].find()
	print "[+] ", files.count()
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
    	given_name = request.form["name"]
    	if given_name == None:
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
    						"target2" : row["Target 2"]
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
					prev["highlight"] = True
					item["highlight"] = True
					skip_subsequent_flag = True

			if item["action"] == "" or item["action"] == opp_action: 
				skip_subsequent_flag = False		

		_coll.append(item)		

	return _coll


#----------------------------------------
# launch
#----------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)