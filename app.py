                                                                                         
import streamlit as st
from openai import OpenAI
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
from datetime import datetime
import tempfile
import os

# =========================
# LETTER TEMPLATES
# =========================
TEMPLATES = {
    "Entlassungsbericht": {
        "de": """ENTLASSUNGSBERICHT
Hinweis:
Dieser Arztbrief ist anonymisiert und dient ausschließlich zu Dokumentationszwecken.
Praxis/Klinik: [Praxis/Klinik]
Abteilung: [Abteilung]
Behandelnder Arzt: [Arzt]
Datum: [Datum]

Patientenangaben (anonymisiert):
• Alter: {{ALTER}}
• Geschlecht: {{GESCHLECHT}}

Aufnahmegrund:
{{AUTOMATISCH AUSFORMULIERT}}
...
Unterschrift:
[Arzt / Praxis]
""",
        "en": """DISCHARGE SUMMARY
Note:
This medical letter is anonymized and for documentation purposes only.
Clinic/Practice: [Clinic/Practice]
Department: [Department]
Attending Physician: [Physician]
Date: [Date]

Patient Details (anonymized):
• Age: {{AGE}}
• Sex: {{SEX}}

Reason for Admission:
{{AUTOMATICALLY FORMULATED}}
...
Signature:
[Physician / Clinic]
"""
    },
    "Befundbericht": {
        "de": """BEFUNDBERICHT
Hinweis:
Dieser Bericht ist anonymisiert und dient ausschließlich zu Dokumentationszwecken.
...
Unterschrift:
[Arzt / Praxis]
""",
        "en": """DIAGNOSTIC REPORT
Note:
This report is anonymized and for documentation purposes only.
...
Signature:
[Physician / Clinic]
"""
    },
    "Überweisung": {
        "de": """ÜBERWEISUNG
Hinweis:
Dieser Arztbrief ist anonymisiert und dient ausschließlich zu Dokumentationszwecken.
...
Unterschrift:
[Arzt / Praxis]
""",
        "en": """REFERRAL
Note:
This referral is anonymized and for documentation purposes only.
...
Signature:
[Physician / Clinic]
"""
    },
    "Konsiliarbericht": {
        "de": """KONSILIARBERICHT
Hinweis:
Dieser Bericht ist anonymisiert und dient ausschließlich zu Dokumentationszwecken.
...
Unterschrift:
[Arzt / Praxis]
""",
        "en": """CONSULTATION LETTER
Note:
This consultation letter is anonymized and for documentation purposes only.
...
Signature:
[Physician / Clinic]
"""
    },
    "Sonstiges": {
        "de": """ÄRZTLICHER BERICHT
Hinweis:
Dieser Bericht ist anonymisiert und dient ausschließlich zu Dokumentationszwecken.
...
Unterschrift:
[Arzt / Praxis]
""",
        "en": """OTHER MEDICAL REPORT
Note:
This report is anonymized and for documentation purposes only.
...
Signature:
[Physician / Clinic]
"""
    }
}

# Mapping für Brieftypen im Dropdown
LETTER_TYPE_NAMES = {
    "de": ["Entlassungsbericht", "Befundbericht", "Überweisung", "Konsiliarbericht", "Sonstiges"],
    "en": ["Discharge Summary", "Diagnostic Report", "Referral", "Consultation Letter", "Others"]
}

LETTER_TYPE_KEY = {
    "Discharge Summary": "Entlassungsbericht",
    "Diagnostic Report": "Befundbericht",
    "Referral": "Überweisung",
    "Consultation Letter": "Konsiliarbericht",
    "Others": "Sonstiges",
    "Entlassungsbericht": "Entlassungsbericht",
    "Befundbericht": "Befundbericht",
    "Überweisung": "Überweisung",
    "Konsiliarbericht": "Konsiliarbericht",
    "Sonstiges": "Sonstiges"
}

# =========================
# PAGE CONFIGURATION
# =========================
st.set_page_config(
    page_title="Medical Letter Assistant",
    page_icon="🩺",
    layout="centered"
)

# =========================
# BRANDING & CSS
# =========================
st.markdown("""
<style>
body { background-color: #EAF2F8; }
.block-container { padding-top: 2rem; }
h1,h2,h3 { color: #0F4C81; font-family: 'Helvetica', sans-serif; }
.stButton>button { background-color: #0F4C81; color: white; border-radius: 8px; height: 3em; font-weight: bold; }
.stTextArea textarea { border-radius: 8px; padding: 0.5em; font-family: 'Courier New', monospace; }
</style>
""", unsafe_allow_html=True)

# =========================
# SESSION STATE INIT
# =========================
if "registered" not in st.session_state: st.session_state.registered = False
if "generated_letter" not in st.session_state: st.session_state.generated_letter = ""

# =========================
# HEADER & LOGO
# =========================
st.image("logo.png", width=150, caption="Medical Letter Assistant")
st.markdown("## 🩺 Medical Letter Assistant")
st.caption("Non-Profit Clinical Documentation Tool – Anonymized Data Only")
st.divider()

