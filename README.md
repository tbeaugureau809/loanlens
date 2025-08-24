# LoanLens  

####  Video Demo: https://youtu.be/ZpJVNhKyqo8

---

> **Note**  
> This repo is a **portfolio/demo** of my first full project. It is **not intended for installation or reuse**. The code and data model show my approach; the demo video is the primary way to experience the app.


##  Project Description  

**LoanLens** is a prototype web application built for **transfer pricing analysts** and professionals working with **intercompany financing agreements**.  

The application provides a structured workflow for capturing and organizing loan agreements so that critical terms (e.g., **maturity dates, tranche amounts, interest rates**) are no longer buried in PDFs or spreadsheets. Instead, they are stored in a central database where they can be searched, analyzed, and output into reports.  

The system is designed around the four main steps analysts typically follow:  

1. **Capturing data** — entering manually or extracting loan agreement details through parser.  
2. **Reviewing data** — ensuring accuracy and completeness of captured terms.  
3. **Performing searches** — finding comparable transactions and surfacing red flags.  
4. **Documenting results** — generating reports, narratives, and supporting tables.  

By automating and standardizing these steps, LoanLens reduces the **manual burden** of keeping track of dozens or hundreds of agreements, while also improving **consistency** and making results more **defensible** for tax authorities.  

---

##  Current Features  

- **User authentication**: analysts can register and log in.  
- **Client dashboard**: view or add clients, and attach loan agreements.  
- **Agreement capture**: store essential loan terms in SQL Server for later analysis.  
- **Data centralization**: eliminates redundancy and enables automated report generation.  

---

##  Potential Enhancements  

2. **Client relationship mapping**   
   - Visualize connections between clients and agreements.  
   - Auto-populate dashboards when agreements are shared across related clients.  

3. **Editable client dashboard tables**   
   - Allow in-place editing of agreements, rather than re-entering data.  

4. **Expanded data capture**   
   - Support more fields (e.g., collateral type, jurisdiction, amendments).  

5. **Improved security**
   - Encrypt user passwords in the database.  
   - Follow best practices for authentication.  

6. **Payable vs. receivable classification**  
   - Split dashboards into inbound vs outbound loan positions for clearer reporting.  

7. **Export options**  
   - Output agreements into Excel tables or preformatted Word report templates.  

8. **Client-side entry portal**   
   - Allow clients to pre-enter agreement details or add documents before analyst review.  

---

##  Tech Stack  

- **Python 3.8+**  
- **Flask** for the web application  
- **SQL Server** (managed through SQL Server Management Studio)  
- **pandas / openpyxl** for Excel manipulation  
- - **spaCy** for natural language processing (used for text extraction/scanning features)



##  Database Schema (SQL Server)

> Managed in **SQL Server Management Studio (SSMS)**. Below are the core tables as implemented.

### **Users**

Stores login credentials for analysts.

| Column   | Type         | Notes                             |
|----------|--------------|-----------------------------------|
| id       | INT (PK)     | Identity, primary key             |
| username | VARCHAR(50)  | Unique login name                 |
| password | VARCHAR(50)  | Currently plain text (should be hashed in production) |

---

### **Clients**

Represents companies under review.

| Column     | Type          | Notes                                           |
|------------|---------------|-------------------------------------------------|
| client_id  | INT (PK)      | Identity, primary key                           |
| client_name| VARCHAR(100)  | Client name                                     |
| has_report | VARCHAR(3)    | Must be `YES` or `NO` (default = `NO`)          |

---

### **demo_loan_agreement**

Holds loan-level details tied to a client.

| Column        | Type         | Notes                              |
|---------------|--------------|------------------------------------|
| id            | INT (PK)     | Identity, primary key              |
| client_id     | INT (FK)     | References Clients(client_id)      |
| original_date | DATE         | Agreement origination date         |
| maturity_date | DATE         | Loan maturity date                 |
| currency      | VARCHAR(10)  | Currency code (e.g., USD, EUR)     |
| principal     | FLOAT        | Principal amount                   |
| interest_rate | VARCHAR(10)  | Stored as text (e.g., "5.25%")     |
| lender        | VARCHAR(255) | Lender name                        |
| borrower      | VARCHAR(255) | Borrower name                      |

---

### Example DDL (for reference / portfolio)

```sql
CREATE TABLE [dbo].[users](
    [id] INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    [username] VARCHAR(50) NOT NULL UNIQUE,
    [password] VARCHAR(50) NOT NULL
);

CREATE TABLE [dbo].[clients](
    [client_id] INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    [client_name] VARCHAR(100) NOT NULL,
    [has_report] VARCHAR(3) NOT NULL CONSTRAINT df_has_report DEFAULT('NO'),
    CONSTRAINT chk_has_report CHECK (has_report IN ('YES','NO'))
);

CREATE TABLE [dbo].[demo_loan_agreement](
    [id] INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    [client_id] INT NOT NULL FOREIGN KEY REFERENCES clients(client_id),
    [original_date] DATE NULL,
    [maturity_date] DATE NULL,
    [currency] VARCHAR(10) NULL,
    [principal] FLOAT NULL,
    [interest_rate] VARCHAR(10) NULL,
    [lender] VARCHAR(255) NULL,
    [borrower] VARCHAR(255) NULL
);
