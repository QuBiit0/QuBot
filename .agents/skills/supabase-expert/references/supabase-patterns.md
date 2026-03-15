# Supabase Patterns

## RLS (Row Level Security)
Siempre habilitar RLS en todas las tablas públicas.
```sql
alter table "public"."todos" enable row level security;

create policy "Users can view their own todos"
on "public"."todos"
for select using (auth.uid() = user_id);
```

## Edge Functions
Usar para lógica de negocio compleja o webhooks.
- Mantenerlas stateless.
- Usar Deno standard library.

## Database Webhooks
Evitar lógica pesada en triggers de base de datos; preferir webhooks a Edge Functions.
