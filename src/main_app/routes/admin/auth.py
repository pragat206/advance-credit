from fastapi import Request, Response
from starlette.middleware.sessions import SessionMiddleware

SESSION_KEY = "admin_authenticated"

# Call this in FastAPI app: app.add_middleware(SessionMiddleware, secret_key="your-secret-key")

def set_admin_session(response: Response):
    response.set_cookie(key=SESSION_KEY, value="1", httponly=True, max_age=60*60*8)

def clear_admin_session(response: Response):
    response.delete_cookie(SESSION_KEY)

def is_admin_authenticated(request: Request):
    return request.cookies.get(SESSION_KEY) == "1" 