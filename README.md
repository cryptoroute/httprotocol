
# httprotocol

A lightweight but feature-rich Python HTTP client library with CLI support — built with **zero external dependencies**.

It offers advanced functionality inspired by `requests` while maintaining minimalism and full standard library compatibility.

## Features

- Full HTTP method support: `GET`, `POST`, `PUT`, `DELETE`, `PATCH`, `HEAD`  
- Automatic JSON response parsing (`response.json()`)  
- Unicode-safe response bodies  
- Cookie persistence with `.txt` file saving option  
- Session-like persistent connections & connection pooling  
- Multipart form-data & file upload support  
- Streaming downloads with optional progress callbacks  
- Automatic gzip/deflate response decompression  
- Proxy support (HTTP(S))  
- Basic authentication support  
- Retry system with exponential backoff for unreliable connections  
- Browser-style SSL verification (with option to disable)  
- International domain & URL handling (IDN support)  
- CLI tool `httpclient-cli` included for quick requests  
- Debug mode for inspecting requests and responses  
- Simple middleware injection for request customization  
- Minimal footprint, zero dependencies  

## Installation

```bash
pip install httprotocol
```

## Quick Example

```python
from httprotocol.client import HttpClient

client = HttpClient(debug=True)

response = client.get("https://httpbin.org/get", params={"test": "123"})
print(response.status_code)
print(response.json())
```

## CLI Example

```bash
httpclient-cli https://httpbin.org/get -X GET -H "User-Agent=MyClient"
```

## License

MIT License
