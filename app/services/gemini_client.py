# app/services/gemini_client.py
import google.generativeai as genai
from flask import current_app # Access Flask app context for config
import logging

# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def configure_gemini():
    """Configure Gemini client using API key from Flask config."""
    api_key = current_app.config.get('GEMINI_API_KEY')
    if not api_key:
        logger.error("GEMINI_API_KEY not found in application configuration.")
        raise ValueError("Gemini API Key is not configured.")
    try:
        genai.configure(api_key=api_key)
        logger.info("Gemini client configured successfully.")
    except Exception as e:
        logger.error(f"Failed to configure Gemini client: {e}")
        raise # Re-raise the exception

def generate_text_from_gemini(prompt_text):
    """Send prompt to configured Gemini model and return generated text."""
    try:
        # Ensure Gemini is configured
        # if not genai.is_configured():
        #      configure_gemini()
        configure_gemini()

        # Get model name from config, use default if not set
        model_name = current_app.config.get('GEMINI_MODEL_NAME', 'gemini-1.5-flash')
        logger.info(f"Using Gemini model: {model_name}")
        model = genai.GenerativeModel(model_name)

        # Generate content
        response = model.generate_content(prompt_text)
        logger.info("Received response from Gemini.")

        # Extract text content (handle potential response structure variations)
        # Check common attributes/structures for text content
        if hasattr(response, 'text'): return response.text
        if response.parts: return "".join(part.text for part in response.parts)
        # Check candidates as a fallback
        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            return "".join(part.text for part in response.candidates[0].content.parts)

        # If text cannot be extracted
        logger.warning(f"Unexpected Gemini response structure: {response}")
        raise ValueError("Could not extract text content from Gemini response.")

    except ValueError as ve: # Handle config errors or response parsing issues
        logger.error(f"Value error during Gemini call: {ve}")
        raise # Re-raise specific error
    except Exception as e: # Handle network or other API errors
        logger.error(f"Unexpected error during Gemini API call: {e}", exc_info=True)
        # Raise a more generic error indicating communication failure
        raise ConnectionError(f"Failed to communicate with Gemini API: {e}")