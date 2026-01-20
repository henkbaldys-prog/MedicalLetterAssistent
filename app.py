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
.stTextInput>div>div>input, .stTextArea textarea { border-radius: 8px; padding: 0.5em; }
textarea { font-family: 'Courier New', monospace; }
.stSelectbox>div>div>div>select { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# =========================
# SESSION STATE INIT
# =========================
if "registered" not in st.session_state: st.session_state.registered = False
if "generated_letter" not in st.session_state: st.session_state.generated_letter = ""
if "mock_mode" not in st.session_state: st.session_state.mock_mode = True

# =========================
# HEADER
# =========================
st.markdown("## 🩺 Medical Letter Assistant")
st.caption("Non-Profit Clinical Documentation Tool – anonymisierte Testversion")
st.divider()

# =========================
# REGISTRATION
# =========================
if not st.session_state.registered:
    st.subheader("Access Registration")
    name = st.text_input("Your Name / Organisation", "")
    email = st.text_input("Email Address", "")
    agree = st.checkbox("I agree to the Privacy Policy and Legal Notice")
    if st.button("Continue"):
        if not name or not email or not agree:
            st.warning("Please complete all fields.")
        else:
            st.session_state.registered = True
            st.session_state.user_name = name
            st.success("Access granted. Welcome!")
            st.rerun()
    st.stop()

# =========================
# LANGUAGE
# =========================
language = st.selectbox("Language / Sprache", ["English", "Deutsch"], index=1)

# =========================
# MOCK MODE TOGGLE
# =========================
st.checkbox("Enable Mock Mode (offline testing)", value=True, key="mock_mode")

# =========================
# CLINICAL NOTES INPUT
# =========================
st.subheader("Clinical Notes (anonymized)")
notes = st.text_area(
    "Enter raw medical notes:",
    height=250,
    placeholder="Describe symptoms, observations, lab results, etc."
)

# =========================
# PROMPT GENERATION (LEGAL & PERFECT, ANONYMIZED)
# =========================
def generate_prompt(notes, lang="de"):
    # Anonymisierte Patientendaten
    patient_age = "ca. 50 Jahre"
    patient_sex = "männlich"
    ward = "Innere Medizin, stationär"
    stay_period = "Aufenthalt von 5 Tagen"

    if lang.lower().startswith("en"):
        return f"""
You are a highly experienced medical documentation assistant. 
Create a perfect, professional, fully structured discharge letter based on anonymized patient data.
Use clear, concise, clinical language. Apply these improvements:
•⁠  ⁠Include any provided medication names and doses (if mentioned) clearly.
•⁠  ⁠Include follow-up instructions and recommended outpatient control.
•⁠  ⁠Add explicit warning signs for which the patient should seek urgent care.
•⁠  ⁠Mention relevant laboratory, imaging, or EKG findings if present, in concise structured format.
•⁠  ⁠Ensure uniform section headers and consistent formatting.
•⁠  ⁠Avoid redundancies and filler words; sentences must be precise and professional.
•⁠  ⁠Formal tone, neutral, human-like style.
•⁠  ⁠Do NOT include any real patient identifiers (names, exact DOB, addresses).

Patient Details:
•⁠  ⁠Age: {patient_age}
•⁠  ⁠Sex: {patient_sex}
•⁠  ⁠Ward: {ward}
•⁠  ⁠Stay period: {stay_period}

Clinical Notes (anonymized):
{notes}

Requirements:
1.⁠ ⁠Formal header with anonymized patient details, date, and subject line.
2.⁠ ⁠Sections: History / Presenting Complaint, Examination, Investigations / Diagnostics, Findings / Results, Treatment / Clinical Management, Discharge Status / Recommendations.
3.⁠ ⁠All sections fully phrased in complete sentences.
4.⁠ ⁠Professional medical terminology, readable by any clinician.
5.⁠ ⁠No placeholders, no special characters, no asterisks, no exclamations.
6.⁠ ⁠Produce a single, ready-to-send document.
"""
    else:
        return f"""
Du bist ein sehr erfahrener medizinischer Dokumentationsassistent. 
Erstelle einen perfekt strukturierten, professionellen Entlassungsbrief basierend auf anonymisierten Patientendaten.
Nutze klare, präzise, klinische Sprache. Wende diese Verbesserungen an:
•⁠  ⁠Füge die Medikation mit Dosierungen ein, falls vorhanden, und kennzeichne Änderungen deutlich.
•⁠  ⁠Nenne Nachsorgetermine und ambulante Kontrollmaßnahmen.
•⁠  ⁠Gib Warnhinweise für Symptome an, bei denen der Patient sofort ärztliche Hilfe aufsuchen sollte.
•⁠  ⁠Erwähne relevante Laborwerte, Bildgebung oder EKG-Befunde in prägnanter Form.
•⁠  ⁠Einheitliche Abschnittsüberschriften und konsistente Formatierung.
•⁠  ⁠Vermeide Wiederholungen und unnötige Füllworte; Sätze müssen präzise und professionell sein.
•⁠  ⁠Formeller, neutraler, menschlich wirkender Stil.
•⁠  ⁠Keine echten Patientendaten verwenden (Name, genaues Geburtsdatum, Adresse).

Patientendaten (anonymisiert):
•⁠  ⁠Alter: {patient_age}
•⁠  ⁠Geschlecht: {patient_sex}
•⁠  ⁠Station: {ward}
•⁠  ⁠Aufenthaltsdauer: {stay_period}

Klinische Notizen (anonymisiert):
{notes}

Anforderungen:
1.⁠ ⁠Formeller Kopf mit anonymisierten Patientendaten, Datum und Betreff.
2.⁠ ⁠Abschnitte: Anamnese / Vorstellung, Untersuchung, Diagnostik / Untersuchungen, Befunde / Ergebnisse, Therapie / Klinisches Management, Entlassungszustand / Empfehlungen.
3.⁠ ⁠Alle Abschnitte in vollständigen Sätzen.
4.⁠ ⁠Professionelle medizinische Sprache, für jeden Arzt lesbar.
5.⁠ ⁠Keine Platzhalter, Sonderzeichen, Sternchen oder Ausrufezeichen.
6.⁠ ⁠Ein fertiges, direkt versandbereites Dokument erzeugen.
"""
# =========================
# MOCK RESPONSE
# =========================
def mock_medical_letter(notes, lang):
    now = datetime.now().strftime('%Y-%m-%d')
    if lang.lower().startswith("en"):
        return f"""Patient Name: Patient A
Date: {now}
Subject: Clinical Summary

History:
{notes or 'Patient presented with general symptoms requiring evaluation.'}

Examination:
Physical examination unremarkable. Vital signs within normal limits.

Findings:
No acute pathological findings.

Treatment:
Patient managed according to standard protocols.

Discharge Status:
Patient discharged in stable condition.

Generated by Medical Letter Assistant.
"""
    else:
        return f"""Patient: Patient A
Datum: {now}
Betreff: Arztbrief

Anamnese:
{notes or 'Patient stellte sich mit allgemeinen Symptomen vor, die eine Untersuchung erforderten.'}

Untersuchung:
Körperliche Untersuchung unauffällig. Vitalzeichen im Normbereich.

Befund:
Keine akuten pathologischen Befunde.

Therapie:
Patient unter Standardprotokollen behandelt.

Entlassungszustand:
Patient in stabilem Zustand entlassen.

Erstellt mit Medical Letter Assistant.
"""

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
# GENERATE LEGAL MEDICAL LETTER
# =========================
if st.button("Generate Perfect Medical Letter", disabled=not notes.strip()):
    with st.spinner("Generating perfect medical letter..."):
        try:
            if st.session_state.mock_mode:
                st.session_state.generated_letter = mock_medical_letter(notes, language)
            else:
                prompt = generate_prompt(notes, language)
                response = client.chat.completions.create(
                    model="gpt-4.1",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1500
                )
                st.session_state.generated_letter = response.choices[0].message.content
            st.success("Perfect medical letter generated successfully!")
        except Exception as e:
            st.error(f"Error generating letter: {e}")

# =========================
# DISPLAY & PDF
# =========================
if st.session_state.generated_letter:
    st.subheader("Medical Letter")
    st.text_area("", st.session_state.generated_letter, height=400)

    if st.button("Download PDF"):
        with tempfile.NamedTemporaryFile(delete=True, suffix=".pdf") as temp:
            c = canvas.Canvas(temp.name, pagesize=A4)
            width, height = A4
            y = height - 80
            c.setFont("Helvetica-Bold", 16)
            c.drawString(40, y, "🩺 Medical Letter Assistant")
            y -= 25
            c.setFont("Helvetica", 12)
            c.drawString(40, y, f"Generated by: {st.session_state.user_name}")
            y -= 20
            c.drawString(40, y, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            y -= 30
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
# FOOTER
# =========================
st.divider()
with st.expander("Legal Notice / Impressum"):
    st.markdown("""
*Operator:* Henk Baldys  
*Contact:* henkbaldys@icloud.com  
Non-profit project. No stored data.
""")
with st.expander("Privacy Policy / Datenschutz"):
    st.markdown("""
No data storage.  
No tracking.  
No analytics.  
Session-only processing.
""")
st.caption("This tool assists in documentation only and does not provide medical advice.")
