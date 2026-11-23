r"""Real MCP round trip: official MCP Python SDK client -> `uv run atlas mcp` over stdio.

Needs the SDK in a separate venv (pip install mcp; uv could not install its pywin32 dependency on this machine):
    <venv>\Scripts\python docs/evaluation/v0.5/mcp_roundtrip.py <repo> <scratch VISUAL_ATLAS_HOME> [brief] [off|auto]
The committed output (mcp-roundtrip.json) was made with design systems off, so no private catalogue data is in it."""
import json, os, sys
import anyio
from mcp import Client, StdioServerParameters
import mcp.types as types

REPO = sys.argv[1]
HOME = sys.argv[2]
BRIEF = sys.argv[3] if len(sys.argv) > 3 else 'A calm opener slide: one small boat on a wide, empty sea'
SYSTEMS = sys.argv[4] if len(sys.argv) > 4 else 'off'

async def main():
    params = StdioServerParameters(command='uv', args=['run', '--directory', REPO, 'atlas', 'mcp'],
                                   env={'VISUAL_ATLAS_HOME': HOME, 'VISUAL_ATLAS_DESIGN_SYSTEMS': SYSTEMS,
                                        'PATH': os.environ['PATH'], 'USERPROFILE': os.environ['USERPROFILE']})
    async with Client(params) as client:
        out = {'protocol_version': client.protocol_version, 'server_info': str(client.server_info)}
        tools = await client.list_tools()
        out['tools'] = [t.name for t in tools.tools]
        r = await client.call_tool('advise', {'brief': BRIEF, 'limit': 4})
        s = r.structured_content
        out['advise'] = {'is_error': r.is_error, 'route': s['route']['system'], 'refs': [(x['ref'], x['layer'], x['licence']['label'], x['reasons'][:2]) for x in s['results']]}
        first = s['results'][0]['ref']
        v = await client.call_tool('view_reference', {'ref': first, 'max_size': 512})
        img = [c for c in v.content if isinstance(c, types.ImageContent)][0]
        out['view'] = {'ref': first, 'mime': img.mime_type, 'base64_chars': len(img.data)}
        bad = await client.call_tool('get_reference', {'ref': r'..\..\Windows\win.ini'})
        out['traversal'] = {'is_error': bad.is_error, 'text': bad.content[0].text}
        print(json.dumps(out, indent=1, ensure_ascii=False))

anyio.run(main)
