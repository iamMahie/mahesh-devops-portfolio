---
name: WedStudiozs
description: An immersive photography and film gallery, with a practical studio workspace.
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
  film: "#281c25"
typography:
  display:
    fontFamily: "Aptos, Segoe UI, -apple-system, BlinkMacSystemFont, Arial, sans-serif"
    fontSize: "clamp(3rem, 6.4vw, 5.6rem)"
    fontWeight: 550
    lineHeight: 1.08
    letterSpacing: "-.04em"
  headline:
    fontFamily: "Aptos, Segoe UI, -apple-system, BlinkMacSystemFont, Arial, sans-serif"
    fontSize: "clamp(2.1rem, 3.8vw, 3.5rem)"
    fontWeight: 550
    lineHeight: 1.08
  body:
    fontFamily: "Aptos, Segoe UI, -apple-system, BlinkMacSystemFont, Arial, sans-serif"
    fontSize: "16px"
    lineHeight: 1.65
  label:
    fontFamily: "Aptos, Segoe UI, -apple-system, BlinkMacSystemFont, Arial, sans-serif"
    fontSize: "14px"
    fontWeight: 550
rounded:
  control: "4px"
  field: "0"
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

# Design System: WedStudiozs

## Overview

**Creative North Star: "Step into the photographs."**

The user requested a clean, animated 3D photography website. Soft-white
surfaces and plum remain recognizable; sans-serif typography and
perspective-layered photographic prints replace the previous flat serif
journal. Actual studio work is the visual material, not generated decoration.

Public pages invite exploration, playback and conversation. The admin workspace
shares the palette but stays flat and task-oriented. No frontend framework,
WebGL runtime, remote font download or JavaScript build step is required.

Product facts and asset provenance live in PRODUCT.md and
`app/static/img/sources.json`. Content workflows live in `guide.md`.

## Colors

Paper and white carry reading and input surfaces. Ink is the main text color;
muted plum-grey is reserved for secondary text. Plum identifies the primary
action and the closing enquiry section. Wash separates longer passages without
requiring cards. The homepage film section uses a deep plum-black field with
light text and pale plum secondary text. Error and success colors communicate state in
combination with text, not by color alone.

## Typography

Public pages use a local Aptos / Segoe UI / platform-sans stack, including
display headings. Admin keeps its existing platform-sans stack. The wordmark
is spelled WedStudiozs, with restrained tracking and a small photography/films
descriptor. No font download is needed for the first render.

Public headings use fluid sizes and plum, non-italic emphasis. Body copy has
a maximum measure of 68 characters. Captions are deliberately smaller and must
never carry essential instructions on their own. Administrative headings
prioritize scanability over display scale.

## Layout

Public content uses a 1280px maximum-width container, 96px total desktop gutter,
56px at the intermediate breakpoint, and 36px on mobile. Major public layout
breakpoints are 1000px, 760px, and 420px.

The home opening centres its headline and actions above three floating prints.
The centre print leads; smaller side prints rotate toward it. All three remain
on mobile, where captions are removed and transforms are smaller in footprint.
The desktop selected-work grid has unequal widths and staggered baselines;
on mobile the first photograph spans the grid, with the remainder below.
Ordinary journal grids move from three columns to two, then one.
Photographs use `object-fit: contain` to preserve the original collages,
typography, and attribution.

Forms use a two-column introduction/form layout, becoming a single column
below 760px. Field pairs stack on narrow phones. Mobile navigation is a normal
document-flow menu, not an overlay. Without JavaScript, navigation remains
visible and customer forms still submit. Reel grids use three columns, two
below 760px, and one below 420px. Video frames are 9:16 and contain their source
without cropping. Admin content editing uses stacked, labelled form sections,
not a second 3D interface.

## Elevation & Depth

Surfaces remain flat except for photographic material. The hero uses 1300px
perspective, preserve-3d transforms and pointer-driven rotation bounded to a
small angle. A one-second entrance establishes the gallery; motion does not
run endlessly. Print shadows are offset and blurred, with no neon halo.

Hovered/focused portfolio photographs scale to 1.045 without changing layout
or cropping the original. Detail gallery images scale to 1.04. The lightbox
uses a dark backdrop for focused viewing.

Reduced-motion mode disables the entrance, hero transforms and hover movement.
Desktop visitors can also pause the hero's depth with an explicit control.

## Shapes

Public buttons have 4px corners; fields and admin controls remain square.
The circular wordmark and receipt
confirmation mark are small exceptions with distinct roles, not a global card
shape. Controls have at least 44px touch height; standard public form fields and
primary actions are 52px high.

## Components

### Navigation

The wordmark links home. Work, films, approach, contact, and enquiry are the public
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

### Films

Video starts muted on fine-pointer hover and pauses on leaving. Play/Pause,
Mute/Unmute and optional captions are explicit controls. Touch and
reduced-motion users play manually. Moving offscreen or hiding the tab pauses
playback; only one enhanced player runs at a time. Pause returns sound to muted.
No-JavaScript visitors retain native video controls.

Required poster images and `preload="none"` keep the page image-led before
interaction. If no real film is published, show an honest Instagram link, not
a fake player. Playback failures explain recovery and retain the direct file
link. Short hover transitions support interaction without moving surrounding
layout. All content is visible without JavaScript or animation.

## Do's and Don'ts

- Do use actual studio work, preserve attribution, and link original posts.
- Do separate curated Instagram content from database-managed collections.
- Do keep every state useful: loading, empty, blocked playback, error, success, and expired login.
- Do use the same application and local assets across public and admin pages.
- Don't invent testimonials, customer counts, delivery promises, or availability.
- Don't put portfolio content inside nested decorative cards.
- Don't use Instagram's expiring CDN addresses as permanent image locations.
- Don't require JavaScript for a customer to contact the studio.
- Don't crop or blur photographs to create the depth effect.
- Don't animate the admin workspace or hijack scrolling to make it feel immersive.
- Don't claim small Instagram previews are high-resolution originals.
