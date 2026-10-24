-- 24/10/2026: "Guess10" becomes "Booster" also in the database, and Hard versions of both modes.
--
-- Hard: same game, but only the outer frame tiles (worth 5) can be opened. 200 points in play per card
-- (170 = the 34 outer tiles, plus 30 for one wrong guess), each wrong guess costs 30, 2 guesses.
-- Daily Hard has its own card, distribution and calendar; Booster Hard has its own leaderboard.
-- Boosters in progress under the old name are dropped (agreed).

-- ---------------------------------------------------------------- old API out
drop function if exists public.g10_start(uuid);
drop function if exists public.g10_state(uuid, uuid);
drop function if exists public.g10_next(uuid, uuid);
drop function if exists public._g10_round(public.runs, int);
drop function if exists public._g10_stats(int);
drop function if exists public.daily_get(uuid);
drop function if exists public._daily_for(date);
drop function if exists public._daily_stats(date, int, boolean);
drop function if exists public.leaderboard(int);
drop function if exists public.admin_set_daily(date, text, int);
drop function if exists public.admin_clear_daily(date);

-- ---------------------------------------------------------------- tables
alter table public.rounds add column if not exists hard boolean not null default false;
alter table public.runs   add column if not exists hard boolean not null default false;
alter table public.daily_schedule add column if not exists hard boolean not null default false;

drop index if exists public.rounds_daily_user_idx;
drop index if exists public.rounds_daily_guest_idx;
drop index if exists public.rounds_run_idx;
alter table public.rounds drop constraint if exists rounds_mode_check;
delete from public.rounds where mode = 'g10' and not over;          -- unfinished old boosters
update public.rounds set mode = 'booster' where mode = 'g10';
alter table public.rounds add constraint rounds_mode_check check (mode in ('daily', 'booster'));
create unique index rounds_daily_user_idx  on public.rounds (day, hard, user_id)  where mode = 'daily' and user_id is not null;
create unique index rounds_daily_guest_idx on public.rounds (day, hard, guest_id) where mode = 'daily' and user_id is null;
create unique index rounds_run_idx on public.rounds (run_id, idx) where mode = 'booster';

alter table public.daily_schedule drop constraint if exists daily_schedule_pkey;
alter table public.daily_schedule add primary key (day, hard);

-- ---------------------------------------------------------------- rules
create or replace function public.g_points_for(p_hard boolean) returns int language sql immutable as $$
  select case when p_hard then 200 else 1000 end $$;
create or replace function public.g_penalty_for(p_hard boolean) returns int language sql immutable as $$
  select case when p_hard then 30 else 50 end $$;
-- tiles that can be opened: all of them, or in Hard only the outer frame
create or replace function public.tile_ok(t int, p_hard boolean) returns boolean language sql immutable as $$
  select t between 0 and 83 and (not p_hard or public.tile_value(t) = 5) $$;

create or replace function public.round_score(p_opened int[], p_start int, p_wrong int, p_hard boolean) returns int
language sql immutable as $$
  select greatest(0, public.g_points_for(p_hard)
    - coalesce((select sum(public.tile_value(t)) from (select distinct t from unnest(p_opened) t) o
                where t <> p_start and public.tile_ok(t, p_hard)), 0)
    - public.g_penalty_for(p_hard) * p_wrong)::int
$$;
drop function if exists public.round_score(int[], int, int);

create or replace function public._clean_tiles(p_opened int[], p_hard boolean) returns int[] language sql immutable as $$
  select coalesce(array_agg(distinct t order by t), '{}') from unnest(p_opened) t where public.tile_ok(t, p_hard)
$$;

-- ---------------------------------------------------------------- what the browser sees
create or replace function public._round_json(r public.rounds) returns jsonb language sql stable security definer set search_path = public as $$
  select jsonb_build_object(
    'round_id', r.id, 'mode', r.mode, 'hard', r.hard, 'day', r.day, 'run_id', r.run_id, 'idx', r.idx,
    'start_tile', r.start_tile, 'opened', to_jsonb(r.opened), 'wrong', r.wrong, 'guesses', to_jsonb(r.guesses),
    'over', r.over, 'won', r.won, 'score', r.score,
    'points', public.g_points_for(r.hard), 'tries', public.g_tries(), 'penalty', public.g_penalty_for(r.hard),
    'art', public.art_key(r.card_id, false),
    'art_full', case when r.over then public.art_key(r.card_id, true) end,
    'next_art', case when r.mode = 'booster' and r.idx < 9 then
      (select public.art_key(x.cards[r.idx + 2], false) from public.runs x where x.id = r.run_id) end,
    'card', case when r.over then (
      select jsonb_build_object('name', c.name, 'set_name', c.set_name, 'number', c.number, 'image', c.image)
      from public.cards c where c.id = r.card_id) end)
