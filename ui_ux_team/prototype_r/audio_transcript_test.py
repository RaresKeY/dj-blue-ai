import google.generativeai as genai
import time
import os
import settings

# 1. Setup your API Key
genai.configure(api_key=os.getenv("AI_STUDIO"))
for model in genai.list_models():
    # Only show models that can generate content
    if 'generateContent' in model.supported_generation_methods:
        print(f"Name: {model.name}")
        print(f"Display Name: {model.display_name}")
        print(f"Description: {model.description}")
        print("-" * 50)

def test_audio_to_text(file_path):
    # 2. Upload the audio file to Google's servers
    print(f"Uploading file: {file_path}...")
    audio_file = genai.upload_file(path=file_path)

    # 3. Wait for the file to be processed (crucial for audio)
    while audio_file.state.name == "PROCESSING":
        print(".", end="", flush=True)
        time.sleep(2)
        audio_file = genai.get_file(audio_file.name)

    if audio_file.state.name == "FAILED":
        raise ValueError("Audio processing failed.")

    print("\nFile processed. Sending to model...")

    # 4. Initialize the model 
    # (Using the 2.5 Flash string you provided)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash-native-audio-dialog")

    # 5. Generate Text from Audio
    # You can ask it to transcribe, summarize, or answer questions about the audio
    prompt = "Please provide a detailed text transcription of this audio and summarize the main points."
    
    response = model.generate_content([prompt, audio_file])

    # 6. Output the text result
    print("-" * 30)
    print("MODEL TEXT RESPONSE:")
    print(response.text)
    print("-" * 30)

# Run the test
if __name__ == "__main__":
    # Replace with your actual audio file path
    test_audio_to_text("ui_ux_team/prototype_r/chunk_combined_stereo.wav")