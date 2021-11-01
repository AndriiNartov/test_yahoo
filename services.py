import json
import io
import requests
from datetime import datetime, timedelta
from math import floor
from time import mktime, time

import pandas as pd
import redis

from sqlalchemy.orm import Session

from db.database import engine
from db.models import Company, TradingDayInfoRecord
from db.schemas import DayTradingRecord
from config import redis_host
from exceptions import CompanyDoesNotExists, CompanyIsAlreadyExists

TEST_COMPANIES = [
    'PD',
    'AAPL',
    'ZUO',
    'PINS',
    'ZM',
    'DOCU',
    'CLDR',
    'RUN'
]


redis = redis.Redis(host=redis_host)


class RequestToYahoo:
    __base_url = 'https://query1.finance.yahoo.com/v7/finance/download'
    __interval = '1d'
    __events = 'history'
    __user_agent_headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
    }

    def __init__(self, ticker, period1=-631159200, period2=floor(time())):
        self.params = {
            'period1': period1,
            'period2': period2,
            'interval': self.__interval,
            'events': self.__events,
        }
        self.url = f'{self.__base_url}/{ticker}'

    @property
    def headers(self):
        return self.__user_agent_headers

    def make_request(self):
        return requests.get(self.url, headers=self.headers, params=self.params)


class ProcessingByDB:

    def __init__(self, ticker, db):
        self.ticker = ticker.lower()
        self.db = db

    def check_if_company_exists(self):
        return self.db.query(Company).filter_by(ticker=self.ticker).scalar()

    def get_company(self):
        company = self.db.query(Company).filter_by(ticker=self.ticker).first()
        if company:
            return company
        raise CompanyDoesNotExists(f'Company with ticker "{self.ticker}" does not exist')

    def create_new_company(self):
        if not self.check_if_company_exists():
            new_company = Company(ticker=self.ticker)
            self.db.add(new_company)
            self.db.commit()
            self.db.refresh(new_company)
            return new_company
        raise CompanyIsAlreadyExists(f'Company with ticker "{self.ticker}" is already exists')

    def create_new_records(self, content, company_id):
        if not redis.exists(self.ticker):
            redis.lpushx(self.ticker, "")
        pd_content = pd.read_csv(io.StringIO(content.decode('utf-8')))
        pd_content = pd_content[pd_content['Open'].notna()]
        pd_content.rename(
            columns={
                'Date': 'date',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Adj Close': 'adj_close',
                'Volume': 'volume',
            },
            inplace=True
        )
        for row in pd_content.values.tolist():
            new_record = {
                'date': row[0],
                'open': row[1],
                'high': row[2],
                'low': row[3],
                'close': row[4],
                'adj_close': row[5],
                'volume': row[6]
            }
            json_line = DayTradingRecord.json(DayTradingRecord.parse_obj(new_record))
            redis.rpush(self.ticker, json_line)
        pd_content.insert(7, 'company_id', company_id)
        pd_content.to_sql(name='records', if_exists='append', con=engine, index=False)

    def get_records(self):
        return self.db.query(TradingDayInfoRecord).filter_by(company_id=self.get_company().id)

    def update_db(self, last_record, company_id):
        last_record_next_unix_date = mktime((last_record + timedelta(1)).timetuple())
        response = get_response_from_yahoo(self.ticker, period1=floor(last_record_next_unix_date))
        cleaned_str_content = self.clean_str_content_from_existing_records(response.text)
        self.create_new_records(cleaned_str_content.encode(), company_id)

    def check_if_db_needs_update(self):
        if self.check_if_company_exists():
            company = self.get_company()
            if not company.records:
                response = get_response_from_yahoo(self.ticker)
                self.create_new_records(response.content, company.id)
            now = datetime.fromtimestamp(time()).date()
            last_record = self.db.query(TradingDayInfoRecord).filter_by(company_id=company.id).order_by(TradingDayInfoRecord.id.desc()).first()
            if now - last_record.date > timedelta(0):
                self.update_db(last_record.date, company.id)

    def clean_str_content_from_existing_records(self, str_content):
        last_record = self.db.query(TradingDayInfoRecord).filter_by(company_id=self.get_company().id).order_by(
            TradingDayInfoRecord.id.desc()).first()
        last_record_str_date = last_record.date.strftime('%Y-%m-%d')
        new_str_content_list = []
        for line in str_content.split('\n'):
            if not line.split(',')[0] == last_record_str_date:
                new_str_content_list.append(line)
        return '\n'.join(new_str_content_list)

    def sync_redis_with_db(self):
        redis.delete(self.ticker)
        company = self.get_company()
        records = self.db.query(TradingDayInfoRecord).filter_by(company_id=company.id)
        for record in records:
            json_line = DayTradingRecord.json(DayTradingRecord.from_orm(record))
            redis.rpush(self.ticker, json_line)


def get_result_for_client(db: Session, ticker: str):
    company = db.query(Company).filter_by(ticker=ticker).first()
    records_number = db.query(TradingDayInfoRecord).filter_by(company_id=company.id).count()
    records = []
    res_obj = {
        'id': company.id,
        'ticker': ticker,
        'records': records
    }
    if redis.llen(ticker) == records_number:
        for record in redis.lrange(ticker, 0, redis.llen(ticker)):
            records.append(json.loads(record))
    else:
        db_proc = ProcessingByDB(ticker, db)
        for record in db_proc.get_records():
            records.append(DayTradingRecord.from_orm(record))
        db_proc.sync_redis_with_db()
    return res_obj


def get_company_not_found_response(ticker: str):
    res_obj = {
        'ticker': ticker,
        'message': f"There is not data for company '{ticker.upper()}'. Check company ticker spelling."
    }
    return res_obj


def get_result_for_company_test_list(db: Session, ticker: str):
    company = db.query(Company).filter_by(ticker=ticker.lower()).first()
    records = db.query(TradingDayInfoRecord).filter_by(company_id=company.id)
    return records


def get_response_from_yahoo(ticker: str, *args, **kwargs):
    req_to_yahoo = RequestToYahoo(ticker, *args, **kwargs)
    response = req_to_yahoo.make_request()
    return response


def create_company_and_records(db_proc: ProcessingByDB, response_content: bytes):
    new_company = db_proc.create_new_company()
    db_proc.create_new_records(response_content, new_company.id)
