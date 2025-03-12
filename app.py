from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from models import User, Task, CompletedTask, Donation, engine
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from config import settings
import requests
import random

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database session
SessionLocal = sessionmaker(bind=engine)

class WalletConnect(BaseModel):
    telegram_id: str
    wallet_address: str

class UserResponse(BaseModel):
    telegram_id: str
    username: Optional[str]
    total_tokens: int
    wallet_address: Optional[str]
    check_in_streak: int
    tasks_completed: int
    total_referrals: int
    join_date: datetime

class TaskCompletion(BaseModel):
    telegram_id: str
    task_title: str

class ReferralCode(BaseModel):
    telegram_id: str
    referral_code: str

class DonationRequest(BaseModel):
    telegram_id: str
    amount_egld: float
    transaction_hash: str

# Task rewards
TASK_REWARDS = {
    "Join Telegram Group": 1000,
    "Follow on Twitter": 1000,
    "Retweet Announcement": 500,
    "Join Discord": 1000,
    "Share a Meme": 1500
}

@app.get("/")
def read_root():
    return {"message": "Welcome to BeniDrop Airdrop API"}

@app.post("/api/register")
def register_user(telegram_id: str, username: Optional[str] = None):
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        if user:
            return UserResponse(
                telegram_id=user.telegram_id,
                username=user.username,
                total_tokens=user.total_tokens,
                wallet_address=user.wallet_address,
                check_in_streak=user.check_in_streak,
                tasks_completed=len(user.completed_tasks),
                total_referrals=len(user.referrals),
                join_date=user.join_date
            )
        
        # Generate unique referral code
        referral_code = f"BENI{random.randint(10000, 99999)}"
        while session.query(User).filter(User.referral_code == referral_code).first():
            referral_code = f"BENI{random.randint(10000, 99999)}"
        
        new_user = User(
            telegram_id=telegram_id,
            username=username,
            referral_code=referral_code,
            join_date=datetime.utcnow(),
            total_tokens=settings.WELCOME_BONUS
        )
        session.add(new_user)
        session.commit()
        
        return UserResponse(
            telegram_id=new_user.telegram_id,
            username=new_user.username,
            total_tokens=new_user.total_tokens,
            wallet_address=new_user.wallet_address,
            check_in_streak=new_user.check_in_streak,
            tasks_completed=0,
            total_referrals=0,
            join_date=new_user.join_date
        )
    finally:
        session.close()

@app.get("/api/user/{telegram_id}")
def get_user(telegram_id: str):
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return UserResponse(
            telegram_id=user.telegram_id,
            username=user.username,
            total_tokens=user.total_tokens,
            wallet_address=user.wallet_address,
            check_in_streak=user.check_in_streak,
            tasks_completed=len(user.completed_tasks),
            total_referrals=len(user.referrals),
            join_date=user.join_date
        )
    finally:
        session.close()

@app.post("/api/complete-task")
def complete_task(task: TaskCompletion):
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.telegram_id == task.telegram_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if task exists
        if task.task_title not in TASK_REWARDS:
            raise HTTPException(status_code=400, detail="Invalid task")
        
        # Check if task already completed
        completed = session.query(CompletedTask).filter(
            CompletedTask.user_id == user.id,
            CompletedTask.task_title == task.task_title
        ).first()
        
        if completed:
            raise HTTPException(status_code=400, detail="Task already completed")
        
        # Add completed task
        new_completed_task = CompletedTask(
            user_id=user.id,
            task_title=task.task_title,
            completed_at=datetime.utcnow()
        )
        session.add(new_completed_task)
        
        # Add reward
        reward = TASK_REWARDS[task.task_title]
        user.total_tokens += reward
        session.commit()
        
        return {
            "status": "success",
            "tokens_earned": reward,
            "total_tokens": user.total_tokens
        }
    finally:
        session.close()

@app.post("/api/use-referral")
def use_referral(referral: ReferralCode):
    session = SessionLocal()
    try:
        # Get referrer
        referrer = session.query(User).filter(User.referral_code == referral.referral_code).first()
        if not referrer:
            raise HTTPException(status_code=404, detail="Invalid referral code")
        
        # Get user
        user = session.query(User).filter(User.telegram_id == referral.telegram_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if user already used a referral code
        if user.referred_by:
            raise HTTPException(status_code=400, detail="Already used a referral code")
        
        # Can't use own referral code
        if user.id == referrer.id:
            raise HTTPException(status_code=400, detail="Cannot use own referral code")
        
        # Update user and referrer
        user.referred_by = referrer.id
        referrer.total_tokens += settings.REFERRAL_REWARD
        user.total_tokens += settings.REFERRAL_BONUS
        session.commit()
        
        return {
            "status": "success",
            "tokens_earned": settings.REFERRAL_BONUS,
            "total_tokens": user.total_tokens
        }
    finally:
        session.close()

@app.post("/api/connect-wallet")
def connect_wallet(data: WalletConnect):
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.telegram_id == data.telegram_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.wallet_address = data.wallet_address
        session.commit()
        return {"status": "success", "message": "Wallet connected successfully"}
    finally:
        session.close()

@app.get("/api/leaderboard")
def get_leaderboard():
    session = SessionLocal()
    try:
        top_users = session.query(User).order_by(User.total_tokens.desc()).limit(10).all()
        return [
            {
                "username": user.username or "Anonymous",
                "total_tokens": user.total_tokens,
                "rank": idx + 1
            }
            for idx, user in enumerate(top_users)
        ]
    finally:
        session.close()

@app.post("/api/daily-check-in/{telegram_id}")
def daily_check_in(telegram_id: str):
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if user already checked in today
        today = datetime.utcnow().date()
        if user.last_check_in and user.last_check_in.date() == today:
            raise HTTPException(status_code=400, detail="Already checked in today")
        
        # Update check-in streak
        if user.last_check_in and (today - user.last_check_in.date()).days == 1:
            user.check_in_streak += 1
        else:
            user.check_in_streak = 1
        
        # Update user
        user.last_check_in = datetime.utcnow()
        user.total_tokens += settings.DAILY_CHECK_IN_REWARD
        session.commit()
        
        return {
            "status": "success",
            "streak": user.check_in_streak,
            "tokens_earned": settings.DAILY_CHECK_IN_REWARD
        }
    finally:
        session.close()

@app.post("/api/record-donation")
def record_donation(donation: DonationRequest):
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.telegram_id == donation.telegram_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        new_donation = Donation(
            user_id=user.id,
            amount_egld=donation.amount_egld,
            message=f"Thank you for the coffee! Transaction: {donation.transaction_hash}"
        )
        session.add(new_donation)
        session.commit()
        
        return {"status": "success", "message": "Thank you for your donation!"}
    finally:
        session.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
