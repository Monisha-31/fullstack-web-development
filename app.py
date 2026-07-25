import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from utils import extract_text_from_file
from model import analyze_resume, load_models

# Ensure wide layout
st.set_page_config(page_title="AI Resume Analyzer", layout="wide")

def display_gauge_chart(score):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Suitability Score", 'font': {'size': 24}},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "rgba(50, 205, 50, 0.8)" if score >= 70 else ("rgba(255, 165, 0, 0.8)" if score >= 40 else "rgba(255, 69, 0, 0.8)")},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 40], 'color': 'rgba(255, 69, 0, 0.1)'},
                {'range': [40, 70], 'color': 'rgba(255, 165, 0, 0.1)'},
                {'range': [70, 100], 'color': 'rgba(50, 205, 50, 0.1)'}],
        }
    ))
    fig.update_layout(height=400, margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(fig, use_container_width=True)

def main():
    st.title("🚀 AI Resume Matching & Skill Gap Analyzer")
    st.markdown("Upload a resume and select a target job role to see how well the candidate matches the industry profile, what skills they already have, and what they need to learn.")

    # Load categories for dropdown (also doubles as our "is the model
    # trained?" check — load_models() returns None, None, None if the
    # artifact files aren't found next to model.py)
    vectorizer, category_vectors, category_keywords = load_models()
    if vectorizer is None:
        st.warning("⚠️ Model not trained yet! Please run `python train.py` in your terminal to process the dataset and generate the model.")
        return

    categories = sorted(list(category_vectors.keys()))

    col1, col2 = st.columns([1, 2])

    with col1:
        st.header("1. Input Data")
        target_role = st.selectbox("🎯 Select Target Job Role", categories)
        
        uploaded_file = st.file_uploader("📄 Upload Resume (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])
        
        analyze_btn = st.button("🔍 Analyze Resume", type="primary")

    with col2:
        st.header("2. Analysis Results")
        
        if analyze_btn:
            if uploaded_file is not None:
                with st.spinner("Analyzing resume against industry profile..."):
                    # Extract text
                    resume_text = extract_text_from_file(uploaded_file)
                    
                    if not resume_text.strip():
                        st.error("Could not extract any text from the uploaded file.")
                    else:
                        # Call model
                        try:
                            results = analyze_resume(resume_text, target_role)
                            
                            score = results['score']
                            matched = results['matched_skills']
                            missing = results['missing_skills']
                            
                            st.subheader("Candidate Suitability")
                            display_gauge_chart(score)
                            
                            if score >= 75:
                                st.success("🌟 **Strong Fit:** This candidate is highly suitable for the role based on keyword matching.")
                            elif score >= 50:
                                st.warning("👍 **Moderate Fit:** The candidate has some relevant skills but may require additional training.")
                            else:
                                st.error("⚠️ **Weak Fit:** This candidate is currently lacking many foundational skills for the role.")
                                
                            col_skills1, col_skills2 = st.columns(2)
                            with col_skills1:
                                st.markdown("### ✅ Matched Skills (Reason for Fit)")
                                if matched:
                                    for skill in matched[:15]:  # show up to 15
                                        st.markdown(f"- {skill.title()}")
                                else:
                                    st.info("No major skills matched.")
                                    
                            with col_skills2:
                                st.markdown("### ❌ Missing Skills (Necessary to Gain)")
                                if missing:
                                    for skill in missing[:15]:
                                        st.markdown(f"- {skill.title()}")
                                else:
                                    st.info("Candidate possesses all top industry keywords!")
                                    
                        except Exception as e:
                            st.error(f"Error during analysis: {e}")
            else:
                st.warning("Please upload a resume to begin analysis.")
        else:
            st.info("👈 Please select a role, upload a resume, and click 'Analyze Resume'.")

if __name__ == "__main__":
    main()
