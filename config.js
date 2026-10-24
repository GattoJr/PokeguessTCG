/* Supabase connection for the game and the admin panel.
   Both values are public by design (they are visible in any browser that opens the site):
   access to the data is controlled by the database rules, not by keeping these secret.
   Find them in Supabase > Project Settings > API (or "API Keys"): Project URL and the publishable / anon key. */
window.PG_CONFIG = {
  supabaseUrl: 'https://uyqcrpixzmfjcvqsgctk.supabase.co',
  supabaseKey: 'sb_publishable_3Md2uJXPdZQEX4roGASxsw_TWBCy6S2',
  /* Google OAuth "Web application" client ID (public). When set, sign-in uses Google's button on this site,
     so the Google window names this site instead of the Supabase address. Empty = the old redirect sign-in. */
  googleClientId: '537670397579-pvquktc8hus4i4k9q78vgm1jsjr6reht.apps.googleusercontent.com'
};
