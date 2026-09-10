# WED STUDIOZS

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users and purpose

Visitors explore photography portfolios, enquire about an event, request a
consultation, or contact the studio. Studio administrators publish portfolios
and manage enquiries, consultation requests, and messages.

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

Preserve the WED STUDIOZS name and photography focus. The user chose the
photography-journal direction: large real photographs, soft-white backgrounds,
deep plum accents, and an uncluttered admin workspace.

## Principles

- Photography and clear customer journeys lead; interface decoration follows.
- Forms preserve user input and explain failures in plain language.
- Administrative actions operate on real application data.
- Startup, readiness, and logs tell the truth about application state.
- Support mobile, keyboard navigation, and reduced motion.
