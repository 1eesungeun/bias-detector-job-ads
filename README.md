# Bias Detector for Job Ads

A lightweight Streamlit web app that helps users identify biased language in job advertisements. It combines a transparent rule-based detector with Google Gemini explanations to make AI bias visible and understandable.

**Main Features**  
- Rule-based scanning for categories like age, gender, and language bias.  
- Gemini-powered contextual explanations and inclusive rewrite suggestions.  
- Simple two-column interface with Quick Highlights and Explanations tabs.  
- Educational focus on fairness, awareness, and responsible AI use.

**Run the App**  
1. Get a Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey).  
2. Add it to a `.env` file:  
   `GOOGLE_API_KEY=your_own_api_key_here`  
3. Run locally:  
   `python -m streamlit run app.py`

**Repository**  
https://github.com/1eesungeun/bias-detector-job-ads
