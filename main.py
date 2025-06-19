# main.py — API FastAPI para wallet digital
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
import bcrypt

# Base de datos SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./wallet.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Modelos SQLAlchemy
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    balance = Column(Float, default=0)
    transactions = relationship("Transaction", back_populates="user")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(String)  # "add", "send", "receive"
    amount = Column(Float)
    description = Column(String)
    final_balance = Column(Float)
    user = relationship("User", back_populates="transactions")

Base.metadata.create_all(bind=engine)

# Pydantic Schemas
class RegisterData(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginData(BaseModel):
    email: EmailStr
    password: str

class AddMoneyData(BaseModel):
    email: EmailStr
    amount: float

class SendMoneyData(BaseModel):
    sender_email: EmailStr
    recipient_email: EmailStr
    amount: float
    note: str = ""

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['https://wallet.keber.cl'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/register")
def register(data: RegisterData, db: Session = Depends(get_db)):
    if db.query(User).filter_by(email=data.email).first():
        raise HTTPException(status_code=400, detail="Email ya registrado")
    hashed_pw = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
    user = User(name=data.name, email=data.email, hashed_password=hashed_pw, balance=1000)
    db.add(user)
    db.commit()
    return {"message": "Usuario registrado correctamente"}

@app.post("/login")
def login(data: LoginData, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=data.email).first()
    if not user or not bcrypt.checkpw(data.password.encode(), user.hashed_password.encode()):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    return {"message": "Login exitoso", "name": user.name, "email": user.email, "balance": user.balance}

@app.get("/balance/{email}")
def get_balance(email: EmailStr, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"balance": user.balance}

@app.get("/transactions/{email}")
def get_transactions(email: EmailStr, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return [
        {
            "type": t.type,
            "amount": t.amount,
            "description": t.description,
            "final_balance": t.final_balance
        }
        for t in user.transactions
    ]

@app.post("/add")
def add_money(data: AddMoneyData, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user.balance += data.amount
    t = Transaction(user_id=user.id, type="add", amount=data.amount, description="Añadido a la cuenta", final_balance=user.balance)
    db.add(t)
    db.commit()
    return {"message": "Fondos añadidos", "new_balance": user.balance}

@app.post("/send")
def send_money(data: SendMoneyData, db: Session = Depends(get_db)):
    sender = db.query(User).filter_by(email=data.sender_email).first()
    recipient = db.query(User).filter_by(email=data.recipient_email).first()
    if not sender or not recipient:
        raise HTTPException(status_code=404, detail="Usuario(s) no encontrado(s)")
    if sender.balance < data.amount:
        raise HTTPException(status_code=400, detail="Saldo insuficiente")

    sender.balance -= data.amount
    recipient.balance += data.amount

    db.add(Transaction(user_id=sender.id, type="send", amount=data.amount, description=f"a {data.recipient_email}: {data.note}", final_balance=sender.balance))
    db.add(Transaction(user_id=recipient.id, type="receive", amount=data.amount, description=f"de {data.sender_email}: {data.note}", final_balance=recipient.balance))
    db.commit()
    return {"message": "Transferencia realizada", "new_balance": sender.balance}

