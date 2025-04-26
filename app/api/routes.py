# app/api/routes.py
from flask import request, current_app, jsonify
from . import api_bp # Application Blueprint
from app.models.models import db, User, TripPlanHistory # Database Models
from app.utils.helpers import api_response # Response Helper
from app.services.smart_trip_planner_ai import create_plan # AI Service
from app.schemas.request_schemas import UserRegisterSchema, UserLoginSchema, TripPlanRequestSchema # Request Schemas
from app.schemas.response_schemas import TripPlanHistorySchema, AuthTokenSchema # Response Schemas
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity # JWT Utilities
from werkzeug.security import check_password_hash # Password Hashing
from marshmallow import ValidationError # Validation Error Class
import logging
from datetime import date # Date object type

# Logger instance
logger = logging.getLogger(__name__)

# Instantiate Schemas for reuse
user_register_schema = UserRegisterSchema()
user_login_schema = UserLoginSchema()
trip_plan_schema = TripPlanRequestSchema()
trip_history_schema = TripPlanHistorySchema(many=True) # Schema for lists of history objects
auth_token_schema = AuthTokenSchema()

# --- Authentication Routes ---

@api_bp.route('/auth/register', methods=['POST'])
def register_user():
    """Register New User Route"""
    json_data = request.get_json()
    if not json_data: return api_response(message="No input data provided.", status_code=400, success=False)

    try: # Validate request body via schema
        data = user_register_schema.load(json_data)
    except ValidationError as err:
        # Return validation errors if schema validation fails
        return api_response(data=err.messages, message="Input validation failed.", status_code=400, success=False)

    username = data['username']
    # Check if username already exists in the database
    if User.query.filter_by(username=username).first():
        return api_response(message="Username already exists.", status_code=409, success=False) # Return 409 Conflict

    # Create new User object
    new_user = User(username=username)
    new_user.set_password(data['password'])
    try: # Attempt to save the new user to the database
        db.session.add(new_user)
        db.session.commit()
        logger.info(f"User '{username}' registered successfully.")
        return api_response(message="User created successfully.", status_code=201) # Return 201 Created
    except Exception as e: # Handle potential database errors during commit
        db.session.rollback() # Rollback transaction on error
        logger.error(f"Database error during user registration: {e}", exc_info=True)
        return api_response(message="Failed to register user due to a server error.", status_code=500, success=False)

@api_bp.route('/auth/login', methods=['POST'])
def login_user():
    """Login User Route"""
    json_data = request.get_json()
    if not json_data: return api_response(message="No input data provided.", status_code=400, success=False)

    try: # Validate request body via schema
        data = user_login_schema.load(json_data)
    except ValidationError as err:
        return api_response(data=err.messages, message="Input validation failed.", status_code=400, success=False)

    username = data['username']
    password = data['password']
    # Find user by username
    user = User.query.filter_by(username=username).first()

    # Verify password and create JWT if valid
    if user and user.check_password(password):
        # Convert user ID to string for JWT identity
        access_token = create_access_token(identity=str(user.id))
        logger.info(f"User '{username}' logged in successfully.")
        # Serialize the token response using schema
        token_data = auth_token_schema.dump({"access_token": access_token})
        return api_response(data=token_data, message="Login successful.")
    else:
        # Invalid credentials
        logger.warning(f"Failed login attempt for username '{username}'.")
        return api_response(message="Invalid username or password.", status_code=401, success=False) # Return 401 Unauthorized

# --- Trip Planning Route ---

@api_bp.route('/planning', methods=['POST'])
@jwt_required() # Protected Route: Requires valid JWT
def plan_trip():
    """Create Trip Plan Route"""
    current_user_id = get_jwt_identity() # Get user ID from JWT payload (now a string)

    json_data = request.get_json()
    if not json_data: return api_response(message="No input JSON provided.", status_code=400, success=False)

    try: # Validate input via schema
        # user_input will contain date objects after validation
        user_input = trip_plan_schema.load(json_data)
        logger.info(f"Planning request validated for user {current_user_id}.")
    except ValidationError as err:
        return api_response(data=err.messages, message="Input validation failed.", status_code=400, success=False)

    try:
        # Call AI service to generate the plan
        generated_itinerary = create_plan(user_input)

        # --- Prepare data for JSONB column ---
        # Create a copy of the input to modify for JSON storage
        request_input_for_db = user_input.copy()
        # Convert date objects in the copy to ISO format strings
        if isinstance(request_input_for_db.get('start_date'), date):
            request_input_for_db['start_date'] = request_input_for_db['start_date'].isoformat()
        if isinstance(request_input_for_db.get('end_date'), date):
            request_input_for_db['end_date'] = request_input_for_db['end_date'].isoformat()
        # ------------------------------------

        # Create and save history entry to the database
        history_entry = TripPlanHistory(
            user_id=current_user_id,
            request_input=request_input_for_db, # <-- FIX: Use the dictionary with string dates for JSONB
            generated_itinerary=generated_itinerary,
            destination_city=user_input.get('travel_destination'),
            start_date=user_input.get('start_date'), # Use original date object for the Date column
            end_date=user_input.get('end_date')      # Use original date object for the Date column
        )
        db.session.add(history_entry)
        db.session.commit() # Commit the transaction
        logger.info(f"Trip plan saved to history for user {current_user_id}, history ID {history_entry.id}.")

        # Return the generated itinerary
        return api_response(data={"itinerary": generated_itinerary}, message="Trip plan generated successfully.")

    except (ValueError, ConnectionError) as service_err: # Handle known errors from AI service
        logger.error(f"AI Service Error (Planning) for user {current_user_id}: {service_err}")
        status_code = 503 if isinstance(service_err, ConnectionError) else 500
        error_msg = "AI planning service is currently unavailable." if isinstance(service_err, ConnectionError) else f"AI service configuration error."
        return api_response(message=error_msg, status_code=status_code, success=False)
    except Exception as e: # Handle other errors (like DB commit failure)
        db.session.rollback() # Rollback DB session on error
        logger.error(f"Unexpected Error (Planning) for user {current_user_id}: {e}", exc_info=True)
        # Check if it's the specific JSON serialization error
        if isinstance(e, TypeError) and "is not JSON serializable" in str(e):
             return api_response(message="Internal error: Failed to save planning data due to serialization issue.", status_code=500, success=False)
        # Generic internal error for other exceptions
        return api_response(message="An internal error occurred during trip planning.", status_code=500, success=False)

# --- History Retrieval Route ---

@api_bp.route('/history', methods=['GET'])
@jwt_required() # Protected Route: Requires valid JWT
def get_history():
    """Get User Trip History Route (Last 10)"""
    current_user_id = get_jwt_identity()
    try:
        # Query latest 10 history entries for the user
        histories = TripPlanHistory.query.filter_by(user_id=current_user_id)\
                                     .order_by(TripPlanHistory.created_at.desc())\
                                     .limit(10).all()

        # Serialize results using the schema
        result = trip_history_schema.dump(histories)
        logger.info(f"Retrieved {len(histories)} history entries for user {current_user_id}.")
        return api_response(data=result, message="Trip history retrieved successfully.")

    except Exception as e: # Handle potential DB or serialization errors
        logger.error(f"Error retrieving history for user {current_user_id}: {e}", exc_info=True)
        return api_response(message="Failed to retrieve trip history.", status_code=500, success=False)