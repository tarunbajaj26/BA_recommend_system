import streamlit as st
import pandas as pd
import re
import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
OPENROUTER_API_KEY = st.secrets["OPENROUTER_API_KEY"]

# Streamlit Page Config
st.set_page_config(page_title="Mentor-Led Internships For You!!", page_icon="🎯", layout="wide")

# ✅ Custom CSS for better UI (UpGrad + MentorMind theme)
st.markdown("""
    <style>
    .main, .stApp {
        background-color: #FFFFFF;
        overflow: auto; /* Allow scroll */
    }
    .stButton button {
        background-color: #E32636; /* UpGrad red */
        color: white;
        font-size: 16px;
        font-weight: bold;
        border-radius: 8px;
        padding: 12px 20px;
        border: none;
    }
    .stButton button:hover {
        background-color: #B22222; /* Darker red */
    }
    .recommend-card {
        background-color: #F8F8F8; /* Light gray */
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        color: #333;
        border-left: 5px solid #E32636; /* Red accent */
        height: auto;
    }
    h1, h2, h3 {
        color: #E32636;
    }
    p {
        color: #333;
    }
    .top-banner {
        display: flex;
        justify-content: center; /* Center logo */
        align-items: center;
        margin-bottom: 20px;
    }
    .top-banner img {
        max-height: 80px; /* Slightly bigger logo */
        width: auto;
    }
    </style>
""", unsafe_allow_html=True)

# ✅ Add Banner with Two Logos (UpGrad & MentorMind)
st.markdown("""
    <div class='top-banner'>  
        <img src='https://assets.upgrad.com/2781/_next/static/media/upgrad-header-logo.325f003e.svg'>
        <img src='https://mentormind-static-assets.s3.ap-south-1.amazonaws.com/mentormind_logo.png'>
    </div>
""", unsafe_allow_html=True)

# ✅ Attractive Title & Quote
st.markdown("<h1 style='text-align:center;'>🎯 Mentor-Led Internships</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align:center;color:#333;'>Real Skills. Real Mentors. Real Impact.</h3>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:#555;'>Build your future with industry experts guiding every step.</p>", unsafe_allow_html=True)

# Load CSV data
csv_path = "Bussinessanalytics(mentormind) internships.csv"
df = pd.read_csv(csv_path)
df = df.apply(lambda x: x.astype(str).str.strip())

# Precompute unique options for dropdowns
unique_domains = sorted(df["Job Functions → Name"].dropna().unique())
unique_experience_levels = sorted(df["Experience level"].dropna().unique())
unique_skills = sorted(df[df["Constant Type"] == "Skills"]["Constants → Name"].dropna().unique())
unique_tools = sorted(df[df["Constant Type"] == "Tools"]["Constants → Name"].dropna().unique())
unique_job_roles = sorted(df[df["Constant Type"] == "Job Role"]["Constants → Name"].dropna().unique())

# Utility function to get unique values from a column
def get_unique_values(filtered_df, column):
    return list(filtered_df[column].dropna().unique())

# ✅ Exact Match Recommendation Logic
def recommend_menternships(domains, job_roles, experience_levels, tools, skills):
    filtered_df = df
    if experience_levels:
        filtered_df = filtered_df[filtered_df["Experience level"].str.lower().isin([e.lower() for e in experience_levels])]

    recommendations = []

    for menternship in filtered_df["Menternship"].unique():
        ment_df = filtered_df[filtered_df["Menternship"] == menternship]

        # Extract details
        skills_list = get_unique_values(ment_df[ment_df["Constant Type"] == "Skills"], "Constants → Name")
        tools_list = get_unique_values(ment_df[ment_df["Constant Type"] == "Tools"], "Constants → Name")
        job_roles_list = get_unique_values(ment_df[ment_df["Constant Type"] == "Job Role"], "Constants → Name")
        domain_list = get_unique_values(ment_df, "Job Functions → Name")

        work_techniques = get_unique_values(ment_df[ment_df["Content Type"] == "Work Techniques"], "Menternship Infos → Content")
        deliverables = get_unique_values(ment_df[ment_df["Content Type"] == "Deliverables"], "Menternship Infos → Content")

        # ✅ Flexible Matching Logic: Count matches
        match_count = 0

        if domains and any(d.lower() in [dl.lower() for dl in domain_list] for d in domains):
            match_count += 1
        if job_roles and any(j.lower() in [jr.lower() for jr in job_roles_list] for j in job_roles):
            match_count += 1
        if skills and any(any(s.lower() in sk.lower() for sk in skills_list) for s in skills):
            match_count += 1
        if tools and any(any(t.lower() in tl.lower() for tl in tools_list) for t in tools):
            match_count += 1

        # ✅ Dropdown-based condition remains strict
        if match_count >= 3:
            recommendations.append({
                "Menternship": menternship,
                "Company": ment_df["Company Name"].iloc[0],
                "Experience Level": ment_df["Experience level"].iloc[0],  # ✅ Actual internship level
                "Domain": domain_list,
                "Skills": skills_list,
                "Tools": tools_list,
                "Job Roles": job_roles_list,
                "Work Techniques": work_techniques,
                "Deliverables": deliverables,
                "Website": ment_df["Website URL"].iloc[0]
            })

    return recommendations

