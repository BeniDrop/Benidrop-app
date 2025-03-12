from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True, nullable=False)
    username = Column(String)
    wallet_address = Column(String)
    total_tokens = Column(Integer, default=0)
    check_in_streak = Column(Integer, default=0)
    last_check_in = Column(DateTime)
    referral_code = Column(String, unique=True)
    referred_by = Column(Integer, ForeignKey('users.id'))
    join_date = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    completed_tasks = relationship("CompletedTask", back_populates="user")
    donations = relationship("Donation", back_populates="user")
    referrals = relationship("User", backref="referrer", remote_side=[id])

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    reward = Column(Integer)
    task_type = Column(String)  # telegram_join, twitter_follow, etc.
    
    # Relationships
    completed_by = relationship("CompletedTask", back_populates="task")

class CompletedTask(Base):
    __tablename__ = "completed_tasks"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    task_id = Column(Integer, ForeignKey('tasks.id'))
    task_title = Column(String, nullable=False)
    completion_date = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="completed_tasks")
    task = relationship("Task", back_populates="completed_by")

class Donation(Base):
    __tablename__ = "donations"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    amount_egld = Column(Float, nullable=False)
    message = Column(String)
    donation_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="donations")

# Create database engine
engine = create_engine("sqlite:///benidrop.db")

# Create all tables
def init_db():
    Base.metadata.create_all(engine)
