from sqlalchemy import BigInteger, Date, Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base


class Company(Base):
    __tablename__ = 'companies'
    id = Column(Integer, primary_key=True, unique=True, index=True)
    ticker = Column(String, unique=True)
    records = relationship('TradingDayInfoRecord', back_populates='company')


class TradingDayInfoRecord(Base):
    __tablename__ = 'records'
    id = Column(Integer, primary_key=True, unique=True, index=True)
    date = Column(Date)
    open = Column(Float(asdecimal=True, decimal_return_scale=6))
    high = Column(Float(asdecimal=True, decimal_return_scale=6))
    low = Column(Float(asdecimal=True, decimal_return_scale=6))
    close = Column(Float(asdecimal=True, decimal_return_scale=6))
    adj_close = Column(Float(asdecimal=True, decimal_return_scale=6))
    volume = Column(BigInteger)
    company_id = Column(Integer, ForeignKey('companies.id'))
    company = relationship('Company', back_populates='records')

    def __str__(self):
        return f'{self.date}, {self.open}, {self.high}, {self.low}, {self.close}, {self.adj_close}, {self.volume}'
