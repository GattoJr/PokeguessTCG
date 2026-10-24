-- 24/10/2026: finer score distribution for the chart, and faster artwork.
--
-- Artwork: each picture (covered, or uncovered once the card is over) is saved once in a PUBLIC storage bucket
-- under an unguessable name, so the browser loads it straight from Supabase's CDN instead of waking the
-- image function every time. The name is md5(secret : card : variant): it reveals nothing about the card,
-- and the browser only receives the uncovered name after the card is over.

create table if not exists public.app_secret (id int primary key default 1 check (id = 1), secret text not null);
alter table public.app_secret enable row level security;
insert into public.app_secret (id, secret) values (1, gen_random_uuid()::text || gen_random_uuid()::text)
on conflict (id) do nothing;

create or replace function public.art_key(p_card text, p_full boolean) returns text
language sql stable security definer set search_path = public as $$
  select md5((select secret from public.app_secret where id = 1) || ':' || p_card || ':' || case when p_full then 'full' else 'tiles' end)
$$;

-- public bucket for the pictures (only on Supabase; skipped where there is no storage schema)
do $$ begin
  if to_regclass('storage.buckets') is not null then
    insert into storage.buckets (id, name, public) values ('art', 'art', true)
    on conflict (id) do update set public = true;
  end if;
end $$;

-- what the browser may know about a round: nothing about the card until it is over
create or replace function public._round_json(r public.rounds) returns jsonb language sql stable security definer set search_path = public as $$
  select jsonb_build_object(
    'round_id', r.id, 'mode', r.mode, 'day', r.day, 'run_id', r.run_id, 'idx', r.idx,
    'start_tile', r.start_tile, 'opened', to_jsonb(r.opened), 'wrong', r.wrong, 'guesses', to_jsonb(r.guesses),
    'over', r.over, 'won', r.won, 'score', r.score,
    'points', public.g_points(), 'tries', public.g_tries(), 'penalty', public.g_penalty(),
    'art', public.art_key(r.card_id, false),
    'art_full', case when r.over then public.art_key(r.card_id, true) end,
    -- Guess10: the next card's picture, so the browser can load it while this card is played
    'next_art', case when r.mode = 'g10' and r.idx < 9 then
      (select public.art_key(x.cards[r.idx + 2], false) from public.runs x where x.id = r.run_id) end,
    'card', case when r.over then (
      select jsonb_build_object('name', c.name, 'set_name', c.set_name, 'number', c.number, 'image', c.image)
      from public.cards c where c.id = r.card_id) end)
$$;

-- Daily distribution: 21 columns of 50 points (0-49, 50-99 ... 950-999, 1000). A missed card counts as 0.
create or replace function public._daily_stats(p_day date, p_score int, p_won boolean) returns jsonb
language sql stable security definer set search_path = public as $$
  with f as (select coalesce(score, 0) as score, won from public.rounds where mode = 'daily' and day = p_day and over)
  select jsonb_build_object(
    'players', (select count(*) from f),
    'missed',  (select count(*) from f where not won),
    'buckets', (select jsonb_agg((select count(*) from f where least(score / 50, 20) = b) order by b)
                from generate_series(0, 20) b),
    'beaten',  (select count(*) from f where (not won and coalesce(p_won, false)) or (won and p_won and score < p_score)),
    'width', 50)
$$;

-- Guess10 distribution of each player's best total: 21 columns of 500 points (0-499 ... 9500-9999, 10000)
create or replace function public._g10_stats(p_total int) returns jsonb
language sql stable security definer set search_path = public as $$
  with b as (
    select max(total) best from public.runs where finished_at is not null
    group by coalesce(user_id::text, 'g' || guest_id::text))
  select jsonb_build_object(
    'players', (select count(*) from b),
    'buckets', (select jsonb_agg((select count(*) from b where least(best / 500, 20) = k) order by k)
                from generate_series(0, 20) k),
    'beaten',  (select count(*) from b where best < p_total),
    'width', 500)
$$;

revoke execute on function public.art_key(text, boolean) from public, anon, authenticated;
grant execute on function public.art_key(text, boolean) to service_role;
grant select on public.runs to service_role;
