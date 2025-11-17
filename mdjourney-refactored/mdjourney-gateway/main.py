
import fastapi
import httpx
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import Response

from gateway_process_manager_local import start_backend_process_local, stop_backend_process_local

app = fastapi.FastAPI()

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key="your-secret-key")

# In-memory store for available ports
# In a real-world scenario, you'd use a more robust method
# for port allocation and management.
available_ports = list(range(8001, 8011))
used_ports = {}

@app.post("/api/session/start")
async def start_session(request: Request):
    """
    Starts a new session, allocating a backend instance to the user.
    """
    if not available_ports:
        raise fastapi.HTTPException(status_code=503, detail="No available backend instances")

    port = available_ports.pop(0)
    pid = start_backend_process_local(port)

    request.session["backend_port"] = port
    request.session["backend_pid"] = pid
    used_ports[port] = pid

    return {"message": f"Session started, backend running on port {port}"}

@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def reverse_proxy(request: Request):
    """
    Reverse proxies all other /api requests to the user's allocated backend.
    """
    backend_port = request.session.get("backend_port")
    if not backend_port:
        raise fastapi.HTTPException(status_code=401, detail="Not authenticated")

    client = httpx.AsyncClient()
    url = f"http://localhost:{backend_port}{request.url.path.replace('/api', '')}"

    # Copy headers, removing 'host' as it's not needed
    headers = dict(request.headers)
    headers.pop("host", None)

    # Stream the request body
    req_body = request.stream()

    try:
        # Forward the request to the backend
        backend_response = await client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=req_body,
            timeout=30.0,
        )

        # Create a streaming response to send back to the client
        return Response(
            content=backend_response.content,
            status_code=backend_response.status_code,
            headers=dict(backend_response.headers),
        )
    except httpx.RequestError as e:
        # Handle connection errors to the backend
        raise fastapi.HTTPException(
            status_code=502,
            detail=f"Error connecting to backend: {e}",
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
