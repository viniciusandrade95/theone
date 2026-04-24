# booking_with_fragmented_inputs

- Verdict: FAIL
- Conversation ID: None
- Session ID: None
- Judge: DISABLED

## Transcript

```text
Turn 1 user: Quero marcar
Turn 1 assistant: 
Turn 2 user: Corte
Turn 2 assistant: 
Turn 3 user: amanhã
Turn 3 assistant: 
Turn 4 user: 16h17
Turn 4 assistant: 
Turn 5 user: Audit User, 11999998888
Turn 5 assistant: 
Turn 6 user: sim, pode confirmar
Turn 6 assistant: 
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
- step 1: assertion_failure: expected status collecting, got response=None workflow=None
- step 1: assertion_failure: expected route workflow, got None
- step 1: assertion_failure: expected workflow book_appointment, got None
- step 1: assertion_failure: reply missing expected text: serviço
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
- step 2: assertion_failure: expected status collecting, got response=None workflow=None
- step 2: assertion_failure: expected route workflow, got None
- step 2: assertion_failure: expected workflow book_appointment, got None
- step 2: assertion_failure: expected slot service to be present
- step 3: upstream_runtime_failure: HTTP request failed with status 502: <!DOCTYPE html>
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
- step 3: upstream_runtime_failure: response body is not a JSON object
- step 3: assertion_failure: expected status collecting, got response=None workflow=None
- step 3: assertion_failure: expected route workflow, got None
- step 3: assertion_failure: expected workflow book_appointment, got None
- step 3: assertion_failure: expected slot service to be present
- step 3: assertion_failure: expected slot date to be present
- step 4: upstream_runtime_failure: HTTP request failed with status 502: <!DOCTYPE html>
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
- step 4: upstream_runtime_failure: response body is not a JSON object
- step 4: assertion_failure: expected status awaiting_confirmation, got response=None workflow=None
- step 4: assertion_failure: expected route workflow, got None
- step 4: assertion_failure: expected workflow book_appointment, got None
- step 4: assertion_failure: reply missing any expected text: confirmação, confirmar, tudo certo, posso encaminhar, pré-agendamento
- step 4: assertion_failure: expected slot service to be present
- step 4: assertion_failure: expected slot date to be present
- step 4: assertion_failure: expected slot time to be present
- step 5: upstream_runtime_failure: HTTP request failed with status 502: <!DOCTYPE html>
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
- step 5: upstream_runtime_failure: response body is not a JSON object
- step 5: assertion_failure: expected status awaiting_confirmation, got response=None workflow=None
- step 5: assertion_failure: expected route workflow, got None
- step 5: assertion_failure: expected workflow book_appointment, got None
- step 5: assertion_failure: reply missing any expected text: confirmação, confirmar, tudo certo, posso encaminhar, pré-agendamento
- step 5: assertion_failure: expected slot service to be present
- step 5: assertion_failure: expected slot date to be present
- step 5: assertion_failure: expected slot time to be present
- step 5: assertion_failure: expected slot customer_name to be present
- step 5: assertion_failure: expected slot phone to be present
- step 6: upstream_runtime_failure: HTTP request failed with status 502: <!DOCTYPE html>
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
- step 6: upstream_runtime_failure: response body is not a JSON object
- step 6: assertion_failure: expected status completed, got response=None workflow=None
- step 6: assertion_failure: expected route workflow, got None
- step 6: assertion_failure: expected workflow book_appointment, got None
- step 6: assertion_failure: reply missing any expected text: registr, agend, pré-agendamento, confirm
- step 6: assertion_failure: expected action_result.ok=True, got None

## CRM Verification

```json
{
  "status": "SKIPPED",
  "reasons": [
    "no CRM verification configured"
  ]
}
```
