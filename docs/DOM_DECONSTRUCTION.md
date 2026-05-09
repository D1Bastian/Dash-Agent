# Text-Only DOM Deconstruction

Dash uses text and accessibility semantics to operate web pages without exposing raw page internals to the user.

## Inputs

- Visible text
- Accessible names
- ARIA roles
- Labels and placeholders
- Form hierarchy
- Semantic input types
- Button names
- Validation and error text
- URL and document state changes

## Excluded From User Output

- Screenshots
- Image analysis
- Raw DOM dumps
- JavaScript snippets
- CSS selector telemetry
- Passwords, tokens, recovery codes, or full credential values

## Field Mapping Strategy

1. Find the nearest form or dialog container.
2. Map controls by accessible label, role, placeholder, and input type.
3. Prefer stable semantics over generated IDs or classes.
4. Focus the field before entry.
5. Send real keyboard/input/change events.
6. Read the field value back to verify that the frontend registered it.
7. Submit only after all required visible fields are verified.

## Verification Strategy

CAPTCHA, MFA, email, phone, and payment confirmation are human checkpoints. Dash pauses, asks the user to complete the prompt, watches for URL or DOM state changes, then resumes the mission.
