# Keeping WedStudiozs up to date

The studio workspace is at **`/admin`** on the same domain as the website.
Use **Portfolios** for photo collections and **Website content** for films,
footer text, and contact details. Changes saved there live in the database;
they do not require an image rebuild or an application restart.

## First access

This release adds the `reels` and `site_content` tables in migration `0002`.
From `wed-studiozs`, using the application's Python environment and the database
configuration for the environment you intend to update:

```bash
alembic upgrade head
python -m app.cli create-admin --email your-address@example.com
```

Run the migration before deploying this application version. The second command
is only needed if you do not already have an account. It asks for a password
without displaying it; it does not reset an existing account. There is no
default admin password.

Open `http://localhost:8000/admin` locally, or `https://your-domain/admin` in
production. Production login needs HTTPS because the session cookie is marked
Secure. Use **Sign out** when you finish on a shared device.

## Photographs and collections

In **Portfolios**, choose **New portfolio**, enter a title and category, then
add a cover image URL and an optional description. **Save portfolio publishes
the collection immediately**; portfolios do not have a draft switch.
**Feature this portfolio** makes it eligible for the homepage's collections
section, which displays up to three featured collections.

Use **Edit & gallery** to change a collection. Under **Gallery photographs**,
add image URLs and descriptive captions, then use **Add image**. Each
photograph has its own **Save image**, **Use as cover**, and **Delete image**
controls. Lower **Order** numbers appear first; zero is valid. Reopen the
collection after changing order to see the updated arrangement.

Changing a gallery image's URL does not automatically change an already chosen
cover. Use **Use as cover** again if that photograph should remain the cover.
Deleting a gallery entry does not delete its source file or clear a separately
stored cover URL. To remove a cover, clear **Cover image URL** and save the
portfolio.

Keep an existing **Page address** unless you mean to change the public link.
Removing a portfolio removes its gallery records too, but not the original
files on your media host.

### Where the images come from

The workspace stores **links**, not uploaded files. For example:

```text
https://your-media-domain.example/weddings/gayatri-portrait-v2.webp
/static/img/gayatri-portrait-v2.jpg
```

Replace the example domain with your actual media host. An HTTPS URL must be
readable by a visitor's browser without signing in. A `/static/img/...` URL maps
to a file under `app/static/img/` in the application artifact. Adding that file
requires your normal rebuild and deployment; typing the URL in admin does not
create it. Prefer versioned filenames when replacing media so browser/CDN
caches cannot keep serving the old file.

Use your originals, not screenshots or Instagram preview downloads. The
current five bundled Instagram photographs are roughly **512 x 640** previews.
Hover enlargement cannot recover detail missing from those files. For new
photographs, export a compressed JPEG/WebP at roughly 1600-2000 pixels on the
long edge, check it at the intended display size, and balance quality against
download size. The site keeps the full image visible rather than cropping it.
Write captions that describe the photograph; gallery captions also provide
accessible image text.

### The curated journal and homepage prints

The **Instagram journal** is separate from database-managed collections.
Its existing stories, homepage prints, and selected-work photographs are
curated application content, not editable through Portfolios.

| What to update | Source |
|---|---|
| Journal title, description, category, accessible image text and post ID | `app/web/journal.py` |
| Bundled photograph | `app/static/img/<post_id>.jpg` |
| Original source attribution | `app/static/img/sources.json` |
| Homepage's chosen prints and selected stories | `app/templates/index.html` |

The homepage currently references positions in `STORIES`; keep its five records
unless you also update those selections. Replacing an original photograph with
a better export of the same work can keep its filename and post attribution;
cache invalidation then belongs to the deployment. For different work, update
its story and provenance rather than attaching the old credit to a new image.
Application-content edits need a rebuild and rollout. Regular new collections
can stay entirely in the admin workflow above.

## Reels and films

Open **Website content** and find **Add a film**. Enter the film title, a direct
video URL, and a poster image URL. A poster is required so visitors see a clear
frame before choosing to play.

Accepted video locations look like:

```text
https://your-media-domain.example/films/celebration-v1.mp4
/static/media/celebration-v1.webm
```

The path must end in `.mp4` or `.webm`. Use MP4 with H.264 video and AAC audio
for broad device compatibility, ideally exported for streaming with metadata
at the start of the file ("fast start"). A vertical 9:16 export suits the reel
layout; other aspect ratios remain uncropped, with space around them.

