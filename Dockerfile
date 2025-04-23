FROM pdf2htmlex/pdf2htmlex:0.18.8.rc2-master-20200820-ubuntu-20.04-x86_64

RUN apt update && apt install -y curl
RUN apt upgrade -y

ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:/server/.venv/bin/:$PATH"

ADD . /server
WORKDIR /server
RUN uv sync --frozen
RUN mkdir pdf

EXPOSE 8000
ENTRYPOINT ["uvicorn", "--host", "0.0.0.0", "--port", "8000", "--app-dir=src", "pdf2htmlserver:app"]
