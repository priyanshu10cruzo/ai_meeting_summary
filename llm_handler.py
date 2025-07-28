import ollama
from config import Config
import streamlit as st
import re

class LLMHandler:
    def __init__(self):
        self.client = ollama.Client(host=Config.OLLAMA_BASE_URL)
        self.model = Config.OLLAMA_MODEL
    
    def check_model_availability(self):
        """Check if the required model is available"""
        try:
            models = self.client.list()['models']
            available_models = [model['name'] for model in models]
            
            if self.model not in available_models:
                st.error(f"Model '{self.model}' not found. Available models: {available_models}")
                st.info(f"Please run: `ollama pull {self.model}` to download the model")
                return False
            return True
        except Exception as e:
            st.error(f"Error checking model availability: {str(e)}")
            return False

    def test_simple_summary(self, transcript):
      """Test with simplified prompt"""
      prompt = self._create_simple_test_prompt(transcript)
    
      try:
        response = self.client.generate(
            model=self.model,
            prompt=prompt,
            options={'temperature': 0.1, 'num_predict': 500}
        )
        
        print("🧪 TEST RESPONSE:")
        print(response['response'])
        return response['response']
        
      except Exception as e:
        print(f"❌ TEST ERROR: {str(e)}")
        return None

    def _create_simple_test_prompt(self, transcript):
     """Create a simplified prompt for testing"""
     return f"""[INST] You are a meeting summarizer. Analyze this transcript and provide:

## MEETING SUMMARY
[Write a 2-3 sentence summary of the main discussion]

## KEY POINTS
[List 2-3 main topics discussed]

## ACTION ITEMS
[List any tasks or follow-ups mentioned]

TRANSCRIPT:
{transcript[:1000]}  # Limit to first 1000 chars for testing

Respond in exactly the format shown above. [/INST]"""
    
    def generate_meeting_summary(self, transcript, meeting_context=""):
        """Generate comprehensive meeting summary using Llama2"""
        
        # Combine transcript with any additional context from RAG
        full_context = transcript
        if meeting_context:
            full_context += f"\n\nAdditional Context:\n{meeting_context}"
        
        prompt = self._create_summary_prompt(full_context)
        
        try:
            with st.spinner("Generating comprehensive meeting summary..."):
                response = self.client.generate(
                    model=self.model,
                    prompt=prompt,
                    options={
                        'temperature': Config.TEMPERATURE,
                        'num_predict': Config.MAX_TOKENS,
                        'top_k': 40,
                        'top_p': 0.9,
                        'stop': ['[INST]', '</s>']
                    }
                )
            
            return self._parse_summary_response(response['response'])
            
        except Exception as e:
            st.error(f"Error generating summary: {str(e)}")
            return None
    
    def _create_summary_prompt(self, transcript):
        """Create the optimized prompt for Llama2"""
        return f"""[INST] <<SYS>>
You are an expert meeting analyst specializing in comprehensive meeting summarization and key information extraction. Your task is to analyze meeting transcripts and provide structured, actionable insights.

Always follow this exact output format:

## MEETING SUMMARY
[Provide a comprehensive summary in 250-300 words covering the main discussion points, decisions made, and overall meeting flow]

## KEY DETAILS EXTRACTED
### 📅 Meeting Information
- **Date**: [Extract or indicate if not mentioned]
- **Duration**: [Extract or indicate if not mentioned]  
- **Participants**: [List participants mentioned]

### 🎯 Main Topics Discussed
- [Topic 1 with brief description]
- [Topic 2 with brief description]
- [Continue as needed]

### ⚡ Action Items & Next Steps
- [Action item 1] - Assigned to: [Person] - Due: [Date if mentioned]
- [Action item 2] - Assigned to: [Person] - Due: [Date if mentioned]
- [Continue as needed]

### 🔑 Key Decisions Made
- [Decision 1 with context]
- [Decision 2 with context]
- [Continue as needed]

### 📋 Important Notes & Follow-ups
- [Important point 1]
- [Important point 2]
- [Continue as needed]

Only extract information that is explicitly mentioned in the transcript. If information is not available, indicate "Not specified in transcript".
<</SYS>>

Analyze the following meeting transcript and provide a structured summary with extracted key details:

TRANSCRIPT:
{transcript}

Please provide the analysis following the exact format specified above. [/INST]"""
    
    def _parse_summary_response(self, response):
     """Parse the LLM response into structured components with better error handling"""
     try:
         sections = {}
        
        # Clean the response
         response = response.strip()
        
        # Debug: Print response structure
         print(f"🔍 DEBUG: Response has {len(response)} characters")
         print(f"🔍 DEBUG: Looking for section markers...")
        
        # More flexible regex patterns (case insensitive, flexible spacing)
         patterns = {
            'summary': [
                r'## MEETING SUMMARY\s*(.*?)(?=##|###|$)',
                r'##\s*MEETING\s*SUMMARY\s*(.*?)(?=##|###|$)',
                r'MEETING SUMMARY[:\s]*(.*?)(?=MEETING INFORMATION|KEY DETAILS|$)'
            ],
            'meeting_info': [
                r'### 📅 Meeting Information\s*(.*?)(?=###|$)',
                r'###\s*📅\s*Meeting Information\s*(.*?)(?=###|$)',
                r'MEETING INFORMATION[:\s]*(.*?)(?=MAIN TOPICS|$)'
            ],
            'topics': [
                r'### 🎯 Main Topics Discussed\s*(.*?)(?=###|$)',
                r'###\s*🎯\s*Main Topics Discussed\s*(.*?)(?=###|$)',
                r'MAIN TOPICS DISCUSSED[:\s]*(.*?)(?=ACTION ITEMS|$)'
            ],
            'action_items': [
                r'### ⚡ Action Items & Next Steps\s*(.*?)(?=###|$)',
                r'###\s*⚡\s*Action Items & Next Steps\s*(.*?)(?=###|$)',
                r'ACTION ITEMS[:\s]*(.*?)(?=KEY DECISIONS|$)'
            ],
            'decisions': [
                r'### 🔑 Key Decisions Made\s*(.*?)(?=###|$)',
                r'###\s*🔑\s*Key Decisions Made\s*(.*?)(?=###|$)',
                r'KEY DECISIONS[:\s]*(.*?)(?=IMPORTANT NOTES|$)'
            ],
            'notes': [
                r'### 📋 Important Notes & Follow-ups\s*(.*?)(?=###|$)',
                r'###\s*📋\s*Important Notes & Follow-ups\s*(.*?)(?=###|$)',
                r'IMPORTANT NOTES[:\s]*(.*?)$'
            ]
        }
        
        # Try multiple patterns for each section
         for section_name, pattern_list in patterns.items():
            content = None
            for pattern in pattern_list:
                match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
                if match:
                    content = match.group(1).strip()
                    print(f"🔍 DEBUG: Found {section_name} using pattern {pattern[:30]}...")
                    break
            
            if content and content.strip():
                sections[section_name] = content
            else:
                sections[section_name] = f"{section_name.replace('_', ' ').title()} not available"
                print(f"⚠️  DEBUG: No content found for {section_name}")
        
        # If no sections found at all, return the raw response
         if all(val.endswith("not available") for val in sections.values()):
            print("❌ DEBUG: No sections parsed successfully, returning raw response")
            sections['summary'] = response
            sections['error'] = "Failed to parse structured response - showing raw output"
         return sections
        
     except Exception as e:
        print(f"❌ DEBUG: Error parsing response: {str(e)}")
        return {
            "summary": response if response else "No response received", 
            "error": f"Failed to parse structured response: {str(e)}"
        }


# Add a test method
    def test_simple_summary(self, transcript):
     """Test with simplified prompt"""
     prompt = self._create_simple_test_prompt(transcript)
    
     try:
        response = self.client.generate(
            model=self.model,
            prompt=prompt,
            options={'temperature': 0.1, 'num_predict': 500}
        )
        
        print("🧪 TEST RESPONSE:")
        print(response['response'])
        return response['response']
        
     except Exception as e:
        print(f"❌ TEST ERROR: {str(e)}")
        return None


