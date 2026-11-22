-- Comment box for the flat plan site.
-- Paste this whole file into Supabase → SQL Editor → "New query" → Run. Safe to run more than once.
--
-- Anyone with the site link can ADD a comment and READ comments (so pins show on the plan).
-- Nobody can edit or delete through the site; you can still do that yourself in the Supabase dashboard.

create table if not exists public.comments (
  id          bigint generated always as identity primary key,
  created_at  timestamptz not null default now(),
  page        text not null check (page in ('2d', '3d', 'home')),
  name        text check (char_length(name) <= 60),
  body        text not null check (char_length(body) between 1 and 2000),
  x           double precision,          -- plan metres (east)   — null if not pinned
  y           double precision,          -- plan metres (south)  — null if not pinned
  z           double precision,          -- height in metres (3D pins only)
  layout      text check (char_length(layout) <= 80)   -- bathroom option being looked at
);

alter table public.comments enable row level security;

-- read + add only (no update / delete policies → those are blocked)
drop policy if exists "anyone can read comments" on public.comments;
create policy "anyone can read comments" on public.comments
  for select to anon, authenticated using (true);

drop policy if exists "anyone can add comments" on public.comments;
create policy "anyone can add comments" on public.comments
  for insert to anon, authenticated with check (true);

grant select, insert on public.comments to anon, authenticated;
