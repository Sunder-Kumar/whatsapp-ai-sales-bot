from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    language = Column(String, default="roman_urdu") # roman_urdu / english / mixed
    created_at = Column(DateTime, default=datetime.utcnow)

    conversations = relationship("Conversation", back_populates="customer")
    messages = relationship("Message", back_populates="customer")
    orders = relationship("Order", back_populates="customer")

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, ForeignKey("customers.phone"), nullable=False)
    stage = Column(String, default="start") # start, assessment, recommendation, objection, payment_pending, delivered
    selected_package = Column(String, nullable=True)
    selected_duration = Column(String, nullable=True)
    country = Column(String, nullable=True)
    device_type = Column(String, nullable=True)
    ai_paused = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = relationship("Customer", back_populates="conversations")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, ForeignKey("customers.phone"), nullable=False)
    role = Column(String, nullable=False) # customer / ai
    content = Column(Text, nullable=False)
    message_type = Column(String, default="text") # text / voice / image
    media_path = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # For RAG and training
    is_training_example = Column(Boolean, default=False)
    training_label = Column(String, nullable=True) # good_example / bad_example

    customer = relationship("Customer", back_populates="messages")

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, ForeignKey("customers.phone"), nullable=False)
    package_name = Column(String, nullable=False)
    duration = Column(String, nullable=False)
    amount_paid = Column(Float, nullable=False)
    payment_method = Column(String, nullable=False)
    payment_screenshot_path = Column(String, nullable=True)
    status = Column(String, default="pending") # pending / verified / delivered / refunded
    created_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime, nullable=True)

    customer = relationship("Customer", back_populates="orders")

class PaymentEvent(Base):
    __tablename__ = "payment_events"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, nullable=False)
    screenshot_path = Column(String, nullable=False)
    ocr_text = Column(Text, nullable=True)
    verified = Column(Boolean, default=False)
    verified_at = Column(DateTime, nullable=True)
    rejection_reason = Column(String, nullable=True)

class Credential(Base):
    __tablename__ = "credentials"

    id = Column(Integer, primary_key=True, index=True)
    package_name = Column(String, nullable=False)
    login_email = Column(String, nullable=False)
    login_password = Column(String, nullable=False)
    profile_pin = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    assigned_to = Column(String, nullable=True) # phone number
    assigned_at = Column(DateTime, nullable=True)
