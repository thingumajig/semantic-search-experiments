FROM python:3.8.0

WORKDIR /code 

COPY ./pyproject.toml /code/pyproject.toml
COPY ./Трудовой_кодекс.xlsx /code/Трудовой_кодекс.xlsx
COPY ./search_imgs.zip /code/search_imgs.zip

RUN pip install poetry
RUN poetry config virtualenvs.create false \
  && poetry install --no-dev --no-interaction --no-ansi

COPY ./app/ /code/app/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
