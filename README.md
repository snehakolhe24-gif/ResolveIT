# ResolveIT
online complaint management system
ResolveIT is a Streamlit web app for submitting, tracking, and managing complaints.

## Features
- User account registration and login
- Complaint submission with category and priority
- Personal complaint tracking
- Admin dashboard and status updates
- SQLite database for users and complaints

## Run locally
```bash
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

## Deploy on Streamlit Community Cloud
1. Upload `streamlit_app.py`, `requirements.txt`, and `README.md` to a GitHub repository.
2. Go to https://share.streamlit.io/ and sign in with GitHub.
3. Create an app, select your repository and branch.
4. Set the main file path to `streamlit_app.py`, then deploy.

## Demo admin account
- Username: `admin`
- Password: `Admin@123`

Change demo credentials and improve authentication before using this app publicly. The bundled SQLite database is created on startup; local app filesystems on hosting platforms may be temporary, so use a managed database for durable production storage.

