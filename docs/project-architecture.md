# 🏦 Banking Management System — Project Architecture

<p align="center">
  <strong>A modular banking management application built with Python, Tkinter and SQLite.</strong>
  <br />
  Layered architecture · Separation of concerns · Reliable financial operations
</p>

---

## 📑 Table of Contents

- [1. Project Overview](#-1-project-overview)
- [2. Technology Stack](#-2-technology-stack)
- [3. System Architecture](#-3-system-architecture)
- [4. Presentation Layer](#-4-presentation-layer)
- [5. Business Logic Layer](#-5-business-logic-layer)
- [6. Data Access Layer](#-6-data-access-layer)
- [7. Database Layer](#-7-database-layer)
- [8. Database Design](#-8-database-design)
- [9. Core Banking Workflows](#-9-core-banking-workflows)
- [10. Security and Integrity](#-10-security-and-integrity)
- [11. Project Directory Structure](#-11-project-directory-structure)
- [12. Team Responsibilities](#-12-team-responsibilities)
- [13. Development Strategy](#-13-development-strategy)

---

## 🎯 1. Project Overview

The Banking Management System is a desktop application designed to manage clients, bank accounts and financial operations.

The application provides two interfaces:

- **Client Portal:** Account information, deposits, withdrawals, transfers, transaction history and statements.
- **Admin Panel:** Client management, account management, operation monitoring, reports and system statistics.

The system follows a **layered architecture**, separating the user interface, business rules, database access and data storage.

### Architectural Objectives

- Maintain clear separation of responsibilities.
- Make the code easier to test and maintain.
- Allow three developers to work in parallel.
- Protect financial data through validation and access control.
- Ensure transfers are processed atomically.
- Simplify future extensions and improvements.

---

## 🛠️ 2. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| Tkinter / ttk | Desktop graphical user interface |
| SQLite | Relational database |
| SQL | Database queries and constraints |
| `dataclasses` | Structured application models |
| `unittest` or `pytest` | Automated testing |
| Git & GitHub | Version control and collaboration |

**Additional libraries:** A PDF-generation library may be added for downloadable statements. An optional `ttk` theme can improve the visual appearance.

The project should use Python's built-in `sqlite3` module unless the team agrees on another database access library.

---

## 🏗️ 3. System Architecture

The system is divided into four layers.

```text
┌─────────────────────────────────────────────────────┐
│                  PRESENTATION LAYER                 │
│                                                     │
│       Tkinter / ttk — Client Portal & Admin         │
│                                                     │
│  Home · Authentication · Dashboard · Operations     │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│                  BUSINESS LOGIC LAYER               │
│                                                     │
│  AuthService · BankService · ReportService          │
│                                                     │
│  Validation · Banking Rules · Permissions           │
│  Deposits · Withdrawals · Transfers                 │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│                    DATA ACCESS LAYER                │
│                                                     │
│  ClientDAO · CompteDAO · OperationDAO · UserDAO     │
│                                                     │
│  CRUD · Parameterized SQL · Data Retrieval          │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│                     DATABASE LAYER                 │
│                                                     │
│                     SQLite                          │
│                                                     │
│       Clients · Accounts · Operations · Users       │
└─────────────────────────────────────────────────────┘
```

### How the layers communicate

1. The user interacts with a Tkinter screen.
2. The screen calls the appropriate service method.
3. The service validates the request and enforces business rules.
4. The service uses DAOs to retrieve or modify database records.
5. The database executes SQL operations and returns results.
6. The service returns a result or raises a meaningful exception.
7. The interface displays the result or an appropriate error message.

> **Important:** The interface must not execute banking SQL directly. All financial operations must pass through the business logic layer.

---

## 🖥️ 4. Presentation Layer

**Location:** `views/`

**Responsibility:** Display information, collect input and provide navigation.

### Main components

| File | Responsibility |
|---|---|
| `main.py` | Initialize the application and manage navigation |
| `views/home_view.py` | Home Page |
| `views/auth_view.py` | Client and administrator login |
| `views/registration_view.py` | Client registration |
| `views/dashboard_view.py` | Client and admin dashboards |
| `views/profile_view.py` | Client profile management |
| `views/clients_view.py` | Admin client management |
| `views/comptes_view.py` | Account management |
| `views/operations_view.py` | Deposits, withdrawals and transfers |
| `views/transactions_view.py` | Transaction history |
| `views/reports_view.py` | Reports and statements |
| `views/settings_view.py` | Administrative settings |

### Responsibilities

- Validate basic input formats.
- Display forms, tables and dashboard statistics.
- Call service methods.
- Display success messages and errors.
- Refresh information after successful operations.
- Hide or disable features that the current user cannot access.

The presentation layer should remain independent of SQL queries and database implementation details.

---

## ⚙️ 5. Business Logic Layer

**Location:** `services/`, `models/` and `exceptions.py`

**Responsibility:** Implement banking rules and coordinate operations.

### 5.1. `models/models.py`

Defines the main application data models using Python dataclasses.

**Client**
- Client ID
- Name
- Date of birth
- National ID
- Address
- Email
- Telephone

**Compte**
- Account ID
- Client ID
- Account number
- IBAN, if implemented
- Balance
- Status
- Opening date

**Operation**
- Operation ID
- Account ID
- Operation type
- Amount
- Operation date
- Description
- Transfer reference, when applicable

### 5.2. `services/auth_service.py`

Handles authentication and access control.

Responsibilities:

- Authenticate clients and administrators.
- Verify password hashes.
- Identify the current user's role.
- Associate a client login with the correct client record.
- Prevent unauthorized access to protected operations.

### 5.3. `services/bank_service.py`

Implements the main banking operations.

| Method | Responsibility |
|---|---|
| `ajouter_client()` | Create a client |
| `ouvrir_compte()` | Open an account |
| `cloturer_compte()` | Close an eligible account |
| `depot()` | Deposit money |
| `retrait()` | Withdraw money |
| `virement()` | Transfer money between accounts |
| `releve()` | Retrieve an account statement |

The service must validate every operation, even if the interface already validates the user's input.

### 5.4. `services/report_service.py`

Handles report generation.

Responsibilities:

- Retrieve authorized account data.
- Prepare transaction summaries.
- Generate account statements.
- Export reports to PDF, if implemented.

### 5.5. `exceptions.py`

Defines meaningful exceptions, for example:

- `SoldeInsuffisantError`
- `CompteClotureError`
- `ClientIntrouvableError`
- `CompteIntrouvableError`
- `VirementInvalideError`
- `AuthentificationError`
- `AccesInterditError`

The interface catches expected exceptions and displays clear messages.

### Core business rules

- Account balances must never become negative.
- Closed accounts must reject financial operations.
- Transfers must have a positive amount.
- Source and destination accounts must be valid and eligible.
- A client cannot access another client's private account information.
- A client with accounts cannot be deleted under the project's agreed rules.
- Both sides of a transfer must succeed together or fail together.

---

## 🗄️ 6. Data Access Layer

**Location:** `dao/` and `db_manager.py`

**Responsibility:** Separate SQL queries from banking rules.

### DAO components

| File | Responsibility |
|---|---|
| `dao/client_dao.py` | Client CRUD and client queries |
| `dao/compte_dao.py` | Account CRUD and account queries |
| `dao/operation_dao.py` | Operation records and transaction history |
| `dao/user_dao.py` | User credentials and role records |
| `db_manager.py` | Connections, schema initialization and transaction management |

### CRUD operations

CRUD stands for:

- **Create:** Insert a new record.
- **Read:** Retrieve records.
- **Update:** Modify an existing record.
- **Delete:** Remove an eligible record.

DAOs should use parameterized SQL queries rather than constructing queries by concatenating user input.

### Connection and transaction management

The team must agree on a shared database transaction interface before implementation.

For example:

- `db_manager.py` provides connection and transaction management.
- A normal DAO method can use an existing connection or obtain one through an agreed helper.
- A transfer service opens one transaction and passes the same connection to all DAO methods involved.
- Only the outer transaction manager commits or rolls back that transaction.

This prevents the debit from being committed separately from the credit.

---

## 🧱 7. Database Layer

**Technology:** SQLite

The database stores the persistent information used by both the client and admin interfaces.

### Main tables

| Table | Purpose |
|---|---|
| `clients` | Personal information about clients |
| `comptes` | Bank accounts and balances |
| `operations` | Deposits, withdrawals and transfer records |
| `users` | Login credentials, roles and account access status |

### Database responsibilities

- Maintain primary and foreign keys.
- Enforce unique identifiers.
- Validate permitted values through constraints.
- Prevent invalid relationships.
- Preserve financial transaction history.
- Support atomic financial operations.

SQLite foreign-key enforcement should be enabled on every relevant connection.

---

## 🔗 8. Database Design

### 8.1. Entity Relationship Diagram

```text
┌────────────────────┐
│      CLIENTS       │
├────────────────────┤
│ PK id              │
│ nom                │
│ prenom             │
│ date_naissance     │
│ carte_nationale    │
│ adresse            │
│ email              │
│ telephone          │
└─────────┬──────────┘
          │
          │ 1
          │
          │ N
┌─────────▼──────────┐
│      COMPTES       │
├────────────────────┤
│ PK id              │
│ FK client_id       │
│ numero_compte      │
│ iban               │
│ solde              │
│ statut             │
│ date_ouverture     │
│ date_cloture       │
└─────────┬──────────┘
          │
          │ 1
          │
          │ N
┌─────────▼──────────┐
│     OPERATIONS     │
├────────────────────┤
│ PK id              │
│ FK compte_id       │
│ type               │
│ montant            │
│ date_operation     │
│ description        │
│ reference_virement │
└────────────────────┘


┌────────────────────┐
│       USERS        │
├────────────────────┤
│ PK id              │
│ username           │
│ mot_de_passe_hash  │
│ role               │
│ FK client_id       │
│ actif              │
└────────────────────┘
```

**Relationships:**

- One client can own multiple accounts.
- One account can have multiple operation records.
- A user record may be associated with a client record.
- An administrator account does not need an associated client.

For a simple academic project, one operation record per account is sufficient. A transfer is represented by two linked operation records sharing a transfer reference: one debit and one credit.

### 8.2. Constraints

Recommended constraints include:

- Primary keys for all main tables.
- Unique client identifiers, usernames and account numbers.
- Unique IBANs if IBAN generation is implemented.
- Foreign keys between clients and accounts, accounts and operations, and users and clients.
- `CHECK (solde >= 0)` for account balances.
- `CHECK (montant > 0)` for operation amounts.
- A constraint restricting account status to supported values.
- A constraint restricting user roles to supported values.

Database constraints complement business validation; they do not replace it.

---

## 💸 9. Core Banking Workflows

### 9.1. Deposit

```text
Client Interface
      |
      ▼
BankService.depot()
      |
      ▼
Validate Account, Amount and Status
      |
      ▼
Begin Database Transaction
      |
      ├── Update Account Balance
      └── Insert Operation Record
      |
      ▼
Commit Transaction
      |
      ▼
Return Result to Interface
```

If any database step fails, the transaction should be rolled back.

### 9.2. Withdrawal

```text
Client Interface
      |
      ▼
BankService.retrait()
      |
      ▼
Validate Account, Amount and Status
      |
      ▼
Check Available Balance
      |
      ▼
Begin Database Transaction
      |
      ├── Decrease Account Balance
      └── Insert Operation Record
      |
      ▼
Commit Transaction
      |
      ▼
Return Result to Interface
```

The balance check and update must be protected against conflicting operations. Do not rely exclusively on a balance value displayed earlier in the interface.

### 9.3. Transfer

```text
Client Interface
      |
      ▼
BankService.virement()
      |
      ▼
Validate Source, Destination and Amount
      |
      ▼
Begin ONE Database Transaction
      |
      ├── Debit Source Account
      ├── Insert Debit Operation
      ├── Credit Destination Account
      └── Insert Credit Operation
      |
      ├── All Steps Succeed → COMMIT
      │
      └── Any Step Fails → ROLLBACK
      |
      ▼
Return Result to Interface
```

**Atomicity:** A transfer must never leave money debited from the source without being credited to the destination.

The debit, credit and both operation records must use the same transaction and database connection.

---

## 🔐 10. Security and Integrity

Security responsibilities are shared across the application.

### Authentication

- Store password hashes, never plaintext passwords.
- Use an appropriate password-hashing algorithm.
- Verify credentials through the authentication service.
- Restrict administrator access to authorized users.

### Authorization

- Enforce permissions in the service layer.
- Restrict clients to their own accounts and transaction records.
- Do not rely on hidden buttons as the only access-control mechanism.
- Validate ownership before returning account information.

### Financial integrity

- Validate amounts and account status in the service layer.
- Use SQL constraints as a second layer of protection.
- Use atomic database transactions for financial operations.
- Preserve transaction records for auditing.
- Avoid direct balance editing through ordinary client forms.

### Data protection

- Avoid committing real personal data or credentials to GitHub.
- Use fictional seed data for development.
- Keep local database files containing private data out of version control.
- Provide safe error messages without exposing SQL statements or sensitive details.

> **Scope note:** This is an educational banking simulation. A real banking product requires additional security controls, regulatory compliance, operational safeguards and independent security testing.

---

## 📁 11. Project Directory Structure

```text
banking-management-system/
│
├── README.md
├── requirements.txt
├── .gitignore
│
├── docs/
│   ├── user-interface.md
│   ├── project-architecture.md
│   ├── project-organisation.md
│   ├── database-schema.md
│   └── business-rules.md
│
├── database/
│   ├── schema.sql
│   └── seed.py
│
├── models/
│   ├── __init__.py
│   └── models.py
│
├── dao/
│   ├── __init__.py
│   ├── client_dao.py
│   ├── compte_dao.py
│   ├── operation_dao.py
│   └── user_dao.py
│
├── services/
│   ├── __init__.py
│   ├── bank_service.py
│   ├── auth_service.py
│   └── report_service.py
│
├── views/
│   ├── __init__.py
│   ├── home_view.py
│   ├── auth_view.py
│   ├── registration_view.py
│   ├── dashboard_view.py
│   ├── profile_view.py
│   ├── clients_view.py
│   ├── comptes_view.py
│   ├── operations_view.py
│   ├── transactions_view.py
│   ├── reports_view.py
│   └── settings_view.py
│
├── tests/
│   ├── __init__.py
│   ├── test_client_dao.py
│   ├── test_compte_dao.py
│   ├── test_operation_dao.py
│   └── test_bank_service.py
│
└── rapport/
    └── rapport.md
```

This is the target structure. Files can be added progressively as the corresponding features are implemented.

---

## 👥 12. Team Responsibilities

The project is divided among three team members.

| Team Member | Main Responsibility | Main Deliverables |
|---|---|---|
| Person 1 | Data and persistence | SQL schema, database manager, DAOs, seed data, DAO tests |
| Person 2 | Domain and business rules | Models, exceptions, banking services, service tests |
| Person 3 | Interface and user experience | Tkinter screens, navigation, forms, dashboards and UI validation |

### Integration contracts

Before parallel implementation begins, agree on:

1. DAO method names and parameters.
2. Service method signatures.
3. How database connections are passed to DAO methods.
4. Which layer owns commit and rollback.
5. Exceptions raised by each service method.
6. The format of results returned to the interface.

These agreements minimize integration conflicts.

---

## 📅 13. Development Strategy

### Week 1 — Foundation

- [ ] Agree on the architecture and method signatures.
- [ ] Implement the database schema and constraints.
- [ ] Implement the DAOs and demo data.
- [ ] Implement models and exceptions.
- [ ] Develop the banking service using mocks where necessary.
- [ ] Build the initial Tkinter screens.
- [ ] Test database and service components independently.

### Week 2 — Integration and Delivery

- [ ] Connect the interface to the services.
- [ ] Integrate authentication and permissions.
- [ ] Complete deposits, withdrawals and transfers.
- [ ] Test rollback behavior and invalid operations.
- [ ] Complete transaction history and reports.
- [ ] Fix integration issues.
- [ ] Capture screenshots and finish the report.
- [ ] Verify that the application starts correctly from a clean setup.

### Definition of Done

The initial version is ready when:

- Clients and administrators can authenticate.
- The core client and account management workflows work.
- Deposits and withdrawals update balances and operation records consistently.
- Transfers succeed or roll back completely.
- Invalid operations are rejected with clear messages.
- Tests pass and the setup instructions are reproducible.
- No real credentials or private client data are committed to the repository.

---

<p align="center">
  <strong>Banking Management System</strong>
  <br />
  <em>Modular architecture. Reliable transactions. Maintainable code.</em>
</p>