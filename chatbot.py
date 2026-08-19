import json
from client import client
import re
import datetime
import html
import os
import sys
from urllib.parse import quote_plus, unquote, urlparse, parse_qs
from urllib.request import Request, urlopen


def get_runtime_base_dir():
    # For PyInstaller one-folder/one-file builds, prefer executable folder.
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = get_runtime_base_dir()


def get_bundle_dir():
    # PyInstaller extracts bundled data to _MEIPASS.
    return getattr(sys, "_MEIPASS", BASE_DIR)


BUNDLE_DIR = get_bundle_dir()


def resolve_data_path(filename):
    # Prefer file beside executable/script to allow local overrides.
    primary = os.path.join(BASE_DIR, filename)
    if os.path.exists(primary):
        return primary
    # Fallback to bundled data location for packaged builds.
    bundled = os.path.join(BUNDLE_DIR, filename)
    if os.path.exists(bundled):
        return bundled
    return primary


def read_json_file(filename):
    path = resolve_data_path(filename)
    with open(path, encoding="utf-8") as f:
        return json.load(f)

# Load global config
config = read_json_file("config.json")
MODEL = config.get("openai_model", "gpt-4")

# Load general instructions
instructions = read_json_file("instructions.json")

# Load patient case
case = read_json_file("matspjälkning_II.json")


def get_lab_test_names(case_data):
    detailed = case_data.get("lab_results", {}).get("detailed", [])
    return [item.get("test", "").strip() for item in detailed if item.get("test")]


LAB_TEST_NAMES = get_lab_test_names(case)
ANALYSPORTALEN_DOMAIN = "analysportalen-labmedicin.skane.se"
REFERENCE_CACHE = {}


def strip_html_to_text(raw_html):
    # Remove scripts/styles and tags, then normalize whitespace.
    no_scripts = re.sub(r"<script[\\s\\S]*?</script>", " ", raw_html, flags=re.IGNORECASE)
    no_styles = re.sub(r"<style[\\s\\S]*?</style>", " ", no_scripts, flags=re.IGNORECASE)
    no_tags = re.sub(r"<[^>]+>", " ", no_styles)
    text = html.unescape(no_tags)
    return re.sub(r"\\s+", " ", text).strip()


def extract_duckduckgo_target(link):
    # DuckDuckGo wraps external links in /l/?uddg=...
    if "duckduckgo.com/l/?" in link or "duckduckgo.com/l/?" in link.replace("//", "https://"):
        parsed = urlparse(link)
        params = parse_qs(parsed.query)
        if "uddg" in params and params["uddg"]:
            return unquote(params["uddg"][0])
    return link


def find_analysportalen_url(test_name):
    query = f'site:{ANALYSPORTALEN_DOMAIN} "{test_name}"'
    search_url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
    try:
        req = Request(search_url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=12) as response:
            html_body = response.read().decode("utf-8", errors="ignore")

        # Match result links from DuckDuckGo HTML endpoint
        candidates = re.findall(r'href="([^"]+)"', html_body)
        for link in candidates:
            target = extract_duckduckgo_target(link)
            if ANALYSPORTALEN_DOMAIN in target:
                return target
    except Exception:
        pass

    # Fallback: Bing HTML search
    try:
        bing_url = f"https://www.bing.com/search?q={quote_plus(query)}"
        req = Request(bing_url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=12) as response:
            html_body = response.read().decode("utf-8", errors="ignore")

        links = re.findall(r'<a\\s+href="(https?://[^"]+)"', html_body)
        for link in links:
            if ANALYSPORTALEN_DOMAIN in link:
                return link
    except Exception:
        pass

    return ""


def find_relevant_excerpt(page_text, test_name):
    lowered = page_text.lower()
    test_lower = test_name.lower()
    keywords = [test_lower, "analysprincip", "metod", "analysmetod"]

    first_index = -1
    for key in keywords:
        idx = lowered.find(key)
        if idx != -1:
            first_index = idx if first_index == -1 else min(first_index, idx)

    if first_index == -1:
        return page_text[:1000]

    start = max(0, first_index - 300)
    end = min(len(page_text), first_index + 1200)
    return page_text[start:end]


