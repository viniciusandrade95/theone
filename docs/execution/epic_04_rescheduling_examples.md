# epic_04_rescheduling Examples

## Success

User:

```text
quero remarcar meu corte para amanhã às 16h17
```

Expected assistant:

```text
Resumo para confirmação: remarcação de seu próximo agendamento para amanhã às 16:17. Posso confirmar?
```

User:

```text
sim, pode confirmar
```

Expected CRM side effect:

- same appointment id is updated
- `starts_at` changes to requested date/time
- `ends_at` preserves the existing duration

## Conflict

User:

```text
quero remarcar meu corte para amanhã às 15h
```

Precondition:

- another appointment already occupies that location/time

Expected assistant:

```text
Esse horário não está disponível para remarcação.
```

Expected CRM side effect:

- no appointment is moved
- operation response includes `error_code=appointment_overlap`

## Ambiguous Target

User:

```text
quero remarcar para amanhã às 16h
```

Precondition:

- tenant has more than one upcoming appointment that could match

Expected assistant:

```text
Encontrei mais de um agendamento possível. Informe a referência do agendamento que deseja remarcar.
```

Expected CRM side effect:

- no update
- operation response includes `error_code=appointment_ambiguous`

## Missing Time

User:

```text
quero remarcar meu corte para amanhã
```

Expected assistant:

```text
E qual horário você prefere?
```

Expected CRM side effect:

- no availability lookup requiring update
- no CRM mutation

## Interruption

User:

```text
quero remarcar meu corte para amanhã
```

Assistant asks for time. User interrupts:

```text
qual o endereço?
```

Expected assistant behavior:

- preserves reschedule state
- answers or acknowledges interruption
- resumes when the user provides `16h17`

## Correction

User:

```text
quero remarcar meu corte para amanhã às 16h
```

Assistant summarizes. User changes:

```text
não, pode ser 17h
```

Expected assistant:

```text
Resumo para confirmação: remarcação ... às 17:00. Posso confirmar?
```

Expected CRM side effect:

- no update on the correction turn
- availability is checked again for the new time
