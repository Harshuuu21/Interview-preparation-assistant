import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if GEMINI_API_KEY and not GROQ_API_KEY:
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)

class GroqWrapper:
    def __init__(self, model_name="llama-3.1-8b-instant", temperature=0.7, json_mode=False):
        from groq import Groq
        self.client = Groq(api_key=GROQ_API_KEY)
        self.model_name = model_name
        self.temperature = temperature
        self.json_mode = json_mode
        
    def generate_content(self, prompt: str):
        response_format = {"type": "json_object"} if self.json_mode else None
        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            response_format=response_format
        )
        class Response:
            text = completion.choices[0].message.content
        return Response()

def get_model(model_name: str = "gemini-2.0-flash", temperature: float = 0.7, json_mode: bool = False):
    if GROQ_API_KEY:
        # Use Groq if the key is provided
        # Use llama-3.1-8b-instant or llama3-70b-8192
        return GroqWrapper(model_name="llama-3.1-8b-instant", temperature=temperature, json_mode=json_mode)
        
    # Otherwise use Gemini
    import google.generativeai as genai
    generation_config = genai.types.GenerationConfig(
        temperature=temperature,
    )
    if json_mode:
        generation_config.response_mime_type = "application/json"
    
    return genai.GenerativeModel(
        model_name=model_name,
        generation_config=generation_config
    )

