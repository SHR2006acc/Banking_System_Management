# 🏦 Banking Management System — User Interface

<p align="center">
  <strong>A desktop banking application built with Python, Tkinter and SQLite.</strong>
  <br />
  A simple, organized interface for clients and bank administrators.
</p>

---

## 📑 Table of Contents

- [1. Overview](#-1-overview)
- [2. Application Navigation](#-2-application-navigation)
- [3. Home Page](#-3-home-page)
- [4. Client Portal](#-4-client-portal)
- [5. Admin Panel](#-5-admin-panel)
- [6. Authentication & Registration](#-6-authentication--registration)
- [7. Interface Design Guidelines](#-7-interface-design-guidelines)
- [8. Error Handling & Validation](#-8-error-handling--validation)
- [9. Implementation Structure](#-9-implementation-structure)
- [10. Development Priorities](#-10-development-priorities)

---

## 🎯 1. Overview

The Banking Management System provides a graphical user interface (GUI) for managing clients, bank accounts and financial operations.

The interface is divided into three main areas:

| Area | Purpose | Access |
|---|---|---|
| 🏠 Home Page | Navigation, bank information and authentication | Everyone |
| 👤 Client Portal | Personal accounts, transactions and statements | Authenticated clients |
| 🛡️ Admin Panel | Client management, accounts, operations and reports | Authorized administrators |

**Technology:** Python · Tkinter/ttk · SQLite

> **Design principle:** The interface collects user input and displays results. All banking rules and permissions are enforced by the business logic layer.

---

## 🧭 2. Application Navigation

```text
                    🏦 BANKING MANAGEMENT SYSTEM
                               |
                           HOME PAGE
                               |
             ┌─────────────────┼─────────────────┐
             |                 |                 |
        Client Login      Registration       Admin Login
             |                 |                 |
             |          Create Client Profile    |
             |                 |                 |
             |           Open Account            |
             |                 |                 |
             ▼                 ▼                 ▼
       CLIENT PORTAL       CLIENT PORTAL      ADMIN PANEL
             |                                   |
     ┌───────┼────────┐                  ┌───────┼────────┐
     |       |        |                  |       |        |
 Dashboard Profile Accounts          Dashboard Clients Accounts
     |       |        |                  |       |        |
 Operations Transactions               Operations Reports
     |       |                           |        |
 Statements Security                  Reports  Settings
     |                                   |        |
     └─────────────── Logout ────────────┴────────┘
```

### Navigation Rules

- Clients must log in before accessing private account information.
- Administrators must use a separate authorized login.
- Registration creates a client profile and initiates the account-opening workflow.
- Clients can only access their own accounts and transactions.
- Administrators can access management features according to their permissions.
- Logout returns the user to the Home Page.

---

## 🏠 3. Home Page

**Purpose:** Provide the main entry point to the application.

### Components

- Bank name and logo
- Welcome message
- Client Login button
- Client Registration button
- Admin Login button
- About the Bank
- Banking Policies
- Contact Information

### Navigation

```text
HOME PAGE
├── Client Login
│   └── Client Authentication
├── Client Registration
│   └── Registration Form
├── Admin Login
│   └── Administrator Authentication
├── About the Bank
├── Policies
└── Contact Information
```

The Home Page must not display private client information or account balances.

---

## 👤 4. Client Portal

The Client Portal allows authenticated clients to view their information and perform permitted banking operations.

### 4.1. Dashboard

**Purpose:** Provide an overview of the client's banking activity.

**Components:**
- Personalized welcome message
- Total account balance
- Account status
- Number of accounts
- Quick-action buttons
- Recent transactions

**Quick Actions:**

| Action | Destination |
|---|---|
| Deposit | Deposit form |
| Withdraw | Withdrawal form |
| Transfer | Transfer form |
| View Statements | Reports and Statements |

### 4.2. My Profile

**Purpose:** Display and update personal information.

**Information displayed:**
- First and last name
- Date of birth
- National ID card number
- Address
- Email
- Telephone number

**Available actions:**
- View personal information
- Edit permitted information
- Change password

Sensitive identifiers should be displayed only when necessary and protected from unauthorized access.

### 4.3. My Accounts

**Purpose:** Display accounts belonging to the authenticated client.

**Account information:**
- Account number
- IBAN, if implemented
- Current balance
- Account status
- Account opening date

**Available actions:**
- View account details
- Select an account for an operation
- Download an account confirmation document

Clients must not be able to change account balances directly.

### 4.4. Operations

**Purpose:** Allow clients to perform permitted banking operations.

#### 💰 Deposit

1. Select an account.
2. Enter the amount.
3. Validate the amount.
4. Confirm the operation.
5. Display the result and updated balance.

#### 💸 Withdrawal

1. Select an account.
2. Enter the amount.
3. Validate the amount and available balance.
4. Confirm the operation.
5. Display the result and updated balance.

#### 🔄 Transfer

1. Select the source account.
2. Enter the recipient's account number.
3. Enter the transfer amount.
4. Validate the recipient and amount.
5. Display the transfer summary.
6. Confirm the transfer.
7. Optionally request a transaction PIN.
8. Display the result and updated balances.

**Important:** Both sides of a transfer and both transaction records must be saved in one atomic database transaction.

### 4.5. Transactions

**Purpose:** Display the client's transaction history.

**Features:**
- View deposits, withdrawals and transfers
- Search transactions
- Filter by transaction type
- Filter by date range
- View transaction details

**Suggested table columns:**

| Date | Type | Description | Amount |
|---|---|---|---:|
| 18/10/2026 | Deposit | Cash deposit | +500.00 |
| 18/10/2026 | Withdrawal | Cash withdrawal | -100.00 |
| 18/10/2026 | Transfer | Money transfer | -50.00 |

*Illustrative data only. Currency and formatting should be configured consistently.*

### 4.6. Reports and Statements

**Purpose:** Generate documents containing account and transaction information.

**Features:**
- Select an account
- Select a date range
- Generate an account statement
- Download a statement as PDF
- Export transaction history
- Download account confirmation information

Documents must contain only information the authenticated client is authorized to access.

### 4.7. Bank Information

**Purpose:** Provide general information about the bank.

**Sections:**
- About the Bank
- Available Services
- Contact Information
- Banking Policies
- Terms and Conditions
- Updates and Announcements

This section can be accessible from the Home Page as well.

### 4.8. Security

**Purpose:** Provide basic account security controls.

**Features:**
- Change password
- Set or change transaction PIN, if implemented
- Secure logout

Passwords must never be displayed in plaintext or stored as plaintext.

---

## 🛡️ 5. Admin Panel

The Admin Panel provides authorized administrators with tools for managing clients, accounts and operations.

### 5.1. Dashboard

**Purpose:** Present an overview of the banking system.

**Statistics:**
- Total number of clients
- Total number of accounts
- Total account balances
- Total number of operations
- Transaction statistics
- Financial charts

> Total account balances are not the same as bank profit. Profit calculations require separate financial revenue and expense data.

### 5.2. Client Management

**Features:**
- View all clients
- Search clients by name, email or identifier
- Register a client
- Update client information
- View client details
- Delete a client only if the agreed business rules allow it

### 5.3. Account Management

**Features:**
- View all accounts
- Open an account for an existing client
- View account information
- Check account balance and status
- Close an account according to the bank's rules

An account should not be closed while it has an outstanding balance unless a specific, documented procedure allows it.

### 5.4. Operations Management

**Features:**
- View all operations
- Search transactions
- Filter by transaction type or date
- View transaction details
- Monitor deposits, withdrawals and transfers

Financial records should be preserved for auditing rather than silently edited or deleted.

### 5.5. Reports

**Features:**
- Client reports
- Account reports
- Transaction reports
- Financial statistics
- PDF report generation

### 5.6. Settings

**Features:**
- Manage administrator access
- Configure application settings
- Manage security settings

Access to administrative functions must be restricted by role and permission checks.

---

## 🎨 6. Authentication & Registration

### 6.1. Client Login

**Fields:**
- Username or email
- Password

**Actions:**
- Login
- Navigate to registration
- Return to Home Page

### 6.2. Client Registration

**Fields:**
- First name
- Last name
- Date of birth
- National ID card number
- Address
- Email
- Telephone
- Username
- Password
- Confirm password

**Registration workflow:**

```text
Registration Form
       |
Validate Inputs
       |
Check Unique Identifiers
       |
Create Client Profile
       |
Open Bank Account
       |
Display Account Confirmation
```

The client profile and bank account are separate database entities, even if the registration workflow creates both.

### 6.3. Admin Login

**Fields:**
- Administrator username
- Password

Administrative accounts should be created through a controlled setup process, not through public client registration.

---

## 🖌️ 7. Interface Design Guidelines

The application should use a consistent visual style across all screens.

| Element | Recommendation |
|---|---|
| Framework | Tkinter with `ttk` widgets |
| Navigation | Sidebar or notebook tabs |
| Data tables | `ttk.Treeview` |
| Forms | Labels, entries, selectors and buttons |
| Notifications | `messagebox` dialogs |
| Layout | Consistent spacing and alignment |
| Theme | A clean, readable `ttk` theme |
| Currency | Consistent formatting |
| Dates | Consistent date format |

### Recommended Layout

```text
┌─────────────────────────────────────────────────────┐
│ Bank Name                              User / Logout │
├──────────────┬──────────────────────────────────────┤
│              │                                      │
│  Dashboard   │         Page Title                   │
│  Profile     │                                      │
│  Accounts    │         Main Content                 │
│  Operations  │         Forms / Tables / Cards       │
│  Transactions│                                      │
│  Reports     │                                      │
│  Security    │                                      │
│              │                                      │
└──────────────┴──────────────────────────────────────┘
```

Use a layout that fits the screen and allows tables and forms to resize where appropriate.

---

## ⚠️ 8. Error Handling & Validation

The interface must provide clear feedback for invalid input and failed operations.

| Situation | Expected behavior |
|---|---|
| Empty required field | Display a validation message |
| Invalid amount | Reject the input |
| Insufficient balance | Explain that the balance is insufficient |
| Closed account | Reject the operation |
| Unknown recipient | Display a suitable error |
| Incorrect credentials | Display a generic authentication error |
| Unauthorized action | Deny access |
| Database failure | Display a safe error message and preserve transaction integrity |
| Successful operation | Display confirmation and refresh the relevant data |

The UI must call the business service rather than executing banking SQL directly.

---

## 🧩 9. Implementation Structure

The interface is implemented in the `views/` directory.

```text
views/
├── home_view.py
├── auth_view.py
├── registration_view.py
├── dashboard_view.py
├── profile_view.py
├── clients_view.py
├── comptes_view.py
├── operations_view.py
├── transactions_view.py
├── reports_view.py
└── settings_view.py
```

| File | Responsibility |
|---|---|
| `home_view.py` | Home Page and main navigation |
| `auth_view.py` | Client and admin login |
| `registration_view.py` | Client registration |
| `dashboard_view.py` | Dashboard views |
| `profile_view.py` | Client profile and password changes |
| `clients_view.py` | Admin client management |
| `comptes_view.py` | Account management |
| `operations_view.py` | Deposits, withdrawals and transfers |
| `transactions_view.py` | Transaction history |
| `reports_view.py` | Statements and reports |
| `settings_view.py` | Administrative settings |

The `main.py` file initializes the application and coordinates navigation between views.

The business logic is implemented separately in `services/`, and database access is handled by `dao/` and `db_manager.py`.

---

## 🚀 10. Development Priorities

To meet the two-week deadline, implement features in the following order.

### Phase 1 — Core Interface
- [ ] Home Page
- [ ] Client Login
- [ ] Admin Login
- [ ] Client Registration
- [ ] Basic navigation

### Phase 2 — Banking Features
- [ ] Client Dashboard
- [ ] Client Profile
- [ ] Account Management
- [ ] Deposits and Withdrawals
- [ ] Transfers
- [ ] Transaction History

### Phase 3 — Administration & Reports
- [ ] Admin Dashboard
- [ ] Client Management
- [ ] Account Management
- [ ] Operations Monitoring
- [ ] Reports and Statements

### Phase 4 — Quality & Security
- [ ] Input validation
- [ ] Error handling
- [ ] Permission checks
- [ ] Consistent styling
- [ ] Integration testing
- [ ] Screenshots and documentation

---

<p align="center">
  <strong>Banking Management System</strong>
  <br />
  <em>Clear navigation. Reliable operations. Secure data.</em>
</p>