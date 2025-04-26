# app/services/smart_trip_planner_ai.py
from app.utils.helpers import format_gemini_prompt
from app.services.gemini_client import generate_text_from_gemini
import logging

logger = logging.getLogger(__name__)

def create_plan(user_input):
    """Create Trip Plan Service Logic"""
    try:
        # 1. Format the prompt using validated user input
        prompt = format_gemini_prompt(user_input)
        logger.info("Formatted prompt for AI plan generation.")

        # 2. Call the Gemini service to generate the itinerary
        itinerary = generate_text_from_gemini(prompt)
        logger.info("AI itinerary generated successfully.")
        return itinerary

    except (ValueError, ConnectionError) as service_error:
        # Propagate known errors from the Gemini client
        logger.error(f"AI Service error during plan creation: {service_error}")
        raise
    except Exception as e:
        # Catch any other unexpected errors during this process
        logger.error(f"Unexpected error during plan creation service: {e}", exc_info=True)
        raise Exception(f"An internal error occurred while creating the trip plan.") # Wrap in generic exception