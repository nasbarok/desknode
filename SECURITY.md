# Security policy

## Do not open a public issue

**Do not open a public issue, pull request or comment for a security vulnerability.**
Everything posted there is public the moment it is posted: a vulnerability reported that way is a
vulnerability published.

## What belongs here

A **security vulnerability** is a flaw that lets someone do, through DeskNode, something they
should not be able to do: run code, read or change data, or take control of a PC or a board.
A bug that only makes DeskNode misbehave — a wrong reading, a frozen screen, a failed install —
is not one: it goes to the
[bug report form](https://github.com/nasbarok/desknode/issues/new?template=bug_report.yml).
When in doubt, report it privately: it costs nothing to be told it was an ordinary bug.

## Report it privately, through GitHub

**[Report a vulnerability](https://github.com/nasbarok/desknode/security/advisories/new)** — or,
from the repository page, open the **Security** tab and click **Report a vulnerability**.

This is GitHub's *private vulnerability reporting*: the report goes **privately to the
maintainer**, not to the public.

- You need a **GitHub account, signed in**. Measured on another public repository where this
  reporting is enabled, the link above redirects to the sign-in page when there is no session.
- There is **no e-mail address** for security reports, deliberately: this project publishes none.

⚠️ **Dated 2026-09-13: this form cannot be reached yet.** GitHub offers private vulnerability
reporting on **public repositories only**, and on that date this repository is still private.
Turning the setting on is part of the switch to public (`dn8` — see
[`docs/roadmap.md`](docs/roadmap.md)), and until then nobody outside the repository can read
this page anyway.

*Annotated on 2026-09-15 (`dn8-8`): the repository became public that day, so the reason given
above no longer holds. Turning the reporting setting on is a separate gesture, played **after**
this text was published, and this note does ⛔ not say that it is on: that is written here only
once the setting has been read back. A visitor who is not signed in to GitHub does not reach a
form at all: the link above leads to the sign-in page, so sign in first. If, once signed in, the
link still does not open a form, the setting is not on yet — come back to this page later, and do
not fall back to a public issue: the first section of this page still applies. The form has not
been tried from a second account.*

*Measured on 2026-09-15 (`dn8-8`): the reporting setting was turned on after the switch and read
back as enabled. The form itself has still not been tried from a second account.*

## What to include

- **Which part is affected**: the firmware, the Windows agent, the local install page and the
  script that serves it, or a tool of this repository.
- **The version**: the firmware SHA printed at boot (how to read it:
  [Reporting a bug](CONTRIBUTING.md#reporting-a-bug)), or the commit you cloned. The `v0.1.0-beta`
  release binary shows `version 55006c1`; a build from a clone at or after that tag shows
  `v0.1.0-beta` or `v0.1.0-beta-<n>-g<sha>`.
- **How to reproduce it**, step by step, and **what an attacker gains** from it.
- **Whether it is already public** anywhere else.

A vulnerability in a third-party component listed in [`THIRD-PARTY.md`](THIRD-PARTY.md) belongs
to that component's own project first.

## Which version is covered

There is no release yet: the version covered is the **default branch, `main`**. Once a first
release exists, the covered version is the **latest release**, and older releases are not
patched.

*Annotated on 2026-09-14 (`dn8-7`): a first release now exists — `v0.1.0-beta`, a pre-release.
GitHub's "latest release" label leaves pre-releases out, so the covered version is named here
explicitly: the **most recent release, pre-releases included** — today `v0.1.0-beta`.*

## What happens after you report

**No response time is promised, and no fix date either.** DeskNode is a personal project, and
what that means for everything — security reports included — is written in one place:
[What this project is, honestly](CONTRIBUTING.md#what-this-project-is-honestly).
