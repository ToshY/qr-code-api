ARG PYTHON_IMAGE_VERSION=3.13

FROM python:${PYTHON_IMAGE_VERSION}-alpine AS builder

LABEL maintainer="ToshY (github.com/ToshY)"

ENV PYTHONUNBUFFERED=1

WORKDIR /build

COPY . .

RUN pip install --prefix=/install -r requirements.txt \
    && pip install --prefix=/install .

FROM python:${PYTHON_IMAGE_VERSION}-alpine AS prod

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=builder /install /usr/local
COPY --from=builder /build/site /app/site

RUN mkdir -p ./output

EXPOSE 8000

ENTRYPOINT ["qr"]
CMD ["--help"]

FROM python:${PYTHON_IMAGE_VERSION}-alpine AS dev

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt requirements.dev.txt ./

RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r requirements.dev.txt

EXPOSE 8000
