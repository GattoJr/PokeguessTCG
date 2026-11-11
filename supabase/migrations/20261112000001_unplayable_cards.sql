-- 12/11/2026: cards that can no longer be drawn.
-- My First Battle (mfb, 28 cards) has no picture anywhere (TCGdex and pokemontcg.io), so those cards showed a
-- broken artwork. They stay in the table, because past dailies and rounds point to them (foreign keys), but the
-- random draws (daily, Booster/Guess10, admin "New random card") now only pick playable cards.

alter table public.cards add column if not exists playable boolean not null default true;
update public.cards set playable = false where set_id = 'mfb';

create or replace function public._daily_for(p_day date, p_hard boolean) returns public.daily_schedule
language plpgsql security definer set search_path = public as $$
declare s public.daily_schedule; c text;
begin
  select * into s from public.daily_schedule where day = p_day and hard = p_hard;
  if found then return s; end if;
  select id into c from public.cards
   where playable and id not in (select card_id from public.daily_schedule where day > p_day - 365)
   order by random() limit 1;
  insert into public.daily_schedule (day, hard, card_id, start_tile, auto)
  values (p_day, p_hard, c, public.random_start(c), true)
  on conflict (day, hard) do nothing;
  select * into s from public.daily_schedule where day = p_day and hard = p_hard;
  return s;
end $$;

create or replace function public._fill_days(p_from date, p_days integer) returns integer
language plpgsql security definer set search_path = public as $$
declare d date; h boolean; c text; n int := 0;
begin
  for i in 0 .. greatest(p_days, 0) - 1 loop
    d := p_from + i;
    foreach h in array array[false, true] loop
      if exists (select 1 from public.daily_schedule where day = d and hard = h) then continue; end if;
      select id into c from public.cards
       where playable and id not in (select card_id from public.daily_schedule where day between d - 365 and d + 365)
       order by random() limit 1;
      if c is null then continue; end if;
      insert into public.daily_schedule (day, hard, card_id, start_tile, auto)
      values (d, h, c, public.random_start(c), true)
      on conflict (day, hard) do nothing;
      n := n + 1;
    end loop;
  end loop;
  return n;
end $$;

create or replace function public.admin_random_card(p_day date, p_not text default null) returns text
language plpgsql security definer set search_path = public as $$
begin
  perform public._need_admin();
  return (select id from public.cards
          where playable and id is distinct from p_not
            and id not in (select card_id from public.daily_schedule
                           where day between coalesce(p_day, public.g_today()) - 365 and coalesce(p_day, public.g_today()) + 365)
          order by random() limit 1);
end $$;

create or replace function public.booster_start(p_guest uuid, p_hard boolean default false) returns jsonb
language plpgsql security definer set search_path = public as $$
declare uid uuid := auth.uid(); cs text[]; st int[]; run public.runs; r public.rounds;
begin
  if uid is null and p_guest is null then raise exception 'missing player'; end if;
  select array_agg(id), array_agg(public.random_start(id)) into cs, st
    from (select id from public.cards
          where playable and id not in (select card_id from public.daily_schedule where day = public.g_today())
          order by random() limit 10) x;
  insert into public.runs (user_id, guest_id, cards, starts, hard) values (uid, p_guest, cs, st, coalesce(p_hard, false))
  returning * into run;
  r := public._booster_round(run, 0);
  return public._run_json(run) || jsonb_build_object('round', public._round_json(r));
end $$;
