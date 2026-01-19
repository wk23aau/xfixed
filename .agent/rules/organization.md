# XAgent Organization Rules

## Core Principles

1. **Hierarchy First**: Always respect the agent hierarchy. Escalate to directors for cross-team coordination, to CTO-001 for strategic decisions, and to ARCH-001 for system-wide synthesis.

2. **Atomic Tasks**: Break down work into atomic, single-agent tasks. Each task should be completable by one agent.

3. **Clear Artifacts**: Every agent must produce clear, reviewable artifacts that prove work was completed correctly.

## Communication Protocol

- Use structured JSON for inter-agent communication
- Include agent ID, task ID, and timestamp in all messages
- Escalate blockers immediately to the responsible director

## Code Standards

- All Python code must follow PEP8
- All TypeScript must be strictly typed
- All APIs must be documented with OpenAPI/Swagger
- All UI components must be accessible (WCAG 2.1 AA)

## Security Requirements

- Never commit secrets to version control
- All user input must be validated
- All API endpoints must be authenticated
- Follow OWASP Top 10 guidelines
