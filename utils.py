import streamlit as st
import hashlib
import datetime
import json
import os

def generate_meeting_id(audio_file):
    """Generate unique meeting ID based on file content and timestamp"""
    file_hash = hashlib.md5(audio_file.getvalue()).hexdigest()[:8]
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"meeting_{timestamp}_{file_hash}"

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0B"
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f} {size_names[i]}"

def save_meeting_data(meeting_id, transcript, summary_data):
    """Save meeting data for future reference"""
    try:
        data_dir = "meeting_data"
        os.makedirs(data_dir, exist_ok=True)
        
        meeting_data = {
            "meeting_id": meeting_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "transcript": transcript,
            "summary": summary_data
        }
        
        file_path = os.path.join(data_dir, f"{meeting_id}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(meeting_data, f, ensure_ascii=False, indent=2)
        
        return True, file_path
    except Exception as e:
        return False, str(e)

def load_meeting_data(meeting_id):
    """Load saved meeting data"""
    try:
        file_path = os.path.join("meeting_data", f"{meeting_id}.json")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Error loading meeting data: {str(e)}")
    return None

def display_summary_section(title, content, icon="📋"):
    """Display a formatted summary section"""
    st.markdown(f"### {icon} {title}")
    if content and content.strip():
        st.markdown(content)
    else:
        st.info("No information available for this section.")
    st.markdown("---")

def create_download_data(meeting_id, transcript, summary_data):
    """Create downloadable data in multiple formats"""
    # Text format
    text_content = f"""MEETING SUMMARY REPORT
Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Meeting ID: {meeting_id}

{'='*50}
MEETING SUMMARY
{'='*50}
{summary_data.get('summary', 'Not available')}

{'='*50}
MEETING INFORMATION
{'='*50}
{summary_data.get('meeting_info', 'Not available')}

{'='*50}
MAIN TOPICS DISCUSSED
{'='*50}
{summary_data.get('topics', 'Not available')}

{'='*50}
ACTION ITEMS & NEXT STEPS
{'='*50}
{summary_data.get('action_items', 'Not available')}

{'='*50}
KEY DECISIONS MADE
{'='*50}
{summary_data.get('decisions', 'Not available')}

{'='*50}
IMPORTANT NOTES & FOLLOW-UPS
{'='*50}
{summary_data.get('notes', 'Not available')}

{'='*50}
FULL TRANSCRIPT
{'='*50}
{transcript}
"""
    
    return text_content
