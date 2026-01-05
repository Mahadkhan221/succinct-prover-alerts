import grpc
import logging
from typing import Any, Dict, List, Optional

import proto.network_pb2_grpc as network_pb2_grpc
import proto.types_pb2 as types_pb2


def _hex_to_bytes(addr: str) -> bytes:
    a = addr.strip()
    if a.startswith("0x") or a.startswith("0X"):
        a = a[2:]
    return bytes.fromhex(a)


def _proof_request_to_dict(r: types_pb2.ProofRequest) -> Dict[str, Any]:
    return {
        "request_id": r.request_id.hex(),
        "fulfillment_status": int(r.fulfillment_status),
        "execution_status": int(r.execution_status),
        "requester": r.requester.hex(),
        "fulfiller": (r.fulfiller.hex() if getattr(r, "fulfiller", None) else None),
        "created_at": getattr(r, "created_at", None),
        "updated_at": getattr(r, "updated_at", None),
        # keep useful URIs if present
        "program_uri": getattr(r, "program_uri", None),
        "stdin_uri": getattr(r, "stdin_uri", None),
        "program_public_uri": getattr(r, "program_public_uri", None),
        "stdin_public_uri": getattr(r, "stdin_public_uri", None),
    }


def fetch_latest_assigned_or_fulfilled(endpoint: str, prover_address: str) -> Optional[Dict[str, Any]]:
    host = endpoint.replace("https://", "").replace("http://", "").rstrip("/")
    if ":" not in host:
        host = f"{host}:443"

    channel = grpc.secure_channel(host, grpc.ssl_channel_credentials())
    stub = network_pb2_grpc.ProverNetworkStub(channel)

    prover_bytes = _hex_to_bytes(prover_address)

    def query(status_enum: int, status_name: str) -> Optional[Dict[str, Any]]:
        req = types_pb2.GetFilteredProofRequestsRequest(
            fulfillment_status=status_enum,
            fulfiller=prover_bytes,
            limit=1,
            page=1,
        )
        resp = stub.GetFilteredProofRequests(req, timeout=20)
        if not resp.requests:
            return None

        pr = resp.requests[0]
        details = _proof_request_to_dict(pr)

        return {
            "status": status_name,
            "id": pr.request_id.hex(),
            "details": details,
        }

    out = query(types_pb2.FulfillmentStatus.ASSIGNED, "ASSIGNED")
    if out:
        return out

    out = query(types_pb2.FulfillmentStatus.FULFILLED, "FULFILLED")
    if out:
        return out

    return None