$$;

-- distribution: 21 columns from 0 to the maximum (Daily 50 points wide, Daily Hard 10); a missed card counts as 0
create or replace function public._daily_stats(p_day date, p_hard boolean, p_score int, p_won boolean) returns jsonb
language sql stable security definer set search_path = public as $$
  with f as (select coalesce(score, 0) as score, won from public.rounds
             where mode = 'daily' and day = p_day and hard = p_hard and over),
       w as (select case when p_hard then 10 else 50 end as v)
  select jsonb_build_object(
    'players', (select count(*) from f),
    'missed',  (select count(*) from f where not won),
    'buckets', (select jsonb_agg((select count(*) from f where least(score / w.v, 20) = b) order by b)
                from generate_series(0, 20) b),
    'beaten',  (select count(*) from f where (not won and coalesce(p_won, false)) or (won and p_won and score < p_score)),
    'width', w.v)
  from w
$$;

-- Booster: best total of each player (Booster 500 points wide, Booster Hard 100)
create or replace function public._booster_stats(p_total int, p_hard boolean) returns jsonb
language sql stable security definer set search_path = public as $$
  with b as (
    select max(total) best from public.runs where finished_at is not null and hard = p_hard
    group by coalesce(user_id::text, 'g' || guest_id::text)),
       w as (select case when p_hard then 100 else 500 end as v)
  select jsonb_build_object(
    'players', (select count(*) from b),
    'buckets', (select jsonb_agg((select count(*) from b where least(best / w.v, 20) = k) order by k)
                from generate_series(0, 20) k),
    'beaten',  (select count(*) from b where best < p_total),
    'width', w.v)
  from w
$$;

create or replace function public._run_json(p_run public.runs) returns jsonb language sql stable security definer set search_path = public as $$
  select jsonb_build_object('run_id', p_run.id, 'cards', 10, 'hard', p_run.hard, 'finished', p_run.finished_at is not null,
    'total', coalesce(p_run.total, (select coalesce(sum(score), 0) from public.rounds where run_id = p_run.id and over)),
    'done', (select count(*) from public.rounds where run_id = p_run.id and over))
$$;

-- ---------------------------------------------------------------- Daily
-- the day's card for a mode; if none is scheduled the server picks one, never the other mode's card of that day
create or replace function public._daily_for(p_day date, p_hard boolean) returns public.daily_schedule
language plpgsql volatile security definer set search_path = public as $$
declare s public.daily_schedule; c text;
begin
  select * into s from public.daily_schedule where day = p_day and hard = p_hard;
  if found then return s; end if;
  select id into c from public.cards
   where id not in (select card_id from public.daily_schedule where day > p_day - 365)
   order by random() limit 1;
  insert into public.daily_schedule (day, hard, card_id, start_tile, auto)
  values (p_day, p_hard, c, public.random_start(c), true)
  on conflict (day, hard) do nothing;
  select * into s from public.daily_schedule where day = p_day and hard = p_hard;
  return s;
end $$;

create or replace function public.daily_get(p_guest uuid, p_hard boolean default false) returns jsonb
language plpgsql volatile security definer set search_path = public as $$
declare d date := public.g_today(); s public.daily_schedule; r public.rounds; uid uuid := auth.uid(); res jsonb;
        h boolean := coalesce(p_hard, false);
begin
  if uid is null and p_guest is null then raise exception 'missing player'; end if;
  s := public._daily_for(d, h);
  if uid is not null then
    select * into r from public.rounds where mode = 'daily' and day = d and hard = h and user_id = uid;
  else
    select * into r from public.rounds where mode = 'daily' and day = d and hard = h and user_id is null and guest_id = p_guest;
  end if;
  if not found then
    insert into public.rounds (mode, hard, day, user_id, guest_id, card_id, start_tile, opened)
    values ('daily', h, d, uid, p_guest, s.card_id, s.start_tile, array[s.start_tile])
    on conflict do nothing
    returning * into r;
    if r.id is null then
      select * into r from public.rounds where mode = 'daily' and day = d and hard = h
        and ((uid is not null and user_id = uid) or (uid is null and user_id is null and guest_id = p_guest));
    end if;
  end if;
  res := public._round_json(r) || jsonb_build_object('next_reset', ((d + 1)::timestamp at time zone 'utc'));
  if r.over then res := res || jsonb_build_object('stats', public._daily_stats(d, h, r.score, r.won)); end if;
  return res;
