import speech_recognition as sr
import pyttsx3
import datetime
import wikipedia
import pywhatkit
import os
import json
import requests
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import screen_brightness_control as sbc
import re
import openai

engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)
engine.setProperty('rate', 150)

def speak(text):
    """Converts text to speech using pyttsx3."""
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"Error in speak function: {e}")
        # Fallback to a simpler print statement if TTS fails
        print(text)

def wish_user():
    hour = datetime.datetime.now().hour
    if hour < 12:
        speak("Good morning, sir.")
    elif hour < 18:
        speak("Good afternoon, sir.")
    else:
        speak("Good evening, sir.")
    speak("I am JARVIS. How can I help you today?")

def take_command():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.pause_threshold = 1
        try:
            audio = r.listen(source, timeout=3, phrase_time_limit=5)
        except sr.WaitTimeoutError:
            speak("I didn't hear anything. Please try again.")
            return ""
    try:
        print("Recognizing...")
        query = r.recognize_google(audio)
        print(f"You said: {query}")
    except Exception:
        speak("Sorry, I did not catch that. Please say again.")
        return ""
    return query.lower()

DATA_FILE = "user_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)

def get_weather(city):
    api_key = "ea0623778e69c7768edac859f45ce83c"  # Replace with your API key
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if data["cod"] != 200:
            return "Sorry, I couldn't find the weather for that location."
        weather = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        return f"The weather in {city} is {weather} with a temperature of {temp}°C."
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        return "Sorry, I couldn't get the weather information right now."
    except Exception as err:
        print(f"Other error occurred: {err}")
        return "Sorry, I couldn't get the weather information right now."

def get_latest_news(topic):
    api_key = "dd42e4c7c9c549f3a905933b0c0e84b6"  # Replace with your API key
    url = f"https://newsapi.org/v2/everything?q={topic}&sortBy=popularity&apiKey={api_key}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        articles = response.json().get("articles", [])
        if not articles:
            return f"Sorry, I couldn't find any news about {topic}."
        headlines = [article["title"] for article in articles[:5]]
        return f"Here are the latest headlines for {topic}: " + "; ".join(headlines)
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        return "Sorry, I couldn't get the news right now."
    except Exception as err:
        print(f"Other error occurred: {err}")
        return "Sorry, I couldn't get the news right now."

def set_volume(level):
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    # Set volume level (0.0 to 1.0)
    volume.SetMasterVolumeLevelScalar(level / 100, None)

def get_volume():
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    return volume.GetMasterVolumeLevelScalar() * 100

def set_brightness(level):
    sbc.set_brightness(level)

def get_brightness():
    try:
        return sbc.get_brightness()[0]
    except IndexError:
        return 50

OPENAI_API_KEY = "sk-c552bfd8d54c4c4e984d52775533a4cf"

def ask_openai(question):
    if not OPENAI_API_KEY:
        return "OpenAI API key is not set. Please set the OPENAI_API_KEY environment variable."
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": question}
            ],
            max_tokens=200,
            temperature=0.7,
        )
        answer = response.choices[0].message.content.strip()
        return answer
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return "Sorry, I couldn't get an answer from OpenAI."

DEEPSEEK_API_KEY = "sk-c552bfd8d54c4c4e984d52775533a4cf"  # Replace with your DeepSeek API key

def ask_deepseek(question):
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",  # Use the correct model name for DeepSeek
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": question}
        ],
        "max_tokens": 200,
        "temperature": 0.7
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        answer = data["choices"][0]["message"]["content"].strip()
        return answer
    except Exception as e:
        print(f"DeepSeek API error: {e}")
        return "Sorry, I couldn't get an answer from DeepSeek."

