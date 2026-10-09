import requests

url = "http://127.0.0.1:5000/register"

data = {
    "name": "Test User",
    "email": "newuser@example.com",
    "password": "test123"
}

response = requests.post(url, json=data)

print("Status:", response.status_code)
print("Response:", response.json())