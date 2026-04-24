# booking_with_short_affirmations

- Verdict: FAIL
- Conversation ID: None
- Session ID: None
- Judge: DISABLED

## Transcript

```text
Turn 1 user: Corte amanhã 16h17 Audit User 11999998888
Turn 1 assistant: 
Turn 2 user: ok
Turn 2 assistant: 
```

## Failures

- step 1: upstream_runtime_failure: HTTP request failed with status 502: <!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>502</title>
    <style>@font-face {
  font-family: "Roobert";
  font-weight: 500;
  font-style: normal;
  font-stretch: normal;
  src: url("data:font/woff2;base64,d09GMk9UVE8AAKewAAwAAAABa6QAAKdfAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAADYKmehqCHhuC4UocpRQGYACLBgE2AiQDkygEBgWFRwcgW8pqkQKZcr0u0nk2H+gc25rBL5CqkDOqYXNqo87dNmL1mgByHi4yIGwcgLFJz2f/////f/pSkaHK
- step 1: upstream_runtime_failure: response body is not a JSON object
- step 1: assertion_failure: expected workflow book_appointment, got None
- step 1: assertion_failure: expected slot service to be present
- step 1: assertion_failure: expected slot date to be present
- step 1: assertion_failure: expected slot time to be present
- step 2: upstream_runtime_failure: HTTP request failed with status 502: <!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>502</title>
    <style>@font-face {
  font-family: "Roobert";
  font-weight: 500;
  font-style: normal;
  font-stretch: normal;
  src: url("data:font/woff2;base64,d09GMk9UVE8AAKewAAwAAAABa6QAAKdfAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAADYKmehqCHhuC4UocpRQGYACLBgE2AiQDkygEBgWFRwcgW8pqkQKZcr0u0nk2H+gc25rBL5CqkDOqYXNqo87dNmL1mgByHi4yIGwcgLFJz2f/////f/pSkaHK
- step 2: upstream_runtime_failure: response body is not a JSON object
- step 2: assertion_failure: expected workflow book_appointment, got None

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
