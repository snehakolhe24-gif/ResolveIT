import streamlit as st
import sqlite3
import hashlib
import os
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="ResolveIT", page_icon="🛠️", layout="wide")

DB_PATH = os.path.join(os.path.dirname(__file__), "complaints.db")

st.markdown("""
<style>
.stApp { background: #f6f7fb; color: #20243a; }
.block-container { max-width: 1150px; padding-top: 2rem; }
.brand { font-size: 32px; font-weight: 800; color: #5145e5; }
div.stButton > button[kind="primary"] { background: #5145e5; border-color: #5145e5; }
[data-testid="stMetric"] { background: white; padding: 16px; border: 1px solid #e8eaf2; border-radius: 14px; }
</style>
""", unsafe_allow_html=True)

def connect():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def init_db():
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user'
        );
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        """)
        admin = db.execute("SELECT id FROM users WHERE username='admin'").fetchone()
        if not admin:
            db.execute(
                "INSERT INTO users(name, username, password_hash, role) VALUES(?,?,?,?)",
                ("Administrator", "admin", hash_password("Admin@123"), "admin")
            )

def get_user(username):
    with connect() as db:
        return db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()

def get_complaints(user_id=None):
    with connect() as db:
        query = """SELECT c.id AS ID, u.name AS User, c.title AS Title,
                   c.category AS Category, c.priority AS Priority,
                   c.description AS Description, c.status AS Status,
                   c.created_at AS Date, c.user_id AS user_id
                   FROM complaints c JOIN users u ON u.id=c.user_id"""
        if user_id is not None:
            query += " WHERE c.user_id=?"
            rows = db.execute(query + " ORDER BY c.id DESC", (user_id,)).fetchall()
        else:
            rows = db.execute(query + " ORDER BY c.id DESC").fetchall()
    return [dict(r) for r in rows]

init_db()

if "user" not in st.session_state:
    st.session_state.user = None

st.markdown('<div class="brand">🛠️ ResolveIT</div>', unsafe_allow_html=True)
st.caption("Online Complaint Management System")

if st.session_state.user is None:
    login_tab, register_tab = st.tabs(["Login", "Create account"])
    with login_tab:
        st.subheader("Welcome Back")
        st.write("Login to manage and track your complaints.")
        with st.form("login_form"):
            username = st.text_input("Username", key="login_username").strip()
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Login", type="primary", use_container_width=True)
        if submitted:
            user = get_user(username)
            if user and user["password_hash"] == hash_password(password):
                st.session_state.user = {
                    "id": user["id"], "name": user["name"],
                    "username": user["username"], "role": user["role"]
                }
                st.rerun()
            else:
                st.error("Invalid username or password.")
        st.info("Demo admin login: **admin** / **Admin@123**")
    with register_tab:
        st.subheader("Create an account")
        with st.form("register_form", clear_on_submit=True):
            name = st.text_input("Full name")
            username = st.text_input("Choose a username")
            password = st.text_input("Create password", type="password")
            confirm = st.text_input("Confirm password", type="password")
            create = st.form_submit_button("Create account", type="primary")
        if create:
            name, username = name.strip(), username.strip()
            if not name or not username:
                st.error("Please enter your name and username.")
            elif len(password) < 8:
                st.error("Password must be at least 8 characters.")
            elif password != confirm:
                st.error("Passwords do not match.")
            else:
                try:
                    with connect() as db:
                        db.execute(
                            "INSERT INTO users(name, username, password_hash, role) VALUES(?,?,?,'user')",
                            (name, username, hash_password(password))
                        )
                    st.success("Account created. Please log in.")
                except sqlite3.IntegrityError:
                    st.error("That username is already taken.")
else:
    user = st.session_state.user
    with st.sidebar:
        st.title("ResolveIT")
        st.write(f"Signed in as **{user['name']}**")
        if user["role"] == "admin":
            pages = ["Dashboard", "All Complaints", "Submit Complaint"]
        else:
            pages = ["Dashboard", "Submit Complaint", "My Complaints"]
        page = st.radio("Navigation", pages)
        if st.button("Logout"):
            st.session_state.user = None
            st.rerun()

    if page == "Dashboard":
        st.title("Dashboard")
        complaints = get_complaints(None if user["role"] == "admin" else user["id"])
        total = len(complaints)
        pending = sum(c["Status"] == "Pending" for c in complaints)
        in_progress = sum(c["Status"] == "In Progress" for c in complaints)
        resolved = sum(c["Status"] == "Resolved" for c in complaints)
        a, b, c, d = st.columns(4)
        a.metric("Total Complaints", total)
        b.metric("Pending", pending)
        c.metric("In Progress", in_progress)
        d.metric("Resolved", resolved)
        st.subheader("Recent complaints")
        if complaints:
            st.dataframe(pd.DataFrame(complaints).drop(columns=["user_id"]), use_container_width=True, hide_index=True)
        else:
            st.info("No complaints submitted yet.")

    elif page == "Submit Complaint":
        st.title("Submit a Complaint")
        with st.form("complaint_form", clear_on_submit=True):
            title = st.text_input("Complaint title")
            category = st.selectbox("Category", ["Water", "Electricity", "Roads", "Education", "Healthcare", "Sanitation", "Other"])
            priority = st.selectbox("Priority", ["Low", "Medium", "High"])
            description = st.text_area("Complaint description")
            submit = st.form_submit_button("Submit complaint", type="primary")
        if submit:
            if not title.strip() or not description.strip():
                st.error("Please complete the title and description.")
            else:
                with connect() as db:
                    db.execute(
                        """INSERT INTO complaints(user_id,title,category,description,priority,status,created_at)
                           VALUES(?,?,?,?,?,'Pending',?)""",
                        (user["id"], title.strip(), category, description.strip(), priority,
                         datetime.now().strftime("%Y-%m-%d %H:%M"))
                    )
                st.success("Complaint submitted successfully.")
                st.rerun()

    elif page in ("My Complaints", "All Complaints"):
        st.title("All Complaints" if user["role"] == "admin" else "My Complaints")
        complaints = get_complaints(None if user["role"] == "admin" else user["id"])
        if not complaints:
            st.info("No complaints available.")
        for complaint in complaints:
            with st.expander(f"#{complaint['ID']} · {complaint['Title']} · {complaint['Status']}"):
                st.write(f"**Submitted by:** {complaint['User']}")
                st.write(f"**Category:** {complaint['Category']}  |  **Priority:** {complaint['Priority']}")
                st.write(f"**Date:** {complaint['Date']}")
                st.write(complaint["Description"])
                if user["role"] == "admin":
                    options = ["Pending", "In Progress", "Resolved"]
                    current_index = options.index(complaint["Status"]) if complaint["Status"] in options else 0
                    with st.form(f"status_{complaint['ID']}"):
                        new_status = st.selectbox("Update status", options, index=current_index)
                        update = st.form_submit_button("Save status")
                    if update:
                        with connect() as db:
                            db.execute("UPDATE complaints SET status=? WHERE id=?", (new_status, complaint["ID"]))
                        st.success("Status updated.")
                        st.rerun()

st.divider()
st.caption("ResolveIT · Online Complaint Management System")
