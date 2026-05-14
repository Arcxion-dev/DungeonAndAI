# Project Instructions

This project utilizes a collection of specialized agent skills. You MUST strictly follow these rules:

## Skill Activation Mandate (CRITICAL)
- **Mandatory Usage:** You MUST proactively identify and ACTIVATE matching skills for EVERY task. Do not rely on general knowledge if a skill exists.
- **Verification:** Before starting any sub-task (UI, Backend, Data), check `.gemini/skills/` and use `activate_skill`.
- **Expert Performance:** Once a skill is activated, you must strictly adhere to its specific instructions and use its bundled resources (scripts/references) to ensure professional-grade output.

## Workflow Rules
- **Direct Implementation:** For bug fixes or logic updates, use the `senior-backend` or `code-reviewer` skills.
- **Data Integrity:** Use `database-schema-designer` when modifying JSON structures.
- **UI/UX:** Use `frontend-design` or `ux-researcher-designer` for interface improvements.
