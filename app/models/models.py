# app/models/models.py
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID # Import UUID type for PostgreSQL
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timezone # Import timezone for server defaults
from sqlalchemy import func # Import func for database functions like now()
from .. import db # Import db instance from app/__init__.py
import uuid # Import Python's uuid module
import pytz

app_timezone = pytz.timezone('Asia/Jakarta')

class User(db.Model):
    """User Model - Updated Schema"""
    __tablename__ = 'users'

    id = db.Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = db.Column(db.String(120), nullable=True) # User's full name, optional
    email = db.Column(db.String(120), unique=True, nullable=False, index=True) # User's email, must be unique and required, indexed
    password = db.Column(db.String(256), nullable=True) # Hashed password, nullable for OAuth users
    auth_provider = db.Column(db.String(50), nullable=False, default='local') # Authentication provider ('local', 'google', etc.)
    photo_url = db.Column(db.Text, nullable=True) # URL for user's profile picture
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    trip_plan_histories = db.relationship('TripPlanHistory', back_populates='user', lazy=True, cascade="all, delete-orphan")

    # Password hashing methods (Updated to handle nullable password)
    def set_password(self, password):
        """Hashes the password if provided."""
        if password:
            self.password_hash = generate_password_hash(password)
        else:
            self.password_hash = None # Set to None for OAuth users without local password

    def check_password(self, password):
        """Checks the provided password against the stored hash."""
        # Return False if there's no hash or no password provided
        if not self.password_hash or not password:
            return False
        return check_password_hash(self.password_hash, password)

    # Repr method (Updated to use email)
    def __repr__(self):
        """String representation of the User object."""
        return f'<User {self.email}>'


class TripPlanHistory(db.Model):
    """Trip History Model"""
    __tablename__ = 'trip_plan_histories'

    # --- No changes needed here based on the request ---
    id = db.Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Foreign key type matches User.id
    user_id = db.Column(PG_UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    request_input = db.Column(JSONB, nullable=False) # Store user request as JSON
    generated_itinerary = db.Column(JSONB, nullable=False) # Store parsed AI response as JSONB
    # Use server_default for creation timestamp
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    destination_city = db.Column(db.String(100)) # Indexed field example
    start_date = db.Column(db.Date) # Store dates if provided
    end_date = db.Column(db.Date)
    # --- ---------------------------------------- ---

    # Relationship back to User (No change needed here)
    user = db.relationship('User', back_populates='trip_plan_histories')

    def __repr__(self):
        """String representation of the TripPlanHistory object."""
        # Represent UUIDs as strings for readability
        return f'<TripPlanHistory {str(self.id)} for User {str(self.user_id)}>'

