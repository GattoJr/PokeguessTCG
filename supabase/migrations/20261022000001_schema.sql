-- PokeguessTCG: database schema and game logic.
-- The browser never reads tables directly: every table has row level security on and no policies.
-- Everything goes through the security-definer functions below, which act as the referee:
-- the card name stays on the server until the card is over, and the server computes the score.

-- ---------------------------------------------------------------- tables

create table if not exists public.layouts (
  serie text primary key,
  crop  float8[] not null,   -- artwork window: [left, top, width, height] as fractions of the card
  evo   float8[] not null,   -- pre-evolution picture (covered on evolved cards)
  evot  float8[] not null,   -- "Evolves from ..." text (covered on evolved cards)
  mega  float8[] not null    -- "The Mega-Evolved form of ..." box (covered on Mega cards)
);

create table if not exists public.cards (
  id       text primary key,          -- "<set>-<number>", e.g. sv01-001
  serie    text not null references public.layouts(serie),
  set_id   text not null,
  set_name text not null,
  number   text not null,
  name     text not null,
  rarity   text,
  has_evo  boolean not null default false,
  image    text not null              -- TCGdex base url; add /high.png, /high.webp ...
);
create index if not exists cards_name_idx on public.cards (lower(name));

create table if not exists public.admins (
  user_id uuid primary key references auth.users(id) on delete cascade
);

create table if not exists public.profiles (
  id         uuid primary key references auth.users(id) on delete cascade,
  username   text not null check (username ~ '^[A-Za-z0-9_]{3,16}$'),
  created_at timestamptz not null default now()
);
create unique index if not exists profiles_username_idx on public.profiles (lower(username));

create table if not exists public.daily_schedule (
  day        date primary key,
  card_id    text not null references public.cards(id),
  start_tile int  not null check (start_tile between 0 and 83),
  auto       boolean not null default false,   -- true when the server picked it because the day was empty
  created_at timestamptz not null default now()
);

create table if not exists public.runs (              -- one Guess10 session
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid references auth.users(id) on delete cascade,
  guest_id    uuid,
  cards       text[] not null,
  starts      int[]  not null,
  total       int,
  created_at  timestamptz not null default now(),
  finished_at timestamptz
);
create index if not exists runs_user_idx on public.runs (user_id) where finished_at is not null;

create table if not exists public.rounds (            -- one card played by one player
  id          uuid primary key default gen_random_uuid(),
  mode        text not null check (mode in ('daily','g10')),
  day         date,                                   -- daily only
  run_id      uuid references public.runs(id) on delete cascade,   -- g10 only
  idx         int,                                    -- g10 only: 0..9
  user_id     uuid references auth.users(id) on delete cascade,
  guest_id    uuid,
  card_id     text not null references public.cards(id),
  start_tile  int  not null,
  opened      int[] not null default '{}',
  wrong       int  not null default 0,
  guesses     text[] not null default '{}',
  over        boolean not null default false,
  won         boolean,
  score       int,
  created_at  timestamptz not null default now(),
  finished_at timestamptz
);
create unique index if not exists rounds_daily_user_idx  on public.rounds (day, user_id)  where mode = 'daily' and user_id is not null;
create unique index if not exists rounds_daily_guest_idx on public.rounds (day, guest_id) where mode = 'daily' and user_id is null;
create unique index if not exists rounds_run_idx on public.rounds (run_id, idx) where mode = 'g10';

alter table public.layouts        enable row level security;
alter table public.cards          enable row level security;
alter table public.admins         enable row level security;
alter table public.profiles       enable row level security;
alter table public.daily_schedule enable row level security;
alter table public.runs           enable row level security;
alter table public.rounds         enable row level security;

insert into public.layouts (serie, crop, evo, evot, mega) values
  ('sv',   '{0.087,0.105,0.836,0.360}', '{0.030,0.066,0.148,0.112}', '{0.190,0.089,0.330,0.030}', '{0,0,0,0}'),
  ('me',   '{0.087,0.105,0.836,0.360}', '{0.022,0.060,0.165,0.125}', '{0.185,0.089,0.340,0.030}', '{0.550,0.085,0.385,0.055}'),
  ('swsh', '{0.087,0.105,0.836,0.362}', '{0.036,0.062,0.124,0.096}', '{0.172,0.090,0.360,0.030}', '{0,0,0,0}')
on conflict (serie) do update set crop = excluded.crop, evo = excluded.evo, evot = excluded.evot, mega = excluded.mega;

-- ---------------------------------------------------------------- rules of the game

