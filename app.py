import os
from flask import Flask, request, render_template, send_from_directory
import csv

#----------------------------------------
# initialization
#----------------------------------------

app = Flask(__name__)

app.config.update(
    DEBUG = True,
)

ALLOWED_EXTENSIONS = set(['csv',])

#----------------------------------------
# controllers
#----------------------------------------

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        given_name = request.form["given_name"]
        if file and allowed_file(file.filename):
        	print file.filename
        	print given_name
        	for row in csv.DictReader(file.stream):
    				if row["Date/Time"] != "":
        				print float(row["Target 1"])
       #  	with open(file.stream) as f:
    			# for row in csv.DictReader(f):
    			# 	if row["Date/Time"] != "":
       #  				print float(row["Target 1"])
            # file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # return redirect(url_for('uploaded_file',
                                    # filename=filename))
    return ""

@app.route("/")
def index():
    return render_template('index.html')

#----------------------------------------
# launch
#----------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)