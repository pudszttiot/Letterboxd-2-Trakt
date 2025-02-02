import requests

CLIENT_ID = "TRAKT_CLIENT_ID"
CLIENT_SECRET = "TRAKT_CLIENT_SECRET"
REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"

# Step 1: User Authorization
print("Visit the following URL to authorize:")
print(f"https://trakt.tv/oauth/authorize?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}")

# Step 2: User enters the code from Trakt
auth_code = input("Enter the code from Trakt: ")

# Step 3: Exchange code for Access Token
url = "https://api.trakt.tv/oauth/token"
payload = {
    "code": auth_code,
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "redirect_uri": REDIRECT_URI,
    "grant_type": "authorization_code"
}
response = requests.post(url, json=payload)

if response.status_code == 200:
    access_token = response.json()["access_token"]
    print(f"Access Token: {access_token}")
else:
    print("Error:", response.json())
