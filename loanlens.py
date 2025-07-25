from pydoc import text
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import pyodbc

from scanner.scanner_interface import run_scanner_script
import os

from util.normalize import normalize_name

app = Flask(__name__)

app.secret_key = "bears_eat_beats"

conn_str = (
    "Driver={SQL Server};"
    "Server=TROY\\SQLEXPRESS;"
    "Database=LoanOrg;"
    "Trusted_Connection=yes;"
    )
## This is the starting page
@app.route("/", methods=["GET", "POST"])
def homepage():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

    return render_template("home.html")
## Dashboard is where you can select clients or add a new client. Returns you back to dashboard.html
@app.route("/dashboard")
def dashboard():
    with pyodbc.connect(conn_str) as conn:
        cursor=conn.cursor()
        cursor.execute("SELECT client_id,client_name FROM clients WHERE has_report = 'YES'")
        clients = cursor.fetchall()

    return render_template("dashboard.html", clients=clients)
## Route that from Dashboard you can add a new client. Returns add_client.html
@app.route("/add-client", methods=["GET","POST"])
def add_client():
    if request.method=="POST":
        raw_name = request.form["client_name"]
        normal_name=normalize_name(raw_name)

        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM clients WHERE LOWER(REPLACE(REPLACE(REPLACE(client_name, ' ', ''), '-', ''), '.','')) = ?", normal_name)
            result = cursor.fetchone()

            if result[0]>0:
                return "client already exists"
            cursor.execute("INSERT INTO clients(client_name, has_report) VALUES(?,?)", raw_name, 'YES')
            conn.commit()
            return redirect(url_for("dashboard"))

    return render_template("add_client.html")

#route and html page for adding agreements. When finished it redirects you to agreement_entry.html
@app.route("/add-agreement", methods=["GET", "POST"])
def loan_form():

    client_id = session.get("client_id")
    if not client_id:
        return "missing client id", 400


    if request.method == "POST":
        borrower = request.form["borrower"]
        lender = request.form["lender"]
        original_date = request.form["original_date"]
        maturity_date = request.form["maturity_date"]
        currency = request.form["currency"]
        principal = request.form["principal"]
        interest_rate = request.form["interest_rate"]
        
        if not borrower or not lender or not original_date or not maturity_date or not currency or not principal or not interest_rate:
            return "Missing Required Fields", 400
        if not all(field.replace(" ","").isalpha() and len(field) <= 100 for field in [borrower, lender, currency]):
            return "Invalid characters for parties or too long of entry"
        try: 
            principal_value = float(principal)
            if principal_value <= 0:
                return "principal must be a positive number", 400
        except ValueError:
            return "Invalid principal format", 400
        try:
            interest_clean = interest_rate.strip().replace("%","")
            interest_value = float(interest_clean)
            if interest_value <= 0 or interest_value > 100:
                return "Interest rate must be between 0 and 100", 400
        except ValueError:
            return "Invalid interest rate format", 400

        #allows the python code to connect to the database you have already made
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            cursor.execute(""" 
                INSERT INTO demo_loan_agreement ( client_id, lender, borrower, original_date, maturity_date, currency, principal, interest_rate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, client_id, lender, borrower, original_date, maturity_date, currency, principal, interest_rate)
            conn.commit()
        return redirect(url_for("client_dashboard", client_id=client_id))

    return render_template("agreement_entry.html", client_id=client_id)

@app.route("/scan-agreement", methods=["GET", "POST"])
def scan_agreement():
    client_id = session.get("client_id")
    if not client_id:
        return "missing client id", 400

    if request.method == "POST":
        uploaded_file = request.files.get("agreement_file")
        if not uploaded_file or uploaded_file.filename == "":
            return "No file uploaded", 400

        temp_path = os.path.join("temp_uploads", uploaded_file.filename)
        os.makedirs("temp_uploads", exist_ok=True)
        uploaded_file.save(temp_path)

        data = run_scanner_script(temp_path)
        os.remove(temp_path)

        with pyodbc.connect(conn_str) as conn:
            cursor  = conn.cursor()
            cursor.execute("""
            INSERT INTO demo_loan_agreement(
                client_id,original_date, maturity_date, currency, principal, interest_rate, lender, borrower
                )
                VALUES (?,?,?,?,?,?,?,?)
                """, client_id,
                data.get("original_date"),
                data.get("maturity_date"),
                data.get("currency"),
                data.get("principal"),
                data.get("interest_rate"),
                data.get("lender"),
                data.get("borrower")
                
                

                )
            conn.commit()
        return redirect(url_for("client_dashboard", client_id=client_id))


## Takes the client number so that have that information for the Client Dashboard
@app.route("/client/<int:client_id>")
def client_dashboard(client_id):

    with pyodbc.connect(conn_str) as conn:
        cursor=conn.cursor()
        cursor.execute("SELECT client_name FROM clients WHERE client_id = ?", client_id)
        client = cursor.fetchone()
        client_name = client[0]

        if not client:
            return "Client not found", 404
        session['client_id'] = client_id
    return render_template("client_dashboard.html", client_name=client_name)

## Simply redirects me to the client_dashboard 
@app.route("/go-to-client", methods=["POST"])
def go_to_client():
    client_id = request.form.get("client")
    if not client_id:
        return "No Client selected",400

    return redirect(url_for("client_dashboard", client_id=client_id))

@app.route('/api/loans')
def api_loans():
    client_id = session.get('client_id')
    if not client_id:
        return jsonify([]), 400

    try:
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    lender,
                    borrower,
                    original_date,
                    currency,
                    principal, 
                    interest_rate,
                    maturity_date 
                FROM demo_loan_agreement
                WHERE client_id = ?
            """, client_id)
         
            cols = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            loans = [dict(zip(cols,row)) for row in rows]

    except Exception as e:
        app.logger.error("Error in /api/loans:", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500
    return jsonify(loans)
if __name__=="__main__":
    app.run(debug=True)