def get_analysportalen_reference(test_name):
    if test_name in REFERENCE_CACHE:
        return REFERENCE_CACHE[test_name]

    result = {
        "test": test_name,
        "source_url": "",
        "excerpt": ""
    }

    try:
        url = find_analysportalen_url(test_name)
        if not url:
            REFERENCE_CACHE[test_name] = result
            return result

        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=12) as response:
            raw_page = response.read().decode("utf-8", errors="ignore")

        page_text = strip_html_to_text(raw_page)
        excerpt = find_relevant_excerpt(page_text, test_name)

        result["source_url"] = url
        result["excerpt"] = excerpt
    except Exception:
        # Keep graceful fallback so chat continues even if web lookup fails.
        pass

    REFERENCE_CACHE[test_name] = result
    return result


def mentioned_tests_in_question(question):
    lowered = question.lower()
    mentioned = []
    for test in LAB_TEST_NAMES:
        if test.lower() in lowered:
            mentioned.append(test)
    return mentioned


def build_reference_context(question):
    mentioned_tests = mentioned_tests_in_question(question)
    needs_principle_check = "analysprincip" in question.lower() or "analysmetod" in question.lower() or "metod" in question.lower()

    if not mentioned_tests and not needs_principle_check:
        return ""

    # If no explicit test name but user asks about principle, include all loaded tests as potential references is too large.
    # Instead, do nothing and let the model ask a clarification question.
    if not mentioned_tests:
        return (
            "Extern faktakontroll: Studenten frågar om analysprincip men inget specifikt test nämns. "
            "Be studenten ange testnamn (t.ex. P-Natrium) innan du bedömer korrekthet."
        )

    refs = []
    for test in mentioned_tests:
        ref = get_analysportalen_reference(test)
        if ref["source_url"] and ref["excerpt"]:
            refs.append(
                f"Test: {test}\\nKälla: {ref['source_url']}\\nUtdrag: {ref['excerpt']}"
            )

    if not refs:
        return (
            "Extern faktakontroll: Ingen källa kunde hämtas från Analysportalen just nu. "
            "Säg att du inte kan verifiera exakt analysprincip i denna tur och be studenten kontrollera i Analysportalen."
        )

    joined_refs = "\\n\\n".join(refs)
    return (
        "Extern faktakontroll från Analysportalen (använd detta för att bedöma studentens beskrivning av analysprincip):\\n"
        f"{joined_refs}\\n\\n"
        "Instruktion: Om studenten beskriver analysprincipen, jämför mot utdraget och ge kort feedback: korrekt/delvis korrekt/felaktig, "
        "med en kort motivering."
    )

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
    reference_context = build_reference_context(question)
    messages = [{"role": "system", "content": system_prompt}]
    if reference_context:
        messages.append({"role": "system", "content": reference_context})
    messages.extend([
        *history,
        {"role": "user", "content": question}
    ])
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.4
    )
    return response.choices[0].message.content

def print_role_based_answer(answer):
    # Remove leading/trailing whitespace for accurate matching
    stripped = answer.lstrip()
    if re.match(r"^(Handledare|Lärare|Tutor):", stripped, re.IGNORECASE):
        text = re.sub(r"^(Handledare|Lärare|Tutor):", "", stripped, flags=re.IGNORECASE).strip()
        print("\033[1mHandledare:\033[0m", text, "\n")
    else:
        text = re.sub(r"^Patienten:", "", stripped, flags=re.IGNORECASE).strip()
        print("Patienten:", text, "\n")

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
            output_path = os.path.join(BASE_DIR, filename)
            with open(output_path, "w", encoding="utf-8") as f:
                for msg in history:
                    role = msg["role"].capitalize()
                    f.write(f"{role}: {msg['content']}\n\n")
            print(f"Konversationen har sparats i {filename}.")
            break
        try:
            answer = ask_patient(question, history)
            print()
            print_role_based_answer(answer)
            # Add user and assistant turns to history
            history.append({"role": "user", "content": question})
            history.append({"role": "assistant", "content": answer})
            # Summarize every 10 exchanges (20 messages)
            history = summarize_history(history)
        except Exception as e:
            print("Fel:", str(e))
