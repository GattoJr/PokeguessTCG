-- 24/10/2026: pre-fill the daily calendar so the admin only has to confirm or adjust.
-- Every empty day from today for the next N days gets a random card (Daily and Daily Hard separately),
-- marked auto = true ("to confirm" in the admin panel). Unconfirmed days are still played normally.
-- Cards are never repeated within a year, and a day's Normal and Hard cards are always different.

create or replace function public._fill_days(p_from date, p_days int) returns int
language plpgsql volatile security definer set search_path = public as $$
declare d date; h boolean; c text; n int := 0;
begin
  for i in 0 .. greatest(p_days, 0) - 1 loop
    d := p_from + i;
    foreach h in array array[false, true] loop
      if exists (select 1 from public.daily_schedule where day = d and hard = h) then continue; end if;
      select id into c from public.cards
       where id not in (select card_id from public.daily_schedule where day between d - 365 and d + 365)
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

-- from the admin panel: fill the empty days from today on
create or replace function public.admin_fill(p_days int default 100) returns int
language plpgsql volatile security definer set search_path = public as $$
begin
  perform public._need_admin();
  return public._fill_days(public.g_today(), least(greatest(coalesce(p_days, 100), 1), 366));
end $$;

revoke execute on function public._fill_days(date, int) from public, anon, authenticated;
revoke execute on function public.admin_fill(int) from public, anon;
grant execute on function public.admin_fill(int) to authenticated;

-- fill the next 100 days now
select public._fill_days(public.g_today(), 100);