end $$;

-- ---------------------------------------------------------------- playing a card (both modes)
create or replace function public.guess(p_round uuid, p_guest uuid, p_name text, p_opened int[]) returns jsonb
language plpgsql volatile security definer set search_path = public as $$
declare r public.rounds; g text := public.norm_name(p_name); c public.cards; res jsonb; v_repeat boolean := false;
begin
  select * into r from public.rounds where id = p_round for update;
  if not found or not public._owns(r.user_id, r.guest_id, p_guest) then raise exception 'round not found'; end if;
  if r.over or g = '' then return public._round_json(r); end if;
  select * into c from public.cards where id = r.card_id;
  r.opened := public._clean_tiles(r.opened || coalesce(p_opened, '{}'), r.hard);
  if g = public.norm_name(c.name) then
    r.over := true; r.won := true; r.score := public.round_score(r.opened, r.start_tile, r.wrong, r.hard); r.finished_at := now();
  elsif g = any(r.guesses) then
    v_repeat := true;
  else
    r.wrong := r.wrong + 1; r.guesses := r.guesses || g;
    if r.wrong >= public.g_tries() then r.over := true; r.won := false; r.score := 0; r.finished_at := now(); end if;
  end if;
  update public.rounds set opened = r.opened, wrong = r.wrong, guesses = r.guesses, over = r.over, won = r.won,
    score = r.score, finished_at = r.finished_at where id = r.id;
  res := public._round_json(r) || jsonb_build_object('repeat', v_repeat,
    'potential', public.round_score(r.opened, r.start_tile, r.wrong, r.hard));
  if r.over and r.mode = 'daily' then res := res || jsonb_build_object('stats', public._daily_stats(r.day, r.hard, r.score, r.won)); end if;
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
      opened = public._clean_tiles(r.opened || coalesce(p_opened, '{}'), r.hard)
    where id = r.id returning * into r;
  end if;
  res := public._round_json(r);
  if r.mode = 'daily' then res := res || jsonb_build_object('stats', public._daily_stats(r.day, r.hard, r.score, r.won)); end if;
  return res;
end $$;

-- ---------------------------------------------------------------- Booster
create or replace function public._booster_round(p_run public.runs, p_idx int) returns public.rounds
language plpgsql volatile security definer set search_path = public as $$
declare r public.rounds;
begin
  select * into r from public.rounds where run_id = p_run.id and idx = p_idx and mode = 'booster';
  if found then return r; end if;
  insert into public.rounds (mode, hard, run_id, idx, user_id, guest_id, card_id, start_tile, opened)
  values ('booster', p_run.hard, p_run.id, p_idx, p_run.user_id, p_run.guest_id, p_run.cards[p_idx + 1], p_run.starts[p_idx + 1],
          array[p_run.starts[p_idx + 1]])
  returning * into r;
  return r;
end $$;

