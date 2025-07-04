from httpclient.client import HttpClient  # Adjusted import to your project structure
import os

client = HttpClient(debug=True)

# --- GET Test
print("\n--- [GET] JSONPlaceholder Post ---")
res = client.get("https://jsonplaceholder.typicode.com/posts/1")
print(res.status_code)
print(res.json())
res.raise_for_status()

# --- POST Test (Form Data)
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
print("Text Content (first 100 chars):", res.text[:100])
print("Headers:", dict(res.headers))

# --- TIMEOUT & RETRY Test
print("\n--- [GET] Timeout Example ---")
try:
    res = client.get("https://postman-echo.com/delay/5", timeout=2)
    print(res.status_code)
except Exception as e:
    print("Timeout triggered or retried out:", e)

# --- BASIC AUTH Test
print("\n--- [GET] Basic Auth Example ---")
auth_client = HttpClient(auth=("postman", "password"), debug=True)
res = auth_client.get("https://postman-echo.com/basic-auth")
print(res.status_code)
print(res.json())

# --- JSON SAFE Test
print("\n--- [GET] JSON Safe Example ---")
res = client.get("https://postman-echo.com/get")
safe_json = res.get_json_safe(default={"error": "Invalid JSON"})
print("Safe JSON Fallback Example:", safe_json)

# --- STREAM RESPONSE Raw Example (Simulated with large response) ---
print("\n--- [STREAM RESPONSE] Bytes ---")
byte_count = 0
test_url = "https://postman-echo.com/bytes/1024"

for chunk in client.stream_response(test_url, chunk_size=128):
    byte_count += len(chunk)

print(f"Total Bytes Streamed: {byte_count}")

# --- DOWNLOAD FILE Example ---
print("\n--- [DOWNLOAD FILE] Example ---")
dest_file = "test_download.bin"
client.download("https://postman-echo.com/bytes/512", dest_file)
print(f"File downloaded: {dest_file} (size: {os.path.getsize(dest_file)} bytes)")
os.remove(dest_file)
