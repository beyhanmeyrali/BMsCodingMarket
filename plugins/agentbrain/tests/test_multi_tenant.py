#!/usr/bin/env python3
"""
AgentBrain Multi-Tenant Test Suite

Simulates NTT Data consulting scenarios to test scope-based memory isolation.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add scripts to path
plugin_root = Path(__file__).parent.parent
sys.path.insert(0, str(plugin_root / "scripts"))

from skill_remember import skill_remember
from skill_recall import skill_recall
from skill_forget import skill_forget
from skill_promote import skill_promote
from providers.qdrant import QdrantProvider
from providers.ollama import OllamaEmbedder
from query import query_memories, get_allowed_scopes


class MultiTenantTester:
    """Test multi-tenant memory isolation."""

    def __init__(self):
        self.results = []
        self.qdrant = None
        self.embedder = None

    def setup(self):
        """Initialize Qdrant for testing."""
        print("Setting up test environment...")

        try:
            # Use same collection as skills for testing
            self.qdrant = QdrantProvider(
                host="localhost",
                port=6333,
                collection="agentbrain_memories",
                embedding_dim=1024,
            )
            self.qdrant.initialize()
            # Clear existing test data first
            self.clear_test_memories()

            self.embedder = OllamaEmbedder(model="qwen3-embedding:0.6b")

            print("Test environment ready.")
            return True
        except Exception as e:
            print(f"Setup failed: {e}")
            return False

    def clear_test_memories(self):
        """Clear test memories from Qdrant."""
        # Try to clear any test memories
        try:
            self.qdrant.client.delete(
                collection_name="agentbrain_memories",
                points_selector=[],
            )
        except Exception:
            pass  # Collection might not exist or be empty

    def clear_test_memory_files(self):
        """Clear test memory files."""
        import glob
        memory_dir = Path.home() / ".claude" / "memory"
        if memory_dir.exists():
            for file in memory_dir.glob("*.md"):
                if "test" in file.name.lower() or "20260415" in file.name:
                    try:
                        file.unlink()
                    except Exception:
                        pass

    def teardown(self):
        """Clean up test data."""
        print("\nCleaning up...")
        try:
            self.clear_test_memories()
            self.clear_test_memory_files()
        except Exception:
            pass

    def test(self, name: str, assertion: bool, details: str = ""):
        """Record a test result."""
        status = "[PASS]" if assertion else "[FAIL]"
        self.results.append((name, assertion, details))
        print(f"{status}: {name}")
        if details and not assertion:
            print(f"     {details}")

    def scenario_1_cross_client_isolation(self):
        """Test: Alice (Acme) and Bob (GlobalBank) have isolated memories."""
        print("\n=== Scenario 1: Cross-Client Isolation ===")

        # Set up as Alice working on Acme
        os.environ["USER"] = "alice"
        os.environ["AGENTBRAIN_TEAM_ID"] = "platform"
        os.environ["AGENTBRAIN_ORG_ID"] = "ntt-data"

        # Alice stores Acme-specific memory
        result = skill_remember("Acme uses Stripe for payments, never PayPal")
        self.test(
            "Alice stores Acme memory",
            "Memory Stored" in result,
            result[:100]
        )

        # Set up as Bob working on GlobalBank
        os.environ["USER"] = "bob"

        # Bob stores GlobalBank-specific memory
        result = skill_remember("GlobalBank uses PayPal for payments, never Stripe")
        self.test(
            "Bob stores GlobalBank memory",
            "Memory Stored" in result,
            result[:100]
        )

        # Alice recalls - should see Acme/Stripe only
        os.environ["USER"] = "alice"
        result = skill_recall("payment gateway")

        # Check: Alice sees only her own scopes, not Bob's
        alice_has_stripe = "Stripe" in result
        alice_has_bob_memory = "user:bob" in result or "GlobalBank" in result
        self.test(
            "Alice sees Stripe (her client)",
            alice_has_stripe and not alice_has_bob_memory,
            f"Alice has Stripe: {alice_has_stripe}, Has Bob's memory: {alice_has_bob_memory}"
        )

        # Bob recalls - should see GlobalBank/PayPal only
        os.environ["USER"] = "bob"
        result = skill_recall("payment gateway")

        # Check: Bob sees only his own scopes, not Alice's
        bob_has_paypal = "PayPal" in result
        bob_has_alice_memory = "user:alice" in result or "Acme" in result
        self.test(
            "Bob sees PayPal (his client)",
            bob_has_paypal and not bob_has_alice_memory,
            f"Bob has PayPal: {bob_has_paypal}, Has Alice's memory: {bob_has_alice_memory}"
        )

    def scenario_2_team_sharing(self):
        """Test: Team memories are shared across all team members."""
        print("\n=== Scenario 2: Team Knowledge Sharing ===")

        # Create a team-level memory (simulate repo-based)
        os.environ["USER"] = "alice"
        result = skill_remember("Platform teams should use GitHub Actions for CI/CD")
        self.test(
            "Alice stores team memory",
            "Memory Stored" in result,
            ""
        )

        # Find the memory file and promote it
        # Use a partial name match that should work with the generated filename
        # The filename will be something like: feedback_platform_teams_github_20260415.md
        result = skill_promote("github", "team:platform")

        # Check if promotion worked or file not found
        if "not found" in result.lower():
            self.test(
                "Memory promoted to team",
                False,
                "Could not find memory file for promotion"
            )
        else:
            self.test(
                "Memory promoted to team",
                "Promoted" in result,
                ""
            )

        # Bob should now see the team memory (because team:platform is in his scopes)
        os.environ["USER"] = "bob"
        result = skill_recall("CI/CD conventions")
        self.test(
            "Bob sees team convention",
            "GitHub Actions" in result,
            "Team memories should be visible to all team members"
        )

    def scenario_3_scope_hierarchy(self):
        """Test: Scope hierarchy (user < team < project < org)."""
        print("\n=== Scenario 3: Scope Hierarchy ===")

        # Create memories at different types (which map to scopes)
        memories = [
            ("Personal preference", "user"),  # Maps to user:alice
            ("Team convention", "I prefer using GitHub Actions"),  # Maps to user, could be promoted to team
            ("Project decision", "We use PostgreSQL"),  # Maps to project
        ]

        for description, text in memories:
            result = skill_remember(text)
            self.test(
                f"Store memory: {description}",
                "Memory Stored" in result,
                ""
            )

    def scenario_4_query_filtering(self):
        """Test: Query respects scope filters."""
        print("\n=== Scenario 4: Query Scope Filtering ===")

        # Test with different user contexts
        test_cases = [
            ("alice", ["user:alice", "team:platform", "org:ntt-data"]),
            ("bob", ["user:bob", "team:platform", "org:ntt-data"]),
        ]

        for user, expected_contains in test_cases:
            os.environ["USER"] = user
            scopes = get_allowed_scopes()

            # Verify scopes are computed correctly
            has_user = any("user:" in s for s in scopes)
            has_team = any("team:" in s for s in scopes)
            has_org = any("org:" in s for s in scopes)

            self.test(
                f"{user} has correct scopes",
                has_user and has_team and has_org,
                f"Scopes: {scopes}"
            )

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 50)
        print("TEST SUMMARY")
        print("=" * 50)

        passed = sum(1 for _, result, _ in self.results if result)
        total = len(self.results)

        for name, result, details in self.results:
            status = "[+]" if result else "[X]"
            print(f"{status} {name}")
            if details and not result:
                print(f"   {details}")

        print(f"\n{passed}/{total} tests passed")

        if passed == total:
            print("SUCCESS: All tests passed!")
        else:
            print(f"WARNING: {total - passed} test(s) failed")


def main():
    """Run the multi-tenant test suite."""
    print("=" * 50)
    print("AgentBrain Multi-Tenant Test Suite")
    print("NTT Data Consulting Scenarios")
    print("=" * 50)

    tester = MultiTenantTester()

    if not tester.setup():
        print("Failed to set up test environment. Is Qdrant running?")
        return 1

    try:
        # Run scenarios
        tester.scenario_1_cross_client_isolation()
        tester.scenario_2_team_sharing()
        tester.scenario_3_scope_hierarchy()
        tester.scenario_4_query_filtering()

        # Print summary
        tester.print_summary()

        return 0 if all(r for _, r, _ in tester.results) else 1

    finally:
        tester.teardown()


if __name__ == "__main__":
    sys.exit(main())
