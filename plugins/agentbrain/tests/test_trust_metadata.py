#!/usr/bin/env python3
"""
Unit tests for Trust Metadata, Domain Tagging, and Retrieval Modes
"""

import os
import sys
from pathlib import Path

# Add scripts to path
plugin_root = Path(__file__).parent.parent
sys.path.insert(0, str(plugin_root / "scripts"))

from providers.base import Memory, TrustMetadata


def test_trust_metadata():
    """Test TrustMetadata dataclass."""
    print("Testing TrustMetadata...")

    # Test basic creation
    trust = TrustMetadata(
        source_type="adr",
        approval_status="approved",
        confidence=0.9,
        owner="platform-team"
    )

    assert trust.source_type == "adr"
    assert trust.approval_status == "approved"
    assert trust.confidence == 0.9
    assert trust.owner == "platform-team"
    print("  [OK] Basic creation works")

    # Test is_trusted()
    assert trust.is_trusted() == True
    print("  [OK] is_trusted() returns True for approved+high confidence")

    trust_draft = TrustMetadata(
        source_type="manual",
        approval_status="draft",
        confidence=0.5
    )
    assert trust_draft.is_trusted() == False
    print("  [OK] is_trusted() returns False for draft+low confidence")

    # Test is_stale()
    import time
    trust_old = TrustMetadata(
        source_type="manual",
        last_validated=int(time.time()) - 100000000  # Very old
    )
    assert trust_old.is_stale() == True
    print("  [OK] is_stale() returns True for old timestamp")

    trust_fresh = TrustMetadata(
        source_type="manual",
        last_validated=int(time.time())
    )
    assert trust_fresh.is_stale() == False
    print("  [OK] is_stale() returns False for fresh timestamp")

    print("PASS: TrustMetadata tests\n")
    return True


def test_memory_with_trust():
    """Test Memory with trust metadata and domain tags."""
    print("Testing Memory with TrustMetadata...")

    # Test with TrustMetadata object
    trust = TrustMetadata(
        source_type="incident",
        approval_status="draft",
        confidence=0.5
    )

    memory = Memory(
        file_path="test.md",
        scope="project:test",
        type="project",
        content="Test content",
        trust=trust,
        domain_tags=["RAP", "CDS", "OData"]
    )

    assert memory.trust.source_type == "incident"
    assert memory.trust.approval_status == "draft"
    assert memory.domain_tags == ["RAP", "CDS", "OData"]
    print("  [OK] Memory with TrustMetadata and domain_tags works")

    # Test with dict trust (should auto-convert)
    memory2 = Memory(
        file_path="test2.md",
        scope="user:test",
        type="user",
        content="Test content 2",
        trust={
            "source_type": "manual",
            "approval_status": "approved",
            "confidence": 0.8
        }
    )

    assert isinstance(memory2.trust, TrustMetadata)
    assert memory2.trust.approval_status == "approved"
    print("  [OK] Memory auto-converts dict to TrustMetadata")

    print("PASS: Memory with TrustMetadata tests\n")
    return True


def test_retrieval_modes():
    """Test retrieval mode configurations."""
    print("Testing Retrieval Modes...")

    from query import RETRIEVAL_MODES

    # Check all modes are defined
    expected_modes = [
        "similar_incidents",
        "conventions",
        "approved_standards",
        "example_solutions",
        "architecture_decisions"
    ]

    for mode in expected_modes:
        assert mode in RETRIEVAL_MODES, f"Missing mode: {mode}"
        config = RETRIEVAL_MODES[mode]
        assert "filter_source_types" in config or "require_approval" in config
    print(f"  [OK] All {len(expected_modes)} retrieval modes defined")

    # Check specific mode configs
    incident_mode = RETRIEVAL_MODES["similar_incidents"]
    assert incident_mode["filter_source_types"] == ["incident"]
    print("  [OK] similar_incidents filters by incident source")

    standards_mode = RETRIEVAL_MODES["approved_standards"]
    assert standards_mode["require_approval"] == True
    assert standards_mode["min_confidence"] >= 0.8
    print("  [OK] approved_standards requires approval and high confidence")

    print("PASS: Retrieval Modes tests\n")
    return True


def test_query_function_signature():
    """Test that query_memories accepts new parameters."""
    print("Testing query_memories signature...")

    import inspect
    from query import query_memories

    sig = inspect.signature(query_memories)
    params = list(sig.parameters.keys())

    assert "retrieval_mode" in params, "Missing retrieval_mode parameter"
    assert "domain_tags" in params, "Missing domain_tags parameter"
    print("  [OK] query_memories has retrieval_mode parameter")
    print("  [OK] query_memories has domain_tags parameter")

    print("PASS: query_memories signature tests\n")
    return True


def test_upsert_function_signature():
    """Test that upsert_memory accepts new parameters."""
    print("Testing upsert_memory signature...")

    import inspect
    from upsert import upsert_memory

    sig = inspect.signature(upsert_memory)
    params = list(sig.parameters.keys())

    assert "domain_tags" in params, "Missing domain_tags parameter"
    assert "trust_metadata" in params, "Missing trust_metadata parameter"
    print("  [OK] upsert_memory has domain_tags parameter")
    print("  [OK] upsert_memory has trust_metadata parameter")

    print("PASS: upsert_memory signature tests\n")
    return True


def main():
    """Run all unit tests."""
    print("=" * 50)
    print("AgentBrain Trust & Tagging Unit Tests")
    print("=" * 50)
    print()

    results = []

    try:
        results.append(("TrustMetadata", test_trust_metadata()))
    except Exception as e:
        print(f"FAIL: TrustMetadata - {e}\n")
        results.append(("TrustMetadata", False))

    try:
        results.append(("Memory with Trust", test_memory_with_trust()))
    except Exception as e:
        print(f"FAIL: Memory with Trust - {e}\n")
        results.append(("Memory with Trust", False))

    try:
        results.append(("Retrieval Modes", test_retrieval_modes()))
    except Exception as e:
        print(f"FAIL: Retrieval Modes - {e}\n")
        results.append(("Retrieval Modes", False))

    try:
        results.append(("query_memories signature", test_query_function_signature()))
    except Exception as e:
        print(f"FAIL: query_memories signature - {e}\n")
        results.append(("query_memories signature", False))

    try:
        results.append(("upsert_memory signature", test_upsert_function_signature()))
    except Exception as e:
        print(f"FAIL: upsert_memory signature - {e}\n")
        results.append(("upsert_memory signature", False))

    # Summary
    print("=" * 50)
    print("SUMMARY")
    print("=" * 50)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {name}")

    print(f"\n{passed}/{total} tests passed")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
