-- Players can delete their own account from the profile window.
-- Deleting the auth user removes, through "on delete cascade", the profile (username),
-- all games and Boosters linked to the account (so the leaderboard place and badges too),
-- the Google identity and the sign-in sessions.
-- Admin accounts are refused, so the admin panel can't be lost by mistake.

create or replace function public.delete_my_account() returns void
language plpgsql security definer set search_path = public as $$
declare uid uuid := auth.uid();
begin
  if uid is null then
    raise exception 'not signed in' using errcode = '42501';
  end if;
  if exists (select 1 from public.admins a where a.user_id = uid) then
    raise exception 'admin accounts can''t be deleted here' using errcode = '42501';
  end if;
  delete from auth.users where id = uid;
end $$;

revoke all on function public.delete_my_account() from public, anon;
grant execute on function public.delete_my_account() to authenticated;
