"""Load, validate and sync the editable knowledge files (taxonomy and source policies)."""

import hashlib
import json
import re
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from atlas.home import DATA

Slug = Annotated[str, Field(pattern=r'^[a-z0-9]+(-[a-z0-9]+)*$', max_length=60)]
Text = Annotated[str, Field(min_length=1, max_length=1200)]
PROVIDERS = ('aic', 'met', 'cma', 'smithsonian', 'commons')
RELATIONS = ('often_combined', 'opposite_strategy', 'similar_purpose', 'builds_on', 'can_create', 'related')


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


class Named(Strict):
    id: Slug
    name: str = Field(min_length=1, max_length=80)
    description: Text


class Domain(Named):
    variables: list[str] = Field(min_length=1)


class Confusion(Strict):
    technique: Slug
    how_to_tell: Text


class Relation(Strict):
    technique: Slug
    relation: Literal[RELATIONS]


class Source(Strict):
    citation: str = Field(min_length=1, max_length=300)
    url: str = Field(pattern=r'^https://', max_length=500)


class Technique(Strict):
    id: Slug
    name: str = Field(min_length=1, max_length=80)
    aliases: list[str]
    definition: Text
    explanation: Text
    when_it_helps: list[str] = Field(min_length=1)
    observable_cues: list[str] = Field(min_length=1)
    confusions: list[Confusion] = Field(min_length=1)
    limitations: Text
    counterexample: Text
    related: list[Relation] = Field(min_length=1)
    goals: list[str] = Field(min_length=1)
    operations: list[str] = Field(min_length=1)
    domains: list[str] = Field(min_length=1)
    search_hints: dict[str, list[str]]
    sources: list[Source]
    working_definition: bool


class Taxonomy(Strict):
    version: str
    note: str
    goals: list[Named] = Field(min_length=1)
    operations: list[Named] = Field(min_length=1)
    domains: list[Domain] = Field(min_length=1)
    techniques: list[Technique] = Field(min_length=1)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(data_dir: Path = DATA) -> tuple[dict, dict, str, str]:
    """Return (taxonomy, policies, taxonomy_sha, policies_sha); raise ValueError listing every problem."""
    taxonomy_path, policies_path = data_dir / 'taxonomy.json', data_dir / 'source_policies.json'
    try:
        raw = json.loads(taxonomy_path.read_text(encoding='utf-8'))
        taxonomy = Taxonomy.model_validate(raw).model_dump()
        policies = json.loads(policies_path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f'could not read knowledge files: {error}') from None
    except ValidationError as error:
        raise ValueError('taxonomy.json is invalid:\n' + '\n'.join(
            f"  {'.'.join(map(str, item['loc']))}: {item['msg']}" for item in error.errors())) from None
    problems = check(taxonomy, policies)
    if problems:
        raise ValueError('knowledge files have problems:\n' + '\n'.join('  ' + p for p in problems))
    return taxonomy, policies, _sha(taxonomy_path), _sha(policies_path)


def check(taxonomy: dict, policies: dict) -> list[str]:
    """Cross-reference checks that the schema cannot express."""
    problems = []
    ids = {kind: [item['id'] for item in taxonomy[kind]] for kind in ('goals', 'operations', 'domains', 'techniques')}
    for kind, values in ids.items():
        duplicates = {value for value in values if values.count(value) > 1}
        if duplicates:
            problems.append(f'duplicate {kind} ids: {", ".join(sorted(duplicates))}')
    known = {kind: set(values) for kind, values in ids.items()}
    for technique in taxonomy['techniques']:
        tid = technique['id']
        for kind in ('goals', 'operations', 'domains'):
            for target in technique[kind]:
                if target not in known[kind]:
                    problems.append(f'{tid}: unknown {kind[:-1]} "{target}"')
        for item in technique['related'] + technique['confusions']:
            if item['technique'] not in known['techniques']:
                problems.append(f'{tid}: refers to unknown technique "{item["technique"]}"')
            if item['technique'] == tid:
                problems.append(f'{tid}: refers to itself')
        if not technique['sources'] and not technique['working_definition']:
            problems.append(f'{tid}: needs sources or working_definition: true')
        unknown_providers = set(technique['search_hints']) - set(PROVIDERS)
        if unknown_providers:
            problems.append(f'{tid}: search hints for unknown providers {sorted(unknown_providers)}')
    providers = policies.get('providers') or []
    for provider in providers:
        if provider.get('status') not in ('enabled', 'disabled', 'candidate'):
            problems.append(f'policy {provider.get("id")}: status must be enabled, disabled or candidate')
        if not provider.get('evidence_urls') or not provider.get('checked_on'):
            problems.append(f'policy {provider.get("id")}: needs evidence_urls and checked_on')
        if provider.get('status') == 'enabled':
            missing = {'hosts', 'accepted_licenses', 'rule', 'label', 'attribution', 'permitted_mode'} - set(provider)
            if missing:
                problems.append(f'policy {provider["id"]}: enabled providers need {sorted(missing)}')
            if provider['id'] not in PROVIDERS:
                problems.append(f'policy {provider["id"]}: no connector exists for this provider')
            if any(not re.fullmatch(r'[a-z0-9.-]+', host) for host in provider.get('hosts', [])):
                problems.append(f'policy {provider["id"]}: hosts must be bare host names')
        elif not provider.get('reason'):
            problems.append(f'policy {provider.get("id")}: disabled or candidate providers need a reason')
    return problems


def policy(policies: dict, provider_id: str) -> dict:
    for provider in policies['providers']:
        if provider['id'] == provider_id:
            return provider
    raise ValueError(f'unknown provider {provider_id}')


def sync(store, data_dir: Path = DATA, force: bool = False) -> bool:
    """Reload the knowledge files into the database when they changed. Returns True if it synced."""
    taxonomy, policies, taxonomy_sha, policies_sha = load(data_dir)
    current = {row['name']: row['sha256'] for row in store.rows('SELECT name, sha256 FROM data_versions')}
    if not force and current.get('taxonomy') == taxonomy_sha and current.get('source_policies') == policies_sha:
        return False
    store.replace_catalog(taxonomy, policies, taxonomy_sha, policies_sha)
    return True


def coverage(store) -> list[dict]:
    """Techniques ordered by how few non-rejected examples they have (fewest first)."""
    return store.rows(
        "SELECT t.id, t.name, COUNT(a.id) AS examples FROM techniques t "
        "LEFT JOIN annotations a ON a.technique_id=t.id AND a.state!='rejected' "
        "LEFT JOIN images i ON i.id=a.image_id AND i.removed_at IS NULL "
        "GROUP BY t.id ORDER BY examples, t.name")
