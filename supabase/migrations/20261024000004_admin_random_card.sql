-- 24/10/2026: "New random card" in the admin panel: a random playable card not used as a daily within a year
-- of the given day (and not the one currently on it). Only proposes it: nothing is saved until the admin saves.
create or replace function public.admin_random_card(p_day date, p_not text default null) returns text
language plpgsql volatile security definer set search_path = public as $$
begin
  perform public._need_admin();
  return (select id from public.cards
          where id is distinct from p_not
            and id not in (select card_id from public.daily_schedule
                           where day between coalesce(p_day, public.g_today()) - 365 and coalesce(p_day, public.g_today()) + 365)
          order by random() limit 1);
end $$;
revoke execute on function public.admin_random_card(date, text) from public, anon;
grant execute on function public.admin_random_card(date, text) to authenticated;