create or replace function public.g_cols()  returns int language sql immutable as $$ select 12 $$;
create or replace function public.g_rows()  returns int language sql immutable as $$ select 7 $$;
create or replace function public.g_points() returns int language sql immutable as $$ select 1000 $$;  -- points in play per card
create or replace function public.g_penalty() returns int language sql immutable as $$ select 50 $$;  -- per wrong guess
create or replace function public.g_tries() returns int language sql immutable as $$ select 2 $$;     -- wrong guesses allowed
create or replace function public.g_today() returns date language sql stable as $$ select (now() at time zone 'utc')::date $$;

-- tile value: outer frame 5, inner frame 15, centre 60 (tiles numbered 0..83, row by row)
create or replace function public.tile_value(t int) returns int language sql immutable as $$
  select (array[5,15,60,60])[least(least(t / 12, t % 12, 6 - t / 12, 11 - t % 12), 3) + 1]
$$;

-- same text normalisation as the browser: no accents, lower case, only letters and digits separated by one space
create or replace function public.norm_name(s text) returns text language sql immutable as $$
  select trim(regexp_replace(
    translate(lower(coalesce(s, '')), 'áàâäãåéèêëíìîïóòôöõúùûüñçý', 'aaaaaaeeeeiiiiooooouuuuncy'),
    '[^a-z0-9]+', ' ', 'g'))
$$;

-- score of a card: points in play minus the tiles opened (the start tile is free) minus wrong guesses
create or replace function public.round_score(p_opened int[], p_start int, p_wrong int) returns int language sql immutable as $$
  select greatest(0, public.g_points()
    - coalesce((select sum(public.tile_value(t)) from (select distinct t from unnest(p_opened) t) o
                where t <> p_start and t between 0 and 83), 0)
    - public.g_penalty() * p_wrong)::int
$$;

-- covers burnt into the artwork for this card, as fractions of the card [left, top, width, height]
create or replace function public.card_censors(p_card text) returns float8[][] language sql stable as $$
  select coalesce(array_agg(r), '{}') from (
    select l.evo  as r from public.cards c join public.layouts l using (serie) where c.id = p_card and c.has_evo
    union all
    select l.evot      from public.cards c join public.layouts l using (serie) where c.id = p_card and c.has_evo
    union all
    select l.mega      from public.cards c join public.layouts l using (serie) where c.id = p_card and c.name like 'Mega %'
  ) x where r[3] > 0 and r[4] > 0
$$;

-- tiles that show something that is not covered (less than half of the tile under a cover)
create or replace function public.useful_tiles(p_card text) returns int[] language plpgsql stable as $$
declare
  k float8[]; cen float8[]; res int[] := '{}'; t int; bx0 float8; by0 float8; bx1 float8; by1 float8; cov float8;
  i int; n int;
begin
  select l.crop into k from public.cards c join public.layouts l using (serie) where c.id = p_card;
  if k is null then return res; end if;
  cen := public.card_censors(p_card);
  n := coalesce(array_length(cen, 1), 0);
  for t in 0..83 loop
    bx0 := k[1] + (t % 12)::float8 / 12 * k[3];  bx1 := k[1] + (t % 12 + 1)::float8 / 12 * k[3];
    by0 := k[2] + (t / 12)::float8 / 7 * k[4];   by1 := k[2] + (t / 12 + 1)::float8 / 7 * k[4];
    cov := 0;
    for i in 1..n loop
      cov := cov + greatest(0, least(bx1, cen[i][1] + cen[i][3]) - greatest(bx0, cen[i][1]))
                 * greatest(0, least(by1, cen[i][2] + cen[i][4]) - greatest(by0, cen[i][2]))
                 / ((bx1 - bx0) * (by1 - by0));
    end loop;
    if cov <= 0.5 then res := res || t; end if;
  end loop;
  return res;
end $$;

-- free starting tile: random among the cheapest useful tiles
create or replace function public.random_start(p_card text) returns int language sql volatile as $$
  with u as (select unnest(public.useful_tiles(p_card)) t),
       m as (select min(public.tile_value(t)) v from u)
  select coalesce((select t from u, m where public.tile_value(t) = m.v order by random() limit 1),
                  (floor(random() * 84))::int)
$$;

create or replace function public.is_admin() returns boolean language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.admins where user_id = auth.uid())
$$;

-- ---------------------------------------------------------------- internal helpers

