import streamlit as st

def render_footer():
    footer_text = "⚠️ Results are generated using a combination of pre-set patterns and the Google Gemini AI model. Outputs are for education and awareness only.<br>Please review results carefully and verify anything important with official sources or policy."
    st.markdown(
        f"<div style='text-align: center; font-size: small; color: gray; margin-top: 60px; padding-bottom: 20px;'>{footer_text}</div>",
        unsafe_allow_html=True
    )

footer = render_footer
