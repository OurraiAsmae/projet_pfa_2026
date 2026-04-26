"""
BlockML-Gov Authentication Service
MySQL + JWT + bcrypt
"""
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional
import pymysql
import pymysql.cursors
import bcrypt
import jwt
import os
from datetime import datetime, timedelta
import secrets

# ── Config ──────────────────────────────────────────
SECRET_KEY     = os.getenv("JWT_SECRET", "blockmlgov-secret-2026-change-in-prod!")
ALGORITHM      = "HS256"
ACCESS_EXPIRE  = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_EXPIRE = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
MAX_ATTEMPTS   = 5
LOCKOUT_MINUTES = 15

DB_HOST = os.getenv("MYSQL_HOST", "172.29.112.1")
DB_PORT = int(os.getenv("MYSQL_PORT", "3306"))
DB_USER = os.getenv("MYSQL_USER", "blockmlgov")
DB_PASS = os.getenv("MYSQL_PASSWORD", "BlockML@2026!")
DB_NAME = os.getenv("MYSQL_DB", "blockmlgov_auth")

app = FastAPI(title="BlockML-Gov Auth Service", version="1.0.0")

app.add_middleware(CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"],
    allow_headers=["*"], allow_credentials=True)

security = HTTPBearer()

# ── DB Connection ────────────────────────────────────
def get_db():
    return pymysql.connect(
        host=DB_HOST, port=DB_PORT,
        user=DB_USER, password=DB_PASS,
        database=DB_NAME, charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False
    )

# ── Models ───────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str

class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: str
    full_name: str
    email: str
    department: str

class UpdateUserRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

class RefreshRequest(BaseModel):
    refresh_token: str

# ── JWT Utils ────────────────────────────────────────
def create_access_token(user: dict) -> str:
    payload = {
        "sub": str(user["id"]),
        "username": user["username"],
        "role": user["role"],
        "full_name": user["full_name"],
        "email": user["email"],
        "department": user["department"],
        "type": "access",
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_EXPIRE),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token() -> str:
    return secrets.token_urlsafe(64)

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(401, "Invalid token type")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")

# ── Auth Dependency ──────────────────────────────────
def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    return verify_token(creds.credentials)

def require_admin(user=Depends(get_current_user)):
    if user["role"] != "Admin":
        raise HTTPException(403, "Admin role required")
    return user

# ── Audit Logger ─────────────────────────────────────
def log_action(username: str, action: str,
               details: str = "", success: bool = True,
               ip: str = ""):
    try:
        conn = get_db()
        with conn.cursor() as c:
            c.execute("""INSERT INTO audit_log
                (username, action, details, success, ip_address)
                VALUES (%s, %s, %s, %s, %s)""",
                (username, action, details, success, ip))
        conn.commit()
        conn.close()
    except:
        pass

# ════════════════════════════════════════════════════
# AUTH ENDPOINTS
# ════════════════════════════════════════════════════

