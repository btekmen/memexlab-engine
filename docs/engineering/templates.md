
# Templates

## Person

```markdown
---
title: Jane Doe
type: person
created: 'YYYY-MM-DD'
updated: 'YYYY-MM-DD'
status: active
tags:
  - person
aliases:
  - Jane A. Doe
provenance:
  - date: 'YYYY-MM-DD'
    claim: 'Jane Doe is CFO of ExampleCo.'
    source: '[[sources/source-slug]]'
    confidence: high
---

# Jane Doe

## Summary

One-paragraph summary.

## Current Role

- Company:
- Title:
- Location:

## Relationship

- First known:
- Last interaction:
- Strength:
- Best intro path:

## Key Facts

- Fact with source.

## Open Threads

- Thread:

## Notes

- Dated note.
```

## Company

```markdown
---
title: ExampleCo
type: company
created: 'YYYY-MM-DD'
updated: 'YYYY-MM-DD'
status: active
tags:
  - company
provenance:
  - date: 'YYYY-MM-DD'
    claim: 'ExampleCo operates in embedded finance.'
    source: '[[sources/source-slug]]'
    confidence: medium
---

# ExampleCo

## Summary

## Business

## Strategic Relevance

## People

## Relationship History

## Risks

## Sources
```

## Book

```markdown
---
title: Book Title
type: book
author: Author Name
created: 'YYYY-MM-DD'
updated: 'YYYY-MM-DD'
status: working
tags:
  - book
provenance:
  - date: 'YYYY-MM-DD'
    claim: 'Owned in audio format.'
    source: 'Local library record'
    confidence: high
---

# Book Title

_Author · Category · Tier_

## Library Metadata

- Source:
- Format:
- Status:

## Core Thesis

## Mental Models

## Key Examples

## Strategic Translation

## Related
```

## Concept

```markdown
---
title: Concept Name
type: concept
created: 'YYYY-MM-DD'
updated: 'YYYY-MM-DD'
status: draft
tags:
  - concept
relations:
  relates_to:
    - '[[related-concept]]'
provenance:
  - date: 'YYYY-MM-DD'
    claim: 'Core claim.'
    source: '[[sources/source-slug]]'
    confidence: medium
---

# Concept Name

## Definition

## Why It Matters

## Examples

## Failure Modes

## Related
```

## Meeting Note

```markdown
---
title: Meeting with Jane Doe
type: source
created: 'YYYY-MM-DD'
updated: 'YYYY-MM-DD'
status: raw
tags:
  - meeting
attendees:
  - '[[jane-doe]]'
  - '[[exampleco]]'
---

# Meeting with Jane Doe

## Context

## Notes

## Decisions

## Follow-Ups

## Entity Updates
```

## Decision

```markdown
---
title: Decision Title
type: decision
created: 'YYYY-MM-DD'
updated: 'YYYY-MM-DD'
status: active
decision_date: 'YYYY-MM-DD'
owner: Team or Person
review_date: 'YYYY-MM-DD'
tags:
  - decision
provenance:
  - date: 'YYYY-MM-DD'
    claim: 'Decision was made in leadership meeting.'
    source: '[[sources/source-slug]]'
    confidence: high
---

# Decision Title

## Decision

## Context

## Options Considered

## Rationale

## Risks

## Review Trigger
```
