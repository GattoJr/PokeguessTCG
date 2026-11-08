-- More badges: my_badges() also returns, for Normal and Hard separately,
--   booster_days: the days (UTC) on which the player finished at least one Booster, oldest first;
--   booster_done: how many Boosters were finished, and when the 10th, 50th and 100th were finished;
--   skills:       the first time each skill badge was earned (null = not yet):
--     glance   a card named with only the free tile open
--     keen     a card named with at most 3 tiles open (Hard: 5)
--     wire     a card named on the 2nd guess with under 50 points left (Hard: 10)
--     quick    the Daily card named within 15 seconds of opening it
--     complete a Booster with all 10 cards named
--     flawless a Booster with all 10 cards named on the first guess
-- The earlier keys (today, daily, booster) are unchanged. Read-only, as before.

create or replace function public.my_badges(p_guest uuid) returns jsonb
language sql stable security definer set search_path = public as $$
  with me as (select auth.uid() as uid),
  mine as (
    select r.* from public.rounds r, me
    where (case when me.uid is not null then r.user_id = me.uid
                else r.user_id is null and p_guest is not null and r.guest_id = p_guest end)),
  myruns as (
    select u.* from public.runs u, me
    where (case when me.uid is not null then u.user_id = me.uid
                else u.user_id is null and p_guest is not null and u.guest_id = p_guest end)),
  daily as (select hard, day from mine where mode = 'daily' and over and won),
  runs as (
    select u.hard, u.finished_at, u.total,
           max(u.total) over (partition by u.hard order by u.finished_at, u.id
                              rows between unbounded preceding and 1 preceding) as before
    from myruns u where u.finished_at is not null and u.total is not null),
  records as (select * from runs where before is null or total > before),
  done as (
    select hard, finished_at, row_number() over (partition by hard order by finished_at, id) as n
    from myruns where finished_at is not null),
  runcards as (
    select r.run_id, count(*) filter (where r.won) as named, count(*) filter (where r.won and r.wrong = 0) as clean
    from mine r where r.mode = 'booster' and r.run_id is not null group by r.run_id),
  skills as (
    select m.hard,
      min(coalesce(m.finished_at, m.created_at)) filter (where m.won and cardinality(m.opened) = 1) as glance,
      min(coalesce(m.finished_at, m.created_at)) filter (where m.won and cardinality(m.opened) <= case when m.hard then 5 else 3 end) as keen,
      min(coalesce(m.finished_at, m.created_at)) filter (where m.won and m.wrong >= 1 and m.score < case when m.hard then 10 else 50 end) as wire,
      min(m.finished_at) filter (where m.mode = 'daily' and m.won and m.finished_at - m.created_at <= interval '15 seconds') as quick
    from mine m where m.over group by m.hard),
  runskills as (
    select u.hard,
      min(u.finished_at) filter (where c.named >= 10) as complete,
      min(u.finished_at) filter (where c.clean >= 10) as flawless
    from myruns u join runcards c on c.run_id = u.id
    where u.finished_at is not null group by u.hard)
  select jsonb_build_object(
    'today', public.g_today(),
    'daily', jsonb_build_object(
      'normal', coalesce((select jsonb_agg(day order by day) from daily where not hard), '[]'),
      'hard',   coalesce((select jsonb_agg(day order by day) from daily where hard), '[]')),
    'booster', jsonb_build_object(
      'normal', coalesce((select jsonb_agg(jsonb_build_array(finished_at, total) order by finished_at) from records where not hard), '[]'),
      'hard',   coalesce((select jsonb_agg(jsonb_build_array(finished_at, total) order by finished_at) from records where hard), '[]')),
    'booster_days', jsonb_build_object(
      'normal', coalesce((select jsonb_agg(distinct (finished_at at time zone 'utc')::date) from done where not hard), '[]'),
      'hard',   coalesce((select jsonb_agg(distinct (finished_at at time zone 'utc')::date) from done where hard), '[]')),
    'booster_done', jsonb_build_object(
      'normal', jsonb_build_object('n', (select count(*) from done where not hard),
        'at', coalesce((select jsonb_object_agg(n, finished_at) from done where not hard and n in (10, 50, 100)), '{}')),
      'hard', jsonb_build_object('n', (select count(*) from done where hard),
        'at', coalesce((select jsonb_object_agg(n, finished_at) from done where hard and n in (10, 50, 100)), '{}'))),
    'skills', jsonb_build_object(
      'normal', (select jsonb_build_object('glance', s.glance, 'keen', s.keen, 'wire', s.wire, 'quick', s.quick,
                   'complete', (select complete from runskills where not hard), 'flawless', (select flawless from runskills where not hard))
                 from (select false as h) v left join skills s on s.hard = v.h),
      'hard',   (select jsonb_build_object('glance', s.glance, 'keen', s.keen, 'wire', s.wire, 'quick', s.quick,
                   'complete', (select complete from runskills where hard), 'flawless', (select flawless from runskills where hard))
                 from (select true as h) v left join skills s on s.hard = v.h)))
$$;

revoke execute on function public.my_badges(uuid) from public;
grant execute on function public.my_badges(uuid) to anon, authenticated;
