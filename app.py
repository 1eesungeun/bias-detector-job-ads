import os  # This part loads the libraries we need for file and environment variable access.
import streamlit as st  # This loads Streamlit for building the web app.

from intro import render_intro  
import re as _re  # Loads regex for pattern matching.

from dotenv import load_dotenv  # Loads environment variables from a .env file.
load_dotenv()  # This line loads the .env file.

from nav import render_navbar  
from about import render_about  
from footer import render_footer  
from prompts import GEMINI_SYSTEM_PROMPT # Imports the system prompt for Gemini from prompts.py.

# --- Normalize Unicode hyphens/dashes to plain ASCII hyphen so regex matches work ---
_HYPHENS = dict.fromkeys(map(ord, "\u2010\u2011\u2012\u2013\u2014\u2015"), ord("-"))
def _normalize_hyphens(s: str) -> str:
    return s.translate(_HYPHENS)

APP_TITLE = "Bias Detector for Job Ads" # The title of the app shown in the browser tab.

# This section tries to import Google Gemini. If not available, disables AI features.
try:
    import google.generativeai as genai
    _HAS_GEMINI = True
except Exception:
    _HAS_GEMINI = False

def _init_gemini(model_name: str | None = None):
    """
    This function connects to Gemini.
    - Reads the Gemini API key from environment variables.
    - Tries several model names until one works.
    - Returns the Gemini model object, or None if not configured.
    """
    if not _HAS_GEMINI:
        return None
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        genai.configure(api_key=api_key)
    except Exception:
        return None

    # Helper to try both plain and 'models/'-prefixed model names.
    def _try_make(name: str):
        try:
            return genai.GenerativeModel(name)
        except Exception:
            pass
        if not name.startswith("models/"):
            try:
                return genai.GenerativeModel(f"models/{name}")
            except Exception:
                pass
        return None

    # Try the requested model name, then a list of common ones.
    fallback_candidates = [
        model_name,
        "models/gemini-2.5-flash",
        "models/gemini-2.5-pro",
        "models/gemini-2.5-flash-preview-05-20",
        "models/gemini-2.5-pro-preview-06-05",
        "models/gemini-2.5-pro-preview-03-25",
        "models/gemini-2.5-flash-lite-preview-06-17",
        "models/gemini-1.5-pro-latest",
        "models/gemini-1.5-flash-latest",
        "gemini-1.5-pro-latest",
        "gemini-1.5-flash-latest",
        "gemini-1.0-pro",
    ]

    for cand in [c for c in fallback_candidates if c]:
        m = _try_make(cand)
        if m is not None:
            return m
    return None

 # This section defines the default lexicon for instant bias detection.
 # Each category has:
 # - phrases: exact words to match quickly
 # - patterns: regex patterns for more flexible matches
 # - rewrite: a suggested tip for more inclusive wording
 # This list is intentionally small and simple for transparency.
DEFAULT_LEXICON = {
    "age bias": {
        "phrases": ["young", "recent graduate", "new grad", "digital native", "under 30"],
        "patterns": [r"\bunder\s*30\b"],
        "rewrite": "Focus on skills or years of experience, not age."
    },
    "gender bias": {
        "phrases": ["salesman"],
        "patterns": [],
        "rewrite": "Use gender-neutral language such as ‘salesperson’."
    },
    "language/ESL bias": {
        "phrases": ["native English speaker", "no accent"],
        "patterns": [r"\bnative\s+english\s+speaker\b", r"\bno\s+accent(s)?\b"],
        "rewrite": "Specify communication skills (e.g., ‘excellent written and spoken English’)."
    },
    "cultural fit exclusion": {
        "phrases": ["culture fit", "work hard play hard"],
        "patterns": [r"\bculture\s*fit\b", r"\bwork\s*hard\s*play\s*hard\b"],
        "rewrite": "Describe values and behaviours (e.g., collaboration), not vague ‘fit’ terms."
    },
    "nationality/visa bias": {
        "phrases": ["visa sponsorship not available", "PR only"],
        "patterns": [r"\bvisa\s*sponsorship\s*not\s*available\b", r"\bPR\s*only\b"],
        "rewrite": "Say ‘must have the legal right to work in X’ instead of nationality restrictions."
    },
    "appearance bias": {
        "phrases": ["well-presented", "well-groomed"],
        "patterns": [],
        "rewrite": "Focus on professionalism (e.g., ‘client-facing dress code’) rather than appearance."
    }
}

 # These are simple regex rules for the "Quick Highlights" feature.
 # Each rule matches obvious bias phrases and assigns a category label.
