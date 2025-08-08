import json
import os
import bcrypt

USER_DATA_FILE = "users.json"

def load_users():
    if not os.path.exists(USER_DATA_FILE):
        return {}
    with open(USER_DATA_FILE, "r") as f:
        return json.load(f)

def save_users(data):
    with open(USER_DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_account(email, password):
    users = load_users()
    if email in users:
        return False, "Email already exists."
    users[email] = {
        "password": hash_password(password),
        "points": 0,
        "level": 1,
        "streak": 0,
        "last_disposal_date": "",
        "badges": [],
        "current_quest": None
    }
    save_users(users)
    return True, "Account created successfully."

def authenticate_user(email, password):
    users = load_users()
    if email not in users:
        return False, "User not found."
    if not check_password(password, users[email]["password"]):
        return False, "Incorrect password."
    return True, users[email]
