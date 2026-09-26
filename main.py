from fastapi import FastAPI, HTTPException, Depends, Security, status
from fastapi.security import APIKeyHeader
from typing import List, Optional
from pydantic import BaseModel, Field
import sqlite3

app = FastAPI(title="Operations & Ledger API")


API_KEY_NAME = "X-Admin-Key"
ADMIN_API_KEY = "admin-secret-2026"

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


def verify_admin_key(api_key: str = Security(api_key_header)):
    """Validates incoming requests for an admin key."""
    if api_key != ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Invalid or missing X-Admin-Key header",
        )
    return api_key

DATABASE = "test.db"


def get_db_connection():
    """Establishes connection and returns rows as key-value dictionaries."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name like dicts
    return conn


@app.get("/")
def home():
    return {"message": "API is running successfully!"}


@app.get("/students")
def get_all_students():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, course, fee_balance FROM students")
    rows = cursor.fetchall()
    conn.close()

    # Convert SQLite Row objects into standard Python dictionaries
    students = [dict(row) for row in rows]
    return {"count": len(students), "data": students}


@app.get("/students/payments")
def get_students_with_payments():
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
    SELECT 
        students.name,
        students.course,
        payments.amount,
        payments.payment_date
    FROM students
    JOIN payments ON students.id = payments.student_id;
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    records = [dict(row) for row in rows]
    return {"count": len(records), "data": records}

from pydantic import BaseModel, Field


# 1. Define the incoming request schema
class StudentCreate(BaseModel):
    name: str = Field(..., min_length=2, example="Tanishq Dethe")
    course: str = Field(..., example="Python Backend")
    fee_balance: float = Field(default=0.0, ge=0.0)


# 2. POST endpoint to insert a new student
@app.post("/students", status_code=201)
def create_student(student: StudentCreate):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Parameterized SQL query: Using ? prevents SQL injection attacks
    query = """
    INSERT INTO students (name, course, fee_balance)
    VALUES (?, ?, ?);
    """
    cursor.execute(query, (student.name, student.course, student.fee_balance))
    conn.commit()  # Saves the transaction permanently to disk

    new_id = cursor.lastrowid
    conn.close()

    return {
        "message": "Student created successfully",
        "student_id": new_id,
        "data": student.dict(),
    }

# 1. Pydantic schema for incoming payment data
class PaymentCreate(BaseModel):
    student_id: int = Field(
        ..., description="The ID of the student making the payment"
    )
    amount: float = Field(..., gt=0.0, description="Payment amount must be greater than 0")



@app.post(
    "/payments/batch",
    status_code=201,
    dependencies=[Depends(verify_admin_key)],
)
def record_batch_payments(payments: List[PaymentCreate]):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
       
        cursor.execute(
            "SELECT id, name, fee_balance FROM students WHERE id = ?",
            (payment.student_id,),
        )
        student = cursor.fetchone()

        if not student:
            raise HTTPException(
                status_code=404,
                detail=f"Student with ID {payment.student_id} not found.",
            )

        current_balance = student["fee_balance"]

        # Step B: Business logic validation
        if payment.amount > current_balance:
            raise HTTPException(
                status_code=400,
                detail=f"Payment amount ({payment.amount}) exceeds current balance ({current_balance}).",
            )

        # Step C: Insert payment record
        cursor.execute(
            "INSERT INTO payments (student_id, amount) VALUES (?, ?)",
            (payment.student_id, payment.amount),
        )

        # Step D: Deduct balance from student record
        new_balance = current_balance - payment.amount
        cursor.execute(
            "UPDATE students SET fee_balance = ? WHERE id = ?",
            (new_balance, payment.student_id),
        )

        # Step E: Commit both operations together
        conn.commit()

        return {
            "message": "Payment recorded successfully",
            "student_id": payment.student_id,
            "student_name": student["name"],
            "amount_paid": payment.amount,
            "remaining_balance": new_balance,
        }

    except HTTPException:
        # Re-raise explicit HTTP errors without rolling back manually
        conn.rollback()
        raise
    except Exception as e:
        # Roll back changes on unexpected server errors
        conn.rollback()
        raise HTTPException(
            status_code=500, detail=f"Transaction failed: {str(e)}"
        )
    finally:
        conn.close()

@app.get("/reports/summary", dependencies=[Depends(verify_admin_key)])
def get_financial_summary():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Query 1: Overall totals across the entire institution
    overall_query = """
    SELECT 
        COUNT(id) AS total_students,
        COALESCE(SUM(fee_balance), 0.0) AS total_outstanding_dues
    FROM students;
    """
    cursor.execute(overall_query)
    overall_stats = dict(cursor.fetchone())

    # Query 2: Total cash collected from all completed payments
    revenue_query = """
    SELECT 
        COALESCE(SUM(amount), 0.0) AS total_revenue_collected,
        COUNT(payment_id) AS total_transactions
    FROM payments;
    """
    cursor.execute(revenue_query)
    revenue_stats = dict(cursor.fetchone())

    # Query 3: Breakdown per student (aggregating payments made vs remaining balance)
    breakdown_query = """
    SELECT 
        s.id,
        s.name,
        s.course,
        s.fee_balance AS remaining_due,
        COALESCE(SUM(p.amount), 0.0) AS total_paid
    FROM students s
    LEFT JOIN payments p ON s.id = p.student_id
    GROUP BY s.id;
    """
    cursor.execute(breakdown_query)
    breakdown = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {
        "summary": {
            "total_students": overall_stats["total_students"],
            "total_outstanding_dues": overall_stats["total_outstanding_dues"],
            "total_revenue_collected": revenue_stats[
                "total_revenue_collected"
            ],
            "total_transactions": revenue_stats["total_transactions"],
        },
        "student_breakdown": breakdown,
    }

@app.get("/students/defaulters")
def get_defaulters(
    min_balance: float = 0.0,
    course: Optional[str] = None,
    limit: int = 10,
):
    """Fetches students with outstanding balances, sorted from highest to lowest.

    Allows filtering by minimum balance threshold and course.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Dynamic SQL construction with parameterized queries
    query = """
    SELECT id, name, course, fee_balance
    FROM students
    WHERE fee_balance > ?
    """
    params = [min_balance]

    # Add optional course filter if provided in query params
    if course:
        query += " AND LOWER(course) = LOWER(?)"
        params.append(course)

    # Sort highest debt first and limit results
    query += " ORDER BY fee_balance DESC LIMIT ?;"
    params.append(limit)

    cursor.execute(query, tuple(params))
    defaulters = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return {
        "filters_applied": {
            "min_balance": min_balance,
            "course": course,
            "limit": limit,
        },
        "count": len(defaulters),
        "defaulters": defaulters,
    }