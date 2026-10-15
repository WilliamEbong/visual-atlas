# v0.3 source research (checked 2026-10-15, official documentation and live records)

The rule is the constitution's: the app keeps an image only when the source's own record states a permission
it accepts, read by ordinary code (CC0, Public Domain Mark or an explicit public-domain flag, CC BY with
credit). An unclear licence makes an image ineligible. A rule never accepts an image on the strength of free
text.

| Source | Decision | Why |
|---|---|---|
| Rijksmuseum | **Accept** | Each image's own rights statement is a URI |
| National Gallery of Art | **Accept, from its open data** | Per-image `openaccess` flag; no search API, so the app searches a local index |
| Library of Congress | **Reject (disabled)** | Rights are free text that varies by collection; the JSON API was blocked by Cloudflare |
| NASA Image and Video Library | **Reject (disabled)** | No per-item rights field; third-party material is marked only in free text |

## Rijksmuseum — accept
- **Search:** `GET https://data.rijksmuseum.nl/search/collection`.
  - Parameters include `description`, `title`, `creator`, `type`, `imageAvailable=true` and `pageToken`.
  - Returns a Linked Art OrderedCollectionPage of object ids, 100 per page.
  - No key is needed. Docs: https://data.rijksmuseum.nl/docs/search
- **Item:** each id (`https://id.rijksmuseum.nl/…`) resolves to Linked Art JSON-LD when requested with
  `Accept: application/ld+json`. Follow the object's `shows` to the VisualItem, then its `digitally_shown_by`
  to the DigitalObject, whose `access_point` is a IIIF image URL.
- **Rights field:** `VisualItem.subject_to[].classified_as[].id`, a URI. Values seen live:
  - Public Domain Mark 1.0, `https://creativecommons.org/publicdomain/mark/1.0/` (e.g. SK-C-211).
  - In Copyright, `https://rightsstatements.org/vocab/InC/1.0/` (a Karel Appel print).
  - The policy also lists CC0 1.0 and CC BY 4.0. Policy: https://data.rijksmuseum.nl/policy
- **Trap:** the CC0 on the *object's metadata record* (`subject_of … subject_to`) licenses the metadata, not the
  image. The rule ignores it.
- **Images:** IIIF Image API 3 on `iiif.micr.io`. `https://iiif.micr.io/{id}/full/3000,/0/default.jpg` returned
  200 (about 1.4 MB).
- **Rule:** accept when the VisualItem's rights URI is PDM 1.0, CC0 1.0 or CC BY 4.0 (CC BY keeps the credit
  "Rijksmuseum"). Reject In Copyright, any other value, and a missing one.

## National Gallery of Art, Washington — accept, from its open data
- **No keyword search API.** `api.nga.gov` serves IIIF only.
- **Open data:** https://github.com/NationalGalleryOfArt/opendata (CC0; exported daily, latest 2026-10-15).
  - `objects.csv` has object id, title, date, medium, attribution and classification.
  - `published_images.csv` has uuid, `iiifurl`, view type, size, `maxpixels` and `openaccess`; join on
    `depictstmsobjectid = objectid`.
- **Rights field:** `published_images.openaccess`.
  - The data dictionary defines 1 as an open-access image with no usage restrictions, released as CC0 under the
    Gallery's open-access policy, and 0 as a rights-restricted image.
  - A restricted image also carries a small `maxpixels` (e.g. 900).
  - In a 1,458-row sample, one row had `openaccess=1` with `maxpixels=900`; the rule skips it.
- **Images:** IIIF 2, `{iiifurl}/full/!3000,3000/0/default.jpg` returned 200 (about 1.5 MB). Terms:
  https://www.nga.gov/terms-and-notices. Credit: "Courtesy National Gallery of Art, Washington".
- **Rule:** accept when `openaccess` is 1, `maxpixels` is empty and the view is primary (recorded as CC0). Reject
  everything else.
- **How the app searches it:** it downloads the two CSVs once, keeps only open-access primary images in a compact
  local index in the library folder, and searches that index by words.

## Library of Congress — reject (disabled)
- **JSON API:** `https://www.loc.gov/photos/?q=…&fo=json` and `https://www.loc.gov/item/{id}/?fo=json`. The
  documented limit is about 20 requests a minute, and going over it blocks for an hour
  (https://www.loc.gov/apis/json-and-yaml/working-within-limits/).
- **Rights are free text** in `rights_advisory`, `rights_information` and collection-level `rights`, and they vary
  by collection.
  - The Library's own notebook warns that `access_restricted` is not comprehensive.
  - In a sample of its "Free to Use" data package, the rights column had more than ten wordings.
  - Those sets mix public domain, no known copyright and works cleared by the owner, with no per-item
    distinction.
- **Live access:** every request to the www.loc.gov JSON API from this machine got a Cloudflare challenge
  (403, 5 of 5). No attempt was made to get around it.
- **Decision:** disabled. Reconsider only with an exact-match rule (`rights_advisory` exactly "No known
  restrictions on publication.") and a working API.

## NASA Image and Video Library — reject (disabled)
- **API:** `https://images-api.nasa.gov/search?q=…&media_type=image`, `/asset/{nasa_id}`, `/metadata/{nasa_id}`.
  No key is needed. Docs: https://images.nasa.gov/docs/images.nasa.gov_api_docs.pdf
- **No per-item rights field.** NASA's guidelines say its material is generally not subject to copyright in the
  United States, but third-party material is marked only by name. Seen live:
  - A description containing "contains some copyrighted materials".
  - Another containing "copyright Rick Sternbach 1977".
  - Credits like "NASA/JPL-Caltech/ASU" and "For Roscosmos".
  - Guidelines: https://www.nasa.gov/nasa-brand-center/images-and-media/
- **Decision:** disabled. Telling NASA's own work from third-party material would mean interpreting free text;
  "US Government work" is also not a licence the app currently accepts.
