FROM python:3.11-slim-bookworm

ARG MODEL_URL=https://tsd-pub-static.s3.amazonaws.com/ml-models/model-weights-5a6b1be1fa.onnx
ARG MODEL_SHA256=0a6ebd8e30dbf6a450c50f9c0a5406f04ba7eb1c99fd5996e888c78bb383b9aa

RUN apt-get update \
    && apt-get install --no-install-recommends --assume-yes ca-certificates curl jq libglib2.0-0 libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
COPY model ./model
COPY run.sh /run.sh
RUN pip install --no-cache-dir . \
    && curl --fail --location --output /app/model/model-weights.onnx "$MODEL_URL" \
    && echo "$MODEL_SHA256  /app/model/model-weights.onnx" | sha256sum --check --strict \
    && chmod +x /run.sh

EXPOSE 8099
CMD ["/run.sh"]
