create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  full_name text,
  email text,
  avatar_url text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists public.trips (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  trip_id text not null,
  destination text,
  title text,
  duration_days int,
  travelers int,
  budget_per_person numeric,
  feasibility_score int,
  feasibility_status text,
  trip_request text,
  trip_response jsonb not null,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create unique index if not exists trips_user_trip_id_unique
on public.trips(user_id, trip_id);

alter table public.profiles enable row level security;
alter table public.trips enable row level security;

drop policy if exists "Users can view own profile" on public.profiles;
drop policy if exists "Users can insert own profile" on public.profiles;
drop policy if exists "Users can update own profile" on public.profiles;
drop policy if exists "Users can view own trips" on public.trips;
drop policy if exists "Users can insert own trips" on public.trips;
drop policy if exists "Users can update own trips" on public.trips;
drop policy if exists "Users can delete own trips" on public.trips;

create policy "Users can view own profile"
on public.profiles
for select
using (auth.uid() = id);

create policy "Users can insert own profile"
on public.profiles
for insert
with check (auth.uid() = id);

create policy "Users can update own profile"
on public.profiles
for update
using (auth.uid() = id)
with check (auth.uid() = id);

create policy "Users can view own trips"
on public.trips
for select
using (auth.uid() = user_id);

create policy "Users can insert own trips"
on public.trips
for insert
with check (auth.uid() = user_id);

create policy "Users can update own trips"
on public.trips
for update
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

create policy "Users can delete own trips"
on public.trips
for delete
using (auth.uid() = user_id);

notify pgrst, 'reload schema';