@app.post("/auth/login")
async def login(req: LoginRequest, request: Request):
    ip = request.client.host
    conn = get_db()
    try:
        with conn.cursor() as c:
            c.execute("""SELECT id, username, password_hash, role,
                                full_name, email, department,
                                is_active, failed_attempts, locked_until
                         FROM users WHERE username=%s""",
                      (req.username,))
            user = c.fetchone()

        if not user:
            log_action(req.username, "LOGIN_FAILED",
                      "User not found", False, ip)
            raise HTTPException(401, "Invalid credentials")

        # Check locked
        if user["locked_until"] and \
           datetime.utcnow() < user["locked_until"]:
            remaining = (user["locked_until"] - datetime.utcnow()).seconds // 60
            raise HTTPException(423,
                f"Account locked. Try again in {remaining} minutes")

        # Check active
        if not user["is_active"]:
            raise HTTPException(403, "Account disabled")

        # Verify password
        if not bcrypt.checkpw(req.password.encode(),
                              user["password_hash"].encode()):
            # Increment failed attempts
            attempts = user["failed_attempts"] + 1
            locked_until = None
            if attempts >= MAX_ATTEMPTS:
                locked_until = datetime.utcnow() + \
                               timedelta(minutes=LOCKOUT_MINUTES)

            with conn.cursor() as c:
                c.execute("""UPDATE users SET
                    failed_attempts=%s, locked_until=%s
                    WHERE id=%s""",
                    (attempts, locked_until, user["id"]))
            conn.commit()

            log_action(req.username, "LOGIN_FAILED",
                      f"Wrong password (attempt {attempts})", False, ip)

            if locked_until:
                raise HTTPException(423,
                    f"Too many attempts. Account locked {LOCKOUT_MINUTES} min")
            raise HTTPException(401, "Invalid credentials")

        # Success — reset attempts
        access_token  = create_access_token(user)
        refresh_token = create_refresh_token()
        expires_at    = datetime.utcnow() + timedelta(days=REFRESH_EXPIRE)

        with conn.cursor() as c:
            c.execute("""UPDATE users SET
                failed_attempts=0, locked_until=NULL, last_login=%s
                WHERE id=%s""",
                (datetime.utcnow(), user["id"]))
            # Store session
            c.execute("""INSERT INTO sessions
                (user_id, token, refresh_token, expires_at, ip_address)
                VALUES (%s, %s, %s, %s, %s)""",
                (user["id"], access_token, refresh_token,
                 expires_at, ip))
        conn.commit()

        log_action(user["username"], "LOGIN_SUCCESS",
                  f"Role: {user['role']}", True, ip)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_EXPIRE * 60,
            "user": {
                "id": user["id"],
                "username": user["username"],
                "role": user["role"],
                "full_name": user["full_name"],
                "email": user["email"],
                "department": user["department"]
            }
        }
    finally:
        conn.close()

@app.post("/auth/logout")
async def logout(user=Depends(get_current_user),
                 creds: HTTPAuthorizationCredentials = Depends(security)):
    conn = get_db()
    try:
        with conn.cursor() as c:
            c.execute("UPDATE sessions SET is_active=0 WHERE token=%s",
                      (creds.credentials,))
        conn.commit()
        log_action(user["username"], "LOGOUT", "", True)
        return {"message": "Logged out successfully"}
    finally:
        conn.close()

@app.post("/auth/refresh")
async def refresh_token(req: RefreshRequest):
    conn = get_db()
    try:
        with conn.cursor() as c:
            c.execute("""SELECT s.*, u.id as uid, u.username,
                                u.role, u.full_name, u.email,
                                u.department, u.is_active
                         FROM sessions s
                         JOIN users u ON s.user_id = u.id
                         WHERE s.refresh_token=%s
                           AND s.is_active=1
                           AND s.expires_at > NOW()""",
                      (req.refresh_token,))
            session = c.fetchone()

        if not session or not session["is_active"]:
            raise HTTPException(401, "Invalid or expired refresh token")

        user = {
            "id": session["uid"],
            "username": session["username"],
            "role": session["role"],
            "full_name": session["full_name"],
            "email": session["email"],
            "department": session["department"]
        }
        new_token = create_access_token(user)

        with conn.cursor() as c:
            c.execute("UPDATE sessions SET token=%s WHERE refresh_token=%s",
                      (new_token, req.refresh_token))
        conn.commit()

        return {"access_token": new_token, "token_type": "bearer"}
    finally:
        conn.close()

@app.get("/auth/me")
async def get_me(user=Depends(get_current_user)):
    return user

@app.get("/auth/verify")
async def verify(user=Depends(get_current_user)):
    return {"valid": True, "user": user}

# ════════════════════════════════════════════════════
# USER MANAGEMENT (Admin only)
# ════════════════════════════════════════════════════

@app.get("/users")
async def list_users(admin=Depends(require_admin)):
    conn = get_db()
    try:
        with conn.cursor() as c:
            c.execute("""SELECT id, username, role, full_name,
                                email, department, is_active,
                                last_login, created_at, created_by
                         FROM users ORDER BY role, username""")
            users = c.fetchall()
        return {"users": users}
    finally:
        conn.close()

