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

transactions_url = "http://127.0.0.1:5000/transactions"

headers = {
    "Authorization": f"Bearer {token}"
}

response = requests.get(
    transactions_url,
    headers=headers
)

print("Status:", response.status_code)
print("Response:", response.json())