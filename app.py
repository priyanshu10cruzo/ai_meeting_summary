import streamlit as st
import datetime
from audio_processor import AudioProcessor
from rag_system import RAGSystem
from llm_handler import LLMHandler
from utils import *
from config import Config

# Page configuration
st.set_page_config(
    page_title="AI Meeting Summarizer",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #28a745;
    }
</style>
""", unsafe_allow_html=True)

def initialize_components():
    """Initialize all system components"""
    if 'audio_processor' not in st.session_state:
        st.session_state.audio_processor = AudioProcessor()
    
    if 'rag_system' not in st.session_state:
        st.session_state.rag_system = RAGSystem()
    
    if 'llm_handler' not in st.session_state:
        st.session_state.llm_handler = LLMHandler()

def main():
    # Initialize components
    initialize_components()
    
    # Main header
    st.markdown('<h1 class="main-header">🎤 AI Meeting Summarizer</h1>', unsafe_allow_html=True)
    st.markdown("Transform your meeting recordings into actionable insights with AI-powered summarization")
    
    # Sidebar
    with st.sidebar:
        st.header("📋 How it works")
        st.markdown("""
        1. **Upload** your meeting audio file
        2. **Transcribe** using AssemblyAI
        3. **Process** with RAG and vector storage
        4. **Analyze** using Llama2 AI
        5. **Generate** structured summary and insights
        """)
        
        st.header("⚙️ System Status")
        
        # Check system components
        with st.spinner("Checking system components..."):
            # Check Ollama model
            model_available = st.session_state.llm_handler.check_model_availability()
            
            if model_available:
                st.success("✅ Ollama Model Ready")
            else:
                st.error("❌ Ollama Model Not Available")
            
            # Check AssemblyAI
            if Config.ASSEMBLY_AI_API_KEY and Config.ASSEMBLY_AI_API_KEY != "your_assembly_ai_key_here":
                st.success("✅ AssemblyAI Configured")
            else:
                st.error("❌ AssemblyAI API Key Missing")
        
        st.header("📊 Supported Formats")
        st.write(", ".join(Config.SUPPORTED_FORMATS))
        st.write(f"Max file size: {Config.MAX_AUDIO_SIZE_MB}MB")
        st.header("🐛 Debug Options")
        debug_mode = st.checkbox("Enable Debug Mode", help="Shows detailed logs and test responses")
        st.session_state['debug_mode'] = debug_mode
    
        if debug_mode:
          st.warning("Debug mode enabled - check console for detailed logs")
    
    # Main content area
    tab1, tab2, tab3 = st.tabs(["🔄 Process Meeting", "📚 Meeting History", "⚙️ Settings"])
    
    with tab1:
        st.markdown('<div class="section-header"><h2>Upload and Process Meeting Recording</h2></div>', unsafe_allow_html=True)
        
        # File upload
        uploaded_file = st.file_uploader(
            "Choose an audio file",
            type=['mp3', 'wav', 'm4a', 'mp4', 'webm'],
            help=f"Supported formats: {', '.join(Config.SUPPORTED_FORMATS)}. Max size: {Config.MAX_AUDIO_SIZE_MB}MB"
        )
        
        if uploaded_file is not None:
            # Display file info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"**File:** {uploaded_file.name}")
            with col2:
                st.info(f"**Size:** {format_file_size(uploaded_file.size)}")
            with col3:
                st.info(f"**Type:** {uploaded_file.type}")
            
            # Validate file
            is_valid, message = st.session_state.audio_processor.validate_audio_file(uploaded_file)
            
            if not is_valid:
                st.error(f"❌ {message}")
                return
            
            st.success(f"✅ {message}")
            
            # Process button
            if st.button("🚀 Generate Meeting Summary", type="primary", use_container_width=True):
                process_meeting(uploaded_file)
    
    with tab2:
        st.markdown('<div class="section-header"><h2>Meeting History</h2></div>', unsafe_allow_html=True)
        display_meeting_history()
    
    with tab3:
        st.markdown('<div class="section-header"><h2>System Configuration</h2></div>', unsafe_allow_html=True)
        display_settings()

def process_meeting(uploaded_file):
    """Process the uploaded meeting file"""
    
    # Generate meeting ID
    meeting_id = generate_meeting_id(uploaded_file)
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: Transcribe audio
        status_text.text("Step 1/5: Transcribing audio...")
        progress_bar.progress(20)
        
        transcript, error = st.session_state.audio_processor.transcribe_audio(uploaded_file)
        
        if error:
            st.error(f"Transcription failed: {error}")
            return
        
        if not transcript:
            st.error("No transcript generated")
            return
        
        # Step 2: Process and store in vector database
        status_text.text("Step 2/5: Processing transcript and storing in vector database...")
        progress_bar.progress(40)
        
        success, message = st.session_state.rag_system.process_and_store_transcript(transcript, meeting_id)
        
        if not success:
            st.error(f"Vector storage failed: {message}")
            return
        
        # Step 3: Retrieve context (for RAG)
        status_text.text("Step 3/5: Retrieving relevant context...")
        progress_bar.progress(60)
        
        meeting_context = st.session_state.rag_system.get_meeting_context(meeting_id)
        
        # Step 4: Generate summary
        status_text.text("Step 4/5: Generating AI summary...")
        progress_bar.progress(80)
    
        print(f"🔍 DEBUG: About to call LLM with transcript length: {len(transcript)}")
    
    # Test with simple prompt first
        if st.session_state.get('debug_mode', False):
           st.write("🧪 **Debug Mode**: Testing simple prompt...")
           test_response = st.session_state.llm_handler.test_simple_summary(transcript)
           st.text_area("Test Response", test_response, height=300)
    
        summary_data = st.session_state.llm_handler.generate_meeting_summary(transcript, meeting_context)
    
        print(f"🔍 DEBUG: LLM returned: {type(summary_data)}")
        if summary_data:
           print(f"🔍 DEBUG: Summary keys: {list(summary_data.keys())}")
    
        if not summary_data:
           st.error("Failed to generate summary - check console logs for details")
           return
        
        # Step 5: Save and display results
        status_text.text("Step 5/5: Finalizing results...")
        progress_bar.progress(100)
        
        # Save meeting data
        save_success, save_path = save_meeting_data(meeting_id, transcript, summary_data)
        
        if save_success:
            st.success(f"✅ Meeting processed successfully! Data saved to {save_path}")
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        
        # Display results
        display_results(meeting_id, transcript, summary_data)
        
    except Exception as e:
        st.error(f"An error occurred during processing: {str(e)}")
        progress_bar.empty()
        status_text.empty()

def display_results(meeting_id, transcript, summary_data):
    """Display the processed meeting results"""
    
    st.markdown('<div class="section-header"><h2>📊 Meeting Analysis Results</h2></div>', unsafe_allow_html=True)
    
    # Meeting ID and timestamp
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**Meeting ID:** {meeting_id}")
    with col2:
        st.info(f"**Processed at:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Display structured summary
    if 'error' not in summary_data:
        # Summary
        display_summary_section("Meeting Summary", summary_data.get('summary', ''), "📋")
        
        # Meeting Information
        display_summary_section("Meeting Information", summary_data.get('meeting_info', ''), "📅")
        
        # Main Topics
        display_summary_section("Main Topics Discussed", summary_data.get('topics', ''), "🎯")
        
        # Action Items
        display_summary_section("Action Items & Next Steps", summary_data.get('action_items', ''), "⚡")
        
        # Key Decisions
        display_summary_section("Key Decisions Made", summary_data.get('decisions', ''), "🔑")
        
        # Important Notes
        display_summary_section("Important Notes & Follow-ups", summary_data.get('notes', ''), "📋")
        
    else:
        st.error("Error parsing summary. Raw response:")
        st.text_area("Raw Response", summary_data.get('summary', ''), height=300)
    
    # Transcript section
    with st.expander("📄 View Full Transcript", expanded=False):
        st.text_area("Full Transcript", transcript, height=400)
    
    # Download options
    st.markdown("### 💾 Download Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Download as text
        download_content = create_download_data(meeting_id, transcript, summary_data)
        st.download_button(
            label="📄 Download Summary Report",
            data=download_content,
            file_name=f"{meeting_id}_summary.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    with col2:
        # Download transcript only
        st.download_button(
            label="📝 Download Transcript Only",
            data=transcript,
            file_name=f"{meeting_id}_transcript.txt",
            mime="text/plain",
            use_container_width=True
        )

def display_meeting_history():
    """Display history of processed meetings"""
    data_dir = "meeting_data"
    
    if not os.path.exists(data_dir):
        st.info("No meetings processed yet.")
        return
    
    meeting_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
    
    if not meeting_files:
        st.info("No meetings found in history.")
        return
    
    st.write(f"Found {len(meeting_files)} processed meetings:")
    
    for file in sorted(meeting_files, reverse=True):
        meeting_data = load_meeting_data(file.replace('.json', ''))
        
        if meeting_data:
            with st.expander(f"📋 {meeting_data['meeting_id']} - {meeting_data['timestamp'][:19]}"):
                st.write("**Summary:**")
                st.write(meeting_data['summary'].get('summary', 'Not available')[:200] + "...")
                
                if st.button(f"View Full Report", key=f"view_{file}"):
                    display_results(
                        meeting_data['meeting_id'],
                        meeting_data['transcript'],
                        meeting_data['summary']
                    )

def display_settings():
    """Display system settings and configuration"""
    st.markdown("### 🔧 Current Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Audio Processing:**")
        st.write(f"- Max file size: {Config.MAX_AUDIO_SIZE_MB}MB")
        st.write(f"- Supported formats: {', '.join(Config.SUPPORTED_FORMATS)}")
        
        st.markdown("**Text Processing:**")
        st.write(f"- Chunk size: {Config.CHUNK_SIZE}")
        st.write(f"- Chunk overlap: {Config.CHUNK_OVERLAP}")
    
    with col2:
        st.markdown("**AI Models:**")
        st.write(f"- LLM Model: {Config.OLLAMA_MODEL}")
        st.write(f"- Embedding Model: {Config.EMBEDDING_MODEL}")
        st.write(f"- Temperature: {Config.TEMPERATURE}")
        st.write(f"- Max tokens: {Config.MAX_TOKENS}")
    
    st.markdown("### 🔑 API Configuration")
    
    # AssemblyAI API Key
    api_key = st.text_input(
        "AssemblyAI API Key",
        value="*" * len(Config.ASSEMBLY_AI_API_KEY) if Config.ASSEMBLY_AI_API_KEY != "your_assembly_ai_key_here" else "",
        type="password",
        help="Enter your AssemblyAI API key"
    )
    
    if st.button("Test API Connection"):
        if api_key and api_key != "*" * len(Config.ASSEMBLY_AI_API_KEY):
            st.info("API key updated! Please restart the application.")
        else:
            st.warning("Please enter a valid API key.")
    
    st.markdown("### 📊 System Information")
    st.write(f"- Vector DB Path: {Config.VECTOR_DB_PATH}")
    st.write(f"- Collection Name: {Config.COLLECTION_NAME}")
    st.write(f"- Ollama Base URL: {Config.OLLAMA_BASE_URL}")

if __name__ == "__main__":
    main()
