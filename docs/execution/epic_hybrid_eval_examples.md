# Epic Hybrid Eval Examples

These are representative scenario transcripts for future regression review. Exact assistant wording may vary, but deterministic expectations define the required operational behavior.

## Good Transcript
User: Quero marcar um corte amanhã às 16h17 para Audit User, telefone 11999998888

Assistant: Resumo do agendamento de Corte para amanhã às 16:17. Posso confirmar?

User: sim, pode confirmar

Assistant: Tudo certo. O pré-agendamento foi registrado e será confirmado por um atendente.

Expected CRM side effect: appointment/prebook exists for the tenant with service `Corte`.

## Conflict Transcript
User: Quero marcar um corte amanhã às 15h para Audit User, telefone 11999998888

Assistant: Encontrei esse horário e posso tentar confirmar. Está tudo certo?

User: sim

Assistant: Esse horário não está disponível. Posso sugerir outro horário próximo?

Expected CRM side effect: no fake success and no `prebooking_stub`.

## Missing-Data Transcript
User: Quero marcar um corte amanhã às 15h

Assistant: Posso confirmar, mas antes preciso do nome do cliente.

User: Audit User

Assistant: Resumo para confirmação do pré-agendamento de Corte amanhã às 15:00. Tudo certo?

User: pode confirmar

Assistant: Antes de confirmar, qual é o telefone do cliente para este agendamento?

Expected CRM side effect: no prebook attempt until customer name and phone exist or customer_id is present.

## Fragmented Booking Transcript
User: Quero marcar

Assistant: Qual serviço você gostaria de agendar?

User: Corte

Assistant: Quando prefere marcar?

User: amanhã

Assistant: Qual horário funciona melhor?

User: 16h17

Assistant: Resumo para confirmação do pré-agendamento de Corte amanhã às 16:17. Tudo certo?

User: Audit User, 11999998888

Assistant: Resumo para confirmação do pré-agendamento de Corte amanhã às 16:17. Tudo certo?

Expected behavior: workflow remains `book_appointment`, service/date/time/customer identity are preserved, and no RAG or handoff fallback occurs.

## Interruption Transcript
User: Quero marcar um corte amanhã às 18h

Assistant: Corte amanhã às 18:00. Posso confirmar?

User: Qual o endereço mesmo?

Assistant: O atendimento é na unidade principal. Posso continuar com o agendamento de Corte amanhã às 18:00?

User: Pode continuar

Assistant: Para confirmar, preciso do nome e telefone do cliente.

Expected behavior: booking slots stay preserved after the FAQ interruption.

## Weird-Language Transcript
User: opa, queria corta o cabelo amanha la pras 4 e 17 da tarde

Assistant: Entendi: Corte amanhã às 16:17. Qual é o nome do cliente?

User: meu nome é Audit User e o zap é 11999998888

Assistant: Perfeito. Posso confirmar esse pré-agendamento?

User: isso, manda bala

Assistant: Tudo certo. O pré-agendamento foi registrado.

Expected behavior: colloquial input maps to booking intent and preserves service/date/time.
