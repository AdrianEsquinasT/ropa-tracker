-- Cesta de deseos · esquema de Supabase
-- Pegar entero en: Supabase → SQL Editor → New query → Run. Se puede ejecutar más de una vez.

-- Artículos: uno por fila. Cada usuario solo ve y toca los suyos (RLS).
create table if not exists public.items (
  id          uuid primary key default gen_random_uuid(),
  owner       uuid not null default auth.uid() references auth.users(id) on delete cascade,
  art         text not null,                         -- referencia (o identificador interno)
  data        jsonb not null default '{}'::jsonb,    -- nombre, tienda, enlace, foto, tallas, categoría…
  history     jsonb not null default '[]'::jsonb,    -- [{date, price, source}]
  price       numeric(10,2),
  status      text not null default 'manual',
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now(),
  unique (owner, art)
);

-- Preferencias de cada usuario (sus tallas, etc.)
create table if not exists public.settings (
  owner       uuid primary key default auth.uid() references auth.users(id) on delete cascade,
  data        jsonb not null default '{}'::jsonb,
  updated_at  timestamptz not null default now()
);

alter table public.items    enable row level security;
alter table public.settings enable row level security;

drop policy if exists "items: ver lo mío"    on public.items;
drop policy if exists "items: añadir lo mío" on public.items;
drop policy if exists "items: editar lo mío" on public.items;
drop policy if exists "items: borrar lo mío" on public.items;
create policy "items: ver lo mío"    on public.items for select using (auth.uid() = owner);
create policy "items: añadir lo mío" on public.items for insert with check (auth.uid() = owner);
create policy "items: editar lo mío" on public.items for update using (auth.uid() = owner) with check (auth.uid() = owner);
create policy "items: borrar lo mío" on public.items for delete using (auth.uid() = owner);

drop policy if exists "settings: lo mío" on public.settings;
create policy "settings: lo mío" on public.settings for all using (auth.uid() = owner) with check (auth.uid() = owner);

-- Solo usuarios con sesión; los anónimos no ven nada.
revoke all on public.items, public.settings from anon;
grant select, insert, update, delete on public.items, public.settings to authenticated;

-- Fecha de última modificación automática
create or replace function public.touch_updated_at() returns trigger language plpgsql as $$
begin new.updated_at = now(); return new; end $$;
drop trigger if exists items_touch on public.items;
create trigger items_touch before update on public.items for each row execute function public.touch_updated_at();
drop trigger if exists settings_touch on public.settings;
create trigger settings_touch before update on public.settings for each row execute function public.touch_updated_at();
