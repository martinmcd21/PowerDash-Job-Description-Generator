import os
import io
from typing import List, Dict

import streamlit as st
from dotenv import load_dotenv
import streamlit as st, os
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY", "")

from utils.generation import generate_job_description
from utils.export import jd_to_docx, jd_to_markdown

load_dotenv()

st.set_page_config(
    page_title="Job Description Generator",
    page_icon="📝",
    layout="wide",
)

# ---------- Styles (Source Sans Pro + subtle theming) ----------
GOOGLE_FONTS = "https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@300;400;600;700&display=swap"
CUSTOM_CSS = f"""
<link href='{GOOGLE_FONTS}' rel='stylesheet'>
<style>
    html, body, [class*="css"], textarea, input {{
        font-family: 'Source Sans 3', -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif !important;
    }}
    .powerdash-footer {{
        margin-top: 2.5rem;
        padding-top: 1rem;
        border-top: 1px solid rgba(0,0,0,0.08);
        font-size: 0.9rem;
        opacity: 0.8;
        text-align: center;
    }}
    .brand-chip {{ 
        display: inline-flex; align-items: center; gap: .5rem; 
        padding: .25rem .5rem; border-radius: 999px; 
        background: var(--chip-bg, #fffbe6); border: 1px solid #ffe58f; 
        font-size: .85rem;
    }}
    .section-title {{
        font-weight: 700; font-size: 1.15rem; margin: .75rem 0 .25rem 0;
    }}
    .muted {{opacity: 0.85}}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------- Sidebar: Tenant & Model Settings ----------
with st.sidebar:
    st.header("⚙️ Settings")
    st.caption("Configure tenant branding and generation options.")

    # Tenant Branding
    st.subheader("Tenant Branding")
    tenant_name = st.text_input("Organisation name (optional)")
    primary_colour = st.color_picker("Primary colour", "#111827")  # default near-black
    logo_url = st.text_input("Logo URL (optional)")
    show_powerdash = st.toggle("Show 'Powered by PowerDash HR'", value=True)

    # Generation Controls
    st.subheader("Generation Model")
    default_model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    model = st.text_input("OpenAI model", value=default_model, help="E.g., gpt-4.1, gpt-4.1-mini, o3-mini")
    temperature = st.slider("Creativity (temperature)", 0.0, 1.5, 0.4, 0.1)

    st.subheader("House Style (optional)")
    jd_language = st.selectbox("Language", ["English", "Français", "Deutsch", "Español", "Italiano"], index=0)
    tone = st.selectbox("Tone", ["Professional", "Warm", "Concise", "Inclusive", "Energetic"], index=0)
    jurisdiction = st.selectbox("Jurisdiction", ["Global", "UK", "USA", "EU", "Canada", "Australia"], index=1)

    st.caption("Set OPENAI_API_KEY in your environment or Streamlit Secrets.")

# ---------- Header ----------
left, right = st.columns([0.75, 0.25])
with left:
    title_text = "Job Description Generator"
    if tenant_name:
        title_text += f" — {tenant_name}"
    st.title(title_text)
    st.markdown(
        "Generate a polished, inclusive Job Description from a brief or by refining an existing draft."
    )
with right:
    if logo_url:
        st.image(logo_url, caption=tenant_name or "", use_column_width=True)

# ---------- Tabs ----------
TAB_BRIEF, TAB_REWRITE = st.tabs(["From Brief", "Refine Existing Draft"])

with TAB_BRIEF:
    st.subheader("Role Basics")
    col1, col2, col3 = st.columns(3)
    with col1:
        role_title = st.text_input("Job title", placeholder="e.g., Senior Data Analyst")
        level = st.selectbox("Seniority", ["Intern", "Entry", "Associate", "Mid", "Senior", "Lead", "Manager", "Director", "VP", "C-suite"])    
    with col2:
        department = st.text_input("Department/Team", placeholder="e.g., Analytics")
        employment_type = st.selectbox("Employment type", ["Full-time", "Part-time", "Contract", "Fixed-term", "Internship"])    
    with col3:
        location = st.text_input("Location", placeholder="e.g., London (Hybrid)")
        visa = st.selectbox("Visa sponsorship", ["Not available", "Available", "Case-by-case"]) 

    st.subheader("What you'll do — Responsibilities")
    responsibilities = st.text_area("Key duties (one per line)", height=140, placeholder="Lead KPI reporting pipeline\nBuild dashboards in Power BI\nPartner with stakeholders across Ops & Finance")

    st.subheader("What you'll bring — Qualifications")
    qualifications = st.text_area("Requirements (one per line)", height=140, placeholder="3+ years in analytics\nSQL + Python proficiency\nPower BI experience")

    st.subheader("Nice to have (optional)")
    nice_to_have = st.text_area("Nice-to-haves (one per line)", height=100, placeholder="Statistics background\nDBT or Airflow")

    st.subheader("Compensation & Benefits (optional)")
    col4, col5 = st.columns(2)
    with col4:
        salary_range = st.text_input("Salary range (optional)", placeholder="e.g., £55,000–£65,000 + bonus")
        benefits = st.text_area("Benefits (one per line)", height=100, placeholder="25 days holiday + bank holidays\nPrivate healthcare\nPension contribution")
    with col5:
        reporting_line = st.text_input("Reports to (optional)", placeholder="e.g., Head of Analytics")
        travel = st.text_input("Travel (optional)", placeholder="e.g., Occasional travel to sites")

    st.subheader("House Guidance (optional)")
    style_guidance = st.text_area("Paste any house style / guidance", height=120, placeholder="e.g., Write in UK English. Keep bullets short. Avoid jargon. Include EEO statement.")

    generate_from_brief = st.button("Generate Job Description", type="primary")

with TAB_REWRITE:
    st.subheader("Paste your draft JD")
    existing_jd = st.text_area("Existing job description", height=300, placeholder="Paste your current JD here for refinement…")
    st.caption("We'll improve clarity, structure, inclusivity and consistency with the selected options in the sidebar.")
    generate_from_existing = st.button("Refine Draft", type="primary")

# ---------- Generation ----------
if generate_from_brief or generate_from_existing:
    with st.spinner("Thinking…"):
        jd_inputs = {
            "role_title": role_title if generate_from_brief else "",
            "department": department if generate_from_brief else "",
            "level": level if generate_from_brief else "",
            "employment_type": employment_type if generate_from_brief else "",
            "location": location if generate_from_brief else "",
            "visa": visa if generate_from_brief else "",
            "responsibilities": [x.strip() for x in (responsibilities or "").split("\n") if x.strip()] if generate_from_brief else [],
            "qualifications": [x.strip() for x in (qualifications or "").split("\n") if x.strip()] if generate_from_brief else [],
            "nice_to_have": [x.strip() for x in (nice_to_have or "").split("\n") if x.strip()] if generate_from_brief else [],
            "salary_range": salary_range if generate_from_brief else "",
            "benefits": [x.strip() for x in (benefits or "").split("\n") if x.strip()] if generate_from_brief else [],
            "reporting_line": reporting_line if generate_from_brief else "",
            "travel": travel if generate_from_brief else "",
            "style_guidance": style_guidance,
            "existing_jd": existing_jd if generate_from_existing else "",
            "language": jd_language,
            "tone": tone,
            "jurisdiction": jurisdiction,
            "tenant_name": tenant_name,
        }

        try:
            jd = generate_job_description(
                inputs=jd_inputs,
                model=model,
                temperature=temperature,
            )
        except Exception as e:
            st.error(f"Generation failed: {e}")
            jd = None

    if jd:
        st.success("Job Description ready ✨")
        st.markdown(jd["html_preview"], unsafe_allow_html=True)

        # ----- Exports -----
        st.subheader("Export")
        docx_bytes = jd_to_docx(
            jd_sections=jd["sections"],
            title=jd["title"],
            tenant_name=tenant_name,
            logo_url=logo_url,
            primary_colour=primary_colour,
        )
        st.download_button("⬇️ Download DOCX", data=docx_bytes, file_name=f"{jd['slug']}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

        md_bytes = io.BytesIO(jd_to_markdown(jd["sections"], jd["title"]).encode("utf-8"))
        st.download_button("⬇️ Download Markdown", data=md_bytes, file_name=f"{jd['slug']}.md", mime="text/markdown")

# ---------- Footer ----------
if show_powerdash:
    st.markdown(
        f"""
        <div class='powerdash-footer'>
            <span class='brand-chip' style='--chip-bg:{primary_colour}10'>
                ⚡️ Powered by <strong>PowerDash HR</strong>
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )
