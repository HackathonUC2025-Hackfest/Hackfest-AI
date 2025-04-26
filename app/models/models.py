# app/models/models.py
from sqlalchemy.dialects.postgresql import JSONB
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from .. import db
import pytz

# Timezone setting
app_timezone = pytz.timezone('Asia/Jakarta') # Example: WIB

class User(db.Model):
    # ... (kode User tetap sama) ...
    """User Model"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(app_timezone))

    # Relationship to TripPlanHistory
    trip_plan_histories = db.relationship('TripPlanHistory', back_populates='user', lazy=True, cascade="all, delete-orphan")

    # Password hashing methods
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Repr method
    def __repr__(self):
        return f'<User {self.username}>'


class TripPlanHistory(db.Model):
    """Trip History Model"""
    __tablename__ = 'trip_plan_histories'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) # Foreign Key
    request_input = db.Column(JSONB, nullable=False) # Store user request as JSON
    generated_itinerary = db.Column(JSONB, nullable=False) # Store parsed AI response as JSONB
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(app_timezone))
    destination_city = db.Column(db.String(100)) # Indexed field example
    start_date = db.Column(db.Date) # Store dates if provided
    end_date = db.Column(db.Date)

    # Relationship back to User
    user = db.relationship('User', back_populates='trip_plan_histories')

    def __repr__(self):
        return f'<TripPlanHistory {self.id} for User {self.user_id}>'