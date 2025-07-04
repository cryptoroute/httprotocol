# httpprotocol

A lightweight but powerful Python HTTP client library with CLI support.

Supports GET, POST, PUT, DELETE, PATCH, file download, multipart upload, custom headers, proxies, retries, cookies, and more — all with zero external dependencies.

---

## Features

- Full HTTP method support: GET, POST, PUT, DELETE, PATCH  
- Automatic JSON response parsing (`response.json()`)  
- Cookie persistence with optional file saving  
- Multipart form-data and file upload support  
- Retry system with exponential backoff  
- Configurable per-request or global timeouts  
- Custom headers and User-Agent support  
- CLI tool (`httpcli`) included  
- Debug mode for inspecting requests  
- Proxy and basic authentication support  

---

## Installation

Install locally from source:

```bash
pip install httprotocol
