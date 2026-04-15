# AgentBrain Testing Scenarios - NTT Data Style

> **Context:** Testing AgentBrain multi-tenant memory isolation and scope-based retrieval
> **Organization:** NTT Data (global consulting firm)
> **Date:** 2025-04-15

---

## Organization Structure

```
NTT Data (org:ntt-data)
├── Client: Acme Corp (client:acme)
│   ├── Project: E-commerce Platform (project:acme-commerce)
│   └── Project: Mobile App (project:acme-mobile)
├── Client: GlobalBank (client:globalbank)
│   ├── Project: Core Banking (project:gb-core)
│   └── Project: Mobile Banking (project:gb-mobile)
├── Internal Platform Team (team:platform)
│   ├── System: DevOps Pipeline (system:devops)
│   └── System: Monitoring (system:monitoring)
└── Consultants
    ├── alice@ntt-data.com (senior architect)
    ├── bob@ntt-data.com (fullstack dev)
    └── carol@ntt-data.com (data engineer)
```

---

## Test Scenarios

### Scenario 1: Cross-Client Isolation

**Setup:**
- Alice works on Acme Corp e-commerce platform
- Bob works on GlobalBank mobile app
- Both use `/remember` to store client-specific decisions

**Actions:**
```bash
# Alice (in acme-commerce repo)
/remember "Acme uses Stripe for payments, never PayPal"
/remember "Acme's API gateway is Kong, must use Kong plugins"

# Bob (in gb-mobile repo)
/remember "GlobalBank uses PayPal for payments, never Stripe"
/remember "GlobalBank's API gateway is Apigee, must use Apigee policies"
```

**Expected Results:**
- Alice's `/recall "payment gateway"` returns: Stripe, Kong
- Bob's `/recall "payment gateway"` returns: PayPal, Apigee
- Cross-contamination test: Each sees ONLY their client's decisions

**Scope Verification:**
```bash
# Alice's scopes: [user:alice, team:platform, project:acme-commerce, client:acme, org:ntt-data]
# Bob's scopes: [user:bob, team:platform, project:gb-mobile, client:globalbank, org:ntt-data]
```

---

### Scenario 2: Platform-Wide Knowledge Sharing

**Setup:**
- Platform team creates shared conventions in NTT internal repo
- All consultants should see platform conventions

**Team Memory Created:** `ntt-internal/.agentbrain/memory/team/conventions.md`
```markdown
---
type: team
scope: team:platform
---

# Platform Team Conventions

## CI/CD
- All projects use GitHub Actions
- Deployment requires approval from tech lead
- Version tagging: v1.2.3 format

## Security
- Never commit API keys
- Use HashiCorp Vault for secrets
- Enable branch protection rules
```

**Test:**
- Alice (in acme-commerce repo) runs `/recall "CI/CD conventions"`
- Bob (in gb-mobile repo) runs `/recall "deployment process"`

**Expected:** Both retrieve platform team conventions

---

### Scenario 3: Client Confidentiality

**Setup:**
- Carol works on GlobalBank data analytics
- Carol discovers a security vulnerability pattern

**Action:**
```bash
# Carol
/remember "Critical: GlobalBank has SQL injection vulnerability in legacy reports module - use parameterized queries only"
```

**Test:**
- Can Bob (on different GlobalBank project) see this memory?
- Can Alice (Acme Corp) see this memory?

**Expected Scopes:**
- Carol's memory: `project:gb-core` (or `client:globalbank` if promoted)
- Bob sees it (same client)
- Alice does NOT see it (different client)

---

### Scenario 4: Promotion Workflow

**Setup:**
- Alice discovers a useful pattern while working on Acme
- Pattern should be promoted to platform team for reuse

**Action:**
```bash
# Alice discovers pattern
/remember "Use Redis for session storage with 1-hour TTL - reduces database load by 40%"

# Later, promote to team
/promote redis_session_storage --to team:platform
```

**Expected Result:**
- Memory moved from `user:alice` to `team:platform`
- All NTT consultants can now retrieve this pattern

---

### Scenario 5: Org-Wide Policies

**Setup:**
- NTT Data has organization-wide compliance policies

**Org Memory:** `ntt-internal/.agentbrain/memory/org/compliance.md`
```markdown
---
type: reference
scope: org:ntt-data
---

# NTT Data Compliance Policies

## GDPR
- All EU client data must be stored in EU regions
- Data retention: max 2 years for PII

## SOC2
- Enable audit logging for all production systems
- Quarterly access reviews required
```

**Test:**
- All consultants run `/recall "data retention policies"`
- All should retrieve NTT org policies regardless of client/project

---

## Test Execution Script

```bash
#!/bin/bash
# AgentBrain Multi-Tenant Test Suite

echo "=== NTT Data Multi-Tenant Memory Test ==="

# Setup: Start Qdrant
docker-compose -f docker/qdrant-compose.yml up -d

# Test 1: Cross-Client Isolation
echo "Test 1: Cross-Client Isolation"
export CLAUDE_PLUGIN_ROOT=/path/to/agentbrain
export USER=alice
python scripts/skill_remember.py "Acme uses Stripe for payments"

export USER=bob
python scripts/skill_remember.py "GlobalBank uses PayPal for payments"

# Verify isolation
echo "Alice's recall:"
export USER=alice
python scripts/skill_recall.py "payment gateway"

echo "Bob's recall:"
export USER=bob
python scripts/skill_recall.py "payment gateway"

# Test 2: Team Knowledge Sharing
echo "Test 2: Team Knowledge Sharing"
# Team memory already in repo
python -c "from hooks.session_start import sync_repo_memories; sync_repo_memories()"

# Test 3-5: Similar pattern...

# Cleanup
docker-compose -f docker/qdrant-compose.yml down
```

---

## Success Criteria

| Test | Criteria | Pass/Fail |
|------|----------|-----------|
| Cross-Client Isolation | Alice sees Acme only, Bob sees GlobalBank only | |
| Platform Knowledge | All consultants retrieve platform conventions | |
| Client Confidentiality | Same-client visibility, cross-client blocked | |
| Promotion Workflow | User memory → Team memory successful | |
| Org Policies | All consultants retrieve org-wide policies | |
| Scope Filtering | Qdrant query respects scope filters | |
| Fallback Graceful | Missing config degrades to user-only scope | |
