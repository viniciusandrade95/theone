# Epic Autonomous Eval Examples

These examples document the kinds of conversations the autonomous tester is expected to generate and evaluate. They are templates for expected behavior, not live transcripts from a specific run.

## Good Fragmented Booking

Representative user messages:

1. `Quero marcar`
2. `Corte`
3. `amanha`
4. `16h17`
5. `Audit User, 11999998888`
6. `sim, pode confirmar`

Expected assistant behavior:

- Starts `book_appointment`.
- Asks for missing service/date/time instead of summarizing too early.
- Preserves service, date, time, customer name, and phone across turns.
- Executes only after confirmation.

Expected CRM side effect:

- One prebook/appointment record is created, or a valid business conflict is returned.

Failure examples the autonomous tester should flag:

- Slot loss after the identity turn.
- Unexpected `handoff_to_human`.
- `prebooking_stub`.
- Premature confirmation summary before service/date/time exist.

## Missing Data Booking

Representative user messages:

1. `quero marcar corte amanha as 16h`
2. `sim`
3. `Audit User`
4. `11999998888`
5. `pode confirmar`

Expected assistant behavior:

- Blocks execution until customer identity is complete.
- Asks for name and phone with deterministic missing-field prompts.
- Resumes the same booking workflow after the missing data is supplied.

Expected CRM side effect:

- No CRM prebook is attempted before both name and phone are available when `customer_id` is absent.

Failure examples:

- CRM receives a payload missing `customer.name` or `customer.phone`.
- The workflow resets to empty collection after phone input.
- The assistant asks again for a field already supplied.

## Interruption Then Resume

Representative user messages:

1. `quero marcar corte amanha`
2. `quanto custa?`
3. `beleza, 16h17 entao`
4. `Audit User, 11999998888`
5. `sim`

Expected assistant behavior:

- Allows a temporary FAQ/RAG detour when the scenario explicitly permits it.
- Returns to `book_appointment`.
- Preserves previously collected booking slots.

Failure examples:

- The FAQ turn permanently abandons the booking workflow.
- The assistant loses the service/date after answering the FAQ.

## Rescheduling Probe

Representative user messages:

1. `da pra mudar pra sexta?`
2. `meu corte`
3. `16h`
4. `pode`

Expected assistant behavior:

- Routes to `reschedule_appointment` when that workflow is available.
- Asks for appointment identity if ambiguous.
- Does not fake success when no appointment can be resolved.

Expected CRM side effect:

- Existing appointment is updated only when tenant-safe target appointment resolution succeeds.

Failure examples:

- Silent booking fallback.
- Fake reschedule success.
- Destructive update without confirmation.

## Cancellation Probe

Representative user messages:

1. `nao posso ir amanha`
2. `cancela meu corte pfv`
3. `sim`

Expected assistant behavior:

- Routes to cancellation flow when supported.
- Requires confirmation before cancellation.
- Handles ambiguous/no appointment cases cleanly.

Expected CRM side effect:

- Appointment is cancelled only after a resolved target and explicit confirmation.

Failure examples:

- Cancellation executes without confirmation.
- Booking workflow captures cancellation phrasing.
- Assistant claims cancellation succeeded without CRM evidence.

## Weird-Language Booking

Representative user messages:

1. `mano queria cortar amanhã`
2. `pode ser corte`
3. `16h? nao, 17h melhor`
4. `Audit User, 11999998888`
5. `ok`

Expected assistant behavior:

- Interprets colloquial booking intent.
- Preserves the corrected time.
- Reaches confirmation/execution without unnecessary handoff.

Failure examples:

- Uses the old time after correction.
- Treats colloquial input as unsupported.
- Loops by asking for the same slot repeatedly.