-- today's card (or a given day's): if nobody scheduled one, the server picks one at random, the same for everybody
create or replace function public._daily_for(p_day date) returns public.daily_schedule
language plpgsql volatile security definer set search_path = public as $$
declare s public.daily_schedule; c text;
begin
  select * into s from public.daily_schedule where day = p_day;
  if found then return s; end if;
  select id into c from public.cards
   where id not in (select card_id from public.daily_schedule where day > p_day - 365)
   order by random() limit 1;
  insert into public.daily_schedule (day, card_id, start_tile, auto)
  values (p_day, c, public.random_start(c), true)
  on conflict (day) do nothing;
  select * into s from public.daily_schedule where day = p_day;
  return s;
end $$;

create or replace function public._owns(p_user uuid, p_guest uuid, p_req_guest uuid) returns boolean language sql stable as $$
  select (p_user is not null and p_user = auth.uid())
      or (p_user is null and p_guest is not null and p_guest = p_req_guest)
$$;

-- what the browser may know about a round: nothing about the card until it is over
create or replace function public._round_json(r public.rounds) returns jsonb language sql stable security definer set search_path = public as $$
  select jsonb_build_object(
    'round_id', r.id, 'mode', r.mode, 'day', r.day, 'run_id', r.run_id, 'idx', r.idx,
    'start_tile', r.start_tile, 'opened', to_jsonb(r.opened), 'wrong', r.wrong, 'guesses', to_jsonb(r.guesses),
    'over', r.over, 'won', r.won, 'score', r.score,
    'points', public.g_points(), 'tries', public.g_tries(), 'penalty', public.g_penalty(),
    'card', case when r.over then (
      select jsonb_build_object('name', c.name, 'set_name', c.set_name, 'number', c.number, 'image', c.image)
      from public.cards c where c.id = r.card_id) end)
$$;

-- distribution of the day's scores: 0-99, 100-199 ... 900-999, 1000 (11 buckets) plus missed cards
create or replace function public._daily_stats(p_day date, p_score int, p_won boolean) returns jsonb
language sql stable security definer set search_path = public as $$
  with f as (select score, won from public.rounds where mode = 'daily' and day = p_day and over)
  select jsonb_build_object(
    'players', (select count(*) from f),
    'missed',  (select count(*) from f where not won),
    'buckets', (select jsonb_agg((select count(*) from f where won and least(score / 100, 10) = b) order by b)
                from generate_series(0, 10) b),
    'beaten',  (select count(*) from f where (not won and coalesce(p_won, false)) or (won and p_won and score < p_score)),
    'width', 100)
$$;

-- distribution of Guess10 totals, best per player: 0-999 ... 9000-9999, 10000 (11 buckets)
create or replace function public._g10_stats(p_total int) returns jsonb
language sql stable security definer set search_path = public as $$
  with b as (
    select max(total) best from public.runs where finished_at is not null
    group by coalesce(user_id::text, 'g' || guest_id::text))
  select jsonb_build_object(
    'players', (select count(*) from b),
    'buckets', (select jsonb_agg((select count(*) from b where least(best / 1000, 10) = k) order by k)
                from generate_series(0, 10) k),
    'beaten',  (select count(*) from b where best < p_total),
    'width', 1000)
$$;

create or replace function public._g10_round(p_run public.runs, p_idx int) returns public.rounds
language plpgsql volatile security definer set search_path = public as $$
declare r public.rounds;
begin
  select * into r from public.rounds where run_id = p_run.id and idx = p_idx and mode = 'g10';
  if found then return r; end if;
  insert into public.rounds (mode, run_id, idx, user_id, guest_id, card_id, start_tile, opened)
  values ('g10', p_run.id, p_idx, p_run.user_id, p_run.guest_id, p_run.cards[p_idx + 1], p_run.starts[p_idx + 1],
          array[p_run.starts[p_idx + 1]])
  returning * into r;
  return r;
end $$;

create or replace function public._run_json(p_run public.runs) returns jsonb language sql stable security definer set search_path = public as $$
  select jsonb_build_object('run_id', p_run.id, 'cards', 10, 'finished', p_run.finished_at is not null,
    'total', coalesce(p_run.total, (select coalesce(sum(score), 0) from public.rounds where run_id = p_run.id and over)),
    'done', (select count(*) from public.rounds where run_id = p_run.id and over))
$$;

-- ---------------------------------------------------------------- game API (called from the browser)

