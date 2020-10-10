import email, imaplib, base64, threading, re, json, urlextract
from datetime import datetime, timezone
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
	mail.login("phishnetbot@gmail.com", "G0_ph15h!")

	for folder in ["\"[Gmail]/Kaikki viestit\"", "\"[Gmail]/Roskaposti\""]:
		res = mail.select(folder)

		status, data = mail.search(None, "UnSeen")

		mail_ids = []

		for block in data:
			mail_ids += block.split()

		for i in mail_ids:
			# Each value of i corresponds to one email here

			status, data = mail.fetch(i, "(RFC822)")

			for response_part in data:
				if isinstance(response_part, tuple):
					# len(response_part) is 3
					# response_part[0] is some standard thingie (not interesting)
					# response_part[1] contains the message headers and content (interesting, used below)
					# response_part[2] is an ending byte, b")" (not interesting)

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
							if part.get_content_type() == "text/plain":
								mail_content += part.get_payload()
					else:
						mail_content = message.get_payload()

					# So now we have the sender, subject and content (which can be searched for links)
					# Attachments are still a mystery though

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

					sender_search = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", mail_from)
					if sender_search:
						mail_from = sender_search.group(0)

					links = urlextract.URLExtract().find_urls(mail_content)

					mailObject = {"reporter": mail_from_original, "subject": mail_subject, "links": links}
					add_message(mail_from, mailObject)
check_for_emails()

@app.route("/")
def index():
	return app.send_static_file("index.html")

@app.route("/network")
def network():
	return app.send_static_file("network.html")

@app.route("/db-dump")
def db_dump():
	return json.dumps(message_db)

@app.route("/clear-db") # MUST be removed before final product
def clear_db():
	global message_db
	message_db = {}
	write_db()
	return "OK"

