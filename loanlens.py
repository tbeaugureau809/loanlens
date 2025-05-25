from flask import Flask, render_template, request, redirect
import pyodbc

app = Flask(__name__)

conn_str = (
    "Driver={SQL Server};"
    "Server=TROY\\SQLEXPRESS;"
    "Database=LoanOrg;"
    "Trusted_Connection=yes;"
    )

@app.route("/", methods=["GET", "POST"])
def loan_form():
    if request.method == "POST":
        original_date = request.form["original_date"]
        agreement_date = request.form["agreement_date"]
        effective_date = request.form["effective_date"]
        maturity_date = request.form["maturity_date"]
        currency = request.form["currency"]
        principal = request.form["principal"]
        interest_rate = request.form["interest_rate"]

        #allows the python code to connect to the database you have already made
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            cursor.execute(""" 
                INSERT INTO loan_agreement ( original_date, amendment_date, effective_date, maturity_date, currency, principal, interest_rate)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, original_date, agreement_date, effective_date, maturity_date, currency, principal, interest_rate)
            conn.commit()
        return redirect("/")

    return render_template("form.html")

if __name__=="__main__":
    app.run(debug=True)