# =========================
# REGISTRATION
# =========================
if not st.session_state.registered:
    st.subheader("Access Registration")
    st.info("⚠️ Please do NOT enter real patient-identifiable data. Only anonymized or fictional data may be used.")
    name = st.text_input("Your Name")
    email = st.text_input("Email Address")
    confirm_anonymous = st.checkbox("I confirm that I only enter anonymized or fictional patient data")
    agree = st.checkbox("I agree to the Privacy Policy and Legal Notice")
    if st.button("Continue"):
        if not name or not email or not agree or not confirm_anonymous:
            st.warning("Please complete all fields and confirm anonymized data usage.")
        else:
            st.session_state.registered = True
            st.session_state.user_name = name
            st.success("Access granted. Welcome!")
            st.rerun()
    st.stop()

# =========================
# LANGUAGE SELECTION
# =========================
language = st.selectbox("Language / Sprache", ["English", "Deutsch"], index=1)
lang_code = "en" if language.lower() == "english" else "de"

# =========================
# CLINICAL NOTES INPUT
# =========================
st.subheader("Clinical Notes (anonymized only)")
notes = st.text_area("Enter anonymized medical notes:", height=250, placeholder="E.g., Patient presents with general symptoms...")

# =========================
# LETTER TYPE SELECTION
# =========================
letter_type_label = st.selectbox("Select Letter Type / Brief Typ", LETTER_TYPE_NAMES[lang_code])
letter_type = LETTER_TYPE_KEY[letter_type_label]

# =========================
# OPENAI CLIENT
# =========================
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("API key not found! Set OPENAI_API_KEY as environment variable.")
    st.stop()
client = OpenAI(api_key=api_key)

# =========================
# PROMPT GENERATION
# =========================
def generate_prompt(notes, letter_type, lang_code):
    template = TEMPLATES[letter_type][lang_code]
    return template.replace("{{ALTER}}", "[Age]").replace("{{GESCHLECHT}}", "[Sex]").replace("{{AGE}}", "[Age]").replace("{{SEX}}", "[Sex]") + f"\n\nClinical Notes:\n{notes}"

# =========================
# GENERATE MEDICAL LETTER
# =========================
if st.button("Generate Medical Letter", disabled=not notes.strip()):
    with st.spinner("Generating medical letter..."):
        try:
            prompt = generate_prompt(notes, letter_type, lang_code)
            response = client.chat.completions.create(
                model="gpt-4.1",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2500
            )
            st.session_state.generated_letter = response.choices[0].message.content
            st.success("Medical letter generated successfully!")
        except Exception as e:
            st.error(f"Error generating letter: {e}")

# =========================
# DISPLAY & PDF EXPORT
# =========================
if st.session_state.generated_letter:
    st.subheader("Generated Medical Letter")
    st.text_area("", value=st.session_state.generated_letter, height=400)

    if st.button("Download PDF"):
        with tempfile.NamedTemporaryFile(suffix=".pdf") as temp:
            c = canvas.Canvas(temp.name, pagesize=A4)
            width, height = A4

            if os.path.exists("logo.png"):
                c.drawImage("logo.png", 40, height - 70, width=70, preserveAspectRatio=True, mask="auto")

            y = height - 50
            c.setFont("Helvetica-Bold", 14)
            c.drawString(120, y, "Medical Letter Assistant")
            y -= 20

            c.setFont("Helvetica", 9)
            legal_text = (
                "Legal Notice / Impressum: Operator: Henk Baldys | Contact: henkbaldys@icloud.com | "
                "Non-profit project. Only anonymized or fictional data allowed.\n"
                "Privacy Policy: No patient-identifiable data is collected or stored. All inputs are session-only. "
                "No data is logged or tracked. Supports GDPR, HIPAA, PIPEDA, Australian Privacy Principles.\n"
                "Medical Disclaimer: This tool is for documentation only. "
                "It does NOT provide medical advice, diagnosis, or treatment."
            )
            for line in legal_text.split("\n"):
                c.drawString(40, y, line)
                y -= 12
            y -= 15

            c.setFont("Helvetica", 11)
            body_lines = simpleSplit(st.session_state.generated_letter, "Helvetica", 11, width - 80)
            for line in body_lines:
                c.drawString(40, y, line)
                y -= 14
                if y < 40:
                    c.showPage()
                    y = height - 80
                    c.setFont("Helvetica", 11)

            c.showPage()
            c.save()
            temp.seek(0)
            pdf_bytes = temp.read()
            st.download_button("Download PDF", data=pdf_bytes, file_name="medical_letter.pdf", mime="application/pdf")

# =========================
# FOOTER
# =========================
st.divider()
with st.expander("Legal Notice / Impressum"):
    st.markdown("""
**Operator:** Henk Baldys  
**Contact:** henkbaldys@icloud.com  
Non-profit project. Only anonymized or fictional patient data allowed.
""")
with st.expander("Privacy Policy / Datenschutz"):
    st.markdown("""
- No patient-identifiable data is collected or stored.  
- All inputs are processed in-session only.  
- No data is logged, tracked, or used for AI training.  
- Users must only enter anonymized or fictional data.  
- Designed to support GDPR (EU), HIPAA-aligned workflows (USA), PIPEDA (Canada), and Australian Privacy principles.
""")
with st.expander("Medical Disclaimer"):
    st.markdown("""
**Disclaimer:** This tool is for documentation and writing assistance only.  
It does NOT provide medical advice, diagnosis, or treatment recommendations.  
All medical decisions are the responsibility of the licensed healthcare professional.  
No physician-patient relationship is created.  
""")
st.caption("This tool assists in documentation only and does not provide medical advice.")
