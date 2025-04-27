# app/api/routes.py
from flask import request, jsonify # Import jsonify explicitly
from . import api_bp # Application Blueprint
# --- Import models including app_timezone ---
from app.models.models import db, User, TripPlanHistory # Database Models (app_timezone might not be needed directly here now)
# -------------------------------------------
from app.utils.helpers import api_response # Response Helper (still used for some routes)
from app.services.smart_trip_planner_ai import create_plan # AI Service
from app.schemas.request_schemas import UserRegisterSchema, UserLoginSchema, TripPlanRequestSchema # Request Schemas
from app.schemas.response_schemas import TripPlanHistorySchema, AuthTokenSchema # Response Schemas
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity # JWT Utilities
# werkzeug.security is used within the User model
from marshmallow import ValidationError # Validation Error Class
import logging
import json # Import json for parsing
from datetime import date, datetime # Import datetime for logic if needed (limit check removed)
import uuid # <-- Import uuid module

# Logger instance
logger = logging.getLogger(__name__)

# Instantiate Schemas for reuse
user_register_schema = UserRegisterSchema()
user_login_schema = UserLoginSchema()
trip_plan_schema = TripPlanRequestSchema()
trip_history_schema = TripPlanHistorySchema(many=True) # Schema for lists of history objects
auth_token_schema = AuthTokenSchema()

# --- Trip Planning Route ---

@api_bp.route('/planning', methods=['POST'])
@jwt_required() # Protected Route
def plan_trip():
    """Create Trip Plan Route""" # Removed usage limit logic
    current_user_id_str = get_jwt_identity() # Get user ID (as string) from JWT payload
    # Convert JWT identity string to UUID object
    try:
        current_user_id = uuid.UUID(current_user_id_str)
    except ValueError:
        logger.error(f"Invalid UUID format in JWT identity: {current_user_id_str}")
        return jsonify({"error": "Invalid user identifier in token."}), 400

    # --- Get User Object using UUID (Optional but good practice) ---
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"error": "User not found for provided token."}), 404
    # -------------------------------------------------------------

    # --- REMOVED Usage Limit Check Logic ---
    # The logic checking user.is_premium and daily count is removed
    # as those fields are no longer in the User model.
    # Planning is now unlimited for all authenticated users based on current model.
    # ------------------------------------

    # --- Proceed with Planning Request ---
    json_data = request.get_json()
    if not json_data: return jsonify({"error": "No input JSON provided."}), 400

    try: # Validate input via schema
        user_input = trip_plan_schema.load(json_data)
        logger.info(f"Planning request validated for user {current_user_id}.")
    except ValidationError as err:
        # Return simple JSON error for validation failure
        return jsonify({"error": "Input validation failed.", "details": err.messages}), 400

    try:
        # Call AI service to generate the plan
        raw_itinerary_string = create_plan(user_input)
        logger.info(f"Raw AI response received for user {current_user_id}.")

        # Parse JSON response from AI
        parsed_itinerary = None
        try:
            cleaned_json_string = raw_itinerary_string.strip()
            if cleaned_json_string.startswith("```json"):
                cleaned_json_string = cleaned_json_string.removeprefix("```json").strip()
            if cleaned_json_string.endswith("```"):
                cleaned_json_string = cleaned_json_string.removesuffix("```").strip()
            parsed_itinerary = json.loads(cleaned_json_string)
            logger.info(f"Successfully parsed JSON itinerary for user {current_user_id}.")
        except json.JSONDecodeError as json_err:
            logger.error(f"Failed to parse JSON response from AI for user {current_user_id}. Error: {json_err}. Raw: {raw_itinerary_string[:500]}...")
            # Return simple JSON error for parsing failure
            return jsonify({"error": "Failed to process AI response format."}), 500

        # --- Prepare data for DB (convert dates in copy for JSONB) ---
        request_input_for_db = user_input.copy()
        if isinstance(request_input_for_db.get('start_date'), date):
            request_input_for_db['start_date'] = request_input_for_db['start_date'].isoformat()
        if isinstance(request_input_for_db.get('end_date'), date):
            request_input_for_db['end_date'] = request_input_for_db['end_date'].isoformat()

        # Save to DB (save parsed AI response)
        history_entry = TripPlanHistory(
            user_id=current_user_id, # Use UUID object for foreign key
            request_input=request_input_for_db,
            generated_itinerary=parsed_itinerary, # Store parsed Python dict/list
            destination_city=user_input.get('travel_destination'),
            start_date=user_input.get('start_date'),
            end_date=user_input.get('end_date')
        )
        db.session.add(history_entry)
        db.session.commit()  # Commit changes to DB
        logger.info(f"Trip plan saved to history for user {current_user_id}, history ID {history_entry.id}.")

        # --- SUCCESS RESPONSE: Return the parsed itinerary directly ---
        return jsonify(parsed_itinerary), 200
        # ------------------------------------------------------------

    except (ValueError, ConnectionError) as service_err: # Handle AI service errors
        logger.error(f"AI Service Error (Planning) for user {current_user_id}: {service_err}")
        status_code = 503 if isinstance(service_err, ConnectionError) else 500
        error_msg = "AI planning service is currently unavailable." if isinstance(service_err, ConnectionError) else f"AI service configuration error."
        # Return simple JSON error for service failure
        return jsonify({"error": error_msg}), status_code
    except Exception as e: # Handle other unexpected errors
        db.session.rollback()
        logger.error(f"Unexpected Error (Planning) for user {current_user_id}: {e}", exc_info=True)
        # Return simple JSON error for internal server error
        return jsonify({"error": "An internal error occurred during trip planning."}), 500

# --- History Retrieval Route ---
# NOTE: Route name changed as requested in previous interaction
@api_bp.route('/trip-plan-history', methods=['GET'])
@jwt_required()
def get_history():
    """Get User Trip History Route (Last 10)"""
    current_user_id_str = get_jwt_identity() # Get user ID (as string)
    # --- Convert JWT identity string to UUID object ---
    try:
        current_user_id = uuid.UUID(current_user_id_str)
    except ValueError:
        logger.error(f"Invalid UUID format in JWT identity for history: {current_user_id_str}")
        return api_response(message="Invalid user identifier in token.", status_code=400, success=False) # Use api_response for consistency
    # -------------------------------------------------

    try:
        # --- Use UUID object for filtering ---
        # Use filter_by with the UUID object
        histories = TripPlanHistory.query.filter_by(user_id=current_user_id)\
                                     .order_by(TripPlanHistory.created_at.desc())\
                                     .limit(10).all()
        # -----------------------------

        # Serialize the list of history objects using the response schema
        result = trip_history_schema.dump(histories)
        logger.info(f"Retrieved {len(histories)} history entries for user {current_user_id}.")
        # Use api_response for consistency in history list format
        return api_response(data=result, message="Trip history retrieved successfully.")

    except Exception as e: # Handle potential errors during DB query or serialization
        logger.error(f"Error retrieving history for user {current_user_id}: {e}", exc_info=True)
        # Use api_response for internal server error
        return api_response(message="Failed to retrieve trip history.", status_code=500, success=False)

