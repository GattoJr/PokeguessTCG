-- Daily archive: the Daily cards of the days already over (never today, never the days still to come),
-- newest first, with how all players did and how the current player (account or guest) did.
-- Numbering: Daily #1 = 24 October 2026, the public launch; earlier test days are left out.

create or replace function public.daily_archive(p_hard boolean, p_guest uuid, p_before date default null, p_limit int default 60)
returns jsonb
language sql stable security definer set search_path = public as $$
  with me as (select auth.uid() as uid),
  days as (
    select s.day, s.card_id
    from public.daily_schedule s
    where s.hard = coalesce(p_hard, false)
      and s.day < public.g_today()
      and s.day >= date '2026-10-24'
      and (p_before is null or s.day < p_before)
    order by s.day desc
    limit least(greatest(coalesce(p_limit, 60), 1), 200))
  select coalesce(jsonb_agg(jsonb_build_object(
      'day', d.day,
      'no', (d.day - date '2026-10-24') + 1,
      'name', c.name, 'set', c.set_name, 'image', c.image,
      'players', st.players, 'named', st.named, 'avg', st.avg,
      'mine', mine.score, 'mine_won', mine.won
    ) order by d.day desc), '[]'::jsonb)
  from days d
  join public.cards c on c.id = d.card_id
  left join lateral (
    select count(*)::int as players,
           (count(*) filter (where r.won))::int as named,
           round(avg(case when r.won then r.score else 0 end))::int as avg
    from public.rounds r
    where r.mode = 'daily' and r.hard = coalesce(p_hard, false) and r.day = d.day and r.over) st on true
  left join lateral (
    select case when r.won then r.score else 0 end as score, r.won
    from public.rounds r, me
    where r.mode = 'daily' and r.hard = coalesce(p_hard, false) and r.day = d.day and r.over
      and (case when me.uid is not null then r.user_id = me.uid
                else r.user_id is null and p_guest is not null and r.guest_id = p_guest end)
    limit 1) mine on true
$$;

revoke execute on function public.daily_archive(boolean, uuid, date, int) from public;
grant execute on function public.daily_archive(boolean, uuid, date, int) to anon, authenticated;
