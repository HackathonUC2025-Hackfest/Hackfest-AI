# app/api/routes.py
from flask import request, jsonify # Import jsonify explicitly
from . import api_bp # Application Blueprint
from app.models.models import db, User, TripPlanHistory # Database Models
from app.utils.helpers import api_response # Keep for other routes/potential errors
from app.services.smart_trip_planner_ai import create_plan # AI Service
from app.schemas.request_schemas import UserRegisterSchema, UserLoginSchema, TripPlanRequestSchema # Request Schemas
from app.schemas.response_schemas import TripPlanHistorySchema, AuthTokenSchema # Response Schemas
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity # JWT Utilities
from marshmallow import ValidationError # Validation Error Class
import logging
import json # Import json for parsing
from datetime import date # Import date type

# Logger instance
logger = logging.getLogger(__name__)

# Instantiate Schemas for reuse
user_register_schema = UserRegisterSchema()
user_login_schema = UserLoginSchema()
trip_plan_schema = TripPlanRequestSchema()
trip_history_schema = TripPlanHistorySchema(many=True)
auth_token_schema = AuthTokenSchema()

# --- Authentication Routes (Keep using api_response for consistency here) ---

@api_bp.route('/auth/register', methods=['POST'])
def register_user():
    """Register New User Route"""
    json_data = request.get_json()
    # Use api_response for input validation error
    if not json_data: return api_response(message="No input data provided.", status_code=400, success=False)

    try:
        data = user_register_schema.load(json_data)
    except ValidationError as err:
        # Use api_response for schema validation error
        return api_response(data=err.messages, message="Input validation failed.", status_code=400, success=False)

    username = data['username']
    if User.query.filter_by(username=username).first():
        # Use api_response for conflict error
        return api_response(message="Username already exists.", status_code=409, success=False)

    new_user = User(username=username)
    new_user.set_password(data['password'])
    try:
        db.session.add(new_user)
        db.session.commit()
        logger.info(f"User '{username}' registered successfully.")
        # Use api_response for success message
        return api_response(message="User created successfully.", status_code=201)
    except Exception as e:
        db.session.rollback()
        logger.error(f"Database error during user registration: {e}", exc_info=True)
        # Use api_response for internal server error
        return api_response(message="Failed to register user due to a server error.", status_code=500, success=False)

@api_bp.route('/auth/login', methods=['POST'])
def login_user():
    """Login User Route"""
    json_data = request.get_json()
    # Use api_response for input validation error
    if not json_data: return api_response(message="No input data provided.", status_code=400, success=False)

    try:
        data = user_login_schema.load(json_data)
    except ValidationError as err:
        # Use api_response for schema validation error
        return api_response(data=err.messages, message="Input validation failed.", status_code=400, success=False)

    username = data['username']
    password = data['password']
    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
        access_token = create_access_token(identity=str(user.id))
        logger.info(f"User '{username}' logged in successfully.")
        token_data = auth_token_schema.dump({"access_token": access_token})
        # Use api_response for success with token data
        return api_response(data=token_data, message="Login successful.")
    else:
        logger.warning(f"Failed login attempt for username '{username}'.")
        # Use api_response for authentication failure
        return api_response(message="Invalid username or password.", status_code=401, success=False)

# --- Trip Planning Route (Modified Return Type) ---

@api_bp.route('/planning', methods=['POST'])
@jwt_required() # Protected Route
def plan_trip():
    """Create Trip Plan Route - Returns raw itinerary JSON on success"""
    current_user_id = get_jwt_identity()

    json_data = request.get_json()
    # Return simple JSON error if no input
    if not json_data: return jsonify({"error": "No input JSON provided."}), 400

    try: # Validate input via schema
        user_input = trip_plan_schema.load(json_data)
        logger.info(f"Planning request validated for user {current_user_id}.")
    except ValidationError as err:
        # Return simple JSON error for validation failure
        return jsonify({"error": "Input validation failed.", "details": err.messages}), 400

    try:
        # Call AI service
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

        # Save to DB (save raw AI string)
        history_entry = TripPlanHistory(
            user_id=current_user_id,
            request_input=request_input_for_db,
            generated_itinerary=parsed_itinerary,
            destination_city=user_input.get('travel_destination'),
            start_date=user_input.get('start_date'),
            end_date=user_input.get('end_date')
        )
        db.session.add(history_entry)
        db.session.commit()  # Commit changes to DB
        logger.info(f"Trip plan saved to history for user {current_user_id}, history ID {history_entry.id}.")

        # --- SUCCESS RESPONSE: Return the parsed itinerary directly ---
        # Flask automatically sets Content-Type to application/json
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

# --- History Retrieval Route (Keep using api_response for consistency here) ---

@api_bp.route('/trip-plan-history', methods=['GET'])
@jwt_required()
def get_history():
    """Get User Trip History Route (Last 10)"""
    current_user_id = get_jwt_identity()
    try:
        histories = TripPlanHistory.query.filter_by(user_id=current_user_id)\
                                     .order_by(TripPlanHistory.created_at.desc())\
                                     .limit(10).all()
        result = trip_history_schema.dump(histories)
        logger.info(f"Retrieved {len(histories)} history entries for user {current_user_id}.")
        # Use api_response for consistency in history list format
        return api_response(data=result, message="Trip history retrieved successfully.")
    except Exception as e:
        logger.error(f"Error retrieving history for user {current_user_id}: {e}", exc_info=True)
        # Use api_response for internal server error
        return api_response(message="Failed to retrieve trip history.", status_code=500, success=False)