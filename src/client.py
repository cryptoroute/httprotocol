import urllib.request
import urllib.parse
import http.cookiejar
import mimetypes
import uuid
import json
import ssl
import base64
import os
import time
import gzip
import io
import logging
import threading
from typing import Optional, Dict, Union, Callable, Generator


class HttpResponse:
    def __init__(self, status_code, text, headers, url, reason, raw_response=None, raw_bytes=None, cookies=None):
        self.status_code = status_code
        self.text = text
        self.headers = dict(headers)
        self.url = url
        self.reason = reason
        self.raw_response = raw_response
        self.content = raw_bytes
        self.cookies = cookies or {}

    def json(self):
        try:
            return json.loads(self.text)
        except json.JSONDecodeError:
            return None

    def get_json_safe(self, default=None):
        try:
            return json.loads(self.text)
        except Exception:
            return default

    @property
    def ok(self):
        return 200 <= self.status_code < 300

    @property
    def is_success(self):
        return self.ok

    def raise_for_status(self):
        if not self.ok:
            raise Exception(f"HTTP {self.status_code} {self.reason}")


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class HttpClient:
    RETRY_STATUSES = {429, 500, 502, 503, 504}

    def __init__(
        self,
        timeout=10,
        proxies: Optional[Dict[str, str]] = None,
        auth: Optional[tuple] = None,
        follow_redirects=True,
        cookie_file: Optional[str] = None,
        default_headers: Optional[Dict[str, str]] = None,
        max_retries=3,
        backoff_factor=1.0,
        debug=False
    ):
        self.timeout = timeout
        self.proxies = proxies
        self.auth = auth
        self.follow_redirects = follow_redirects
        self.ssl_context = ssl.create_default_context()
        self.cookie_jar = http.cookiejar.LWPCookieJar(cookie_file) if cookie_file else http.cookiejar.CookieJar()
        self.cookie_file = cookie_file
        self.default_headers = default_headers or {
            "User-Agent": "HttpClient/4.0",
            "Accept-Encoding": "gzip, deflate",
            "Accept": "*/*",
            "Connection": "keep-alive"
        }
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.middleware = []
        self._lock = threading.Lock()

        self.logger = logging.getLogger("HttpClient")
        self.logger.setLevel(logging.DEBUG if debug else logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("[%(name)s] %(message)s"))
        self.logger.addHandler(handler)

        if self.cookie_file and os.path.exists(self.cookie_file):
            self.cookie_jar.load(ignore_discard=True)

    def _log(self, *args):
        self.logger.debug(" ".join(map(str, args)))

    def _log_request(self, method, url, headers):
        self._log(f"=> {method} {url}")
        for k, v in headers.items():
            self._log(f"=> {k}: {v}")

    def _log_response(self, response, text):
        self._log(f"<= Status: {response.status} {response.reason}")
        self._log(f"<= URL: {response.geturl()}")
        self._log("<= Headers:")
        for k, v in response.headers.items():
            self._log(f"<= {k}: {v}")
        short = text.strip()
        self._log("<= Body:", short[:200] + ("..." if len(short) > 200 else ""))

    def add_middleware(self, fn: Callable):
        self.middleware.append(fn)

    def _apply_middleware(self, req):
        for fn in self.middleware:
            req = fn(req)
        return req

    def _build_opener(self):
        handlers = [
            urllib.request.HTTPCookieProcessor(self.cookie_jar),
            urllib.request.HTTPSHandler(context=self.ssl_context)
        ]
        if self.proxies:
            handlers.append(urllib.request.ProxyHandler(self.proxies))
        if not self.follow_redirects:
            handlers.append(NoRedirectHandler())
        return urllib.request.build_opener(*handlers)

    def _build_headers(self, headers: Optional[Dict[str, str]]):
        final_headers = self.default_headers.copy()
        if headers:
            final_headers.update(headers)
        if self.auth:
            user_pass = f"{self.auth[0]}:{self.auth[1]}"
            encoded = base64.b64encode(user_pass.encode()).decode()
            final_headers["Authorization"] = f"Basic {encoded}"
        return final_headers

    def _retry_request(self, func, *args, **kwargs):
        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            try:
                result = func(*args, **kwargs)
                if isinstance(result, HttpResponse) and result.status_code in self.RETRY_STATUSES:
                    raise Exception(f"Retry due to status code {result.status_code}")
                return result
            except urllib.error.HTTPError as e:
                error_body = e.read().decode(errors="replace")
                self._log(f"HTTP {e.code} Error: {e.reason}")
                self._log("Error Body:", error_body[:200] + ("..." if len(error_body) > 200 else ""))
                last_exception = e
                if e.code not in self.RETRY_STATUSES:
                    raise e
                time.sleep(self.backoff_factor * (2 ** (attempt - 1)))
            except Exception as e:
                self._log(f"Retry {attempt}/{self.max_retries} failed:", e)
                last_exception = e
                time.sleep(self.backoff_factor * (2 ** (attempt - 1)))
        raise last_exception

    def _decompress(self, response, data: bytes) -> str:
        encoding = response.headers.get("Content-Encoding", "").lower()
        if "gzip" in encoding:
            return gzip.decompress(data).decode()
        elif "deflate" in encoding:
            return io.BytesIO(data).read().decode()
        return data.decode()

    def _parse_cookies(self):
        return {cookie.name: cookie.value for cookie in self.cookie_jar}

    def _request(self, url: str, data: Optional[Union[bytes, dict]] = None, headers: Optional[Dict[str, str]] = None, method: str = "GET", timeout: Optional[int] = None) -> HttpResponse:
        headers = self._build_headers(headers)
        if isinstance(data, dict):
            content_type = headers.get("Content-Type", "").lower()
            if content_type == "application/json":
                data = json.dumps(data).encode("utf-8")
            elif content_type == "application/x-www-form-urlencoded":
                data = urllib.parse.urlencode(data).encode("utf-8")
            else:
                headers["Content-Type"] = "application/json"
                data = json.dumps(data).encode("utf-8")

        req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
        req = self._apply_middleware(req)
        opener = self._build_opener()

        def do_open():
            try:
                with opener.open(req, timeout=timeout or self.timeout) as response:
                    raw = response.read()
            except urllib.error.HTTPError as e:
                response = e
                raw = e.read()

            text = self._decompress(response, raw)
            self._log_request(method, url, headers)
            self._log_response(response, text)
            return HttpResponse(
                response.status, text, response.headers, response.geturl(), response.reason, response, raw_bytes=raw, cookies=self._parse_cookies()
            )

        with self._lock:
            result = self._retry_request(do_open)

        if self.cookie_file:
            self.cookie_jar.save(ignore_discard=True)
        return result

    def get(self, url, params=None, headers=None, timeout=None):
        if params:
            url += "?" + urllib.parse.urlencode(params)
        return self._request(url, headers=headers, method="GET", timeout=timeout)

    def post(self, url, data=None, headers=None, timeout=None):
        if headers is None:
            headers = {}
        if "Content-Type" not in headers:
            headers["Content-Type"] = "application/json"
        return self._request(url, data=data, headers=headers, method="POST", timeout=timeout)

    def put(self, url, data=None, headers=None, timeout=None):
        return self._request(url, data=data, headers=headers, method="PUT", timeout=timeout)

    def patch(self, url, data=None, headers=None, timeout=None):
        return self._request(url, data=data, headers=headers, method="PATCH", timeout=timeout)

    def delete(self, url, headers=None, timeout=None):
        return self._request(url, headers=headers, method="DELETE", timeout=timeout)

    def head(self, url, headers=None, timeout=None):
        return self._request(url, headers=headers, method="HEAD", timeout=timeout)

    def download(self, url, dest_path, timeout=None):
        def do_download():
            req = urllib.request.Request(url, method="GET", headers=self._build_headers({}))
            opener = self._build_opener()
            with opener.open(req, timeout=timeout or self.timeout) as response:
                with open(dest_path, "wb") as out_file:
                    out_file.write(response.read())
            self._log("Downloaded:", dest_path)

        with self._lock:
            self._retry_request(do_download)

    def download_stream(self, url, dest_path, chunk_size=8192, timeout=None, progress_callback: Optional[Callable[[int], None]] = None):
        req = urllib.request.Request(url, method="GET", headers=self._build_headers({}))
        opener = self._build_opener()
        with opener.open(req, timeout=timeout or self.timeout) as response, open(dest_path, "wb") as out_file:
            downloaded = 0
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                out_file.write(chunk)
                downloaded += len(chunk)
                if progress_callback:
                    progress_callback(downloaded)
        self._log("Stream downloaded:", dest_path)

    def post_multipart(self, url, fields: Dict[str, str], file_paths: Dict[str, str], headers=None):
        boundary = uuid.uuid4().hex
        body = b""
        for key, val in fields.items():
            body += f"--{boundary}\r\n".encode()
            body += f'Content-Disposition: form-data; name="{key}"\r\n\r\n{val}\r\n'.encode()

        for key, filepath in file_paths.items():
            filename = os.path.basename(filepath)
            mimetype = mimetypes.guess_type(filename)[0] or "application/octet-stream"
            with open(filepath, "rb") as f:
                content = f.read()
            body += f"--{boundary}\r\n".encode()
            body += f'Content-Disposition: form-data; name="{key}"; filename="{filename}"\r\n'.encode()
            body += f"Content-Type: {mimetype}\r\n\r\n".encode()
            body += content + b"\r\n"

        body += f"--{boundary}--\r\n".encode()
        headers = self._build_headers(headers or {})
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"

        return self._request(url, data=body, headers=headers, method="POST")

    def stream_response(self, url, chunk_size=8192, timeout=None) -> Generator[bytes, None, None]:
        req = urllib.request.Request(url, method="GET", headers=self._build_headers({}))
        opener = self._build_opener()
        with opener.open(req, timeout=timeout or self.timeout) as response:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                yield chunk