RULES = [
    {"regex": r"\byoung\b", "label": "age bias", "weight": 1.0},
    {"regex": r"\brecent\s*grad(uate)?\b|\bnew\s*grad\b", "label": "age bias", "weight": 1.0},
    {"regex": r"\bdigital\s*native\b", "label": "age bias", "weight": 1.0},
    {"regex": r"\bunder\s*30\b", "label": "age bias", "weight": 1.0},
    {"regex": r"\bsalesman\b", "label": "gender bias", "weight": 1.0},
    {"regex": r"\bnative\s+english\s+speaker\b", "label": "language/ESL bias", "weight": 1.0},
    {"regex": r"\bno\s+accent(s)?\b", "label": "language/ESL bias", "weight": 1.0},
    {"regex": r"\bculture\s*fit\b", "label": "cultural fit exclusion", "weight": 1.0},
    {"regex": r"\bwork\s*hard\s*play\s*hard\b", "label": "cultural fit exclusion", "weight": 1.0},
    {"regex": r"\bvisa\s*sponsorship\s*not\s*available\b", "label": "nationality/visa bias", "weight": 1.0},
    {"regex": r"\bPR\s*only\b", "label": "nationality/visa bias", "weight": 1.0},
    {"regex": r"\bwell[-\s]?presented\b|\bwell[-\s]?groomed\b", "label": "appearance bias", "weight": 1.0}
]

 # These regex patterns help reduce false positives in detection.
NEGATION_RE = _re.compile(r"\b(no|not|without)\b", _re.IGNORECASE)  # Finds negation words.
ROLE_NOUNS_RE = _re.compile(r"\b(candidate|applicant|hire|person|team|staff|employee)\b", _re.IGNORECASE)  # Finds job-related nouns.
EOE_WHITELIST_RE = _re.compile(r"equal\s+opportunit(y|ies)|\beoe\b|reasonable\s+accommodation", _re.IGNORECASE)  # Finds EOE/anti-bias statements.

 # This dictionary sets the highlight color for each bias category.
HIGHLIGHT_COLORS = {
    "age bias": "#fde68a",
    "language/ESL bias": "#bfdbfe",
    "cultural fit exclusion": "#fecaca",
    "gender bias": "#fbcfe8",
    "nationality/visa bias": "#fcd34d",
    "appearance bias": "#fca5a5",
}

 # These are short reasons explaining why each bias category is risky.
 # They appear under "Why these were flagged" in the UI.
LABEL_EXPLANATIONS = {
    "language/ESL bias": "ESL = English as a Second Language. Flags wording that excludes non-native speakers.",
    "age bias": "Wording that implies preference based on age (e.g., 'young', 'recent grad').",
    "cultural fit exclusion": "Vague 'fit' language that can gatekeep or hide subjective preferences.",
    "gender bias": "Gendered terms or titles (e.g., 'salesman', 'chairman').",
}

def analyze_with_gemini(text: str, grouped_hits: dict, temperature: float = 0.3) -> str:
    """
    This function sends the user text and detected bias terms to Gemini.
    Gemini returns a plain-English explanation and suggested rewrites.
    If Gemini is not set up, it shows a warning.
    """
    model = _init_gemini()
    if model is None:
        return ("⚠️ Gemini is not configured. Set the GOOGLE_API_KEY environment variable (in a .env file or your shell), then reload the app.")

    # Build the prompt for Gemini: includes user text, detected categories, and instructions.
    detected_list = []
    for k, vs in grouped_hits.items():
        if vs:
            detected_list.append(f"- {k}: " + ", ".join(sorted(set(vs))))
    detected_md = "\n".join(detected_list) if detected_list else "- None from heuristics/lexicon"

    user_prompt = f"""## Input text
{text}

## Detected (heuristics/lexicon)
{detected_md}

## Task
1) If bias is present, list categories and matched terms.
2) For each category, explain why it matters (HCAI rationale).
3) Give specific rewrite options and a one-paragraph neutral rewrite of the full sentence.
4) Keep it under ~300 words. Markdown headings and bullets are fine.
"""
    # Ask Gemini to generate the Markdown output. Show a readable error if it fails.
    try: # The API call and response handling
        resp = model.generate_content(
            [{"role": "user", "parts": [{"text": GEMINI_SYSTEM_PROMPT}, {"text": user_prompt}]}],
            generation_config={"temperature": float(temperature)}
        )
        return resp.text or "Gemini returned no text."
    except Exception as e:
        # If Gemini call fails, try to show available models (for debugging).
        avail = []
        try:
            api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
                for m in genai.list_models():
                    if hasattr(m, "supported_generation_methods") and "generateContent" in getattr(m, "supported_generation_methods", []):
                        avail.append(getattr(m, "name", ""))
        except Exception:
            pass
        hint = f" Available models for this key: {', '.join(avail[:8])}" if avail else ""
        return f"⚠️ Gemini call failed: {e}.{hint}"

