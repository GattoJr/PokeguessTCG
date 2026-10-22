/* Supabase connection for the game and the admin panel.
   Both values are public by design (they are visible in any browser that opens the site):
   access to the data is controlled by the database rules, not by keeping these secret.
   Find them in Supabase > Project Settings > API (or "API Keys"): Project URL and the publishable / anon key. */
window.PG_CONFIG = {
  supabaseUrl: 'https://uyqcrpixzmfjcvqsgctk.supabase.co',
  supabaseKey: 'sb_publishable_3Md2uJXPdZQEX4roGASxsw_TWBCy6S2'
};