def run_jarvis():
    wish_user()
    user_data = load_data()
    while True:
        query = take_command()
        if not query:
            continue

        # Custom Replies first
        custom_replies = {
            "your name": "My name is JARVIS.",
            "my name": "Your name is Raaniit.",
            "who are you": "I am your Python voice assistant.",
            "who created you": "I was created by you.",
            "how are you": "I'm doing well, thanks for asking.",
            "what is my mother name": "your mother name is Tanushree"
        }
        
        is_custom_reply = False
        for key, value in custom_replies.items():
            if key in query:
                speak(value)
                is_custom_reply = True
                break
        if is_custom_reply:
            continue

        # Main command processing logic
        if query.startswith("remember"):
            try:
                parts = query.replace("remember", "", 1).strip().split(" is ")
                if len(parts) == 2:
                    key = parts[0].strip().replace("my ", "").strip().lower()
                    value = parts[1].strip()
                    user_data[key] = value
                    save_data(user_data)
                    speak(f"I will remember your {key}.")
                else:
                    speak("Sorry, I could not remember that. Please use the format 'remember [key] is [value]'.")
            except Exception:
                speak("Sorry, I could not remember that.")
            continue

        elif query.startswith("what is my") or query.startswith("what's my"):
            key = query.replace("what is my", "", 1).replace("what's my", "", 1).strip()
            key = key.replace("my ", "").strip().lower()
            if key in user_data:
                speak(f"Your {key} is {user_data[key]}")
            else:
                speak(f"I don't know your {key} yet.")
            continue

        elif query.startswith("ask") or query.startswith("jarvis"):
            question = query.replace("ask", "", 1).replace("jarvis", "", 1).strip()
            if question:
                response = ask_deepseek(question)
                speak(response)
            else:
                speak("What would you like to ask?")
            continue

        elif query.startswith('wikipedia'):
            speak("Searching Wikipedia...")
            topic = query.replace("wikipedia", "").strip()
            if topic:
                result = wikipedia.summary(topic, sentences=2)
                speak("According to Wikipedia")
                speak(result)
            else:
                speak("What topic would you like to search on Wikipedia?")
            continue

        elif query.startswith('play'):
            song = query.replace("play", "").strip()
            if song:
                speak(f"Playing {song}")
                pywhatkit.playonyt(song)
            else:
                speak("What song would you like to play?")
            continue

        elif 'time' in query:
            time = datetime.datetime.now().strftime('%I:%M %p')
            speak(f"The time is {time}")
            continue

        elif 'stop' in query or 'exit' in query:
            speak("Goodbye, sir!")
            break

        elif query.startswith('open '):
            open_app(query)
            continue

        elif query.startswith('close '):
            close_app(query)
            continue
        
        elif 'sleep' in query:
            sleep_mode()
            continue
        
        elif "shutdown" in query or "shut down" in query:
            speak("Shutting down the computer.")
            os.system("shutdown /s /t 1")
            return

        elif "restart" in query:
            speak("Restarting the computer.")
            os.system("shutdown /r /t 1")
            return

        elif "volume" in query:
            try:
                numbers = re.findall(r'\d+', query)
                if numbers:
                    level = int(numbers[0])
                    if 0 <= level <= 100:
                        set_volume(level)
                        speak(f"Volume set to {level} percent.")
                    else:
                        speak("Please specify a volume level between 0 and 100.")
                elif "increase" in query or "up" in query:
                    current_volume = get_volume()
                    new_volume = min(current_volume + 20, 100)
                    set_volume(new_volume)
                    speak(f"Volume increased to {int(new_volume)} percent.")
                elif "decrease" in query or "down" in query:
                    current_volume = get_volume()
                    new_volume = max(current_volume - 20, 0)
                    set_volume(new_volume)
                    speak(f"Volume decreased to {int(new_volume)} percent.")
                else:
                    speak("What would you like to do with the volume?")
            except Exception as e:
                print(f"Error in volume control: {e}")
                speak("Sorry, I had trouble adjusting the volume.")
            continue

        elif "brightness" in query:
            try:
                numbers = re.findall(r'\d+', query)
                if numbers:
                    level = int(numbers[0])
                    if 0 <= level <= 100:
                        set_brightness(level)
                        speak(f"Brightness set to {level} percent.")
                    else:
                        speak("Please specify a brightness level between 0 and 100.")
                elif "increase" in query or "up" in query:
                    current_brightness = get_brightness()
                    new_brightness = min(current_brightness + 20, 100)
                    set_brightness(new_brightness)
                    speak(f"Brightness increased to {int(new_brightness)} percent.")
                elif "decrease" in query or "down" in query:
                    current_brightness = get_brightness()
                    new_brightness = max(current_brightness - 20, 0)
                    set_brightness(new_brightness)
                    speak(f"Brightness decreased to {int(new_brightness)} percent.")
                else:
                    speak("What would you like to do with the brightness?")
            except Exception as e:
                print(f"Error in brightness control: {e}")
                speak("Sorry, I had trouble adjusting the brightness.")
            continue

        elif "weather" in query:
            speak("For which city?")
            city = take_command()
            if city:
                weather_info = get_weather(city)
                speak(weather_info)
            continue

        elif "news" in query or "latest news" in query:
            speak("What topic are you interested in?")
            topic = take_command()
            if topic:
                news = get_latest_news(topic)
                speak(news)
            continue

        elif "search" in query or "google" in query:
            speak("What should I search for?")
            search_query = take_command()
            if search_query:
                speak(f"Searching for {search_query}")
                pywhatkit.search(search_query)
            else:
                speak("Sorry, I didn't catch the search query.")
            continue

        else:
            response = ask_deepseek(query)
            speak(response)
            continue

def open_app(app_name):
    if 'notepad' in app_name:
        os.system('notepad')
    elif 'chrome' in app_name:
        os.system('start chrome')
    elif 'vs code' in app_name:
        os.system('code')
    elif 'youtube' in app_name:
        # Opens YouTube in default browser
        os.system('start https://www.youtube.com')
    elif 'calculator' in app_name:
        os.system('start calc')
    else:
        speak("Application not available.")

def close_app(app_name):
    if 'notepad' in app_name:
        os.system('taskkill /f /im notepad.exe')
    elif 'chrome' in app_name:
        os.system('taskkill /f /im chrome.exe')
    elif 'microsoft edge' in app_name or 'edge' in app_name:
        speak("Closing Microsoft Edge.")
        os.system('taskkill /f /im msedge.exe')
    elif 'vs code' in app_name:
        os.system('taskkill /f /im Code.exe')
    elif 'youtube' in app_name:
        speak("Closing browser.")
        # Try to close all major browsers
        os.system('taskkill /f /im chrome.exe')
        os.system('taskkill /f /im msedge.exe')
        os.system('taskkill /f /im MicrosoftEdge.exe')
        os.system('taskkill /f /im firefox.exe')
    elif 'calculator' in app_name:
        os.system('taskkill /f /im Calculator.exe')
    else:
        speak("Cannot close this app.")
    
def sleep_mode():
    speak("make sleep.")
    os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")


# Run the assistant
run_jarvis()
