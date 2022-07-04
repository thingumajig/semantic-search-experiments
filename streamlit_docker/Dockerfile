FROM python:3.8.0

WORKDIR /code 

COPY ./pyproject.toml /code/pyproject.toml

RUN pip install poetry
RUN poetry config virtualenvs.create false \
  && poetry install --no-dev --no-interaction --no-ansi
RUN pip install streamlit
COPY ./pages/ /code/pages/
COPY /Semantic_search.py /code/Semantic_search.py
COPY /settings.json /code/settings.json
CMD ["streamlit", "run", "Semantic_search.py"]