-- a new booster of 10 random cards (never one of today's daily cards)
create or replace function public.booster_start(p_guest uuid, p_hard boolean default false) returns jsonb
language plpgsql volatile security definer set search_path = public as $$
declare uid uuid := auth.uid(); cs text[]; st int[]; run public.runs; r public.rounds;
begin
  if uid is null and p_guest is null then raise exception 'missing player'; end if;
  select array_agg(id), array_agg(public.random_start(id)) into cs, st
    from (select id from public.cards
          where id not in (select card_id from public.daily_schedule where day = public.g_today())
          order by random() limit 10) x;
  insert into public.runs (user_id, guest_id, cards, starts, hard) values (uid, p_guest, cs, st, coalesce(p_hard, false))
  returning * into run;
  r := public._booster_round(run, 0);
  return public._run_json(run) || jsonb_build_object('round', public._round_json(r));
end $$;

create or replace function public.booster_state(p_run uuid, p_guest uuid) returns jsonb
language plpgsql volatile security definer set search_path = public as $$
declare run public.runs; r public.rounds;
begin
  select * into run from public.runs where id = p_run;
  if not found or not public._owns(run.user_id, run.guest_id, p_guest) then raise exception 'run not found'; end if;
  select * into r from public.rounds where run_id = run.id order by idx desc limit 1;
  if r.id is null then raise exception 'run not found'; end if;
  return public._run_json(run) || jsonb_build_object('round', public._round_json(r))
    || case when run.finished_at is not null then jsonb_build_object('stats', public._booster_stats(run.total, run.hard)) else '{}'::jsonb end;
end $$;

create or replace function public.booster_next(p_run uuid, p_guest uuid) returns jsonb
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
    r := public._booster_round(run, last.idx + 1);
    return public._run_json(run) || jsonb_build_object('round', public._round_json(r));
  end if;
  if run.finished_at is null then
    update public.runs set finished_at = now(),
      total = (select coalesce(sum(score), 0) from public.rounds where run_id = run.id)
    where id = run.id returning * into run;
  end if;
  return public._run_json(run) || jsonb_build_object('round', public._round_json(last), 'stats', public._booster_stats(run.total, run.hard));
end $$;

-- world leaderboard: best booster of each signed-in player, Normal or Hard
create or replace function public.leaderboard(p_limit int default 50, p_hard boolean default false) returns jsonb
language sql stable security definer set search_path = public as $$
  with best as (
    select distinct on (r.user_id) r.user_id, r.total, r.finished_at
    from public.runs r where r.finished_at is not null and r.user_id is not null and r.hard = coalesce(p_hard, false)
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

create or replace function public.claim_guest(p_guest uuid) returns void
language plpgsql volatile security definer set search_path = public as $$
declare uid uuid := auth.uid();
begin
  if uid is null or p_guest is null then return; end if;
  update public.rounds g set user_id = uid
   where g.guest_id = p_guest and g.user_id is null
     and not (g.mode = 'daily' and exists (
       select 1 from public.rounds o where o.mode = 'daily' and o.day = g.day and o.hard = g.hard and o.user_id = uid));
  update public.runs set user_id = uid where guest_id = p_guest and user_id is null;
end $$;

-- ---------------------------------------------------------------- admin
create or replace function public.admin_schedule(p_from date, p_to date) returns jsonb
language plpgsql stable security definer set search_path = public as $$
begin
  perform public._need_admin();
  return jsonb_build_object('today', public.g_today(), 'days', coalesce((select jsonb_agg(to_jsonb(x) order by x.day, x.hard) from (
    select s.day, s.hard, s.card_id, s.start_tile, s.auto, c.name, c.set_name, c.number, c.serie, c.image,
           (select count(*) from public.rounds r where r.mode = 'daily' and r.day = s.day and r.hard = s.hard) as players
    from public.daily_schedule s join public.cards c on c.id = s.card_id
    where s.day between p_from and p_to) x), '[]'));
end $$;

create or replace function public.admin_set_daily(p_day date, p_card text, p_start int, p_hard boolean default false) returns jsonb
language plpgsql volatile security definer set search_path = public as $$
declare h boolean := coalesce(p_hard, false);
begin
  perform public._need_admin();
  if p_day < public.g_today() then raise exception 'past day'; end if;
  if exists (select 1 from public.rounds where mode = 'daily' and day = p_day and hard = h) then raise exception 'already played'; end if;
  if not exists (select 1 from public.cards where id = p_card) then raise exception 'unknown card'; end if;
  if p_start is null or not public.tile_ok(p_start, h) then raise exception 'bad tile'; end if;
  insert into public.daily_schedule (day, hard, card_id, start_tile, auto) values (p_day, h, p_card, p_start, false)
  on conflict (day, hard) do update set card_id = excluded.card_id, start_tile = excluded.start_tile, auto = false, created_at = now();
  return public.admin_schedule(p_day, p_day);
end $$;

create or replace function public.admin_clear_daily(p_day date, p_hard boolean default false) returns void
language plpgsql volatile security definer set search_path = public as $$
declare h boolean := coalesce(p_hard, false);
begin
  perform public._need_admin();
  if p_day < public.g_today() then raise exception 'past day'; end if;
  if exists (select 1 from public.rounds where mode = 'daily' and day = p_day and hard = h) then raise exception 'already played'; end if;
  delete from public.daily_schedule where day = p_day and hard = h;
end $$;

-- ---------------------------------------------------------------- permissions
revoke execute on all functions in schema public from public, anon, authenticated;
grant execute on function public.daily_get(uuid, boolean), public.guess(uuid, uuid, text, int[]), public.give_up(uuid, uuid, int[]),
  public.booster_start(uuid, boolean), public.booster_state(uuid, uuid), public.booster_next(uuid, uuid),
  public.leaderboard(int, boolean), public.my_profile() to anon, authenticated;
grant execute on function public.set_username(text), public.claim_guest(uuid),
  public.admin_search(text), public.admin_card(text), public.admin_schedule(date, date),
  public.admin_set_daily(date, text, int, boolean), public.admin_clear_daily(date, boolean) to authenticated;
grant execute on function public.art_key(text, boolean) to service_role;
