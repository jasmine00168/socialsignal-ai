# SocialSignal AI — V0.1 Product Brief

## User problem

Small product and operations teams manually scan scattered social posts for customer pain points. The work is slow, inconsistent, and difficult to audit because conclusions are often separated from the original source.

## Target user

- Primary: product managers and growth operators in small teams.
- Secondary: founders, researchers, and content operators validating a market.

## Job to be done

When reviewing social conversations, help me quickly find software-related needs and verify every conclusion against the original wording, so I can decide which opportunity deserves deeper research.

## V0.1 scope

Input:

- Built-in anonymized demo posts.
- User-uploaded CSV with `post_id`, `platform`, `content`, and `source_url`.

AI output:

- Demand classification.
- Target user and usage context.
- Pain point and desired solution.
- Urgency, confidence, and willingness-to-pay signal.
- A verbatim evidence quote that is checked against the source text.

Not in V0.1:

- Automated scraping.
- Account login or multi-account management.
- Automatic publishing.
- Market-size claims based only on social engagement.

## Success criteria

- A first-time user can analyze one post in under two minutes.
- 100% of displayed AI conclusions retain the source post id and URL.
- Evidence quotes are automatically flagged when they are not verbatim.
- The same input always produces a schema-valid result or a clear error.

## Product risks

- A social post is not proof of a large market.
- LLM extraction can misclassify jokes, ads, or vague complaints.
- Platform data collection and publishing require separate permission and compliance work.
- Engagement counts can be manipulated and must not become the sole opportunity score.

