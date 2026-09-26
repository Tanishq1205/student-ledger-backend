# Student Operations & Financial Ledger API

A high-performance backend ledger system built with Python, FastAPI, and SQLite. The service manages academic records, processes multi-table financial transactions with ACID guarantees, and generates aggregated debt and revenue analytics.

---

## 🌐 Live Service & Documentation
* **Interactive API Documentation (Swagger UI):** [https://student-ledger-backend.onrender.com/docs](https://student-ledger-backend.onrender.com/docs)
* **Base API Health Check:** [https://student-ledger-backend.onrender.com](https://student-ledger-backend.onrender.com)
* **Repository:** [https://github.com/Tanishq1205/student-ledger-backend](https://github.com/Tanishq1205/student-ledger-backend)

---

## Key Features

- **Relational Data Modeling:** Normalized SQLite schema with foreign key constraints linking student profiles to ledger transactions.
- **ACID-Compliant Transactions:** Automatic balance deduction with atomic commits and manual rollbacks to prevent inconsistent ledger states.
- **Batch Processing:** Handles multiple payment settlements within a single atomic database transaction.
- **Financial Analytics & Aggregations:** Dynamic SQL reporting calculating outstanding dues, collected revenue, and debtor rankings using `SUM`, `COALESCE`, and `GROUP BY`.
- **API Key Security:** Header-based authentication (`X-Admin-Key`) safeguarding financial summaries and batch processing operations.
- **Interactive Documentation:** Auto-generated OpenAPI (Swagger) interface for schema validation and testing.

---

## Tech Stack

- **Framework:** FastAPI
- **Data Validation:** Pydantic
- **Database:** SQLite3
- **Server:** Uvicorn (ASGI)

---

## API Endpoints

| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/students` | Public | List all registered students |
| `POST` | `/students` | Public | Register a student with balance validation |
| `PATCH` | `/students/{id}/balance` | Public | Update a student's outstanding balance |
| `POST` | `/payments` | Public | Record individual payment with ACID balance deduction |
| `POST` | `/payments/batch` | **Admin** | Process multiple payment records atomically |
| `GET` | `/students/defaulters` | Public | Query outstanding debtors filtered by course & balance |
| `GET` | `/reports/summary` | **Admin** | Aggregated institutional financial breakdown |

---

## Getting Started

### 1. Clone & Set Up Virtual Environment

```bash
git clone [https://github.com/](https://github.com/)<Tanishq1205>/student-ledger-backend.git
cd ledger-api
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate
pip install -r requirements.txt