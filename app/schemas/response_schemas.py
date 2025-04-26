# app/schemas/response_schemas.py
from marshmallow import Schema, fields

class UserSchema(Schema):
    """User Response Schema (Public Info)"""
    id = fields.Int(dump_only=True) # Read-only during serialization
    username = fields.String(dump_only=True)
    created_at = fields.DateTime(dump_only=True, format='iso') # Use ISO 8601 format

class TripPlanHistorySchema(Schema):
    """Trip Plan History Response Schema (List View)"""
    id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
    destination_city = fields.String(dump_only=True)
    start_date = fields.Date(dump_only=True, allow_none=True, format='%Y-%m-%d')
    end_date = fields.Date(dump_only=True, allow_none=True, format='%Y-%m-%d')
    requested_on = fields.DateTime(attribute="created_at", dump_only=True, format='iso') # Rename field for clarity
    input = fields.Dict(attribute="request_input", dump_only=True) # Include the original request input

class AuthTokenSchema(Schema):
    """Auth Token Response Schema"""
    access_token = fields.String(required=True)