# Sequence Diagrams

## Purpose

This file shows how requests move through the system for a clinical question and for governed advisory automation.

## Clinical Question Sequence

```mermaid
sequenceDiagram
	participant User
	participant API as Query API
	participant Safety as Safety Checker
	participant Service as QueryService
	participant Retriever
	participant Decision as SafetyDecisionEngine
	participant Generator
	participant Audit

	User->>API: POST /query
	API->>Safety: validate input
	Safety-->>API: allow or block
	API->>Service: query(question, top_k)
	Service->>Retriever: retrieve evidence
	Retriever-->>Service: chunks and scores
	Service->>Decision: evaluate evidence and output policy
	Decision-->>Service: answer, refuse, clarify, or insufficient_evidence
	alt answer allowed
		Service->>Generator: generate answer
		Generator-->>Service: cited answer
	end
	Service->>Audit: write audit metadata
	Service-->>API: structured response
	API-->>User: answer or refusal
```

## Advisory Draft Sequence

```mermaid
sequenceDiagram
	participant Reviewer
	participant Advisory as Advisory API
	participant Governance as GovernanceRuleEngine
	participant Service as AgenticDevOpsService
	participant Audit as JsonlAuditWriter

	Reviewer->>Advisory: POST /advisory/draft
	Advisory->>Governance: evaluate request
	alt blocked
		Governance-->>Advisory: blocked decision
		Advisory->>Audit: write governance block entry
		Advisory-->>Reviewer: 400 with block details
	else allowed
		Governance-->>Advisory: allowed with warnings
		Advisory->>Service: generate draft output
		Service->>Audit: write advisory audit entry
		Service-->>Advisory: draft_needs_human_review
		Advisory-->>Reviewer: advisory response
	end
```

## Engineering Rationale

The sequence shows that input safety, retrieval confidence heuristics, generation, output validation, and audit logging are separate decisions. That gives reviewers a concrete story for how the platform behaves under both success and refusal paths.

## Systems Engineering Principle

The design is explicit about state transitions. A request is never allowed to skip from user input to trusted answer without intermediate checks.

## Scalability

- The flow supports additional decision branches without changing the client contract.
- Advisory automation remains separate from clinical Q&A.
- The same sequence works with mock generation and live LLM providers.

## Maintainability

Sequence diagrams are kept separate from code so the walkthrough can evolve independently of implementation.

## Verification Strategy

- API and service tests verify the same control flow.
- Refusal and governance tests validate the blocked branches.
- Smoke tests verify the happy-path startup and response cycle.

## Recommendations

- Add a second sequence diagram for document upload and indexing.
- Use this file as the runtime interaction view in the C4 package.