-- Daily: today's round for this player, created if needed
create or replace function public.daily_get(p_guest uuid) returns jsonb
language plpgsql volatile security definer set search_path = public as $$
declare d date := public.g_today(); s public.daily_schedule; r public.rounds; uid uuid := auth.uid(); res jsonb;
begin
  if uid is null and p_guest is null then raise exception 'missing player'; end if;
  s := public._daily_for(d);
  if uid is not null then
    select * into r from public.rounds where mode = 'daily' and day = d and user_id = uid;
  else
    select * into r from public.rounds where mode = 'daily' and day = d and user_id is null and guest_id = p_guest;
  end if;
  if not found then
    insert into public.rounds (mode, day, user_id, guest_id, card_id, start_tile, opened)
    values ('daily', d, uid, p_guest, s.card_id, s.start_tile, array[s.start_tile])
    on conflict do nothing
    returning * into r;
    if r.id is null then   -- created at the same moment by another tab
      select * into r from public.rounds where mode = 'daily' and day = d
        and ((uid is not null and user_id = uid) or (uid is null and user_id is null and guest_id = p_guest));
    end if;
  end if;
  res := public._round_json(r) || jsonb_build_object('next_reset', ((d + 1)::timestamp at time zone 'utc'));
  if r.over then res := res || jsonb_build_object('stats', public._daily_stats(d, r.score, r.won)); end if;
  return res;
end $$;

-- a guess; p_opened = tiles the player has opened so far
create or replace function public.guess(p_round uuid, p_guest uuid, p_name text, p_opened int[]) returns jsonb
language plpgsql volatile security definer set search_path = public as $$
declare r public.rounds; g text := public.norm_name(p_name); c public.cards; res jsonb; v_repeat boolean := false;
begin
  select * into r from public.rounds where id = p_round for update;
  if not found or not public._owns(r.user_id, r.guest_id, p_guest) then raise exception 'round not found'; end if;
  if r.over or g = '' then return public._round_json(r); end if;
  select * into c from public.cards where id = r.card_id;
  r.opened := (select coalesce(array_agg(distinct t order by t), '{}') from unnest(r.opened || coalesce(p_opened, '{}')) t where t between 0 and 83);
  if g = public.norm_name(c.name) then
    r.over := true; r.won := true; r.score := public.round_score(r.opened, r.start_tile, r.wrong); r.finished_at := now();
  elsif g = any(r.guesses) then
    v_repeat := true;
  else
    r.wrong := r.wrong + 1; r.guesses := r.guesses || g;
    if r.wrong >= public.g_tries() then r.over := true; r.won := false; r.score := 0; r.finished_at := now(); end if;
  end if;
  update public.rounds set opened = r.opened, wrong = r.wrong, guesses = r.guesses, over = r.over, won = r.won,
    score = r.score, finished_at = r.finished_at where id = r.id;
  res := public._round_json(r) || jsonb_build_object('repeat', v_repeat,
    'potential', public.round_score(r.opened, r.start_tile, r.wrong));
  if r.over and r.mode = 'daily' then res := res || jsonb_build_object('stats', public._daily_stats(r.day, r.score, r.won)); end if;
  return res;
end $$;

create or replace function public.give_up(p_round uuid, p_guest uuid, p_opened int[]) returns jsonb
language plpgsql volatile security definer set search_path = public as $$
declare r public.rounds; res jsonb;
begin
  select * into r from public.rounds where id = p_round for update;
  if not found or not public._owns(r.user_id, r.guest_id, p_guest) then raise exception 'round not found'; end if;
  if not r.over then
    update public.rounds set over = true, won = false, score = 0, finished_at = now(),
      opened = (select coalesce(array_agg(distinct t order by t), '{}') from unnest(r.opened || coalesce(p_opened, '{}')) t where t between 0 and 83)
    where id = r.id returning * into r;
  end if;
  res := public._round_json(r);
  if r.mode = 'daily' then res := res || jsonb_build_object('stats', public._daily_stats(r.day, r.score, r.won)); end if;
  return res;
end $$;

