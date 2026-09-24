# Computer Autonomy Testing Strategy & Test Suites — Phase 17

## 1. Test Architecture

Phase 17 incorporates deterministic, synthetic GUI testing alongside real environment integration:

| Test Suite | Purpose | Tests |
|---|---|---|
| `test_observation_and_grounding.py` | Observation schemas, spatial predicates, semantic graph, multi-source fusion. | 4 |
| `test_closed_loop_and_actions.py` | Closed loop cycle, expectation engine, outcome verification, emergency stop. | 3 |
| `test_recovery_and_checkpoints.py` | Loop detection, error classification, checkpoint creation, and rollback stack. | 4 |
| `test_terminal_and_safety.py` | Command risk classification, dangerous command blocking, clipboard privacy. | 4 |
| `test_application_adapters.py` | VS Code, Explorer, Excel, PowerPoint adapters, and generic fallback. | 5 |
| `test_computer_server_apis.py` | REST API endpoints (`/api/computer/*`). | 1 |
| `test_computer_e2e_scenarios.py` | All 8 canonical long-horizon E2E workflows. | 7 |
| **Total** | **Phase 17 Dedicated Tests** | **28 Tests (100% Passing)** |

---

## 2. End-to-End Scenarios Verified
1. **Scenario 1**: VS Code test run, observation, and diagnostic parsing.
2. **Scenario 2**: PDF scan, organization proposal with preview, and safe move execution.
3. **Scenario 3**: Excel CSV ingestion and column chart creation (`xlsxwriter`).
4. **Scenario 4**: PowerPoint visual inspection for empty or cluttered slides.
5. **Scenario 5**: README setup and environment dependency check.
6. **Scenario 6**: Emergency interrupt ("Shivani stop") during execution.
7. **Scenario 7**: User manual takeover and external UI change reconciliation.
8. **Scenario 8**: Application crash detection and safe checkpoint resumption.
