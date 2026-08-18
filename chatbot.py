import json
from client import client
import re
import datetime

# Load global config
with open("config.json", encoding="utf-8") as f:
    config = json.load(f)
MODEL = config.get("openai_model", "gpt-4")

# Load general instructions
with open("instructions.json", encoding="utf-8") as f:
    instructions = json.load(f)

# Load patient case
with open("matspjälkning_II.json", encoding="utf-8") as f:
    case = json.load(f)

# Build a richer system prompt from instructions and case data
def build_system_prompt(instructions, case):
    rules_text = " ".join(instructions["rules"])  # svenska regler
    # Extract structured case data
    presentation = case.get("presentation", "")
    background = case.get("background", "")
    clinical = case.get("clinical_findings", {})
    labs = case.get("lab_results", {})
    # Pick only the general vitals (ska kunna lämnas ut tidigt)
    vitals = []
    for key in ["pulser", "kroppstemperatur", "blodtryck", "syresättning"]:
        if key in labs:
            vitals.append(f"- {key.capitalize()}: {labs[key]}")
    vitals_text = "\n".join(vitals)

    # Important: enforce factual consistency without revealing more than allowed
    consistency_clause = (
        "Faktaintegritet: Du får aldrig motsäga fallbeskrivningens fakta. "
        "Om studenten frågar om exempelvis resor ska svaret överensstämma med bakgrunden. "
        "Avslöja endast information enligt reglerna ovan."
    )

    # Compose the system prompt (svenska)
    prompt = (
        f"{rules_text}\n\n"
        f"Fall:\n"
        f"- Presentation: {presentation}\n"
        f"- Bakgrund: {background}\n"
        f"- Kända kliniska fynd (internt faktaunderlag, avslöja endast enligt reglerna): {json.dumps(clinical, ensure_ascii=False)}\n"
        f"- Allmänna vitalparametrar (kan lämnas först vid efterfrågan):\n{vitals_text}\n\n"
        f"{consistency_clause}"
    )
    return prompt

system_prompt = build_system_prompt(instructions, case)

# Maintain conversation history
def ask_patient(question, history):
    # history: list of {role, content} dicts (excluding system)
    messages = [
        {"role": "system", "content": system_prompt},
        *history,
        {"role": "user", "content": question}
    ]
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.2  # lägre temp för bättre konsekvens
    )
    return response.choices[0].message.content

def print_role_based_answer(answer):
    # Remove leading/trailing whitespace for accurate matching
    stripped = answer.lstrip()
    if re.match(r"^(Handledare|Lärare|Tutor):", stripped, re.IGNORECASE):
        text = re.sub(r"^(Handledare|Lärare|Tutor):", "", stripped, flags=re.IGNORECASE).strip()
        print("\033[1mHandledare:\033[0m", text, "\n")
    else:
        print("Patienten:", answer.strip(), "\n")

# Summarize history after every 10 exchanges
def summarize_history(history):
    # Only summarize if there are at least 10 exchanges (20 messages)
    if len(history) < 20:
        return history
    # Use the model to summarize the conversation so far
    summary_prompt = (
        "Sammanfatta kortfattat vad som hittills har diskuterats mellan studenten och patienten/handledaren. "
        "Fokusera på viktiga fynd, frågor och svar. Skriv på svenska."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        *history[:20],  # summarize the first 10 exchanges
        {"role": "user", "content": summary_prompt}
    ]
    summary = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.2
    ).choices[0].message.content
    # Replace the first 20 messages with a summary
    summarized_history = [{"role": "assistant", "content": f"Sammanfattning: {summary}"}] + history[20:]
    return summarized_history

if __name__ == "__main__":
    print("\nVälkommen till det virtuella patientfallet!")
    print("Ställ frågor för att samla information och ställa diagnos. Skriv 'exit' för att avsluta.\n")
    history = []
    while True:
        question = input("Du: ")
        if question.lower() in ["exit", "quit"]:
            print("Avslutar sessionen.")
            # Save conversation log as plain text
            now = datetime.datetime.now().strftime("%y%m%d-%H%M%S")
            filename = f"conversation_{now}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                for msg in history:
                    role = msg["role"].capitalize()
                    f.write(f"{role}: {msg['content']}\n\n")
            print(f"Konversationen har sparats i {filename}.")
            break
        try:
            answer = ask_patient(question, history)
            print_role_based_answer(answer)
            # Add user and assistant turns to history
            history.append({"role": "user", "content": question})
            history.append({"role": "assistant", "content": answer})
            # Summarize every 10 exchanges (20 messages)
            history = summarize_history(history)
        except Exception as e:
            print("⚠️ Fel:", str(e))
