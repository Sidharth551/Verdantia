import streamlit as st

def show_achievement_detail(name, desc, threshold, unlocked):
    status = "✅ Unlocked!" if unlocked else f"🔒 Locked — Earn {threshold} points to unlock."
    st.markdown(f"""
        <div class="quest-box">
            <h4>{name}</h4>
            <p>{desc}</p>
            <p><strong>Points Needed:</strong> {threshold}</p>
            <p><strong>Status:</strong> {status}</p>
        </div>
    """, unsafe_allow_html=True)

def render_achievements_grid(user=None, achievement_defs=None):
    if not user or not achievement_defs:
        st.warning("Achievements data not loaded properly.")
        return

    current_points = user.get("points", 0)

    st.markdown('<div class="achievements-grid">', unsafe_allow_html=True)
    for idx, (name, desc, threshold) in enumerate(achievement_defs):
        unlocked = user["points"] >= threshold
        style = "unlocked" if unlocked else "locked"
        st.markdown(f"""
            <div class="achievement {style}" title="{desc}">
                <strong>{name}</strong><br>
                <small>{desc}</small><br>
                <small>🏁 Requires {threshold} points</small>
            </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

def render_leaderboard_table(data):
    st.markdown('<div style="display:flex; flex-direction:column; align-items:center;">', unsafe_allow_html=True)
    for rank, (name, points) in enumerate(data, start=1):
        st.markdown(f"""
            <div class="leaderboard-entry">
                <strong>#{rank}</strong> — {name} <span style='margin-left:auto;'>⭐ {points}</span>
            </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def render_login_title():
    st.markdown("""
        <div style='text-align:center;'>
            <h1 style='font-size: 2.5rem; font-weight: 700; color: #2E7D32;'>♻️ Verdantia</h1>
            <p style='font-size: 1.1rem; color: #555;'>Join the movement. Recycle smart. Get rewarded.</p>
        </div>
    """, unsafe_allow_html=True)
