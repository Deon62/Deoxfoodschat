from django.shortcuts import render
from django.http import JsonResponse
import google.generativeai as genai
import speech_recognition as sr
from elevenlabs import Voice, VoiceSettings, generate, set_api_key
from io import BytesIO
import base64
import os
import tempfile
from pydub import AudioSegment
import tempfile
import os

custom_temp_dir = "C:/custom_temp"
os.makedirs(custom_temp_dir, exist_ok=True)
tempfile.tempdir = custom_temp_dir



from .config import GEMINI_API_KEY, ELEVEN_API_KEY

# Initialize APIs
genai.configure(api_key=GEMINI_API_KEY)
set_api_key(ELEVEN_API_KEY)

# Initialize speech recognition
recognizer = sr.Recognizer()

# Configure Gemini model
generation_config = {
    "temperature": 0,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
}

system_instruction ="""You are DeoxBot, a humorous  food delivery assistant for DeoxFoods at Egerton University, Kenya.

Personality: Friendly, witty, wit high sense of humour and knowledgeable about Kenyan and international cuisines.
Response Style: Provide plain text responses with no markdown, asterisks, or special characters.
Core Capabilities:

Food Recommendations:
Suggest meals based on time, weather, and occasions.
Recommend student-friendly and budget-friendly options.
Pair local dishes with drinks.
Health Guidance:
Offer dietary options (vegetarian, calories levels track in food,vegan, fitness-focused).
Suggest balanced, nutritious meals.
Guidelines:

Keep it conversational and natural in tone.
Consider dietary restrictions.
Share cooking tips and food facts when relevant"""

roast_instruction = """"You are DeoxBot in ROAST MODE – the savage yet helpful food delivery assistant. Your personality:

Brutally honest, delivering witty comebacks with Kenyan slang and humor.
Always provides accurate food delivery information but wrapped in sharp, sarcastic commentary.
Roasts basic or boring food choices while suggesting better alternatives.
Playfully mocks indecision and unadventurous taste buds.
Keeps roasts food-related, light-hearted, and entertaining—never cruel or offensive."""

kiswahili_instruction = """Wewe ni DeoxBot, msaidizi wa kufurahisha wa huduma ya kusambaza chakula kwa DeoxFoods katika Chuo Kikuu cha Egerton, Kenya.

Tabia: Rafiki, mwenye utani, na mwenye ujuzi wa vyakula vya Kenya na kimataifa.

"""


current_model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
    system_instruction=system_instruction
)

def chat_view(request):
    return render(request, 'chat/chat.html')

def clean_response(text):
    # Remove markdown formatting
    text = text.replace('*', '')
    text = text.replace('**', '')
    text = text.replace('_', '')
    return text

import os
from django.conf import settings
import soundfile as sf
from pydub import AudioSegment

# Create a media directory for audio files
AUDIO_DIR = os.path.join(settings.BASE_DIR, 'media', 'audio')
os.makedirs(AUDIO_DIR, exist_ok=True)

from io import BytesIO

TEMP_AUDIO_DIR = os.path.join(settings.BASE_DIR, 'temp_audio')
os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)

def process_voice(request):
    if request.method == 'POST':
        try:
            audio_data = request.FILES.get('audio')
            if not audio_data:
                return JsonResponse({'error': 'No audio data received'})

            # Save audio file to TEMP_AUDIO_DIR
            temp_file_path = os.path.join(TEMP_AUDIO_DIR, 'temp_audio.webm')
            with open(temp_file_path, 'wb') as f:
                for chunk in audio_data.chunks():
                    f.write(chunk)

            # Convert the saved file to WAV
            audio = AudioSegment.from_file(temp_file_path, format="webm")
            wav_file_path = os.path.join(TEMP_AUDIO_DIR, 'temp_audio.wav')
            audio.export(wav_file_path, format="wav")

            # Transcribe the WAV file
            with sr.AudioFile(wav_file_path) as source:
                audio_recording = recognizer.record(source)
                transcribed_text = recognizer.recognize_google(audio_recording)

            # Process bot response
            bot_text = get_bot_response_text(transcribed_text)

            # Cleanup temp files
            os.remove(temp_file_path)
            os.remove(wav_file_path)

            return JsonResponse({
                'text': transcribed_text,
                'bot_response': bot_text,
                'status': 'success'
            })

        except sr.UnknownValueError:
            return JsonResponse({'error': 'Could not understand audio'})
        except Exception as e:
            return JsonResponse({'error': f'Processing error: {str(e)}'})

    return JsonResponse({'error': 'Invalid request method'})


def get_bot_response_text(text, instruction):
    try:
        # Initialize the model with the instruction
        current_model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=generation_config,
            system_instruction=instruction
        )

        # Generate content
        raw_response = current_model.generate_content(text).text
        return clean_response(raw_response)
    except Exception as e:
        # Log the error and provide a default error response
        print(f"Error in get_bot_response_text: {e}")
        return "I'm sorry, I couldn't generate a response due to an error."

def get_bot_response(request):
    if request.method == 'POST':
        user_input = request.POST.get('message', '').strip()
        
        # Check if input is empty
        if not user_input:
            return JsonResponse({'text': 'I did not receive any input. Please try again.'})
        
        mode = request.POST.get('mode', 'normal')
        
        # Handle modes (normal, roast, Kiswahili, etc.)
        if mode == 'roast':
            instruction = roast_instruction
        elif mode == 'kiswahili':
            instruction = kiswahili_instruction
        else:
            instruction = system_instruction

        try:
            # Call the helper function to get the bot's response
            response = get_bot_response_text(user_input, instruction)
            return JsonResponse({'text': response})
        except Exception as e:
            # Catch any unexpected errors
            print(f"Error in get_bot_response: {e}")
            return JsonResponse({'text': 'An unexpected error occurred. Please try again later.'})

    # Handle non-POST requests
    return JsonResponse({'error': 'Invalid request method'}, status=405)




