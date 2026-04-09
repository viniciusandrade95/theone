# Booking Online (MVP)

## Objetivo
Permitir que um cliente final faça marcações online por **tenant**, através de um **slug público**, com um fluxo simples (mobile-first) e reutilizando a lógica existente de **appointments** e **overlap**.

## O que foi implementado neste MVP
- **Configuração por tenant**: enable/disable + slug + nome público + contactos + janela min/max + `auto_confirm_bookings`.
- **Exposição de serviços**: flag `is_bookable_online` no serviço (apenas serviços ativos + bookable aparecem no público).
- **Página pública por slug**: configuração + serviços + locations ativas.
- **Disponibilidade**: slots por `location.hours_json` (quando existe) e fallback simples quando não existe; slots respeitam a duração total do serviço e só aparecem se o intervalo completo estiver livre.
- **Criação**: cria/reutiliza customer (lookup conservador) e cria appointment usando a lógica existente de overlap.

## Fora de escopo (não implementado)
- Cancelamento/remarcação self-service
- Reminders, notificações internas, outbound
- Staff/profissionais, buffers, pré-pagamento
- Antifraude/reCAPTCHA, analytics de conversão

## Decisões importantes
### `booking_settings` e lookup público por slug
O lookup por slug precisa funcionar sem `X-Tenant-ID`. Para manter o MVP simples, `booking_settings` é uma tabela **sem RLS**, com slug **único**.

### Estado do appointment (sem novo status)
Para manter o impacto mínimo, o appointment continua a usar `status="booked"`. Quando `auto_confirm_bookings=false`, o appointment é criado com `appointments.needs_confirmation=true` (campo auxiliar), evitando introduzir um novo status global.

### Customer lookup (regra conservadora)
1) procura por `phone`  
2) se não encontrar e houver `email`, procura por `email`  
3) se `phone` e `email` apontarem para customers diferentes, devolve erro amigável (sem duplicar silenciosamente)

