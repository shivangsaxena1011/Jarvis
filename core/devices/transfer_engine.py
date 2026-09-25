"""Authenticated Chunked File Transfer Engine for Phase 18.

Implements resumable file transfers across devices with 64KB chunking, progress tracking,
pause/resume mechanics, and strict SHA-256 cryptographic integrity verification.
"""

from __future__ import annotations

import hashlib
import logging
import math
import os
import threading
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

from core.devices.models import (
    DeviceTrustState,
    FileTransferSession,
    TransferStatus,
)
from core.devices.trust_store import TrustStore

logger = logging.getLogger("shivani.devices.transfer")


class TransferEngine:
    """Orchestrates chunked, authenticated, and resumable file transfers between mesh nodes."""

    def __init__(self, trust_store: TrustStore, temp_dir: str = "data/transfers_temp"):
        self.trust_store = trust_store
        self.temp_dir = temp_dir
        self._lock = threading.RLock()
        self._active_buffers: Dict[str, Dict[int, bytes]] = {}
        os.makedirs(self.temp_dir, exist_ok=True)

    def initiate_transfer(
        self,
        source_device_id: str,
        target_device_id: str,
        file_path: str,
        custom_filename: Optional[str] = None,
        chunk_size: int = 64 * 1024,
    ) -> FileTransferSession:
        """Initiate an outbound file transfer from local storage."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Check target device
        target_dev = self.trust_store.get_device(target_device_id)
        if not target_dev or target_dev.trust_state != DeviceTrustState.TRUSTED:
            raise PermissionError(f"Target device '{target_device_id}' is not in TRUSTED state.")

        file_size = os.path.getsize(file_path)
        filename = custom_filename or os.path.basename(file_path)

        # Compute full-file SHA-256 checksum
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(128 * 1024):
                hasher.update(chunk)
        expected_sha256 = hasher.hexdigest()

        total_chunks = math.ceil(file_size / chunk_size) if file_size > 0 else 1
        session_id = f"tx-{uuid.uuid4().hex[:12]}"

        session = FileTransferSession(
            session_id=session_id,
            filename=filename,
            source_device_id=source_device_id,
            target_device_id=target_device_id,
            file_size=file_size,
            bytes_transferred=0,
            chunk_size=chunk_size,
            total_chunks=total_chunks,
            chunks_received=[],
            sha256_checksum=expected_sha256,
            status=TransferStatus.INITIATED,
            local_path=os.path.abspath(file_path),
            created_at=time.time(),
            updated_at=time.time(),
        )

        self.trust_store.save_file_transfer(session)
        logger.info(
            f"Initiated file transfer session '{session_id}' for '{filename}' "
            f"({file_size} bytes, {total_chunks} chunks) -> {target_device_id}."
        )
        return session

    def get_chunk(self, session_id: str, chunk_index: int) -> Tuple[bytes, str]:
        """Read a specific chunk from the source file with its individual SHA-256 digest."""
        session = self.trust_store.get_file_transfer(session_id)
        if not session or not session.local_path:
            raise ValueError(f"Transfer session '{session_id}' not found or local path missing.")

        if not os.path.exists(session.local_path):
            raise FileNotFoundError(f"Local file at '{session.local_path}' no longer exists.")

        offset = chunk_index * session.chunk_size
        with open(session.local_path, "rb") as f:
            f.seek(offset)
            data = f.read(session.chunk_size)

        chunk_hash = hashlib.sha256(data).hexdigest()
        return data, chunk_hash

    def receive_chunk(
        self,
        session_id: str,
        chunk_index: int,
        data: bytes,
        expected_chunk_hash: Optional[str] = None,
    ) -> FileTransferSession:
        """Receive and store an incoming chunk, updating progress and session state."""
        with self._lock:
            session = self.trust_store.get_file_transfer(session_id)
            if not session:
                raise ValueError(f"Transfer session '{session_id}' not found.")

            if session.status in (TransferStatus.CANCELLED, TransferStatus.FAILED):
                raise RuntimeError(f"Cannot accept chunk for session in {session.status.value} status.")

            # Validate individual chunk integrity if hash provided
            if expected_chunk_hash:
                actual_hash = hashlib.sha256(data).hexdigest()
                if actual_hash != expected_chunk_hash:
                    raise ValueError(f"Chunk {chunk_index} hash mismatch! Data corrupted in transit.")

            if session_id not in self._active_buffers:
                self._active_buffers[session_id] = {}

            if chunk_index not in self._active_buffers[session_id]:
                self._active_buffers[session_id][chunk_index] = data
                session.chunks_received.append(chunk_index)
                session.bytes_transferred += len(data)
                session.status = TransferStatus.IN_PROGRESS
                session.updated_at = time.time()
                self.trust_store.save_file_transfer(session)

            return session

    def finalize_transfer(
        self,
        session_id: str,
        destination_dir: str,
    ) -> Tuple[FileTransferSession, str]:
        """Assemble received chunks, verify full-file SHA-256, and save to target directory."""
        with self._lock:
            session = self.trust_store.get_file_transfer(session_id)
            if not session:
                raise ValueError(f"Transfer session '{session_id}' not found.")

            buffer = self._active_buffers.get(session_id, {})
            # Verify all chunks were received
            missing_chunks = [i for i in range(session.total_chunks) if i not in buffer]
            if missing_chunks and session.file_size > 0:
                raise ValueError(f"Cannot finalize: missing chunks {missing_chunks[:5]} (total missing: {len(missing_chunks)}).")

            os.makedirs(destination_dir, exist_ok=True)
            output_path = os.path.join(destination_dir, session.filename)

            # Assemble file and calculate final SHA-256
            hasher = hashlib.sha256()
            with open(output_path, "wb") as out_f:
                for i in range(session.total_chunks):
                    chunk_bytes = buffer.get(i, b"")
                    hasher.update(chunk_bytes)
                    out_f.write(chunk_bytes)

            actual_sha256 = hasher.hexdigest()
            if session.sha256_checksum and actual_sha256 != session.sha256_checksum:
                # Integrity failure: delete corrupted file
                if os.path.exists(output_path):
                    os.remove(output_path)
                session.status = TransferStatus.FAILED
                session.error_message = (
                    f"Integrity check failed: expected {session.sha256_checksum}, got {actual_sha256}."
                )
                self.trust_store.save_file_transfer(session)
                raise ValueError(session.error_message)

            # Successfully verified
            session.status = TransferStatus.COMPLETED
            session.local_path = os.path.abspath(output_path)
            session.updated_at = time.time()
            self.trust_store.save_file_transfer(session)

            # Cleanup memory buffer
            self._active_buffers.pop(session_id, None)

            logger.info(f"File transfer '{session_id}' completed and verified: {output_path}")
            return session, output_path

    def pause_transfer(self, session_id: str) -> FileTransferSession:
        """Pause an ongoing transfer session."""
        session = self.trust_store.get_file_transfer(session_id)
        if not session:
            raise ValueError(f"Transfer session '{session_id}' not found.")
        session.status = TransferStatus.PAUSED
        self.trust_store.save_file_transfer(session)
        logger.info(f"Paused transfer session '{session_id}'.")
        return session

    def resume_transfer(self, session_id: str) -> FileTransferSession:
        """Resume a paused transfer session."""
        session = self.trust_store.get_file_transfer(session_id)
        if not session:
            raise ValueError(f"Transfer session '{session_id}' not found.")
        session.status = TransferStatus.IN_PROGRESS
        self.trust_store.save_file_transfer(session)
        logger.info(f"Resumed transfer session '{session_id}'.")
        return session

    def cancel_transfer(self, session_id: str) -> FileTransferSession:
        """Cancel an in-progress transfer and clear temp buffers."""
        with self._lock:
            session = self.trust_store.get_file_transfer(session_id)
            if not session:
                raise ValueError(f"Transfer session '{session_id}' not found.")
            session.status = TransferStatus.CANCELLED
            self._active_buffers.pop(session_id, None)
            self.trust_store.save_file_transfer(session)
            logger.info(f"Cancelled transfer session '{session_id}'.")
            return session
