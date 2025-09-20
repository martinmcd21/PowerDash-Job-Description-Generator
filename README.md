# White‑Label Job Description (JD) Generator — PowerDash HR

A Streamlit app that generates or refines Job Descriptions with clean structure, inclusive language, and export to DOCX/Markdown. Unbranded by default with an optional subtle "Powered by PowerDash HR" footer.

## ✨ Features
- Generate JDs from a structured brief or refine an existing draft
- Jurisdiction, tone, and language controls
- Optional tenant branding (org name, colour, logo)
- Exports: **DOCX** and **Markdown**
- Uses OpenAI Chat Completions API (model configurable)

## 🚀 Quickstart
1. **Clone** the repo
   ```bash
   git clone https://github.com/<your-username>/powerdash-jd-generator.git
   cd powerdash-jd-generator
   ```
2. **Create a virtual env & install deps**
   ```bash
   python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. **Set your OpenAI key**
   - Option A (local):
     ```bash
     export OPENAI_API_KEY=sk-...  # Windows PowerShell: $Env:OPENAI_API_KEY="sk-..."
     ```
   - Option B: create a `.streamlit/secrets.toml` with:
     ```toml
     OPENAI_API_KEY = "sk-..."
     OPENAI_MODEL = "gpt-4.1-mini"
     ```
4. **Run the app**
   ```bash
   streamlit run app.py
   ```

## 🧩 Deploy to Streamlit Cloud
1. Push this repo to GitHub.
2. In Streamlit Cloud, create a new app from your repo.
3. Add **Secrets** with `OPENAI_API_KEY` (and optional `OPENAI_MODEL`).
4. Deploy. Done.

## 🔧 Config Notes
- Default model is `gpt-4.1-mini`. You can change in the sidebar or via `OPENAI_MODEL`.
- The app injects **Source Sans 3** via Google Fonts for a modern, readable look.
- To hide the footer, switch off the toggle in the sidebar.

## 📄 License
MIT