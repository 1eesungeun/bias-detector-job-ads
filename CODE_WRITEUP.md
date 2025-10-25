Code Title: Bias Detector for Job Ads  
Student Name: Sungeun Lee
Date: 25 October 2025
Repository Link:

1. Code Overview
The Bias Detector for Job Ads is a Python web prototype built with Streamlit. It helps users identify and understand biased language in job advertisements. The app combines a local rule-based highlighter with an AI-driven Gemini explainer that provides short rationales and inclusive rewrites.

2. Main Features & Structure
• app.py – main controller; handles layout, routing, text input, bias detection, and Gemini API calls; renders results.
• prompts.py – defines the system prompt, tone examples, and payload builder that structure how user text and metadata are sent to Gemini for bias analysis and explanations.
• intro.py – defines the left-column content for the Check page, including the introductory text and usage instructions.
• about.py – defines the content for the About page, including an overview of the tool’s purpose, bias categories, target users, privacy explanation, and limitations.
• nav.py – defines the top navigation bar for page switching.
• footer.py – displays the educational disclaimer shown on all pages.

3. Core Logic
The system uses a hybrid detection process that combines a simple rule-based lexicon with AI-powered contextual explanations.
1)	Rule-based layer (local)
The code scans input text using regular expressions and a small lexicon of bias categories—age, gender, language or ESL, culture fit, nationality or visa and appearance. Each category includes common examples such as “young,” “salesman,” or “native English speaker.” Matches appear instantly in the Quick Highlights tab with colour-coded labels. This step runs locally for transparency and data privacy.
2)	Gemini reasoning layer (API-driven)
After local highlighting, the matched sentences are sent to Google Gemini for contextual interpretation. The model analyses the sentence, explains why a term may be exclusionary and suggests a more inclusive rewrite. For example, “young, well-presented salesman” becomes “professional and articulate Sales Executive”.
This workflow turns a static detector into an interactive, educational tool that encourages users to think critically about language.

4. Sample Usage
Setup:
   1. Obtain a Google Gemini API key from https://aistudio.google.com/app/apikey.
   2. Create a `.env` file in the project root and add your key:
      GOOGLE_API_KEY=your_own_api_key_here
   3. Run the application locally using the command:
      python -m streamlit run app.py

Step 1: Try the Example
   1.Click Insert Example Text to load a sample job ad.
   2.Click Analyze to see how the tool highlights potential bias.

Step 2: Explore the Results
   1.Review the Quick Highlights tab — note the colour-coded categories.
   2.Switch to Contextual Explanations to read why certain phrases might be risky and view rewrite suggestions.

Step 3: Try Your Own
   1.Delete the sample and paste a short job ad or sentence of your own.
   2.Click Analyze again and explore the explanations. 

5. Challenges and Solutions
The main challenge during development was realising that a purely rule-based system could never capture every possible form of biased language. Manually listing biased words was not practical because bias depends on culture, phrasing and context. This problem was solved by integrating Google Gemini to complement the rule-based layer. Gemini adds contextual reasoning and inclusive rewrites, making detection more flexible while maintaining transparency and human control.

6. Reflection and Improvements
While the hybrid design improved flexibility and transparency, I realised the system still has limitations. The rule-based component depends on a small set of predefined phrases and regular expressions, which means it can miss subtle or emerging expressions. The Gemini model also relies on an external API and may reproduce bias from its own training data. In addition, response time varies with network performance and the system currently works best with short text snippets, as longer inputs can exceed processing capacity.

Looking ahead, future iterations will focus on scalability by expanding the lexicon in collaboration with linguists and HR specialists, exploring open-source language models for greater transparency and integrating interactive educational modules that explain the social context behind biased terms. These improvements would make the tool more reliable, explainable and socially meaningful.

Through developing this system, I learned that fairness in AI is a continuous process of communication and reflection. It is not a problem that can be solved once and it requires ongoing attention, humility and awareness to ensure technology remains fair, inclusive and trustworthy.





