import streamlit as st
from streamlit_extras.add_vertical_space import add_vertical_space
import os
import json
from dotenv import load_dotenv
from helper import configure_genai, get_gemini_response, extract_pdf_text, prepare_prompt

def init_session_state():
    """Initialize session state variables."""
    if 'processing' not in st.session_state:
        st.session_state.processing = False


def main():
    # Load environment variables
    load_dotenv()
    
    # Initialize session state
    init_session_state()
    
    # Configure Generative AI
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("Please set the GOOGLE_API_KEY in your .env file")
        return
        
    try:
        configure_genai(api_key)
    except Exception as e:
        st.error(f"Failed to configure API: {str(e)}")
        return

    # Sidebar
    with st.sidebar:
        st.title("🎯 Smart ATS")
        st.subheader("About")
        st.write(""" 
        This smart ATS helps you:
        - Evaluate resume-job description match
        - Identify missing keywords
        - Get personalized improvement suggestions
        """)

    # Main content
    st.title("📄 Smart ATS Resume Analyzer")
    st.subheader("Optimize Your Resume for ATS")
    
    # Input sections for job description and resume
    jd = st.text_area(
        "Job Description",
        placeholder="Paste the job description here...",
        help="Enter the complete job description for accurate analysis"
    )
    
    uploaded_file = st.file_uploader(
        "Resume (PDF)",
        type="pdf",
        help="Upload your resume in PDF format"
    )

    # Input sections for cover letter
    company_name = st.text_input("Company Name", placeholder="Enter company name here...")
    job_title = st.text_input("Job Title", placeholder="Enter job title here...")
    personal_message = st.text_area("Personal Message", placeholder="Add a personal message here...")

    # Process button with loading state
    if st.button("Analyze Resume", disabled=st.session_state.processing):
        if not jd:
            st.warning("Please provide a job description.")
            return
            
        if not uploaded_file:
            st.warning("Please upload a resume in PDF format.")
            return
            
        st.session_state.processing = True
        
        try:
            with st.spinner("📊 Analyzing your resume..."):
                # Extract text from PDF
                resume_text = extract_pdf_text(uploaded_file)
                
                # Prepare prompt for resume analysis
                input_prompt = prepare_prompt(resume_text, jd)
                
                # Get and parse response for resume analysis
                response = get_gemini_response(input_prompt)
                response_json = json.loads(response)
                
                # Display results for resume analysis
                st.success("✨ Analysis Complete!")
                
                # Match percentage
                match_percentage = response_json.get("JD Match", "N/A")
                st.metric("Match Score", match_percentage)
                
                # Missing keywords
                st.subheader("Missing Keywords")
                missing_keywords = response_json.get("MissingKeywords", [])
                if missing_keywords:
                    st.write(", ".join(missing_keywords))
                else:
                    st.write("No critical missing keywords found!")
                
                # Profile summary
                st.subheader("Profile Summary")
                st.write(response_json.get("Profile Summary", "No summary available"))
                
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            
        finally:
            st.session_state.processing = False

    # Generate Cover Letter
    if st.button("Generate Cover Letter", disabled=st.session_state.processing):
        if not company_name or not job_title:
            st.warning("Please provide company name and job title for the cover letter.")
            return
        
        st.session_state.processing = True
        
        try:
            with st.spinner("📝 Generating cover letter..."):
                # Prepare the prompt for cover letter generation
                cover_letter_prompt = f"""
                Act as an expert cover letter writer. Write a personalized cover letter for the following job application:

                Job Title: {job_title}
                Company: {company_name}
                Personal Message: {personal_message}

                Resume:
                {resume_text}

                Job Description:
                {jd}

                Provide a professional and persuasive cover letter.
                """
                
                # Generate the cover letter using Gemini
                cover_letter = get_gemini_response(cover_letter_prompt)
                
                # Display the cover letter
                st.subheader("Generated Cover Letter")
                st.write(cover_letter)
                
                # Allow user to download the cover letter
                st.download_button(
                    label="Download Cover Letter",
                    data=cover_letter,
                    file_name="cover_letter.txt",
                    mime="text/plain"
                )
                
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
        
        finally:
            st.session_state.processing = False

if __name__ == "__main__":
    main()