-- Guess10: a new session of 10 random cards (never today's daily card)
create or replace function public.g10_start(p_guest uuid) returns jsonb
language plpgsql volatile security definer set search_path = public as $$
declare uid uuid := auth.uid(); cs text[]; st int[]; run public.runs; r public.rounds; today_card text;
begin
  if uid is null and p_guest is null then raise exception 'missing player'; end if;
  select card_id into today_card from public.daily_schedule where day = public.g_today();
  select array_agg(id), array_agg(public.random_start(id)) into cs, st
    from (select id from public.cards where id is distinct from today_card order by random() limit 10) x;
  insert into public.runs (user_id, guest_id, cards, starts) values (uid, p_guest, cs, st) returning * into run;
  r := public._g10_round(run, 0);
  return public._run_json(run) || jsonb_build_object('round', public._round_json(r));
end $$;

-- Guess10: where a session stands (to resume it after a reload)
create or replace function public.g10_state(p_run uuid, p_guest uuid) returns jsonb
language plpgsql volatile security definer set search_path = public as $$
declare run public.runs; r public.rounds;
begin
  select * into run from public.runs where id = p_run;
  if not found or not public._owns(run.user_id, run.guest_id, p_guest) then raise exception 'run not found'; end if;
  select * into r from public.rounds where run_id = run.id order by idx desc limit 1;
  return public._run_json(run) || jsonb_build_object('round', public._round_json(r))
    || case when run.finished_at is not null then jsonb_build_object('stats', public._g10_stats(run.total)) else '{}'::jsonb end;
end $$;

-- Guess10: next card, or the final result after the tenth
create or replace function public.g10_next(p_run uuid, p_guest uuid) returns jsonb
language plpgsql volatile security definer set search_path = public as $$
declare run public.runs; last public.rounds; r public.rounds;
begin
  select * into run from public.runs where id = p_run for update;
  if not found or not public._owns(run.user_id, run.guest_id, p_guest) then raise exception 'run not found'; end if;
  select * into last from public.rounds where run_id = run.id order by idx desc limit 1;
  if not last.over then
    return public._run_json(run) || jsonb_build_object('round', public._round_json(last));
  end if;
  if last.idx < 9 then
    r := public._g10_round(run, last.idx + 1);
    return public._run_json(run) || jsonb_build_object('round', public._round_json(r));
  end if;
  if run.finished_at is null then
    update public.runs set finished_at = now(),
      total = (select coalesce(sum(score), 0) from public.rounds where run_id = run.id)
    where id = run.id returning * into run;
  end if;
  return public._run_json(run) || jsonb_build_object('round', public._round_json(last), 'stats', public._g10_stats(run.total));
end $$;

-- world leaderboard: best Guess10 of each signed-in player
create or replace function public.leaderboard(p_limit int default 50) returns jsonb
language sql stable security definer set search_path = public as $$
  with best as (
    select distinct on (r.user_id) r.user_id, r.total, r.finished_at
    from public.runs r where r.finished_at is not null and r.user_id is not null
    order by r.user_id, r.total desc, r.finished_at asc),
  ranked as (
    select rank() over (order by b.total desc) as pos, p.username, b.total, b.finished_at, b.user_id
    from best b join public.profiles p on p.id = b.user_id)
  select jsonb_build_object(
    'top', coalesce((select jsonb_agg(jsonb_build_object('pos', pos, 'username', username, 'total', total)
                     order by pos, finished_at) from (select * from ranked order by pos, finished_at limit least(p_limit, 200)) t), '[]'),
    'me',  (select jsonb_build_object('pos', pos, 'username', username, 'total', total) from ranked where user_id = auth.uid()),
    'players', (select count(*) from ranked))
$$;

-- ---------------------------------------------------------------- account

create or replace function public.my_profile() returns jsonb
language sql stable security definer set search_path = public as $$
  select case when auth.uid() is null then null else jsonb_build_object(
    'username', (select username from public.profiles where id = auth.uid()),
    'is_admin', public.is_admin()) end
$$;

create or replace function public.set_username(p_name text) returns jsonb
language plpgsql volatile security definer set search_path = public as $$
declare n text := trim(coalesce(p_name, ''));
begin
  if auth.uid() is null then raise exception 'sign in first'; end if;
  if n !~ '^[A-Za-z0-9_]{3,16}$' then raise exception 'invalid username'; end if;
  if exists (select 1 from public.profiles where lower(username) = lower(n) and id <> auth.uid()) then
    raise exception 'username taken';
  end if;
  insert into public.profiles (id, username) values (auth.uid(), n)
  on conflict (id) do update set username = excluded.username;
  return public.my_profile();
end $$;

-- after signing in: what was played as a guest in this browser moves to the account
create or replace function public.claim_guest(p_guest uuid) returns void
language plpgsql volatile security definer set search_path = public as $$
declare uid uuid := auth.uid();
begin
  if uid is null or p_guest is null then return; end if;
  update public.rounds g set user_id = uid
   where g.guest_id = p_guest and g.user_id is null
     and not (g.mode = 'daily' and exists (
       select 1 from public.rounds o where o.mode = 'daily' and o.day = g.day and o.user_id = uid));
  update public.runs set user_id = uid where guest_id = p_guest and user_id is null;
end $$;

-- ---------------------------------------------------------------- admin

create or replace function public._need_admin() returns void language plpgsql stable security definer set search_path = public as $$
begin
  if not public.is_admin() then raise exception 'not allowed'; end if;
end $$;

create or replace function public.admin_search(p_q text) returns jsonb
language plpgsql stable security definer set search_path = public as $$
begin
  perform public._need_admin();
  return coalesce((select jsonb_agg(to_jsonb(x)) from (
    select c.id, c.name, c.set_name, c.number, c.rarity, c.serie, c.image,
           (select max(day) from public.daily_schedule s where s.card_id = c.id) as last_daily
    from public.cards c
    where public.norm_name(c.name) like '%' || public.norm_name(p_q) || '%'
       or lower(c.set_name) like '%' || lower(trim(p_q)) || '%'
       or lower(c.id) = lower(trim(p_q))
    order by (public.norm_name(c.name) like public.norm_name(p_q) || '%') desc, c.name, c.set_name, c.number
    limit 60) x), '[]');
end $$;

create or replace function public.admin_card(p_card text) returns jsonb
language plpgsql stable security definer set search_path = public as $$
begin
  perform public._need_admin();
  return (select jsonb_build_object('id', c.id, 'name', c.name, 'set_name', c.set_name, 'number', c.number,
      'rarity', c.rarity, 'serie', c.serie, 'image', c.image, 'useful', to_jsonb(public.useful_tiles(c.id)))
    from public.cards c where c.id = p_card);
end $$;

create or replace function public.admin_schedule(p_from date, p_to date) returns jsonb
language plpgsql stable security definer set search_path = public as $$
begin
  perform public._need_admin();
  return jsonb_build_object('today', public.g_today(), 'days', coalesce((select jsonb_agg(to_jsonb(x) order by x.day) from (
    select s.day, s.card_id, s.start_tile, s.auto, c.name, c.set_name, c.number, c.serie, c.image,
           (select count(*) from public.rounds r where r.mode = 'daily' and r.day = s.day) as players
    from public.daily_schedule s join public.cards c on c.id = s.card_id
    where s.day between p_from and p_to) x), '[]'));
end $$;

-- a day can be changed only while nobody has played it yet
create or replace function public.admin_set_daily(p_day date, p_card text, p_start int) returns jsonb
language plpgsql volatile security definer set search_path = public as $$
begin
  perform public._need_admin();
  if p_day < public.g_today() then raise exception 'past day'; end if;
  if exists (select 1 from public.rounds where mode = 'daily' and day = p_day) then raise exception 'already played'; end if;
  if not exists (select 1 from public.cards where id = p_card) then raise exception 'unknown card'; end if;
  if p_start is null or p_start not between 0 and 83 then raise exception 'bad tile'; end if;
  insert into public.daily_schedule (day, card_id, start_tile, auto) values (p_day, p_card, p_start, false)
  on conflict (day) do update set card_id = excluded.card_id, start_tile = excluded.start_tile, auto = false, created_at = now();
  return public.admin_schedule(p_day, p_day);
end $$;

create or replace function public.admin_clear_daily(p_day date) returns void
language plpgsql volatile security definer set search_path = public as $$
begin
  perform public._need_admin();
  if p_day < public.g_today() then raise exception 'past day'; end if;
  if exists (select 1 from public.rounds where mode = 'daily' and day = p_day) then raise exception 'already played'; end if;
  delete from public.daily_schedule where day = p_day;
end $$;

-- ---------------------------------------------------------------- permissions

revoke all on all tables in schema public from anon, authenticated;
revoke execute on all functions in schema public from public, anon, authenticated;
grant execute on function public.daily_get(uuid), public.guess(uuid, uuid, text, int[]), public.give_up(uuid, uuid, int[]),
  public.g10_start(uuid), public.g10_state(uuid, uuid), public.g10_next(uuid, uuid), public.leaderboard(int),
  public.my_profile() to anon, authenticated;
grant execute on function public.set_username(text), public.claim_guest(uuid),
  public.admin_search(text), public.admin_card(text), public.admin_schedule(date, date),
  public.admin_set_daily(date, text, int), public.admin_clear_daily(date) to authenticated;
-- internal helpers keep working inside security-definer functions (they run as the owner)
-- the image function runs with the service role and reads these tables directly
grant select on public.rounds, public.cards, public.layouts, public.admins to service_role;
