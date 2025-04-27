# app/schemas/request_schemas.py
from marshmallow import Schema, fields, validate, validates_schema, ValidationError

class UserRegisterSchema(Schema):
    """User Registration Request Schema"""
    # Changed username to email, added full_name (optional)
    full_name = fields.String(required=False, allow_none=True, validate=validate.Length(max=120))
    email = fields.Email(required=True) # Use Email field for validation
    password = fields.String(required=True, validate=validate.Length(min=6))

class UserLoginSchema(Schema):
    """User Login Request Schema"""
    # Changed username to email
    email = fields.Email(required=True)
    password = fields.String(required=True)

class TripPlanRequestSchema(Schema):
    """Trip Planning Request Schema"""
    travel_destination = fields.String(required=True, validate=validate.Length(min=1))
    start_date = fields.Date(required=False, allow_none=True, format='%Y-%m-%d') # Expect YYYY-MM-DD format
    end_date = fields.Date(required=False, allow_none=True, format='%Y-%m-%d')   # Expect YYYY-MM-DD format
    trip_duration = fields.Integer(required=False, allow_none=True, validate=validate.Range(min=1))
    activity_preferences = fields.List(fields.String(), required=True, validate=validate.Length(min=1))
    travel_budget = fields.Float(required=True, validate=validate.Range(min=0))
    travel_style = fields.String(required=True, validate=validate.OneOf(["Solo traveler", "Romantic couple", "Family with children", "Backpacker", "Luxury traveler"]))
    activity_intensity = fields.String(required=True, validate=validate.OneOf(["Relaxed", "Balanced", "Full"]))

    # Custom cross-field validation method
    @validates_schema
    def validate_dates_or_duration(self, data, **kwargs):
        """Ensure either dates or duration is provided and dates are logical."""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        trip_duration = data.get('trip_duration')
        if not ((start_date and end_date) or trip_duration):
            raise ValidationError("Provide 'start_date'/'end_date' or 'trip_duration'.", field_names=["start_date", "end_date", "trip_duration"])
        if start_date and end_date and start_date > end_date:
            raise ValidationError("End date cannot be before start date.", field_names=["end_date"])

