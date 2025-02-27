FROM python:3.12.8-alpine3.20

RUN apk add --no-cache git openssh shadow bash postgresql-dev

WORKDIR /app

CMD ["tail", "-f", "/dev/null"]