def _escape_html(s: str) -> str:
    # Escapes HTML so user text can be safely shown with highlights.
    import html
    return html.escape(s, quote=False)

def find_bias_rules(text: str, window: int = 40):
    """
    This function checks the text for obvious bias phrases using regex rules.
    - Skips if an EOE (equal opportunity) statement is present.
    - Ignores matches with nearby negation (e.g., "not young").
    - Returns a list of hits and a simple score per category.
    """
    hits = []
    scores = {}
    # Skip if anti-bias statement is found.
    if EOE_WHITELIST_RE.search(text):
        return [], {}

    for rule in RULES:
        pat = rule["regex"]
        label = rule["label"]
        weight = float(rule.get("weight", 1.0))
        needs_ctx = bool(rule.get("needs_context", False))

        # For each regex match, check for negation and context.
        for m in _re.finditer(pat, text, flags=_re.IGNORECASE):
            s, e = m.span()
            # Skip if 'no/not/without' appears shortly before the match.
            pre_start = max(0, s - window)
            pre_context = text[pre_start:s]
            if NEGATION_RE.search(pre_context):
                continue
            # Optionally require a job role noun near the match.
            if needs_ctx:
                ctx_start = max(0, s - window)
                ctx_end = min(len(text), e + window)
                ctx = text[ctx_start:ctx_end]
                if not ROLE_NOUNS_RE.search(ctx):
                    continue

            hits.append({
                "category": label,
                "type": "pattern",
                "term": m.group(0),
                "span": (s, e),
            })
            scores[label] = scores.get(label, 0.0) + weight

    return hits, scores

# This function checks the text for bias using the phrase and pattern lexicon.
def find_bias_lexicon(text: str, lexicon: dict, context_chars: int = 30):
    hits = []
    low = text.lower()
    for cat, cfg in lexicon.items():
        # Check for exact phrases.
        for phrase in cfg.get("phrases", []):
            idx = low.find(phrase.lower())
            if idx != -1:
                start = max(0, idx - context_chars)
                end = min(len(text), idx + len(phrase) + context_chars)
                ctx = text[start:end]
                hits.append({
                    "category": cat,
                    "type": "phrase",
                    "term": phrase,
                    "context": ctx,
                    "rewrite": cfg.get("rewrite", "")
                })
        # Check for regex patterns.
        for pat in cfg.get("patterns", []):
            for m in _re.finditer(pat, text, flags=_re.IGNORECASE):
                span = m.span()
                start = max(0, span[0] - context_chars)
                end = min(len(text), span[1] + context_chars)
                ctx = text[start:end]
                hits.append({
                    "category": cat,
                    "type": "pattern",
                    "term": m.group(0),
                    "context": ctx,
                    "rewrite": cfg.get("rewrite", "")
                })
    return hits

