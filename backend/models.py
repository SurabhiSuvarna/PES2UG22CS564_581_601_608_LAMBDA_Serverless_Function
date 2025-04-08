from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
engine = create_engine('sqlite:///functions.db')  # SQLite for simplicity

class Function(Base):
    __tablename__ = 'functions'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    language = Column(String(10))  # 'python' or 'javascript'
    code = Column(Text)            # User's function code
    timeout = Column(Integer)      # Timeout in seconds

Base.metadata.create_all(engine)  # Create tables