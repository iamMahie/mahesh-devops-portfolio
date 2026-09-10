---
name: WED STUDIOZS
description: A photography journal built around real studio work.
colors:
  paper: "#faf8f6"
  white: "#ffffff"
  ink: "#261c25"
  plum: "#4b2440"
  muted: "#70636c"
  line: "#e2dbe0"
  wash: "#f0e9ed"
  error: "#9b263b"
  success: "#235c47"
typography:
  display:
    fontFamily: "Georgia, Times New Roman, serif"
    fontSize: "clamp(2.8rem, 5.7vw, 5rem)"
    fontWeight: 400
    lineHeight: 1.1
    letterSpacing: "-.035em"
  headline:
    fontFamily: "Georgia, Times New Roman, serif"
    fontSize: "clamp(2.1rem, 3.8vw, 3.5rem)"
    fontWeight: 400
    lineHeight: 1.1
  body:
    fontFamily: "-apple-system, BlinkMacSystemFont, Segoe UI, Arial, sans-serif"
    fontSize: "16px"
    lineHeight: 1.65
  label:
    fontFamily: "-apple-system, BlinkMacSystemFont, Segoe UI, Arial, sans-serif"
    fontSize: "14px"
    fontWeight: 550
rounded:
  control: "0"
components:
  button-primary:
    backgroundColor: "{colors.plum}"
    textColor: "{colors.white}"
    padding: "12px 23px"
    rounded: "{rounded.control}"
  button-secondary:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.plum}"
    padding: "12px 23px"
    rounded: "{rounded.control}"
---

# Design System: WED STUDIOZS

## Overview

**Creative North Star: "The photography journal."**

The user selected an image-led journal with soft-white surfaces and deep plum
accents. Real photographs from the studio's Instagram establish the identity;
the interface gives them room rather than decorating over them.

Public pages invite exploration and conversation. The admin workspace shares
the palette but uses task-oriented layouts, sans-serif text, clear statuses,
and explicit actions. No frontend framework or remotely loaded CSS is required.

This replaces the unrelated Claude design-analysis document previously stored
here. Product facts and asset provenance live in PRODUCT.md and
`app/static/img/sources.json`.

## Colors

Paper and white carry reading and input surfaces. Ink is the main text color;
muted plum-grey is reserved for secondary text. Plum identifies the primary
action and the closing enquiry section. Wash separates longer passages without
requiring cards or shadows. Error and success colors communicate state in
combination with text, not by color alone.

## Typography

Georgia provides public display headings; the system sans stack handles body
copy, navigation, forms, and the administrative interface. No font download is
needed to make the first render usable.

Public headings use fluid sizes and restrained italic emphasis. Body copy has
a maximum measure of 68 characters. Captions are deliberately smaller and must
never carry essential instructions on their own. Administrative headings
prioritize scanability over display scale.

## Layout

Public content uses a 1280px maximum-width container, 96px total desktop gutter,
56px at the intermediate breakpoint, and 36px on mobile. Major public layout
breakpoints are 1000px, 760px, and 420px.

The home opening has an independent headline/action row followed by staggered
photographic prints. Two prints remain on mobile, rather than shrinking three
into illegibility. Journal grids move from three columns to two, then one.
Photographs use `object-fit: contain` to preserve the original collages,
typography, and attribution.

Forms use a two-column introduction/form layout, becoming a single column
below 760px. Field pairs stack on narrow phones. Mobile navigation is a normal
document-flow menu, not an overlay. Without JavaScript, navigation remains
visible and customer forms still submit.

## Elevation & Depth

Public surfaces are flat. Tonal changes, whitespace, and one-pixel rules provide
separation. The photograph viewer alone uses a dark backdrop because it needs
focused attention. Image hover feedback does not move the surrounding layout.

## Shapes

Public buttons and fields have square corners. The circular wordmark and receipt
confirmation mark are small exceptions with distinct roles, not a global card
shape. Controls have at least 44px touch height; standard public form fields and
primary actions are 52px high.

## Components

### Navigation

The wordmark links home. Work, approach, contact, and enquiry are the public
navigation priorities. The footer holds studio workspace access. The active
page is conveyed with `aria-current`; mobile expansion exposes `aria-expanded`.

### Photographs and stories

A photograph leads, with category and title below it. Existing artwork is not
cropped to fit an ornamental container. Curated journal pages link to the
original Instagram post. Database collections are distinct from that curated
snapshot.

### Forms and confirmations

Every field has a visible label. Optional fields are identified explicitly.
Errors preserve values, link to the affected fields, and expose `aria-invalid`.
Successful submission uses a redirect to a private, time-limited receipt.
Consultation copy clearly distinguishes a request from an appointment.

### Image viewer

A native dialog provides focused viewing. Escape closes it, arrow keys browse
multi-image galleries, and focus returns to the opening link. With no scripting,
image links still open the original image.

### Motion

The home prints have one short clipping reveal. Hover states are restrained.
Reduced-motion preferences disable animation and smooth scrolling. Content
remains visible without JavaScript or animation.

## Do's and Don'ts

- Do use actual studio work, preserve attribution, and link original posts.
- Do separate curated Instagram content from database-managed collections.
- Do keep every state useful: loading, empty, error, success, and expired login.
- Do use the same application and local assets across public and admin pages.
- Don't invent testimonials, customer counts, delivery promises, or availability.
- Don't put portfolio content inside nested decorative cards.
- Don't use Instagram's expiring CDN addresses as permanent image locations.
- Don't require JavaScript for a customer to contact the studio.
