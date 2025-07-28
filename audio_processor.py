import assemblyai as aai
import streamlit as st
from config import Config
import tempfile
import os

class AudioProcessor:
    def __init__(self):
        aai.settings.api_key = Config.ASSEMBLY_AI_API_KEY
        
    def validate_audio_file(self, audio_file):
        """Validate uploaded audio file"""
        if audio_file is None:
            return False, "No file uploaded"
        
        # Check file size
        if audio_file.size > Config.MAX_AUDIO_SIZE_MB * 1024 * 1024:
            return False, f"File size exceeds {Config.MAX_AUDIO_SIZE_MB}MB limit"
        
        # Check file format
        file_extension = os.path.splitext(audio_file.name)[1].lower()
        if file_extension not in Config.SUPPORTED_FORMATS:
            return False, f"Unsupported format. Supported: {', '.join(Config.SUPPORTED_FORMATS)}"
        
        return True, "Valid file"
    
    def transcribe_audio(self, audio_file):
        """Transcribe audio using AssemblyAI"""
        try:
            # Save uploaded file to temporary location
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio_file.name)[1]) as tmp_file:
                tmp_file.write(audio_file.getvalue())
                tmp_file_path = tmp_file.name
            
            # Configure transcription settings
            config = aai.TranscriptionConfig(
                speaker_labels=True
            )
            
            # Create transcriber and transcribe
            transcriber = aai.Transcriber(config=config)
            
            with st.spinner("Transcribing audio... This may take a few minutes."):
                transcript = transcriber.transcribe(tmp_file_path)
            
            # Clean up temporary file
            os.unlink(tmp_file_path)
            
            if transcript.status == aai.TranscriptStatus.error:
                return None, f"Transcription failed: {transcript.error}"
            
            # Format transcript with speaker labels if available
            formatted_transcript = self._format_transcript(transcript)
            
            return formatted_transcript, None
            
        except Exception as e:
            return None, f"Error during transcription: {str(e)}"
    
    def _format_transcript(self, transcript):
        """Format transcript with speaker labels"""
        if hasattr(transcript, 'utterances') and transcript.utterances:
            # Format with speaker labels
            formatted_text = ""
            for utterance in transcript.utterances:
                speaker = f"Speaker {utterance.speaker}" if utterance.speaker else "Speaker"
                formatted_text += f"\n{speaker}: {utterance.text}\n"
            return formatted_text.strip()
        else:
            # Fallback to regular transcript
            return transcript.text
