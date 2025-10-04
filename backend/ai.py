# # backend/ai.py
# import requests

# class AIWrapper:
#     def __init__(self, model: str = "llama3", host: str = "http://localhost:11434"):
#         self.model = model
#         self.host = host

#     def query(self, prompt: str, context: str = "") -> str:
#         """Ask Ollama a question with optional context"""
#         try:
#             full_prompt = f"Context:\n{context}\n\nQuestion:\n{prompt}" if context else prompt
#             resp = requests.post(
#                 f"{self.host}/api/generate",
#                 json={"model": self.model, "prompt": full_prompt},
#                 timeout=60,
#             )
#             resp.raise_for_status()
#             # Ollama streams responses, but in simple calls resp.json() works
#             return resp.json().get("response", "No response from AI")
#         except Exception as e:
#             return f"Error: {e}"

#     def summarize(self, text: str, max_length: int = 120) -> str:
#         """Summarize text using Ollama"""
#         try:
#             prompt = f"Summarize the following text in under {max_length} words:\n\n{text}"
#             resp = requests.post(
#                 f"{self.host}/api/generate",
#                 json={"model": self.model, "prompt": prompt},
#                 timeout=60,
#             )
#             resp.raise_for_status()
#             return resp.json().get("response", "No response from AI")
#         except Exception as e:
#             return f"Error: {e}"

#     def categorize(self, text: str) -> list[str]:
#         """Suggest categories/tags for a note using Ollama"""
#         try:
#             prompt = f"Suggest 3 short tags or categories for the following text:\n\n{text}"
#             resp = requests.post(
#                 f"{self.host}/api/generate",
#                 json={"model": self.model, "prompt": prompt},
#                 timeout=60,
#             )
#             resp.raise_for_status()
#             raw = resp.json().get("response", "")
#             # simple cleanup: split by commas/lines
#             return [tag.strip() for tag in raw.replace("\n", ",").split(",") if tag.strip()]
#         except Exception as e:
#             return [f"Error: {e}"]



import requests
import os
from dotenv import load_dotenv

load_dotenv()

class GeminiWrapper:
    def __init__(self, model: str = "gemini-2.0-flash"):
        self.model = model
        self.api_key = os.getenv("GEMINI_API_KEY")  # set in .env or environment

    def _call(self, prompt: str):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        resp = requests.post(url, headers=headers, json=data, timeout=60)
        resp.raise_for_status()
        candidates = resp.json().get("candidates", [])
        if candidates and "content" in candidates[0]:
            parts = candidates[0]["content"].get("parts", [])
            return parts[0].get("text", "") if parts else ""
        return "No response from Gemini"

    def query(self, prompt: str, context: str = "") -> str:
        full_prompt = f"Context:\n{context}\n\nQuestion:\n{prompt}" if context else prompt
        return self._call(full_prompt)

    def summarize(self, text: str, max_length: int = 120) -> str:
        prompt = f"Summarize the following text in under {max_length} words:\n\n{text}"
        return self._call(prompt)

    def categorize(self, text: str) -> list[str]:
        prompt = f"Suggest 3 short tags or categories for the following text:\n\n{text}"
        raw = self._call(prompt)
        return [tag.strip() for tag in raw.replace("\n", ",").split(",") if tag.strip()]
    
    def query_voice(self, prompt: str) -> str:
        return self._call(prompt)