An Instagram reel page, YouTube watch page, share link, or expiring Instagram
CDN address is **not** a direct video file. Upload your own footage to your
chosen media storage first, or bundle it under `app/static/media/` and deploy
it. Only publish footage and audio you have permission to use. Nothing in this
release downloads Instagram videos or adds an upload/storage service.

**Display order** controls placement: lower numbers first, then creation order
for ties. The homepage shows the first three published films; **Films** shows
the full paginated collection. Leave **Publish on the website** unchecked while
preparing an entry. Tick it and save when ready. Draft hides the website entry,
not the underlying file: a publicly hosted URL is still public.

**Edit film** changes an existing entry. To take one offline without losing its
details, uncheck Publish and save. **Remove film** expands an explicit
confirmation; deletion removes the record, not the hosted video.

### What visitors experience

On a mouse-driven desktop, entering a reel starts it **muted** and leaving
pauses it. **Unmute/Mute** changes sound; pausing or leaving resets it to muted.
Only one film plays at a time, and playback stops when its card leaves view or
the browser tab becomes hidden.

On touchscreens, visitors tap **Play/Pause**. Keyboard users can operate the
same buttons. With reduced motion enabled, hover does not start playback:
Play is always available. Without JavaScript, standard browser video controls
remain usable. If autoplay is blocked or a file fails, the page explains the
problem and keeps an **Open film** link available.

Until you publish a film, the website links to the studio's Instagram reels.
No demonstration video is shipped as studio work.

### Captions

For spoken audio, add an **English captions URL** pointing to a `.vtt` file.
The visitor can toggle **Captions**. A simple WebVTT file looks like this:

```text
WEBVTT

00:00.000 --> 00:03.000
[Music]

00:03.000 --> 00:06.000
We are so glad you could be here.
```

Use the film's actual words and sound cues. The optional description/transcript
appears under **About this film**. The current caption field is labelled
English; it is not a multi-language caption manager.

When captions are on another origin, your media host must allow the website's
origin through CORS. Because captioned players use anonymous cross-origin
loading, **both the external video and caption file need appropriate CORS
headers**. Serve video with `video/mp4` or `video/webm`, captions with `text/vtt`,
and support byte-range requests for reliable video delivery and seeking.

## Footer and contact information

Under **Website content → Footer & contact details**, edit:

- **Footer description**: the text beneath WedStudiozs at the bottom of each page.
- **Phone, email, studio address**: shared by the footer, Contact page and
  `/api/v1/contact/info`. A blank field hides that contact method.
- **Instagram handle**: enter only the handle, without `@` or a full URL.
  This changes the footer, contact and films links; original journal credits
  remain tied to the account that published those photographs.

Choose **Save studio details**, then reload the public page. Once these details
are saved, the database values take priority over `BUSINESS_PHONE`,
`BUSINESS_EMAIL` and `BUSINESS_ADDRESS`. Those environment settings are only
initial defaults when no saved settings record exists. Editing `.env` will not
override a saved setting.

The site name is **WedStudiozs**. Footer navigation, copyright formatting,
headline copy and section layout remain in `app/templates/base.html` and the
individual page templates; they are not free-form admin HTML. Stored text is
escaped, so pasted markup is displayed as text rather than executed.

## When something looks wrong

| Symptom | Check |
|---|---|
| A film is missing | Publish is checked, its order is correct, and you are on the right page. Only three appear on the homepage. |
| Poster appears but video will not play | Open the file URL directly. Confirm it is permanent, public, HTTPS, supported by the browser, and served with the correct MIME type. Check CORS if captions are configured. |
| A photograph looks soft when enlarged | Replace the small source with a higher-resolution original. CSS sharpening is not a substitute. |
| An update appears on one device but not another | Check browser/CDN caching and whether both devices use the same environment. Database changes need a page reload, not a rebuild. |
| Login works locally but not on the deployed site | Check HTTPS and the production cookie setting. All replicas need the same `SECRET_KEY`. |
| Content pages fail after deployment | Confirm migration `0002` ran against the same database used by the web application. Check application logs using the request ID. |

Back up the database **and** the media store. They serve different jobs: the
database holds titles, links, publication status and studio details; the media
store holds the photographs and films themselves. Docker, Kubernetes, storage,
backups and delivery configuration remain yours to manage.
