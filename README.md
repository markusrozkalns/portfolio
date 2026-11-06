# rozkalns.design

Portfolio site of Markus Rozkalns, UX/UI designer.

- `src/` — page sources (`*.dc.html`, designed on the Claude Design canvas), images, videos, fonts, files
- `build.py` — turns `src/` into a static site: `python3 build.py` writes `dist/`, `python3 build.py --preview` writes a file-friendly `preview/`
- `dist/` — the built site that Vercel serves (see `vercel.json`)

To publish a change: edit `src/`, run `python3 build.py`, commit `src/` and `dist/`, push.

Visitor statistics: Umami Cloud, cookieless (unique visitors, page views, countries, cities). Set `UMAMI_ID` in `build.py` to the Website ID from cloud.umami.is; leave it empty to build without tracking. Only the live domain is counted, not Vercel previews or `--preview` builds.
