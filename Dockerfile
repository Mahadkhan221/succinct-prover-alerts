FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir grpcio grpcio-tools protobuf requests python-dotenv

COPY proto ./proto

# Generate into proto/
RUN python -m grpc_tools.protoc \
  -I proto \
  --python_out=proto \
  --grpc_python_out=proto \
  proto/types.proto proto/network.proto

# Patch imports so proto package imports work
RUN sed -i 's/^import types_pb2 as types__pb2$/from proto import types_pb2 as types__pb2/' /app/proto/network_pb2_grpc.py && \
    sed -i 's/^import types_pb2 as types__pb2$/from proto import types_pb2 as types__pb2/' /app/proto/network_pb2.py || true

COPY src ./src
COPY .env .env

ENV PYTHONPATH=/app
CMD ["python", "-m", "src.main"]
