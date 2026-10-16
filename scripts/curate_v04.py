"""Bounded v0.4 starter searches; all network and rights checks use the app's existing paths.

Run with an explicit scratch directory outside the repository. This never edits the starter pack.
"""

import argparse
import json
from pathlib import Path

from atlas import catalog, images, providers, rights
from atlas.fetch import Fetcher, FetchError


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('home', type=Path)
    parser.add_argument('query')
    parser.add_argument('--provider', default='commons', choices=providers.PROVIDERS)
    parser.add_argument('--download', action='store_true')
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    if args.home.resolve().is_relative_to(repo) or 'onedrive' in str(args.home.resolve()).lower():
        parser.error('Use a scratch directory outside the repository and OneDrive.')
    args.home.mkdir(parents=True, exist_ok=True)
    policies = catalog.load()[1]
    fetcher = Fetcher(policies)
    path = args.home / 'candidates.json'
    entries = json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
    try:
        for item in providers.search(fetcher, args.provider, args.query, per_page=12, home=args.home):
            item['search_query'] = args.query
            item['rights'] = rights.check(item, catalog.policy(policies, args.provider))
            if args.download and item['rights']['eligible']:
                try:
                    data = fetcher.get_image(args.provider, item['image_url'], headers=item['image_headers'])
                    picture, kind = images.open_checked(data)
                    item['quality_problem'] = images.quality_problem(picture, images.metrics(picture))
                    record, blobs = images.prepare_files(data, picture, kind)
                    images.write_files(args.home / 'media', blobs)
                    item['files'] = record
                except (ValueError, OSError, FetchError) as error:
                    item['download_error'] = getattr(error, 'code', type(error).__name__)
            entries.append(item)
            print(item['provider_item_id'], ascii(item['title']), item['rights'].get('license_code', item['rights'].get('reason')),
                  item.get('files', {}).get('analysis_path', ''))
    finally:
        fetcher.close()
        path.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
