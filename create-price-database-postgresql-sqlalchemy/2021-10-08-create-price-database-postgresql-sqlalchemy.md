## How to Create a Price Database in PostgreSQL Using SQLAlchemy

### Links
- [How to Create a Price Database Using SQLAlchemy Blog Post](https://analyzingalpha.com/price-database-sqlalchemy)
- [How to Create a Price Database YouTube Video](https://youtu.be/dfyB_ZVQ2jE)

### 1. Get Imports


```python
import enum
import numpy as np
import pandas as pd

from sqlalchemy import BigInteger, Boolean, Column, \
                       Date, DateTime, Enum, Float, ForeignKey, Integer, \
                       String, UniqueConstraint, and_, func
from sqlalchemy.orm import relationship
from psql import Base, db, session
```

Let's create a new class that inherits from enum to create constants that we can enumerate over for each of the markets that we'll analyze.

### 2. Create Market Class


```python
class Market(enum.Enum):
    crypto = 'crypto'
    stock = 'stock'
    forex = 'forex'
    futures = 'futures'
   
```

### 3. Create SQLAlchemy Classes & Tables

We'll create two tables. The first is the symbol and minute_bar tables, which have a parent/child relationship. For each table, we create a class an inherit from Base, which let's SQLAlchemy know this is an SQLAlchemy class/table. 


```python
class Symbol(Base):
    __tablename__ = 'symbol'
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    market = Column(Enum(Market), nullable=False)
    active = Column(Boolean, nullable=False)
```

We'll create a relationship on the minute_bar table that utilizes `backref`. SQLAlchemy understands to look at the classes and identify the type of relationship that exists. In our case, it's a one-to-many relationship. Additionally, we create `UniqueConstraint` on the symbol_id and date -- in other words, we should only have one bar per date per symbol.


```python
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
    symbol = relationship('Symbol', backref='symbol')
    UniqueConstraint(symbol_id, date)
```

### 4. Create Database

With our table classes created, let's create a function that creates our database. We use the Base metadata to create all of our classes that inherit from Base.


```python
def create():
    Base.metadata.create_all(db)
```


```python
create()
```
