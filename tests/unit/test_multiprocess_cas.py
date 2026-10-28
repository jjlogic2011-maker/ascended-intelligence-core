import multiprocessing
import time
import pytest
from security.pending_store import PendingStore

def attempt_claim(db_path, pending_id, result_queue):
    """Worker process that tries to claim a pending request."""
    store = PendingStore(db_path)
    # Simulate network latency to force a race condition
    time.sleep(0.1) 
    record = store.claim_status(pending_id, "pending_approval", "processing")
    
    if record is not None:
        result_queue.put("SUCCESS")
    else:
        result_queue.put("FAILED")

def test_multiprocess_cas_only_one_wins(tmp_path):
    db_path = str(tmp_path / "cas_test.sqlite3")
    store = PendingStore(db_path)
    
    # Create a pending record
    pending_id = "req-race-1"
    record = {
        "pending_id": pending_id,
        "status": "pending_approval",
        "action": "deploy",
        "agent_id": "agent-1",
        "requester_id": "user-1",
        "resource": "staging",
        "arguments": {}
    }
    store.put(pending_id, record)

    # Spin up two separate processes to fight for the claim
    result_queue = multiprocessing.Queue()
    p1 = multiprocessing.Process(target=attempt_claim, args=(db_path, pending_id, result_queue))
    p2 = multiprocessing.Process(target=attempt_claim, args=(db_path, pending_id, result_queue))

    p1.start()
    p2.start()
    p1.join()
    p2.join()

    # Collect results
    results = [result_queue.get(), result_queue.get()]
    
    # Assert exactly ONE process succeeded
    assert results.count("SUCCESS") == 1
    assert results.count("FAILED") == 1
