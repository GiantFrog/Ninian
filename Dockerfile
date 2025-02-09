FROM python:3.12
WORKDIR /bot
COPY requirements.txt /bot/
RUN pip install -r requirements.txt
RUN echo "It's $(date), and we don't want to cache any steps below this!"
COPY . /bot
CMD ["python", "main.py"]
