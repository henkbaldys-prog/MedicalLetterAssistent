import streamlit as st
from openai import OpenAI
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
from datetime import datetime
import tempfile
import os

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
if "mock_mode" not in st.session_state: st.session_state.mock_mode = True

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
# LANGUAGE & MOCK MODE
# =========================
language = st.selectbox("Language / Sprache", ["English", "Deutsch"], index=1)
st.checkbox("Enable Mock Mode (offline testing)", value=True, key="mock_mode")

# =========================
# CLINICAL NOTES INPUT
# =========================
st.subheader("Clinical Notes (anonymized only)")
notes = st.text_area("Enter anonymized medical notes:", height=250, placeholder="E.g., Patient presents with general symptoms...")

# =========================
# LETTER TYPE
# =========================
letter_type = st.selectbox("Select Letter Type / Brief Typ", [
    "Entlassungsbericht", "Befundbericht", "Überweisung", "Konsiliarbericht", "Sonstiges"
])

# =========================
# PERFECT PROMPT WITH PLACEHOLDERS
# =========================
def generate_prompt(notes, letter_type="Entlassungsbericht", lang="de"):
    placeholders = {
        "clinic": "[Praxis/Klinik]",
        "department": "[Abteilung]",
        "doctor": "[Oberarzt / behandelnder Arzt]",
        "date": "[Datum]",
        "patient_name": "[Patient Name]",
        "dob": "[Geburtsdatum]",
        "age": "[Alter]",
        "sex": "[Geschlecht]"
    }

    if lang.lower().startswith("en"):
        return f"""
You are a highly experienced medical documentation assistant.
Create a professional {letter_type} with all fields anonymized.
Do NOT include real patient or doctor data.

Clinic/Practice: {placeholders['clinic']}
Department: {placeholders['department']}
Physician: {placeholders['doctor']}
Date: {placeholders['date']}

Patient Details (anonymized):
- Name: {placeholders['patient_name']}
- Date of Birth: {placeholders['dob']}
- Age: {placeholders['age']}
- Sex: {placeholders['sex']}

Clinical Notes:
{notes}

Requirements:
- The letter must be fully structured, professional, and ready for clinical use.
- Include all relevant sections automatically depending on the selected letter type.
- Keep only the placeholders for sensitive data (clinic, doctor, patient, date); everything else must be fully written.
- Formal, neutral, clinical language; perfect style better than average human physician.
- Clearly indicate that this document is anonymized and for documentation purposes only.
- Five letter types supported: Discharge Summary, Diagnostic Report, Referral, Consultation Letter, Others.
"""
    else:
        return f"""
Du bist ein sehr erfahrener medizinischer Dokumentationsassistent.
Erstelle einen professionellen {letter_type}, alle Felder anonymisiert.
Keine echten Patientendaten oder Arztinfos.

Praxis/Klinik: {placeholders['clinic']}
Abteilung: {placeholders['department']}
Arzt / Oberarzt: {placeholders['doctor']}
Datum: {placeholders['date']}

Patientendaten (anonymisiert):
- Name: {placeholders['patient_name']}
- Geburtsdatum: {placeholders['dob']}
- Alter: {placeholders['age']}
- Geschlecht: {placeholders['sex']}

Klinische Notizen:
{notes}

Anforderungen:
- Der Brief muss vollständig strukturiert, professionell und sofort verwendbar sein.
- Enthält alle relevanten Abschnitte je nach gewähltem Brief-Typ.
- Nur die Platzhalter für sensible Daten (Praxis, Arzt, Patient, Datum) bleiben; alles andere ist fertig geschrieben.
- Formelle, neutrale, klinische Sprache; Stil besser als bei einem durchschnittlichen menschlichen Arzt.
- Deutliche Angabe, dass dieser Brief anonymisiert und nur für Dokumentationszwecke ist.
- Unterstützt fünf Brief-Typen: Entlassungsbericht, Befundbericht, Überweisung, Konsiliarbericht, Sonstiges.
"""

# =========================
# MOCK RESPONSE
# =========================
def mock_medical_letter(notes, letter_type="Entlassungsbericht", lang="de"):
    # Returns the full prompt as mock "letter" for offline testing
    return generate_prompt(notes, letter_type, lang)

# =========================
# OPENAI CLIENT
# =========================
api_key = os.getenv("OPENAI_API_KEY")
if not st.session_state.mock_mode:
    if not api_key:
        st.error("API key not found! Set OPENAI_API_KEY as environment variable or enable Mock Mode.")
        st.stop()
    client = OpenAI(api_key=api_key)

# =========================
# GENERATE MEDICAL LETTER
# =========================
if st.button("Generate Medical Letter", disabled=not notes.strip()):
    with st.spinner("Generating medical letter..."):
        try:
            if st.session_state.mock_mode:
                st.session_state.generated_letter = mock_medical_letter(notes, letter_type, language)
            else:
                prompt = generate_prompt(notes, letter_type, language)
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
# DISPLAY & PDF
# =========================
if st.session_state.generated_letter:
    st.subheader("Generated Medical Letter")
    st.text_area("", st.session_state.generated_letter, height=400)

    if st.button("Download PDF"):
        with tempfile.NamedTemporaryFile(delete=True, suffix=".pdf") as temp:
            c = canvas.Canvas(temp.name, pagesize=A4)
            width, height = A4

            # PDF HEADER
            c.drawImage("logo.png", 40, height - 70, width=70, preserveAspectRatio=True, mask='auto')
            y = height - 50
            c.setFont("Helvetica-Bold", 14)
            c.drawString(120, y, "🩺 Medical Letter Assistant")
            y -= 18

            # Legal & Disclaimer
            c.setFont("Helvetica", 9)
            legal_text = (
                "Legal Notice / Impressum: Operator: Henk Baldys | Contact: henkbaldys@icloud.com | "
                "Non-profit project. Only anonymized or fictional data allowed.\n"
                "Privacy Policy: No patient-identifiable data is collected or stored. All inputs are session-only. "
                "No data is logged or tracked. Supports GDPR, HIPAA, PIPEDA, Australian Privacy Principles.\n"
                "Medical Disclaimer: This tool is for documentation only. No medical advice, diagnosis, or treatment provided."
            )
            for line in legal_text.split("\n"):
                c.drawString(40, y, line)
                y -= 12
            y -= 10

            # BODY
            c.setFont("Helvetica", 11)
            lines = simpleSplit(st.session_state.generated_letter, "Helvetica", 11, width - 80)
            for line in lines:
                c.drawString(40, y, line)
                y -= 14
                if y < 40:
                    c.showPage()
                    y = height - 80

            c.showPage()
            c.save()
            temp.seek(0)
            st.download_button("Download PDF", temp, file_name="medical_letter.pdf", mime="application/pdf")

# =========================
# STREAMLIT FOOTER
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