# This function creates HTML for the "Quick Highlights" tab.
# It wraps risky terms in <mark> tags with category colors.
def build_highlighted_html(text: str, lex_hits: list, rule_hits: list) -> str:
    # Collect spans for all matches.
    spans = []
    low = text.lower()
    for h in lex_hits:
        term = h.get("term", "")
        if not term:
            continue
        idx = low.find(term.lower())
        if idx != -1:
            spans.append({"start": idx, "end": idx + len(term), "label": h.get("category", "bias"), "term": term})

    # Add spans from regex RULES matches.
    for h in rule_hits:
        s, e = h["span"]
        spans.append({"start": s, "end": e, "label": h.get("category", "bias"), "term": h.get("term", "")})

    # Merge overlapping spans (keep the longer one).
    spans.sort(key=lambda x: (x["start"], x["end"]))
    merged = []
    for sp in spans:
        if not merged:
            merged.append(sp); continue
        last = merged[-1]
        if sp["start"] <= last["end"]:
            if (sp["end"] - sp["start"]) > (last["end"] - last["start"]):
                merged[-1] = sp
        else:
            merged.append(sp)

    # Build the HTML with highlights.
    out = []; cursor = 0
    for sp in merged:
        if cursor < sp["start"]:
            out.append(_escape_html(text[cursor:sp["start"]]))
        chunk = _escape_html(text[sp["start"]:sp["end"]])
        color = HIGHLIGHT_COLORS.get(sp["label"], "#e5e7eb")
        out.append(
            f'<mark style="background:{color}; padding:0 3px; border-radius:3px;">{chunk}</mark>'
        )
        cursor = sp["end"]
    if cursor < len(text):
        out.append(_escape_html(text[cursor:]))

    return "<div style='line-height:1.8'>" + "".join(out) + "</div>"

# This function renders colored "pills" for each bias category found.
def render_legend(labels: list):
    pills = []
    for lb in labels:
        color = HIGHLIGHT_COLORS.get(lb, "#e5e7eb")
        pills.append(
            f"<span style='display:inline-block; padding:4px 8px; margin:2px; "
            f"border-radius:999px; background:{color}; font-size:12px'>{_escape_html(lb)}</span>"
        )
    return "<div style='margin-top:6px'>" + "".join(pills) + "</div>"

# This function groups all detected terms by bias category for UI and Gemini.
def group_hits_by_label(lex_hits: list, rule_hits: list):
    grouped = {}
    for h in (lex_hits or []):
        lb = h.get("category", "bias")
        grouped.setdefault(lb, []).append(h.get("term", ""))
    for h in (rule_hits or []):
        lb = h.get("category", "bias")
        grouped.setdefault(lb, []).append(h.get("term", ""))
    # Remove duplicates.
    for lb, terms in grouped.items():
        seen = set(); dedup = []
        for t in terms:
            if t not in seen:
                dedup.append(t); seen.add(t)
        grouped[lb] = dedup
    return grouped


# This function fills the text box with an example job ad (for quick testing).
def _insert_example():
    st.session_state["text"] = (
        "Sales Executive — Fast‑Paced Startup\n\n"
        "We are seeking a young, well‑presented salesman to join our dynamic team. "
        "This role is ideal for a recent graduate or new grad who is a true digital native and eager to grow. "
        "Applicants must be under 30 and able to thrive in a high‑energy, culture fit environment where we work hard play hard.\n\n"
        "The ideal candidate is a native English speaker with strong communication skills and no accent in customer interactions. "
        "Prior experience in retail or hospitality is preferred. Visa sponsorship not available; PR only for this position. "
        "You will collaborate with a youthful team and represent our brand in client‑facing settings, so being well‑groomed and professional is essential.\n\n"
        "Responsibilities include meeting weekly sales targets, attending after‑hours client events, and contributing to team initiatives."
    )

 # Streamlit page setup and navigation
st.set_page_config(page_title=APP_TITLE, layout="wide")

render_navbar()

def _get_current_page():
    """
    This function figures out which page to show ("intro" or "about").
    It checks the URL and session state, and keeps the URL updated.
    """
    # Read from URL query params if available.
    if hasattr(st, "query_params"):
        qp = st.query_params
        raw = qp.get("page")
    else:
        qp = st.experimental_get_query_params()
        raw = qp.get("page") if isinstance(qp.get("page"), str) else (qp.get("page", ["intro"])[0] if qp.get("page") else None)

    page = raw or "intro"

    # Use nav button click if present in session state.
    ss_page = st.session_state.get("nav_page")
    if ss_page:
        page = ss_page

    # Normalize the page name.
    page = str(page).lower().strip()
    if page in ("check", "home", "index"):
        page = "intro"
    if page not in ("intro", "about"):
        page = "intro"

    # Write back to query params for easy sharing.
    try:
        if hasattr(st, "query_params"):
            st.query_params["page"] = page
        else:
            st.experimental_set_query_params(page=page)
    except Exception:
        pass

    # Mirror to session state.
    st.session_state["nav_page"] = page
    return page

