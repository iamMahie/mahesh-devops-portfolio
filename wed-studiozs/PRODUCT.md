# WedStudiozs

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users and purpose

Visitors explore photography portfolios and films, enquire about an event, request a
consultation, or contact the studio. Studio administrators publish portfolios
and manage enquiries, consultation requests, and messages. The Website content
workspace manages reel links, publication status, ordering, footer description,
contact details and the studio's Instagram handle.

## Operating context

This is a learning application in a hands-on DevOps project. The user owns the
infrastructure; application development must not change Docker, Kubernetes,
CI/CD, or cloud configuration.

## Capabilities and constraints

Keep FastAPI, server-rendered Jinja templates, the existing REST API, and
PostgreSQL compatibility. Deliver a responsive public website and a working
authenticated admin dashboard in the same application, without another service
or a JavaScript build pipeline. Preserve existing API consumers.

## Evidence on hand

The application has portfolio and gallery records, enquiry and booking state
machines, contact messages, and administrator authentication. The user supplied
https://www.instagram.com/wed_studiozs/ as the source for the portfolio.
Five public photo posts have been captured as local assets, with original
attribution and post links in app/web/journal.py. This is a curated snapshot,
not an automatically refreshed Instagram feed. Preserve the original artwork.
The studio phone, +91 91604 00802, appears in its public post captions.
The old database seed photographs are demonstration content, not commercial
proof. No verified client testimonials, business performance
statistics, prices, availability, or delivery guarantees have been supplied.
Do not invent these claims.

## Brand commitments

Use the user-requested **WedStudiozs** spelling and photography focus. The
October redesign replaces the serif journal presentation with clean sans
typography, layered CSS 3D photographs and responsive hover feedback. Keep
soft-white backgrounds, deep plum accents and an uncluttered admin workspace.
Show whole photographs without decorative cropping. Motion must not obstruct
reading, forms or playback controls.

The user chose to add video URLs later through admin. No actual video footage
has been supplied. Do not invent studio films or imply the Instagram feed is
embedded or synchronized. Direct MP4/WebM URLs support muted hover playback,
pause on exit, explicit sound controls and manual touch/keyboard play.
Reduced-motion users get manual playback. Media upload/storage remains outside
the application; admin stores links. Curated journal stories remain application
content and are documented separately from admin-managed collections.

## Principles

- Photography and clear customer journeys lead; interface decoration follows.
- Forms preserve user input and explain failures in plain language.
- Administrative actions operate on real application data.
- Startup, readiness, and logs tell the truth about application state.
- Support mobile, keyboard navigation, and reduced motion.
