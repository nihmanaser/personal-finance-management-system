import requests

# Login
login_url = "http://127.0.0.1:5000/login"

login_data = {
    "email": "newuser@example.com",
    "password": "test123"
}

login_response = requests.post(
    login_url,
    json=login_data
)

token = login_response.json()["token"]

print("Login:", login_response.json())


# Add transaction
transaction_url = "http://127.0.0.1:5000/transactions"

transaction_data = {
    "category_id": 1,
    "amount": 350.00,
    "type": "expense",
    "description": "Lunch",
    "transaction_date": "2026-10-05"
}

headers = {
    "Authorization": f"Bearer {token}"
}

transaction_response = requests.post(
    transaction_url,
    json=transaction_data,
    headers=headers
)

print("Transaction status:", transaction_response.status_code)
print("Transaction response:", transaction_response.json())