current_page = _get_current_page()

# If user is on About page, show it and stop.
if current_page == "about":
    render_about()
    st.markdown("---")
    render_footer()
    st.stop()

# Fixed temperature for Gemini output (creativity control).
temperature = float(os.getenv("APP_TEMPERATURE", 0.4))

# Layout: two columns (left for intro, right for user input/results).
left_col, spacer, right_col = st.columns([1, 0.05, 1])

with left_col:
    render_intro(col=left_col)  # Show the intro text on the left.

with right_col:
    st.subheader("Paste text to analyse for bias")  # Main input area.
    st.caption("Example: paste a job advertisement.“We're looking for a young, energetic salesman who fits our culture and is a native English speaker.”")
    # This is where the user pastes or types their job ad.
    text_widget = st.text_area(
        "Text",
        height=180,
        key="text",
        placeholder='Paste a job advertisement here'
    )
    # Two buttons: Analyze and Insert Example Text.
    c1, c2 = st.columns([1, 1])
    with c1:
        run = st.button(
            "Analyze",
            type="primary",
            use_container_width=True,
            disabled=(len(st.session_state.get("text", "").strip()) == 0),
        )
    with c2:
        st.button("Insert Example Text", on_click=_insert_example, use_container_width=True)
    st.caption("Tip: Highlights appear instantly; AI explanations may take a few seconds.")

# ==== Main analysis flow ====
# When the user clicks "Analyze," this section runs:
# 1) Scans text for obvious bias phrases (lexicon + regex).
# 2) Groups matches for UI display and Gemini context.
# 3) Calls Gemini for explanations and rewrites.
# 4) Shows results in two tabs: Quick Highlights and Contextual Explanations.
if run:
    # Keep original user text for display; normalize a copy for detection.
    raw_text = st.session_state.get("text", "")
    text = _normalize_hyphens(raw_text)

    # === Rule-based Detection ===
    # Find highlights using lexicon and regex rules on the normalized text.
    lex_hits = find_bias_lexicon(text, DEFAULT_LEXICON, context_chars=30)
    rule_hits, _ = find_bias_rules(text)
    # Group detected terms by bias category for both UI and Gemini.
    grouped = group_hits_by_label(lex_hits, rule_hits)

    # All grouped categories are sent to Gemini.
    grouped_for_gemini = grouped

    # Results are shown in two tabs.
    tabs = st.tabs(["Quick Highlights", "Contextual Explanations"])

    with tabs[0]:
        # This tab shows instant, rule-based highlights in the text.
        st.caption("Quick Highlights: instant matches from a small, transparent phrase list (e.g., “young”, “culture fit”, “native English speaker”). It will not catch everything.")

        if not (lex_hits or rule_hits):
            st.info("No exact matches found by the small pattern list. Subtle or context-dependent bias may still exist. See **Contextual Explanations** for guidance and safer wording.")
        else:
            html = build_highlighted_html(text, lex_hits, rule_hits)
            st.markdown(html, unsafe_allow_html=True)

            # Show legend for detected categories.
            found_labels = []
            for h in lex_hits + rule_hits:
                lb = h.get("category")
                if lb and lb not in found_labels:
                    found_labels.append(lb)
            st.markdown(render_legend(found_labels), unsafe_allow_html=True)

            # Show short reason for each flagged category.
            reasons_md = []
            for lb in found_labels:
                reason = LABEL_EXPLANATIONS.get(lb)
                if reason:
                    reasons_md.append(f"- **{lb.title()}**: {reason}")
            if reasons_md:
                st.markdown("---")
                st.markdown("**Why these were flagged**")
                st.markdown("\n".join(reasons_md))

    # === AI Explanation Display Area ===
    # This tab displays Gemini's Markdown output with explanations and rewrites.
    with tabs[1]:
        st.caption("Contextual Explanations: generated by Google Gemini from your full sentence, with plain‑English reasons and inclusive rewrites.")

        # Show a spinner while Gemini generates output.
        with st.spinner("Generating explanations…"):
            md = analyze_with_gemini(text, grouped_for_gemini, temperature)
        st.markdown(md)

# Footer
if current_page == "intro":
    st.markdown("---")
    render_footer()
