import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def _free_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def test_agent_http_service_health_and_request_validation():
    port = _free_port()
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1",
         "--port", str(port), "--log-level", "warning"],
        cwd=Path(__file__).resolve().parents[1],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    base = f"http://127.0.0.1:{port}"
    try:
        for _ in range(90):
            if process.poll() is not None:
                raise AssertionError(f"agent service exited with status {process.returncode}")
            try:
                with urlopen(base + "/health", timeout=2) as response:
                    assert response.status == 200
                    assert b"kraya-agents" in response.read()
                    break
            except (URLError, TimeoutError, ConnectionError):
                time.sleep(1)
        else:
            raise AssertionError("agent service health endpoint did not become reachable")

        request = Request(
            base + "/workflows/procurement",
            data=b'{"user_input":""}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urlopen(request, timeout=10)
            raise AssertionError("empty workflow input should be rejected")
        except HTTPError as error:
            assert error.code == 422
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
