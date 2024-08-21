from transformers import BlenderbotTokenizer, BlenderbotForConditionalGeneration
from transformers import pipeline
import soundfile as sf
from pydub import AudioSegment
import os
from transformers.utils import logging
logging.set_verbosity_error()
import torch


# Initialize the tokenizer and model
tokenizer = BlenderbotTokenizer.from_pretrained("facebook/blenderbot-400M-distill")
model = BlenderbotForConditionalGeneration.from_pretrained("facebook/blenderbot-400M-distill")

# automatic-speech-recognition model
# ASR = pipeline(task="automatic-speech-recognition",
#                    model="distil-whisper/distil-small.en")

ASR = pipeline("automatic-speech-recognition", model="openai/whisper-small")
text_to_audio_module = pipeline("text-to-speech",
                    model="kakao-enterprise/vits-ljs")

def custom_module_chatBot(user_message):
    input_ids = tokenizer.encode(user_message, return_tensors='pt')

    # Truncate the input_ids to the maximum positional embedding size
    max_length = model.config.max_position_embeddings
    input_ids = input_ids[:, :max_length]

    # Generate attention mask
    attention_mask = torch.ones_like(input_ids)
    # Forward pass through the model with attention mask
    outputs = model.generate(input_ids=input_ids, attention_mask=attention_mask, max_new_tokens=256)

    # Decode the generated response
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response

def speech_recognition(filepath):
    if not filepath or not os.path.exists(filepath):
        return "No audio found or file does not exist."

    output = ASR(filepath)
    return output["text"]


def text_to_audio(text, filename):
    narrated_text = text_to_audio_module(text)

    file_location = os.path.join("/home/dhanesh/savi_month_one/ChatBot/audio_file/", filename)
    # Save the audio to a WAV file
    wav_file_path = "output.wav"
    sf.write(file_location, narrated_text["audio"][0], narrated_text["sampling_rate"], format='WAV')

    # Convert the WAV file to MP3 using pydub
    audio = AudioSegment.from_wav(file_location)
    file_location = file_location.replace(".wav",".mp3")
    print("new file name: ",file_location)
    audio.export(file_location, format="mp3")

    return "/audio_file/"+filename.replace(".wav",".mp3")

