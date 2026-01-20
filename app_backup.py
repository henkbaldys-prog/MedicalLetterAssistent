import streamlit as st
import openai 
import streamlit as st
import openai
# --------------------------
# 1. Dein OpenAI Key hier einfügen
# --------------------------
openai.api_key = "DEIN_OPENAI_KEY_HIER"

# --------------------------
# 2. App-Titel
# --------------------------
st.title("Arzt AI Assistent 🩺")
st.write("Gib medizinische Notizen ein, und die KI erstellt professionellen Arz$

# --------------------------
# 3. Text-Eingabe
# --------------------------
user_input = st.text_area("Patienteninformationen, Symptome, Diagnosen...")

# --------------------------
               [ line 2 of 44 (4%), character 36 of 1453 (2%) ]                 
^G Get Help  ^O WriteOut  ^R Read File ^Y Prev Pg   ^K Cut Text  ^C Cur Pos   
^X Exit      ^J Justify   ^W Where is  ^V Next Pg   ^U UnCut Text^T To Spell  

# --------------------------
# 1. Dein OpenAI Key hier einfügen
# --------------------------
openai.api_key = "DEIN_OPENAI_KEY_HIER"

# --------------------------
# 2. App-Titel
# --------------------------
st.title("Arzt AI Assistent 🩺")
st.write("Gib medizinische Notizen ein, und die KI erstellt professionellen Arztbrief.")

# --------------------------
# 3. Text-Eingabe
# --------------------------
user_input = st.text_area("Patienteninformationen, Symptome, Diagnosen...")

# --------------------------
# 4. Button zum Generieren
# --------------------------
if st.button("Arztbrief erstellen"):
    if user_input.strip() == "":
        st.warning("Bitte zuerst Text eingeben!")
    else:
        with st.spinner("KI erstellt Arztbrief..."):
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "Du bist ein professioneller Arzt, der klar und präzise Arztbriefe erstellt."},
                        {"role": "user", "content": user_input}
                    ],
                    max_tokens=500
                )
                result = response['choices'][0]['message']['content']
                st.subheader("Erstellter Arztbrief:")
                st.write(result)
            except Exception as e:
                st.error(f"Fehler beim Generieren: {e}")



