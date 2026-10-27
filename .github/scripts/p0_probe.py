import json, os, subprocess, tempfile, urllib.request, time
from pathlib import Path

def api(path, data=None):
    url='https://api.github.com/repos/'+os.environ['GITHUB_REPOSITORY']+'/'+path
    request=urllib.request.Request(url,data=json.dumps(data).encode() if data is not None else None,headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=30) as response:return json.load(response)

def cli(*args):
    p=subprocess.run(['toy',*args,'--json'],capture_output=True,text=True,timeout=90)
    if p.returncode:
        try:
            d=json.loads(p.stdout or p.stderr)
            print('CLI failure code:',d.get('code','unknown'))
        except ValueError:print('CLI failure: non-JSON response')
        raise SystemExit(1)
    return json.loads(p.stdout)

assert os.environ.get('TOY_CLI_SESSION_TOKEN'), 'Configure TOY_SESSION_TOKEN'
with tempfile.TemporaryDirectory(prefix='toy-p0-') as home:
    os.environ['TOY_HOME']=home
    who=cli('whoami')
    assert isinstance(who.get('uid'),int)
    toys=cli('mylist','--page','1','--size','2')
    assert isinstance(toys.get('list'),list) and isinstance(toys.get('total'),int)
    print('Fresh home authentication: PASS')
    print('Account-scoped paginated listing: PASS')
    invalid=os.environ['TOY_CLI_SESSION_TOKEN']; os.environ['TOY_CLI_SESSION_TOKEN']='invalid-test-session'
    result=subprocess.run(['toy','whoami','--json'],capture_output=True,text=True,timeout=90)
    assert result.returncode != 0
    os.environ['TOY_CLI_SESSION_TOKEN']=invalid
    assert cli('whoami')['uid']==who['uid']
    print('Invalid credential rejected and valid credential restored: PASS')
    site=Path(home)/'site';site.mkdir();(site/'index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>Toy Action verification</title><h1>Toy Action verification / 发布流程验证</h1><p>Static sample used to verify preview and submission packaging.</p></html>')
    preview=cli('create',str(site),'--title','Toy Action verification','--slug','toy-action-verification-20261027','--visibility','link-only','--category','TOOL')
    assert isinstance(preview.get('preview_url'),str)
    assert not preview.get('id'), 'Record newly observed preview ID semantics before proceeding'
    print('Preview upload accepted; response contains preview_url, no Toy ID: PASS')
    from urllib.parse import urlparse,parse_qs
    parsed=urlparse(preview['preview_url'])
    print('Preview URL shape:',json.dumps({'scheme':parsed.scheme,'host':parsed.hostname,'path_segments':len(parsed.path.strip('/').split('/')),'query_keys':list(parse_qs(parsed.query))}))
    # Never publish the opaque preview identifier in public records.
    state=api('deployments',{'ref':os.environ['GITHUB_SHA'],'task':'toy:p0','auto_merge':False,'required_contexts':[],'environment':'toy-p0','production_environment':False,'payload':{'schema':1,'probe':'hosted-runner','run_id':os.environ['GITHUB_RUN_ID']}})
    assert state['id']
    found=api('deployments?task=toy%3Ap0&environment=toy-p0&per_page=100')
    assert any(x['id']==state['id'] for x in found)
    api('deployments/'+str(state['id'])+'/statuses',{'state':'success','description':'Authentication, preview and record storage verified; no review submission','auto_inactive':False})
    print('GITHUB_TOKEN Deployment write/read/status: PASS')
    summary='## P0 verification\n\nFresh-home authentication, invalid-token rejection/recovery, paginated listing, preview-only upload, and Deployment write/read passed on a GitHub-hosted Ubuntu runner. No Toy review submission was made.\n'
    with open(os.environ['GITHUB_STEP_SUMMARY'],'a') as f:f.write(summary)
