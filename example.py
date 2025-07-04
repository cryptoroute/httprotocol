from httpprotocol.client import HttpClient
import os

client = HttpClient(debug=False)

# --- GET Test
print("\n--- [GET] JSONPlaceholder Post ---")
res = client.get("https://jsonplaceholder.typicode.com/posts/1")
print(res.status_code)
print(res.json())
res.raise_for_status()

# --- POST Test (form data)
print("\n--- [POST] Postman Echo Form ---")
res = client.post(
    "https://postman-echo.com/post",
    data={"username": "testuser", "password": "1234"},
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)
print(res.status_code)
print(res.json())
res.raise_for_status()

# --- PUT Test
print("\n--- [PUT] JSONPlaceholder Update ---")
res = client.put(
    "https://jsonplaceholder.typicode.com/posts/1",
    data={"title": "updated title", "body": "new content", "userId": 1},
    headers={"Content-Type": "application/json"}
)
print(res.status_code)
print(res.json())

# --- PATCH Test
print("\n--- [PATCH] JSONPlaceholder Partial Update ---")
res = client.patch(
    "https://jsonplaceholder.typicode.com/posts/1",
    data={"title": "patched title"},
    headers={"Content-Type": "application/json"}
)
print(res.status_code)
print(res.json())

# --- DELETE Test
print("\n--- [DELETE] JSONPlaceholder Post ---")
res = client.delete("https://jsonplaceholder.typicode.com/posts/1")
print(res.status_code)
print("Deleted? =>", res.ok)

# --- RAW TEXT & HEADERS Example
print("\n--- [GET] Raw Text & Headers ---")
res = client.get("https://postman-echo.com/headers")
print("Text Content:", res.text[:100])
print("Headers:", res.headers)

# --- TIMEOUT & RETRY Test
print("\n--- [GET] Timeout Example ---")
try:
    res = client.get("https://postman-echo.com/delay/5", timeout=2)
except Exception as e:
    print("Timeout triggered:", e)

# --- BASIC AUTH Test
print("\n--- [GET] Basic Auth Example ---")
auth_client = HttpClient(auth=("postman", "password"), debug=True)
res = auth_client.get("https://postman-echo.com/basic-auth")
print(res.status_code)
print(res.json())

# --- JSON SAFE Test
print("\n--- [GET] JSON Safe Example ---")
res = client.get("https://postman-echo.com/get")
print("Safe JSON (should fallback to dict):", res.get_json_safe(default={"error": "Invalid JSON"}))

# --- STREAM RESPONSE Raw Example (Simulated with large response) ---
print("\n--- [STREAM RESPONSE] Bytes ---")
byte_count = 0
test_url = "https://postman-echo.com/bytes/1024"

for chunk in client.stream_response(test_url, chunk_size=128):
    byte_count += len(chunk)

print(f"Total Bytes Streamed: {byte_count}")

# --- CUSTOM HEADERS & USER-AGENT Example
print("\n--- [GET] Custom Headers & User-Agent ---")

custom_client = HttpClient(
    default_headers={
        "User-Agent": "MyCustomClient/1.0 (+https://example.com)",
        "X-Project-Name": "httpprotocol-lib",
        "X-Powered-By": "Python"
    },
    debug=True
)

res = custom_client.get("https://postman-echo.com/headers")

print("Status Code:", res.status_code)

headers_received = res.json().get("headers", {})
print("Returned User-Agent:", headers_received.get("user-agent"))
print("Returned X-Project-Name:", headers_received.get("x-project-name"))
print("Returned X-Powered-By:", headers_received.get("x-powered-by"))