# ✅ Extract structured info from query using OpenRouter API
def extract_requirements_from_query(query):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    prompt = f"""
    Extract the following details from this user query: "{query}"
    - Preferred domains
    - Job roles
    - Skills
    - Tools
    Return them as a JSON object with keys: domains, job_roles, skills, tools
    """

    data = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that extracts structured data."},
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    result = response.json()

    try:
        return json.loads(result["choices"][0]["message"]["content"])
    except:
        return {"domains": [], "job_roles": [], "skills": [], "tools": []}

# ----------------- STREAMLIT UI -----------------
st.sidebar.header("Enter Your Preferences")

preferred_domain = st.sidebar.multiselect("Preferred Domain", unique_domains)
preferred_job_role = st.sidebar.multiselect("Preferred Job Role", unique_job_roles)
experience_level = st.sidebar.multiselect("Experience Level", unique_experience_levels)
tools = st.sidebar.multiselect("Tools", unique_tools)
skills = st.sidebar.multiselect("Skills", unique_skills)

col1, col2 = st.sidebar.columns(2)
with col1:
    get_rec = st.button("Get Recommendations ✅")
with col2:
    clear_inputs = st.button("Clear Inputs 🔄")

if clear_inputs:
    st.experimental_rerun()

if get_rec:
    recs = recommend_menternships(preferred_domain, preferred_job_role, experience_level, tools, skills)
    st.subheader("🎯 Recommendations:")
    if recs:
        st.success(f"✅ {len(recs)} Menternships match your preferences")

        cols = st.columns(2)
        for i, r in enumerate(recs):
            with cols[i % 2]:
                st.markdown(f"""
                    <div class='recommend-card'>
                        <h3>{r['Menternship']} at {r['Company']}</h3>
                        <p><b>Experience Level:</b> {r['Experience Level']}</p>
                        <p><b>Domain:</b> {', '.join(r['Domain'])}</p>
                        <p><b>Skills:</b> {', '.join(r['Skills'])}</p>
                        <p><b>Tools:</b> {', '.join(r['Tools'])}</p>
                        <p><b>Job Roles:</b> {', '.join(r['Job Roles'])}</p>
                        <p><b>Work Techniques:</b> {', '.join(r['Work Techniques'])}</p>
                        <p><b>Deliverables:</b> {', '.join(r['Deliverables'])}</p>
                        <a href="{r['Website']}" target="_blank"><b>🔗 Visit Website</b></a>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("No exact matches found. Try adjusting your inputs.")

# ✅ Query-based Recommendation Section
st.markdown("<hr>", unsafe_allow_html=True)
st.subheader("💬 Or Just Type Your Requirement")
query = st.text_area("Describe the internship you are looking for:", 
                     placeholder="e.g., Suggest me data analysis internship where I can learn Excel and Power BI")

if st.button("Get Recommendations from Query 🔍"):
    if query.strip():
        extracted = extract_requirements_from_query(query)
        matched_domains = extracted.get("domains", [])
        matched_job_roles = extracted.get("job_roles", [])
        matched_skills = extracted.get("skills", [])
        matched_tools = extracted.get("tools", [])

        # ✅ Get all recommendations from main function
        all_recs = recommend_menternships(matched_domains, matched_job_roles, [], matched_tools, matched_skills)

        # ✅ Apply relaxed filter for query-based search (>=1 match)
        recs = []
        for r in all_recs:
            match_count = 0
            if matched_domains and any(d.lower() in [dl.lower() for dl in r['Domain']] for d in matched_domains):
                match_count += 1
            if matched_job_roles and any(j.lower() in [jr.lower() for jr in r['Job Roles']] for j in matched_job_roles):
                match_count += 1
            if matched_skills and any(any(s.lower() in sk.lower() for sk in r['Skills']) for s in matched_skills):
                match_count += 1
            if matched_tools and any(any(t.lower() in tl.lower() for tl in r['Tools']) for t in matched_tools):
                match_count += 1

            if match_count >= 1:  # ✅ Relaxed condition for query-based search
                recs.append(r)

        st.subheader("🔍 Recommendations from Query:")
        if recs:
            st.success(f"✅ {len(recs)} Menternships match your query")

            cols = st.columns(2)
            for i, r in enumerate(recs):
                with cols[i % 2]:
                    st.markdown(f"""
                        <div class='recommend-card'>
                            <h3>{r['Menternship']} at {r['Company']}</h3>
                            <p><b>Experience Level:</b> {r['Experience Level']}</p>
                            <p><b>Domain:</b> {', '.join(r['Domain'])}</p>
                            <p><b>Skills:</b> {', '.join(r['Skills'])}</p>
                            <p><b>Tools:</b> {', '.join(r['Tools'])}</p>
                            <p><b>Job Roles:</b> {', '.join(r['Job Roles'])}</p>
                            <p><b>Work Techniques:</b> {', '.join(r['Work Techniques'])}</p>
                            <p><b>Deliverables:</b> {', '.join(r['Deliverables'])}</p>
                            <a href="{r['Website']}" target="_blank"><b>🔗 Visit Website</b></a>
                        </div>
                    """, unsafe_allow_html=True)
        else:
            st.warning("No recommendations found for your query.")
    else:
        st.error("Please type something to get recommendations.")
