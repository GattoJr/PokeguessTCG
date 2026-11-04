-- Badges (medals). The browser works out which badges a player has from two lists sent by my_badges():
--   daily:   the days on which the player named the Daily card (Normal and Hard separately), oldest first;
--   booster: the player's Booster records over time (each finished Booster that beat all the earlier ones),
--            as [finished_at, total], oldest first.
-- Read-only: nothing new is stored. Badges are earned only by named Daily cards and finished Boosters,
-- and they follow the games when a guest signs in (claim_guest moves the games to the account).

create or replace function public.my_badges(p_guest uuid) returns jsonb
language sql stable security definer set search_path = public as $$
  with me as (select auth.uid() as uid),
  daily as (
    select r.hard, r.day
    from public.rounds r, me
    where r.mode = 'daily' and r.over and r.won
      and (case when me.uid is not null then r.user_id = me.uid
                else r.user_id is null and p_guest is not null and r.guest_id = p_guest end)),
  runs as (
    select u.hard, u.finished_at, u.total,
           max(u.total) over (partition by u.hard order by u.finished_at, u.id
                              rows between unbounded preceding and 1 preceding) as before
    from public.runs u, me
    where u.finished_at is not null and u.total is not null
      and (case when me.uid is not null then u.user_id = me.uid
                else u.user_id is null and p_guest is not null and u.guest_id = p_guest end)),
  records as (select * from runs where before is null or total > before)
  select jsonb_build_object(
    'today', public.g_today(),
    'daily', jsonb_build_object(
      'normal', coalesce((select jsonb_agg(day order by day) from daily where not hard), '[]'),
      'hard',   coalesce((select jsonb_agg(day order by day) from daily where hard), '[]')),
    'booster', jsonb_build_object(
      'normal', coalesce((select jsonb_agg(jsonb_build_array(finished_at, total) order by finished_at) from records where not hard), '[]'),
      'hard',   coalesce((select jsonb_agg(jsonb_build_array(finished_at, total) order by finished_at) from records where hard), '[]')))
$$;

revoke execute on function public.my_badges(uuid) from public;
grant execute on function public.my_badges(uuid) to anon, authenticated;
