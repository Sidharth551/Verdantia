import streamlit as st
import json, os, re
from datetime import datetime, timedelta
from PIL import Image
from gemini_agent import ask_gemini, classify_item_with_ai, classify_image_with_vision_ai
from utils import (
    load_user_data, save_user_data, hash_password, check_password,
)
import ui

# Load CSS
# Find the path of style.css no matter where Streamlit runs
css_path = os.path.join(os.path.dirname(__file__), "style.css")
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

USER_DATA_FILE = "users.json"
STREAK_POPUP_KEY = "streak_popup_shown"
QUOTA_LIMIT = 20

# Utility Functions

def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def calculate_streak(user):
    today = datetime.now().date()
    last = datetime.strptime(user.get("last_login", "2000-01-01"), "%Y-%m-%d").date()
    if today == last:
        return user.get("streak", 0)
    elif today - last == timedelta(days=1):
        return user.get("streak", 0) + 1
    else:
        return 1

def show_streak_popup(streak):
    if streak > 1 and not st.session_state.get(STREAK_POPUP_KEY):
        st.session_state[STREAK_POPUP_KEY] = True
        st.success(f"🔥 You're on a {streak}-day streak!")

def ask_disposal_quiz():
    questions = [
        "Did you clean the item before disposing?",
        "Did you dispose of it in the correct bin/drop-off?",
        "Did you check local recycling guidelines?"
    ]
    answers = []
    for q in questions:
        answers.append(st.radio(q, ["Yes", "No"], key=q))
    return all(ans == "Yes" for ans in answers)

def reward_completed_quests(user):
    for quest in user["weekly_quests"]:
        if quest["progress"] >= quest["target"] and not quest.get("completed"):
            quest["completed"] = True
            user["points"] += 5  # reward per quest
            st.success(f"🎯 Quest completed: {quest['goal']} (+5 points)")

#Session State 

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_email = ""
    st.session_state.nickname = ""
    st.session_state.quota_used = 0

#Authentication 

if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h2 style='text-align:center; font-weight:bold;'>♻️ Verdantia</h2>", unsafe_allow_html=True)
        auth_mode = st.radio("Login or Sign up", ["Login", "Sign up"])
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if auth_mode == "Sign up":
                nickname = st.text_input("Choose a nickname")
                confirm_password = st.text_input("Confirm Password", type="password")
            submitted = st.form_submit_button("Continue")

        if submitted:
            users = load_user_data()
            if not is_valid_email(email):
                st.error("❌ Invalid email format.")
            elif auth_mode == "Sign up":
                if password != confirm_password:
                    st.error("❌ Passwords do not match.")
                elif email in users:
                    st.error("❌ Email already registered.")
                else:
                    users[email] = {
                        "password": hash_password(password),
                        "nickname": nickname,
                        "points": 0, "level": 1, "streak": 1,
                        "last_login": datetime.now().date().isoformat(),
                    }
                    save_user_data(users)
                    st.success("✅ Account created!")
                    st.session_state.authenticated = True
                    st.session_state.user_email = email
                    st.session_state.nickname = nickname
                    st.rerun()
            else:
                if email not in users or not check_password(password, users[email]["password"]):
                    st.error("❌ Invalid credentials.")
                else:
                    st.session_state.authenticated = True
                    st.session_state.user_email = email
                    st.session_state.nickname = users[email]["nickname"]
                    st.rerun()
    st.stop()

# Load User Data

user_data = load_user_data()
user = user_data[st.session_state.user_email]
user["streak"] = calculate_streak(user)
user["last_login"] = datetime.now().date().isoformat()
show_streak_popup(user["streak"])
save_user_data(user_data)

# Sidebar

st.sidebar.markdown("### ♻️ Verdantia")
if st.sidebar.button("🚪 Logout"):
    for k in list(st.session_state):
        st.session_state[k] = False if isinstance(st.session_state[k], bool) else ""
    st.rerun()
st.sidebar.markdown(f"**{st.session_state.nickname}**")
st.sidebar.markdown(f"⭐ Points: {user['points']}")
st.sidebar.markdown(f"🔥 Streak: {user['streak']} days")
st.sidebar.markdown("---")
page = st.sidebar.radio("Menu", ["Chat", "Achievements", "Leaderboard"])

# Chat Page (review and recheck?)

if page == "Chat":
    st.markdown(f"<h2 style='text-align:center'>Hello, {st.session_state.nickname} 👋</h2>", unsafe_allow_html=True)

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for msg in st.session_state.chat_history:
        st.chat_message("user").write(msg["user"])
        st.chat_message("assistant").write(msg["ai"])

    col1, col2 = st.columns([0.9, 0.1])
    with col1:
        user_input = st.chat_input("Ask your recycling question...")
    with col2:
        if st.button("📎", help="Upload image"):
            st.session_state["show_uploader"] = not st.session_state.get("show_uploader", False)

    if st.session_state.get("show_uploader"):
        with st.expander("📂 Drag & Drop or Browse", expanded=True):
            uploaded_image = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])
        if uploaded_image:
            st.session_state["pending_image"] = uploaded_image
            st.image(uploaded_image, caption="Image ready for classification", width=150)
            st.info("✅ Image uploaded. Tap '♻️ Analyze' below.")

    if st.session_state.get("pending_image") and st.button("♻️ Analyze Uploaded Image"):
        if int(st.session_state.quota_used) >= int(st.session_state.quota_used) + 1:
            st.warning("❌ Free quota expired!")
        else:
            image = Image.open(st.session_state["pending_image"])
            category = classify_image_with_vision_ai(image)
            ai_answer = ask_gemini(f"Disposal guide for: {category}")
            st.session_state.chat_history.append({"user": "[Image uploaded]", "ai": ai_answer})
            st.session_state.quota_used += 1

            st.subheader("✅ Quiz Time!")
            if ask_disposal_quiz():
                user["points"] += 10
                st.success("🎉 Correct disposal confirmed! +10 points")
            else:
                st.info("Thanks! You can do even better next time.")

            st.success("🎉 You earned 10 points!")
            st.session_state["pending_image"] = None
            st.session_state["show_uploader"] = False
            save_user_data(user_data)
            st.rerun()

    if user_input:
        if st.session_state.quota_used >=  int(st.session_state.quota_used) + 1 :
            st.warning("❌ Free quota expired!")
        else:
            ai_answer = ask_gemini(user_input)
            st.session_state.chat_history.append({"user": user_input, "ai": ai_answer})
            user["points"] += 10
            st.session_state.quota_used += 1
            save_user_data(user_data)
            st.rerun()

# Achievements Page (more required? review.)

elif page == "Achievements":
    st.title("🏅 Eco Achievements")
    achievement_defs = [
    ("♻️ Plastic Buster", "Earn 50 points", 50),
    ("🌱 Compost Champ", "Earn 100 points", 100),
    ("🚫 No‑Plastic Day", "Earn 150 points", 150),
    ("👕 Clothes Donator", "Earn 200 points", 200),
    ("📆 Weeklong Warrior", "Earn 250 points", 250),
    ("🧠 Sorting Pro", "Earn 300 points", 300),
    ("💻 E‑Waste Slayer", "Earn 400 points", 400),
    ("🌿 Green Thumb", "Earn 500 points", 500),
]
    ui.render_achievements_grid(user, achievement_defs)

# Leaderboard Page

elif page == "Leaderboard":
    st.title("🌍 Leaderboard")
    rows = sorted([(v["nickname"], v["points"]) for v in user_data.values()], key=lambda x: x[1], reverse=True)
    ui.render_leaderboard_table(rows)



