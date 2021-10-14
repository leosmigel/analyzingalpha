import enum
import numpy as np
import pandas as pd

from sqlalchemy import BigInteger, Boolean, Column, \
                       Date, DateTime, Enum, Float, ForeignKey, Integer, \
                       String, UniqueConstraint, and_, func
from sqlalchemy.orm import relationship
from psql import Base, db, session

class Market(enum.Enum):
    crypto = 'crypto'
    stock = 'stock'
    forex = 'forex'
    futures = 'futures'


class Symbol(Base):
    __tablename__ = 'symbol'
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    market = Column(Enum(Market), nullable=False)
    active = Column(Boolean, nullable=False)


class MinuteBar(Base):
    __tablename__ = 'minute_bar'
    id = Column(BigInteger, primary_key=True)
    date = Column(DateTime, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    symbol_id = Column(Integer,
                      ForeignKey('symbol.id',
                                 onupdate="CASCADE",
                                 ondelete="CASCADE"),
                      nullable=False)
    symbol = relationship('Symbol', backref='minute_bars')
    UniqueConstraint(symbol_id, date)


def create():
    Base.metadata.create_all(db)

create()
