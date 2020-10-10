import email, imaplib, base64, threading, re, json, urlextract
from datetime import datetime, timezone
from flask import request
from urllib.parse import urlparse
import dateutil.parser as dparser

from flask import Flask
app = Flask(__name__, static_url_path="")

message_db = {}

try:
	with open("data/db.json", "r") as f:
		message_db = json.loads(f.read())
except:
	pass

def write_db():
	with open("data/db.json", "w") as f:
		f.write(json.dumps(message_db))

def add_message(sender, msg):
	if sender not in message_db:
		message_db[sender] = []
	message_db[sender].append(msg)
	write_db()

def check_for_emails():
	threading.Timer(10, check_for_emails).start()

	mail = imaplib.IMAP4_SSL("imap.gmail.com")
	mail.login("phishnetbot@gmail.com", open("password.txt", "r").read().strip())
	for folder in ["\"[Gmail]/Kaikki viestit\"", "\"[Gmail]/Roskaposti\""]:
		res = mail.select(folder)

		status, data = mail.search(None, "UnSeen")

		mail_ids = []

		for block in data:
			mail_ids += block.split()

		if len(mail_ids) > 0:
			print(str(len(mail_ids)) + " new emails")

		for i in mail_ids:
			status, data = mail.fetch(i, "(RFC822)")

			for response_part in data:
				if isinstance(response_part, tuple):

					message = email.message_from_bytes(response_part[1])

					mail_from_original = message["from"]
					mail_subject = message["subject"]

					mail_time = dparser.parse(message["received"].split("\n")[1].strip(), fuzzy=True).astimezone().strftime("%d/%m/%y %H %p")

					sender_search = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", mail_from_original)
					if sender_search:
						mail_from_original = sender_search.group(0)

					if message.is_multipart():
						mail_content = ""

						for part in message.get_payload():
							if part.get_content_type() in ["text/plain", "text/html", "multipart/alternative"]:
								if type(part.get_payload()) == list:
									for m in part.get_payload():
										tmp = m.as_string()
										tmp = tmp.split("\n\n", 1)[1]

										try:
											tmp = base64.b64decode(tmp).decode("utf-8")
										except:
											pass
										mail_content += tmp
										break
								else:
									mail_content += part.get_payload()
					else:
						mail_content = message.get_payload()

					try:
						mail_content = base64.b64decode(mail_content).decode("utf-8")
					except:
						pass

					mail_from = mail_from_original
					if "Subject: " in mail_content or "From: " in mail_content:
						for l in mail_content.split("\n"):
							if l.startswith("Subject: "):
								mail_subject = l[len("Subject: "):]
							if l.startswith("From: "):
								mail_from = l[len("From: "):]
							if l.startswith("Von: "):
								mail_from = l[len("Von: "):]

					mail_subject = mail_subject.lower()
					while mail_subject.startswith("fw: ") or mail_subject.startswith("fwd: "):
						if mail_subject.startswith("fw: "):
							mail_subject = mail_subject[4:]
						if mail_subject.startswith("fwd: "):
							mail_subject = mail_subject[5:]

					sender_search = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", mail_from)
					if sender_search:
						mail_from = sender_search.group(0)

					links = urlextract.URLExtract().find_urls(mail_content)

					for i in range(len(links)):
						links[i] = urlparse(links[i]).hostname

					links = list(set(links))

					mailObject = {"reporter": mail_from_original, "subject": mail_subject, "links": links, "time": mail_time}
					add_message(mail_from, mailObject)
check_for_emails()

@app.route("/")
def index():
	return app.send_static_file("index.html")

@app.route("/network")
def network():
	return app.send_static_file("network.html")

@app.route("/learn")
def learn():
	return app.send_static_file("educate.html")

@app.route("/db-dump")
def db_dump():
	return json.dumps(message_db)

@app.route("/clear-db") # MUST be removed in final product
def clear_db():
	global message_db
	message_db = {}
	write_db()
	return "OK"

@app.route("/report", methods=["POST"])
def report():
	email = request.args.get("email", default="", type=str)
	add_message(email, {"time": datetime.now().astimezone().strftime("%d/%m/%y %H %p")})
	return "OK"

@app.route("/query")
def query():
	email = request.args.get("email", default="", type=str)
	count = 0
	last = "never"
	if email in message_db:
		count = len(message_db[email])
		if "time" in message_db[email][-1]:
			last = message_db[email][-1]["time"]
		else:
			last = "unknown"
	return "{\"count\": " + str(count) + ", \"last\": \"" + last + "\"}"
