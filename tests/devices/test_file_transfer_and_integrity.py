"""Tests for Phase 18: Authenticated Chunked File Transfer & Cryptographic Integrity Verification."""

import os
import tempfile
import pytest

from core.devices.models import (
    Device,
    DevicePlatform,
    DeviceTrustState,
    TransferStatus,
)
from core.devices.transfer_engine import TransferEngine
from core.devices.trust_store import TrustStore


@pytest.fixture
def transfer_setup():
    temp_dir = tempfile.mkdtemp(prefix="transfer_test_")
    db_path = os.path.join(temp_dir, "transfer.db")
    store = TrustStore(db_path=db_path)

    pc = Device(
        device_id="pc-src",
        display_name="Source PC",
        platform=DevicePlatform.WINDOWS.value,
        trust_state=DeviceTrustState.TRUSTED,
    )
    store.upsert_device(pc)

    phone = Device(
        device_id="phone-dst",
        display_name="Target Phone",
        platform=DevicePlatform.ANDROID.value,
        trust_state=DeviceTrustState.TRUSTED,
    )
    store.upsert_device(phone)

    # Create dummy sample file (150 KB)
    sample_file = os.path.join(temp_dir, "report.pdf")
    payload = b"SHIVANI_PAYLOAD_CHUNK_DATA_" * 5000
    with open(sample_file, "wb") as f:
        f.write(payload)

    yield store, pc, phone, temp_dir, sample_file, payload

    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_chunked_transfer_success(transfer_setup):
    store, pc, phone, temp_dir, sample_file, original_bytes = transfer_setup
    engine = TransferEngine(trust_store=store, temp_dir=temp_dir)

    # Initiate
    session = engine.initiate_transfer(
        source_device_id="pc-src",
        target_device_id="phone-dst",
        file_path=sample_file,
        chunk_size=32 * 1024,  # 32 KB
    )

    assert session.status == TransferStatus.INITIATED
    assert session.total_chunks > 1
    assert session.sha256_checksum != ""

    # Transfer all chunks
    for i in range(session.total_chunks):
        chunk_data, chunk_hash = engine.get_chunk(session.session_id, i)
        updated = engine.receive_chunk(session.session_id, i, chunk_data, expected_chunk_hash=chunk_hash)
        assert updated.status == TransferStatus.IN_PROGRESS

    # Finalize and verify
    dest_dir = os.path.join(temp_dir, "downloads")
    final_session, out_path = engine.finalize_transfer(session.session_id, dest_dir)

    assert final_session.status == TransferStatus.COMPLETED
    assert os.path.exists(out_path)

    with open(out_path, "rb") as f:
        assembled_data = f.read()
    assert assembled_data == original_bytes


def test_chunk_corruption_fails_integrity(transfer_setup):
    store, pc, phone, temp_dir, sample_file, _ = transfer_setup
    engine = TransferEngine(trust_store=store, temp_dir=temp_dir)

    session = engine.initiate_transfer(
        source_device_id="pc-src",
        target_device_id="phone-dst",
        file_path=sample_file,
    )

    # Corrupt chunk 0 hash check
    chunk_data, chunk_hash = engine.get_chunk(session.session_id, 0)
    corrupted_data = b"TAMPERED" + chunk_data[8:]

    with pytest.raises(ValueError, match="hash mismatch"):
        engine.receive_chunk(session.session_id, 0, corrupted_data, expected_chunk_hash=chunk_hash)


def test_pause_resume_and_cancellation(transfer_setup):
    store, pc, phone, temp_dir, sample_file, _ = transfer_setup
    engine = TransferEngine(trust_store=store, temp_dir=temp_dir)

    session = engine.initiate_transfer(
        source_device_id="pc-src",
        target_device_id="phone-dst",
        file_path=sample_file,
    )

    paused = engine.pause_transfer(session.session_id)
    assert paused.status == TransferStatus.PAUSED

    resumed = engine.resume_transfer(session.session_id)
    assert resumed.status == TransferStatus.IN_PROGRESS

    cancelled = engine.cancel_transfer(session.session_id)
    assert cancelled.status == TransferStatus.CANCELLED
