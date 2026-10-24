"""Applies the sign-in settings and the email templates in supabase/auth/ to the Supabase project,
through the Supabase Management API. Run by the GitHub Action "Configure Supabase sign-in".

Needs SUPABASE_ACCESS_TOKEN and SUPABASE_PROJECT_ID in the environment (the same repository secrets
as the deploy action). It changes only the fields listed here: the email sending service (SMTP),
the Google provider and the allowed redirect addresses are left as they are in the Supabase dashboard.
"""
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent / "supabase" / "auth"
TOKEN = os.environ.get("SUPABASE_ACCESS_TOKEN", "")
REF = os.environ.get("SUPABASE_PROJECT_ID", "")
API = f"https://api.supabase.com/v1/projects/{REF}/config/auth"


def call(method, body=None):
    req = urllib.request.Request(
        API,
        method=method,
        data=None if body is None else json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json",
                 "User-Agent": "pokeguesstcg-configure-auth"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        msg = e.read().decode(errors="replace")[:400].replace("\n", " ")
        print(f"::error::{method} config/auth failed: HTTP {e.code} {msg}")
        sys.exit(1)


def main():
    if not TOKEN or not REF:
        print("::notice::Supabase secrets are not set, nothing changed. See SETUP.md.")
        return
    body = json.loads((ROOT / "settings.json").read_text())
    body["mailer_templates_confirmation_content"] = (ROOT / "confirmation.html").read_text()
    body["mailer_templates_recovery_content"] = (ROOT / "recovery.html").read_text()
    call("PATCH", body)
    now = call("GET")
    wrong = []
    for k, v in body.items():
        shown = v if not k.startswith("mailer_templates") else f"<{len(v)} characters>"
        same = now.get(k) == v
        print(f"{'ok ' if same else 'DIFF'} {k} = {shown}" + ("" if same else f" (Supabase has: {now.get(k) if not k.startswith('mailer_templates') else '...'})"))
        if not same:
            wrong.append(k)
    smtp = bool(now.get("smtp_host"))
    print(f"custom email service (SMTP): {'set (' + str(now.get('smtp_host')) + ')' if smtp else 'NOT set'}")
    if not smtp:
        print("::warning::No custom SMTP: Supabase's built-in email only reaches the project's team members, "
              "a few emails per hour. Set one up in Authentication > Emails > SMTP Settings (see SETUP.md).")
    if wrong:
        print("::error::Supabase did not keep these settings: " + ", ".join(wrong))
        sys.exit(1)


if __name__ == "__main__":
    main()
