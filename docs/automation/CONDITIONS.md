# SHIVANI Safe Structured Condition Engine

## 1. Safety Guarantee

The Condition Engine (`core/automation/conditions.py`) enforces strict security constraints:

> **NO `eval()`. NO `exec()`. NO dynamic code evaluation.**
> All conditions must be structured, declarative, typed AST predicates.

This eliminates any possibility of arbitrary code injection through condition expressions, whether imported from community templates or derived from untrusted external sources.

---

## 2. Predicate Operators

The following declarative comparison operators are supported:

| Operator | Behavior |
|---|---|
| `EQUALS` | Strict equality (`actual == expected`) |
| `NOT_EQUALS` | Strict inequality (`actual != expected`) |
| `GREATER_THAN` | Numerical or lexicographical greater than (`actual > expected`) |
| `LESS_THAN` | Numerical or lexicographical less than (`actual < expected`) |
| `CONTAINS` | Substring inclusion or collection membership |
| `NOT_CONTAINS` | Substring exclusion or non-membership |
| `STARTS_WITH` | Prefix match for string values |
| `ENDS_WITH` | Suffix match for string values |
| `EXISTS` | Verifies field is not null and present in context |
| `NOT_EXISTS` | Verifies field is absent or null |
| `IS_EMPTY` | Verifies string, list, or dict is empty |
| `NOT_EMPTY` | Verifies string, list, or dict has one or more elements |
| `MATCHES_REGEX` | Safe regular expression pattern match via `re.search` |

---

## 3. Nested Boolean Logic

Conditions can be grouped into composite trees using `ConditionGroup`:
- **`AND`**: All child predicates and nested groups must evaluate to `True`.
- **`OR`**: At least one child predicate or nested group must evaluate to `True`.
- **`NOT`**: Inverts the evaluation of its child elements.

### Example Structured Condition:
```json
{
  "operator": "AND",
  "predicates": [
    {
      "field": "battery.level",
      "operator": "greater_than",
      "value": 30
    },
    {
      "field": "network.is_metered",
      "operator": "equals",
      "value": false
    }
  ],
  "groups": [
    {
      "operator": "OR",
      "predicates": [
        { "field": "user.is_idle", "operator": "equals", "value": true },
        { "field": "time.is_night", "operator": "equals", "value": true }
      ]
    }
  ]
}
```

---

## 4. Context Resolution

Context variables are resolved using dot-notation path traversal (`field.subfield.property`).
The evaluation context includes:
- System state: `system.battery`, `system.cpu_percent`, `system.memory_percent`.
- Network state: `network.online`, `network.is_metered`.
- User state: `user.idle_seconds`, `user.do_not_disturb`.
- Trigger data: `event.*` for incoming events.
- Step outputs: `step_<id>_output.*` for chained workflow data.
