# letsmock.com

Marketing site, privacy policy and terms for LetsMock. Astro + Tailwind,
building to plain static HTML — there is no Node process in production.

This site is also where the **visual identity lives**. The palette and type
scale in `src/styles/global.css` are the source of truth; the Flutter app
should follow them, not the other way round.

## Develop

```bash
pnpm install
pnpm dev      # http://localhost:4321
pnpm build    # -> dist/
```

## Pages

| Route      | Why it exists                                                     |
| ---------- | ----------------------------------------------------------------- |
| `/`        | Landing page                                                      |
| `/privacy` | **Required by Google Play** — the app records voice               |
| `/terms`   | Subscription terms + the limits of AI-generated feedback          |

`src/components/Scorecard.astro` renders a scorecard in markup rather than an
image, so the page stays truthful while the app is being redesigned. Swap it
for real screenshots once the new app UI lands.

## Deploy (Oracle VM, nginx)

`dist/` is a folder of static files — copy it up and point nginx at it.

```bash
pnpm build
rsync -av --delete dist/ user@<oracle-ip>:/var/www/letsmock/
```

```nginx
server {
    server_name letsmock.com www.letsmock.com;
    root /var/www/letsmock;
    index index.html;

    # Astro emits /privacy/index.html — serve it for /privacy too.
    location / {
        try_files $uri $uri/ $uri.html =404;
    }
}
```

TLS: either Cloudflare proxy (orange cloud, DNS already there) or certbot on
the box. Cloudflare is less to maintain.

## Keep in step

The privacy policy lists exactly what is collected and which processors see it.
Google compares it against the Play Console **Data Safety** form — if you change
what the app stores, change both.
