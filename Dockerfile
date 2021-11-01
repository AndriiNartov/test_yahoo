FROM python:3

WORKDIR /usr/src/app

COPY req.txt .
COPY entrypoint.sh .

RUN python3 -m venv venv
RUN . venv/bin/activate
RUN pip install -r req.txt
RUN chmod +x entrypoint.sh

COPY . .

ENTRYPOINT ["bash", "/usr/src/app/entrypoint.sh"]