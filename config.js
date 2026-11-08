/* Supabase connection for the game and the admin panel.
   Both values are public by design (they are visible in any browser that opens the site):
   access to the data is controlled by the database rules, not by keeping these secret.
   Find them in Supabase > Project Settings > API (or "API Keys"): Project URL and the publishable / anon key. */
window.PG_CONFIG = {
  supabaseUrl: 'https://uyqcrpixzmfjcvqsgctk.supabase.co',
  supabaseKey: 'sb_publishable_3Md2uJXPdZQEX4roGASxsw_TWBCy6S2',
  /* Google OAuth "Web application" client ID (public). When set, sign-in uses Google's button on this site,
     so the Google window names this site instead of the Supabase address. Empty = the old redirect sign-in. */
  googleClientId: '537670397579-pvquktc8hus4i4k9q78vgm1jsjr6reht.apps.googleusercontent.com',
  /* Ads and cookie consent (used by consent.js). Everything is public. */
  ads: {
    client: '',      // AdSense publisher ID, e.g. 'ca-pub-1234567890123456'. Empty = no ads, the ad spaces stay hidden.
    slots: {         // AdSense ad unit IDs (Ads > By ad unit > Display ads), one per space
      side: '',      // PC, right column under the score panel, 300x250
      foot: '',      // PC, above the footer, 728x90
      rail: '',      // very wide screens (1640px+), right of the page, 160x600
      phone: '',     // phones, above the footer, up to 336x100
      page: ''       // site pages (How to play, FAQ, archive…), responsive
    },
    cmp: 'own',      // 'own' = our banner; 'google' = the AdSense Privacy & messaging banner (needed for personalised ads in the EU/UK)
    h5: false,       // true once accepted into H5 Games Ads: a full-screen ad between Boosters
    analytics: ''    // Cloudflare Web Analytics token (cookie-free). Empty = no analytics.
  }
};
