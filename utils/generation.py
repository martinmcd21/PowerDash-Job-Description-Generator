import os
import re
import textwrap
from functools import lru_cache
from typing import Dict, List
from datetime import date

from openai import OpenAI

BASE_SYSTEM_PROMPT = (
    "You are an expert HR copywriter who creates inclusive, clear, and legally aware Job Descriptions. "
    "Write in plain language, avoid jargon, remove bias, and structure with helpful headings. "
    "Follow the selected jurisdictional norms (spelling/phrasing) and ensure reasonable compliance notes."
)

SECTION_ORDER = [
    "About the Role",
    "Key Responsibilities",
    "About You",
    "Nice to Have",
    "Compensation & Benefits",
    "Additional Information",
    "Equal Opportunities",
]

EEO_DEFAULT = {
    "Global": "We are an equal opportunity employer. We celebrate diversity and are committed to creating an inclusive environment for all employees.",
    "UK": "We are an equal opportunities employer. We welcome applications from all suitably qualified individuals regardless of their background.",
    "USA": "We are an Equal Opportunity Employer, including disability and protected veterans, and we consider qualified applicants with criminal histories, consistent with applicable law.",
    "EU": "We are an equal opportunity employer committed to diversity and inclusion in the workplace.",
    "Canada": "We are an equal opportunity employer committed to inclusive, barrier-free recruitment and selection processes.",
    "Australia": "We are an equal opportunity employer committed to diversity and inclusion.",
}

def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-") or "job-description"

@lru_cache(maxsize=1)
def _get_client() -> OpenAI:
    """Create the OpenAI client, reading the key from env or Streamlit secrets."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        try:
            import streamlit as st  # imported lazily so it exists at runtime
            api_key = st.secrets.get("OPENAI_API_KEY")
        except Exception:
            api_key = None
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY not found. Add it in Streamlit Secrets or as an environment variable."
        )
    return OpenAI(api_key=api_key)

def _compose_prompt(inputs: Dict) -> List[Dict[str, str]]:
    brief_mode = not bool(inputs.get("existing_jd"))

    tenant = inputs.get("tenant_name")
    lang = inputs.get("language", "English")
    tone = inputs.get("tone", "Professional")
    jur = inputs.get("jurisdiction", "UK")

    style_guidance = inputs.get("style_guidance") or ""

    if brief_mode:
        title = inputs.get("role_title") or "Job Title"
        dept = inputs.get("department") or ""
        level = inputs.get("level") or ""
        emp = inputs.get("employment_type") or ""
        loc = inputs.get("location") or ""
        visa = inputs.get("visa") or ""

        bullets_resp = "\n".join(inputs.get("responsibilities", []))
        bullets_req = "\n".join(inputs.get("qualifications", []))
        bullets_nice = "\n".join(inputs.get("nice_to_have", []))
        benefits = "\n".join(inputs.get("benefits", []))
        salary = inputs.get("salary_range") or ""
        report = inputs.get("reporting_line") or ""
        travel = inputs.get("travel") or ""

        user_content = f"""
        Create a Job Description from this structured brief.
        Language: {lang}
        Tone: {tone}
        Jurisdiction: {jur}
        Tenant (for style context only, do not insert logo): {tenant or 'Unbranded'}
        Style guidance: {style_guidance}

        ROLE BASICS
        - Title: {title}
        - Level: {level}
        - Department: {dept}
        - Employment type: {emp}
        - Location: {loc}
        - Visa sponsorship: {visa}
        - Reports to: {report}
        - Travel: {travel}
        - Salary range: {salary}

        RESPONSIBILITIES (one per line):
        {bullets_resp}

        REQUIREMENTS (one per line):
        {bullets_req}

        NICE TO HAVE (one per line):
        {bullets_nice}

        BENEFITS (one per line):
        {benefits}

        Output sections in this order: {', '.join(SECTION_ORDER)}.
        Keep bullet points concise (max ~12 words each). Avoid internal acronyms unless explained.
        """
        title_for_slug = title

    else:
        draft = inputs.get("existing_jd")
        user_content = f"""
        Refine and restructure this Job Description to improve clarity, inclusivity and consistency.
        Language: {lang}
        Tone: {tone}
        Jurisdiction: {jur}
        Style guidance: {style_guidance}

        Draft JD to refine:
        ---
        {draft}
        ---

        Output sections in this order where applicable: {', '.join(SECTION_ORDER)}.
        Keep bullet points concise (max ~12 words each). Avoid redundant phrasing.
        """
        first_line = (draft or "").strip().splitlines()[0] if draft else "Job Description"
        title_for_slug = first_line[:80]

    messages = [
        {"role": "system", "content": BASE_SYSTEM_PROMPT},
        {"role": "user", "content": textwrap.dedent(user_content).strip()},
    ]
    return messages, title_for_slug

def generate_job_description(inputs: Dict, model: str, temperature: float = 0.4) -> Dict:
    client = _get_client()  # <-- create/read key at call-time
    messages, title_for_slug = _compose_prompt(inputs)

    completion = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=messages,
    )
    content = completion.choices[0].message.content.strip()

    # Parse sections
    sections = {}
    current = None
    for ln in content.splitlines():
        h = ln.strip().lstrip("# ")
        if any(h.lower().startswith(s.lower()) for s in SECTION_ORDER):
            current = next((s for s in SECTION_ORDER if h.lower().startswith(s.lower())), None)
            sections[current] = []
        else:
            if current is None:
                current = SECTION_ORDER[0]
                sections[current] = []
            sections[current].append(ln)

    # Ensure EEO
    jur = inputs.get("jurisdiction", "UK")
    if "Equal Opportunities" not in sections:
        sections["Equal Opportunities"] = [EEO_DEFAULT.get(jur, EEO_DEFAULT["Global"]) + "\n"]

    title = inputs.get("role_title") or title_for_slug or "Job Description"

    # Simple HTML preview
    html_parts = [
        f"<h2 style='margin-bottom:0'>{title}</h2>",
        f"<div class='muted' style='margin:0 0 .75rem 0'>{inputs.get('location','') or ''}</div>",
    ]
    for sec in SECTION_ORDER:
        if sec in sections:
            body = "\n".join(sections[sec]).strip()
            if not body:
                continue
            body_html = (
                "<ul>" + "".join(f"<li>{line.strip('- ').strip()}</li>" for line in body.split("\n") if line.strip()) + "</ul>"
                if "\n" in body else f"<p>{body}</p>"
            )
            html_parts.append(f"<div class='section-title'>{sec}</div>")
            html_parts.append(body_html)

    html_preview = "\n".join(html_parts)
    return {
        "title": title,
        "slug": _slugify(f"{title}-{date.today().isoformat()}"),
        "sections": sections,
        "html_preview": html_preview,
    }
