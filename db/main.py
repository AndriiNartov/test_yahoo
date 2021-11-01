from fastapi import Depends, FastAPI, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from . import models
from .database import engine, SessionLocal
from services import get_result_for_client, get_result_for_company_test_list, get_company_not_found_response, \
    get_response_from_yahoo, create_company_and_records, ProcessingByDB, TEST_COMPANIES

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

templates = Jinja2Templates(directory="templates")


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/api/{ticker}/")
async def make_client_api_response(ticker: str, db: Session = Depends(get_db)):
    db_proc = ProcessingByDB(ticker, db)
    if not db_proc.check_if_company_exists():
        response = get_response_from_yahoo(ticker)
        if response.status_code == 404:
            return get_company_not_found_response(ticker)
        create_company_and_records(db_proc, response.content)
    else:
        db_proc.check_if_db_needs_update()
    return get_result_for_client(db, ticker)


@app.get('/', include_in_schema=False)
async def index(request: Request):
    context = {
        'request': request,
        'companies': TEST_COMPANIES
    }
    return templates.TemplateResponse('index.html', context)


@app.get('/test/{ticker}/', include_in_schema=False)
async def test_app_for_companies_list(ticker: str, request: Request, db: Session = Depends(get_db)):
    db_proc = ProcessingByDB(ticker, db)
    context = dict()
    if not db_proc.check_if_company_exists():
        response = get_response_from_yahoo(ticker)
        create_company_and_records(db_proc, response.content)
        context['message'] = f"Data for company '{ticker}' were successfully saved to DB!"
    db_proc.check_if_db_needs_update()
    records = get_result_for_company_test_list(db, ticker)
    context['request'] = request
    context['company'] = ticker
    context['records'] = records
    return templates.TemplateResponse('test.html', context)
