from flask import Flask, request
from flask_cors import CORS
from database import get_db_connection
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
import os
import jwt
from datetime import datetime, timedelta, timezone
from functools import wraps

app = Flask(__name__)
CORS(app)

app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

@app.route("/")
def home():
    return {
        "message": "Personal Finance Management API is running!"
    }


@app.route("/register", methods=["POST"])
def register():

    data = request.get_json()

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    # Check if all fields are provided
    if not name or not email or not password:
        return {
            "error": "All fields are required"
        }, 400

    # Hash the password
    password_hash = generate_password_hash(password)

    # Connect to MySQL
    connection = get_db_connection()
    cursor = connection.cursor()

    # Check if email already exists
    cursor.execute(
        "SELECT id FROM users WHERE email = %s",
        (email,)
    )

    existing_user = cursor.fetchone()

    if existing_user:
        cursor.close()
        connection.close()

        return {
            "error": "Email already registered"
        }, 409

    # Insert new user
    cursor.execute(
        """
        INSERT INTO users (name, email, password_hash)
        VALUES (%s, %s, %s)
        """,
        (name, email, password_hash)
    )

    connection.commit()

    cursor.close()
    connection.close()

    return {
        "message": "User registered successfully"
    }, 201

@app.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return {
            "error": "Email and password are required"
        }, 400

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM users WHERE email = %s",
        (email,)
    )

    user = cursor.fetchone()

    cursor.close()
    connection.close()

    if not user:
        return {
            "error": "Invalid email or password"
        }, 401

    if not check_password_hash(user["password_hash"], password):
        return {
            "error": "Invalid email or password"
        }, 401

    token = jwt.encode(
    {
        "user_id": user["id"],
        "exp": datetime.now(timezone.utc) + timedelta(hours=24)
    },
    app.config["JWT_SECRET_KEY"],
    algorithm="HS256"
)
    return {
        "message": "Login successful",
        "token": token,
        "user": {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"]
    }
    }, 200

def token_required(f):

    @wraps(f)
    def decorated(*args, **kwargs):

        token = request.headers.get("Authorization")

        if not token:
            return {
                "error": "Token is missing"
            }, 401

        try:
            # Expected format:
            # Bearer <token>
            token = token.split(" ")[1]

            data = jwt.decode(
                token,
                app.config["JWT_SECRET_KEY"],
                algorithms=["HS256"]
            )

            user_id = data["user_id"]

        except Exception:
            return {
                "error": "Invalid or expired token"
            }, 401

        return f(user_id, *args, **kwargs)

    return decorated


@app.route("/profile", methods=["GET"])
@token_required
def profile(user_id):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        "SELECT id, name, email FROM users WHERE id = %s",
        (user_id,)
    )

    user = cursor.fetchone()

    cursor.close()
    connection.close()

    if not user:
        return {
            "error": "User not found"
        }, 404

    return {
        "user": user
    }, 200

@app.route("/transactions", methods=["POST"])
@token_required
def add_transaction(user_id):

    data = request.get_json()

    category_id = data.get("category_id")
    amount = data.get("amount")
    transaction_type = data.get("type")
    description = data.get("description")
    transaction_date = data.get("transaction_date")

    # Check required fields
    if not category_id or not amount or not transaction_type or not transaction_date:
        return {
            "error": "Category, amount, type and date are required"
        }, 400

    # Validate transaction type
    if transaction_type not in ["income", "expense"]:
        return {
            "error": "Type must be income or expense"
        }, 400

    connection = get_db_connection()
    cursor = connection.cursor()

    # Make sure the category belongs to this user
    cursor.execute(
        """
        SELECT id
        FROM categories
        WHERE id = %s 
        """,
        (category_id,)
    )

    category = cursor.fetchone()

    if not category:
        cursor.close()
        connection.close()

        return {
            "error": "Invalid category"
        }, 400

    # Insert transaction
    cursor.execute(
        """
        INSERT INTO transactions
        (user_id, category_id, amount, type, description, transaction_date)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (
            user_id,
            category_id,
            amount,
            transaction_type,
            description,
            transaction_date
        )
    )

    connection.commit()

    transaction_id = cursor.lastrowid

    cursor.close()
    connection.close()

    return {
        "message": "Transaction added successfully",
        "transaction_id": transaction_id
    }, 201

@app.route("/transactions", methods=["GET"])
@token_required
def get_transactions(user_id):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            t.id,
            c.name AS category,
            t.amount,
            t.type,
            t.description,
            t.transaction_date
        FROM transactions t
        JOIN categories c
            ON t.category_id = c.id
        WHERE t.user_id = %s
        ORDER BY t.transaction_date DESC, t.id DESC
        """,
        (user_id,)
    )

    transactions = cursor.fetchall()

    cursor.close()
    connection.close()

    return {
        "transactions": transactions
    }, 200

@app.route("/budgets", methods=["POST"])
@token_required
def add_budget(user_id):

    data = request.get_json()

    category_id = data.get("category_id")
    amount = data.get("amount")
    month = data.get("month")
    year = data.get("year")

    if not category_id or not amount or not month or not year:
        return {
            "error": "Category, amount, month and year are required"
        }, 400

    connection = get_db_connection()
    cursor = connection.cursor()

    # Check whether the category exists
    cursor.execute(
        """
        SELECT id
        FROM categories
        WHERE id = %s
        """,
        (category_id,)
    )

    category = cursor.fetchone()

    if not category:
        cursor.close()
        connection.close()
        return {"error": "Invalid category"}, 400

    # Add the budget
    cursor.execute(
        """
        INSERT INTO budgets
        (user_id, category_id, amount, month, year)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (
            user_id,
            category_id,
            amount,
            month,
            year
        )
    )

    connection.commit()

    budget_id = cursor.lastrowid

    cursor.close()
    connection.close()

    return {
        "message": "Budget added successfully",
        "budget_id": budget_id
    }, 201

@app.route("/budgets", methods=["GET"])
@token_required
def get_budgets(user_id):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            b.id,
            c.name AS category,
            b.amount,
            b.month,
            b.year
        FROM budgets b
        JOIN categories c
            ON b.category_id = c.id
        WHERE b.user_id = %s
        ORDER BY b.year DESC, b.month DESC
        """,
        (user_id,)
    )

    budgets = cursor.fetchall()

    cursor.close()
    connection.close()

    return {
        "budgets": budgets
    }, 200

if __name__ == "__main__":
    app.run(debug=True)