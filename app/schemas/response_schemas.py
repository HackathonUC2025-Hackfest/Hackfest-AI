# app/schemas/response_schemas.py
from marshmallow import Schema, fields
# import json # Tidak perlu lagi
# import logging # Tidak perlu lagi jika metode dihapus

# logger = logging.getLogger(__name__) # Tidak perlu lagi

class UserSchema(Schema):
    """User Response Schema (Public Info)"""
    id = fields.Int(dump_only=True)
    username = fields.String(dump_only=True)
    created_at = fields.DateTime(dump_only=True, format='iso')

class TripPlanHistorySchema(Schema):
    """Trip History Response Schema (List View)"""
    # Fields that were already correct:
    id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
    destination_city = fields.String(dump_only=True)
    start_date = fields.Date(dump_only=True, allow_none=True, format='%Y-%m-%d')
    end_date = fields.Date(dump_only=True, allow_none=True, format='%Y-%m-%d')
    requested_on = fields.DateTime(attribute="created_at", dump_only=True, format='iso')
    input = fields.Dict(attribute="request_input", dump_only=True) # Contains user's original input

    # --- CORRECT FIELD FOR JSONB DATA ---
    # Use Raw to pass through the Python dict/list loaded by SQLAlchemy from JSONB
    itinerary = fields.Raw(attribute="generated_itinerary", dump_only=True)
    # ------------------------------------

    # --- deserialize_itinerary method REMOVED ---

class AuthTokenSchema(Schema):
    """Auth Token Response Schema"""
    access_token = fields.String(required=True)