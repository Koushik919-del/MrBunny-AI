import streamlit as st
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
import google.auth.transport.requests

def login_with_google():
    if "token" not in st.session_state:
        # Build credentials dynamically from secrets.py
        client_config = {
            "web": {
                "client_id": st.secrets["GOOGLE_CLIENT_ID"],
                "client_secret": st.secrets["GOOGLE_CLIENT_SECRET"],
                "redirect_uris": ["http://localhost:8501/"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }

        flow = Flow.from_client_config(
            client_config,
            scopes=["openid", "email", "profile"],
            redirect_uri="http://localhost:8501/"
        )

        auth_url, _ = flow.authorization_url(prompt='consent')
        st.markdown(f"[Login with Google]({auth_url})")

        if st.query_params.get("code"):
            code = st.query_params["code"]
            flow.fetch_token(code=code)
            credentials = flow.credentials

            request = google.auth.transport.requests.Request()
            id_info = id_token.verify_oauth2_token(
                credentials.id_token, request, flow.client_config["web"]["client_id"]
            )

            st.session_state["token"] = credentials
            st.session_state["user"] = {
                "name": id_info["name"],
                "email": id_info["email"]
            }
            st.rerun()

    else:
        user = st.session_state["user"]
        st.sidebar.success(f"✅ Logged in as {user['name']}")
        st.sidebar.caption(user["email"])
        return user
