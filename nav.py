import streamlit as st

def render_navbar():
    qp = st.query_params if hasattr(st, "query_params") else st.experimental_get_query_params()
    current = (qp.get("page") if isinstance(qp.get("page"), str) else (qp.get("page", ["intro"])[0] if qp.get("page") else "intro")).lower()

    intro_href = "?page=intro"
    about_href = "?page=about"

    intro_active = (current == "intro")
    about_active = (current == "about")

    def pill(label, href, active):
        style = (
            "padding:6px 12px;border-radius:999px;text-decoration:none;"
            "font-size:18px;margin-left:10px;"
            f"background:{'#111827' if active else 'transparent'};"
            f"color:{'#ffffff' if active else '#111827'};"
            f"border:1px solid {'#111827' if active else '#e5e7eb'};"
        )
        return f'<a href="{href}" target="_self" rel="noopener" style="{style}">{label}</a>'

    html = f"""
    <div style="position:sticky;top:0;z-index:999;background:white;border-bottom:1px solid #eee;margin-bottom:20px;">
      <div style="max-width:1280px;margin:0 auto;padding:14px 8px;display:flex;align-items:center;justify-content:space-between;">
        <div style="font-weight:700;font-size:42px;margin-left:0;">Bias Detector for Job Ads</div>
        <div>{pill("Check", intro_href, intro_active)}{pill("About", about_href, about_active)}</div>
      </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)