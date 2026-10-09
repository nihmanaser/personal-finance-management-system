import requests

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

budget_url = "http://127.0.0.1:5000/budgets"

budget_data = {
    "category_id": 1,
    "amount": 5000,
    "month": 10,
    "year": 2026
}

headers = {
    "Authorization": f"Bearer {token}"
}

response = requests.post(
    budget_url,
    json=budget_data,
    headers=headers
)

print("Status:", response.status_code)
print("Response:", response.json())