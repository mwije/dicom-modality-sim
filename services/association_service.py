# Copyright (c) 2026 Malinda Wijeratne
# SPDX-License-Identifier: MIT

from pynetdicom import AE
import socket
from dataclasses import dataclass
from enum import Enum, auto

class AssocFailure(Enum):
    NONE = auto()
    TCP_FAILED = auto()
    REJECTED = auto()
    ERROR = auto()

@dataclass
class AssociationResult:
    assoc: object | None
    failure: AssocFailure
    detail: str | None = None

    def ok(self) -> bool:
        return self.assoc is not None

    def explain(self, context: str) -> str:
        if self.failure == AssocFailure.TCP_FAILED:
            return f"✗ {context}: TCP unreachable"
        if self.failure == AssocFailure.REJECTED:
            return f"✗ {context}: Association rejected ({self.detail})"
        if self.failure == AssocFailure.ERROR:
            return f"✗ {context}: {self.detail}"
        return ""
    
class DicomAssociationFactory:
    def __init__(self, config):
        self.config = config
    
    def tcp_probe(self, host: str, port: int, timeout: float = 3.0) -> bool:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except OSError:
            return False

    def create_assoc(
        self,
        requested_contexts,
        server_host,
        server_port,
        client_ae_title,
        server_ae_title,
        tcp_timeout=3
        ):

        if not self.tcp_probe(server_host, server_port):
            return AssociationResult(
                assoc=None,
                failure=AssocFailure.TCP_FAILED
            )

        ae = AE(ae_title=client_ae_title)
        for cx in requested_contexts:
            ae.add_requested_context(cx)

        try:
            assoc = ae.associate(
                server_host,
                server_port,
                ae_title=server_ae_title
            )

            if assoc.is_established:
                return AssociationResult(assoc=assoc, failure=AssocFailure.NONE)

            return AssociationResult(
                assoc=None,
                failure=AssocFailure.REJECTED,
                detail="Association could not be established"
            )

        except Exception as e:
            return AssociationResult(
                assoc=None,
                failure=AssocFailure.ERROR,
                detail=str(e)
            )
