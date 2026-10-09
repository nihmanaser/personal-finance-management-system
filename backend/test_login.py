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

print("Login status:", login_response.status_code)
print("Login response:", login_response.json())

token = login_response.json()["token"]

profile_url = "http://127.0.0.1:5000/profile"

headers = {
    "Authorization": f"Bearer {token}"
}

profile_response = requests.get(
    profile_url,
    headers=headers
)

print("Profile status:", profile_response.status_code)
print("Profile response:", profile_response.json())