@app.post("/users")
async def create_user(req: CreateUserRequest,
                      admin=Depends(require_admin)):
    valid_roles = ["Admin","Data Scientist","Compliance Officer",
                   "ML Engineer","Fraud Analyst",
                   "Internal Auditor","External Auditor","Regulator"]
    if req.role not in valid_roles:
        raise HTTPException(400, f"Invalid role. Must be one of: {valid_roles}")

    pw_hash = bcrypt.hashpw(req.password.encode(),
                            bcrypt.gensalt(12)).decode()
    conn = get_db()
    try:
        with conn.cursor() as c:
            c.execute("""INSERT INTO users
                (username, password_hash, role, full_name,
                 email, department, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (req.username, pw_hash, req.role,
                 req.full_name, req.email,
                 req.department, admin["username"]))
        conn.commit()
        log_action(admin["username"], "CREATE_USER",
                  f"{req.username} ({req.role})")
        return {"message": f"User {req.username} created successfully",
                "role": req.role}
    except pymysql.IntegrityError as e:
        raise HTTPException(409, f"Username or email already exists")
    finally:
        conn.close()

@app.put("/users/{user_id}")
async def update_user(user_id: int, req: UpdateUserRequest,
                      admin=Depends(require_admin)):
    conn = get_db()
    try:
        updates = []
        values  = []
        if req.full_name is not None:
            updates.append("full_name=%s"); values.append(req.full_name)
        if req.email is not None:
            updates.append("email=%s"); values.append(req.email)
        if req.department is not None:
            updates.append("department=%s"); values.append(req.department)
        if req.role is not None:
            updates.append("role=%s"); values.append(req.role)
        if req.is_active is not None:
            updates.append("is_active=%s")
            values.append(1 if req.is_active else 0)
        if req.password is not None:
            pw_hash = bcrypt.hashpw(req.password.encode(),
                                    bcrypt.gensalt(12)).decode()
            updates.append("password_hash=%s"); values.append(pw_hash)
            updates.append("failed_attempts=0")
            updates.append("locked_until=NULL")

        if not updates:
            raise HTTPException(400, "No fields to update")

        values.append(user_id)
        with conn.cursor() as c:
            c.execute(f"UPDATE users SET {','.join(updates)} WHERE id=%s",
                      values)
            if c.rowcount == 0:
                raise HTTPException(404, "User not found")
        conn.commit()
        log_action(admin["username"], "UPDATE_USER", f"user_id={user_id}")
        return {"message": "User updated successfully"}
    finally:
        conn.close()

@app.delete("/users/{user_id}")
async def delete_user(user_id: int, admin=Depends(require_admin)):
    conn = get_db()
    try:
        with conn.cursor() as c:
            c.execute("SELECT username FROM users WHERE id=%s", (user_id,))
            u = c.fetchone()
            if not u:
                raise HTTPException(404, "User not found")
            if u["username"] == "admin":
                raise HTTPException(400, "Cannot delete admin user")
            c.execute("DELETE FROM users WHERE id=%s", (user_id,))
        conn.commit()
        log_action(admin["username"], "DELETE_USER",
                  f"username={u['username']}")
        return {"message": f"User {u['username']} deleted"}
    finally:
        conn.close()

@app.post("/users/{user_id}/unlock")
async def unlock_user(user_id: int, admin=Depends(require_admin)):
    conn = get_db()
    try:
        with conn.cursor() as c:
            c.execute("""UPDATE users SET
                failed_attempts=0, locked_until=NULL
                WHERE id=%s""", (user_id,))
        conn.commit()
        return {"message": "User unlocked successfully"}
    finally:
        conn.close()

@app.get("/audit-logs")
async def get_audit_logs(limit: int = 100,
                         admin=Depends(require_admin)):
    conn = get_db()
    try:
        with conn.cursor() as c:
            c.execute("""SELECT username, action, details,
                                success, ip_address, timestamp
                         FROM audit_log
                         ORDER BY timestamp DESC
                         LIMIT %s""", (limit,))
            logs = c.fetchall()
        return {"logs": logs}
    finally:
        conn.close()

@app.get("/health")
async def health():
    try:
        conn = get_db()
        conn.ping()
        conn.close()
        return {"status": "ok", "service": "auth-service",
                "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": str(e)}
