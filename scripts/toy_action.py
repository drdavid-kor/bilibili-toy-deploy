#!/usr/bin/env python3
"""Bilibili Toy Action: deterministic packages, explicit submission, recoverable state."""
from __future__ import annotations
import argparse, hashlib, io, json, os, re, shutil, subprocess, sys, tempfile, time, urllib.error, urllib.parse, urllib.request, zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TOOL='bilibili-toy-deploy'
SCHEMA=1
SLUG=re.compile(r'[A-Za-z0-9_-]{1,64}\Z')
SHA=re.compile(r'[0-9a-f]{40}\Z')
META={'title','category','visibility','icon','poster','theme','watermark','activity'}
CATEGORIES={'GAME','INTERACTIVE_PLAY','TOOL','TEST','GUIDE','COLLECTION','OTHER'}
class Failure(Exception): pass
class Unknown(Failure): pass

def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def canonical(data): return json.dumps(data,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def jsonfile(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def save(path,data): Path(path).write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def output(key,value):
    if value is None: return
    value=str(value)
    if '\n' in value or '\r' in value: raise Failure('Invalid multiline Action output')
    dest=os.environ.get('GITHUB_OUTPUT')
    if dest:
        with open(dest,'a') as f:f.write(f'{key}={value}\n')
def summary(message):
    # Only caller-selected non-secret data, never raw CLI output.
    print(message)
    dest=os.environ.get('GITHUB_STEP_SUMMARY')
    if dest:
        with open(dest,'a') as f:f.write(message+'\n\n')
def valid_int(x): return isinstance(x,int) and not isinstance(x,bool) and x>0

def config_load(path):
    cfg=jsonfile(path)
    if not isinstance(cfg,dict) or set(cfg)-{'slug','directory','toy_id','create','metadata'}:raise Failure('Unknown configuration field')
    if not isinstance(cfg.get('slug'),str) or not SLUG.fullmatch(cfg['slug']):raise Failure('slug must use 1–64 ASCII letters, numbers, underscore or hyphen')
    if cfg.get('toy_id') is not None and not valid_int(cfg['toy_id']):raise Failure('toy_id must be a positive integer')
    if not isinstance(cfg.get('directory'),str) or not cfg['directory']:raise Failure('directory is required')
    for key in ('create','metadata'):
        fields=cfg.setdefault(key,{})
        if not isinstance(fields,dict) or set(fields)-META:raise Failure('Unsupported metadata field in '+key)
        for field,value in fields.items():
            if field=='watermark':
                if not isinstance(value,bool):raise Failure('watermark must be a JSON boolean')
            elif not isinstance(value,str) or not value.strip() or '\x00' in value:raise Failure('Metadata values must be nonempty strings')
        if 'category' in fields and fields['category'] not in CATEGORIES:raise Failure('Unsupported category')
        if 'visibility' in fields and fields['visibility'] not in {'link-only','public'}:raise Failure('This beta supports link-only/public visibility; password access must be configured on the platform')
    return cfg

def safe_relative(base,value):
    p=Path(value)
    if p.is_absolute() or '..' in p.parts:raise Failure('Paths must stay within the project directory')
    candidate=base/p
    if any(x.is_symlink() for x in [candidate,*candidate.parents] if x!=base.parent):raise Failure('Symlinks are not supported in publishing paths')
    resolved=candidate.resolve()
    if not resolved.is_relative_to(base.resolve()):raise Failure('Path escapes project directory')
    return resolved

def doctor(package,slug):
    proc=subprocess.run([sys.executable,str(ROOT/'vendor/toy_doctor.py'),str(package),'--slug',slug,'--require-root-index','--json'],capture_output=True,text=True)
    try: report=json.loads(proc.stdout)
    except ValueError:raise Failure('Preflight did not return a valid report')
    for finding in report.get('findings',[]):
        # Static text may include workflow control sequences; print prefixed JSON.
        summary('Preflight '+json.dumps(finding,ensure_ascii=True))
    if proc.returncode or not report.get('ok'):raise Failure('Preflight failed. Fix ERROR findings before retrying.')
    return report

def package(args):
    base=Path(args.config).resolve().parent; cfg=config_load(args.config)
    bundle=Path(args.bundle).resolve()
    src=safe_relative(base,cfg['directory'])
    if bundle==src or bundle.is_relative_to(src):raise Failure('Bundle directory must be outside the published directory')
    bundle.mkdir(parents=True,exist_ok=True)
    if any(bundle.iterdir()):raise Failure('Bundle output directory must be empty')
    for section in ('create','metadata'):
        for kind in ('poster','icon'):
            if kind in cfg[section]:
                asset=safe_relative(base,cfg[section][kind])
                if not asset.is_file():raise Failure('Metadata image does not exist')
                name=f'{section}-{kind}{asset.suffix.lower()}'
                shutil.copyfile(asset,bundle/name);cfg[section][kind]=name
    save(bundle/'config.json',cfg)
    if args.metadata_only:
        if not cfg['metadata']:raise Failure('metadata must contain explicit fields to synchronize')
        pkgsha=None
    else:
        if not src.is_dir() or not (src/'index.html').is_file():raise Failure('Built directory must contain root index.html')
        with zipfile.ZipFile(bundle/'package.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            for f in sorted(src.rglob('*')):
                if f.is_symlink():raise Failure('Package contains a symlink')
                if f.is_file():
                    rel=f.relative_to(src).as_posix()
                    if any(x.startswith('.') or x=='node_modules' for x in f.relative_to(src).parts):raise Failure('Build directory includes hidden/private or dependency files')
                    info=zipfile.ZipInfo(rel,date_time=(2020,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
                    z.writestr(info,f.read_bytes())
        doctor(bundle/'package.zip',cfg['slug']);pkgsha=digest(bundle/'package.zip')
    sha=args.source_sha or os.environ.get('GITHUB_SHA','')
    if sha and not SHA.fullmatch(sha):raise Failure('source-sha must be a full commit SHA')
    assets={p.name:digest(p) for p in bundle.iterdir() if p.name not in {'package.zip','manifest.json'}}
    save(bundle/'manifest.json',{'schema':SCHEMA,'sha':sha,'slug':cfg['slug'],'package_sha':pkgsha,'files':assets,'preview':False,'repository':os.environ.get('GITHUB_REPOSITORY','')})
    output('status','checked');output('bundle',bundle);output('package-sha',pkgsha);summary('Package checked and sealed. / 产物已预检并固定。')

def load_bundle(args,require_preview=False):
    bundle=Path(args.bundle).resolve();manifest=jsonfile(bundle/'manifest.json');cfg=config_load(bundle/'config.json')
    if manifest.get('schema')!=SCHEMA or manifest.get('slug')!=cfg['slug']:raise Failure('Invalid bundle manifest')
    if args.source_sha and manifest.get('sha')!=args.source_sha:raise Failure('Bundle commit does not match requested commit')
    if manifest.get('repository')!=os.environ.get('GITHUB_REPOSITORY',''):raise Failure('Bundle belongs to another repository')
    for name,expected in manifest.get('files',{}).items():
        if Path(name).name!=name or digest(bundle/name)!=expected:raise Failure('Bundle metadata digest mismatch')
    if 'config.json' not in manifest.get('files',{}):raise Failure('Bundle is missing configuration digest')
    if manifest.get('package_sha') and digest(bundle/'package.zip')!=manifest['package_sha']:raise Failure('Package digest mismatch')
    if require_preview and not manifest.get('preview'):raise Failure('No successful preview. Generate a preview for this commit or explicitly use manual override.')
    return bundle,manifest,cfg

class GitHub:
    def __init__(self,repository=None,token=None):
        self.repo=repository or os.environ.get('GITHUB_REPOSITORY','')
        self.token=token or os.environ.get('GH_TOKEN','')
        if not re.fullmatch(r'[\w.-]+/[\w.-]+',self.repo) or not self.token:raise Failure('GitHub repository and token are required')
    def call(self,path,data=None,method=None):
        url='https://api.github.com/repos/'+self.repo+'/'+path
        request=urllib.request.Request(url,data=canonical(data).encode() if data is not None else None,method=method,headers={'Authorization':'Bearer '+self.token,'Accept':'application/vnd.github+json','Content-Type':'application/json','X-GitHub-Api-Version':'2022-11-28'})
        for attempt in range(3 if data is None and method is None else 1):
            try:
                with urllib.request.urlopen(request,timeout=30) as r:return json.load(r)
            except urllib.error.HTTPError as e:
                if e.code>=500 and data is None and attempt<2:time.sleep(attempt+1);continue
                raise Failure(f'GitHub API request failed (HTTP {e.code}); inspect workflow permissions or retry read operations.') from None
            except (urllib.error.URLError,TimeoutError,ValueError):
                if data is None and attempt<2:time.sleep(attempt+1);continue
                raise Failure('GitHub API result unavailable; do not assume a write failed.') from None
    def pages(self,path,key=None):
        result=[]
        for page in range(1,1001):
            value=self.call(path+('&' if '?' in path else '?')+f'per_page=100&page={page}')
            rows=value[key] if key else value
            if not isinstance(rows,list):raise Failure('Unexpected GitHub list response')
            result.extend(rows)
            if len(rows)<100:return result
        raise Failure('GitHub pagination exceeded supported size')
    def records(self,slug,kind=None):
        records=self.pages('deployments?environment='+urllib.parse.quote('toy-'+slug,safe=''))
        return [r for r in records if isinstance(r.get('payload'),dict) and r['payload'].get('tool')==TOOL and r['payload'].get('schema')==SCHEMA and r['payload'].get('slug')==slug and (not kind or r['payload'].get('kind')==kind)]
    def record(self,sha,slug,kind,**payload):
        data={'tool':TOOL,'schema':SCHEMA,'kind':kind,'slug':slug,'sha':sha,'run_id':os.environ.get('GITHUB_RUN_ID',''),'run_attempt':os.environ.get('GITHUB_RUN_ATTEMPT','1'),'actor':os.environ.get('GITHUB_ACTOR',''),**payload}
        record=self.call('deployments',{'ref':sha,'task':'toy:'+kind,'auto_merge':False,'required_contexts':[],'environment':'toy-'+slug,'production_environment':False,'payload':data})
        if not valid_int(record.get('id')):raise Failure('Deployment write returned no ID')
        return record
    def status(self,record,state,description):
        log='https://github.com/'+self.repo+'/actions/runs/'+os.environ.get('GITHUB_RUN_ID','')
        return self.call(f"deployments/{record['id']}/statuses",{'state':state,'description':description[:140],'log_url':log,'auto_inactive':False})
    def state(self,record):
        statuses=self.call(f"deployments/{record['id']}/statuses?per_page=1")
        return statuses[0]['state'] if statuses else 'pending'

class Toy:
    def __init__(self,binary=None):
        self.binary=binary or os.environ.get('TOY_BINARY','toy')
        self.temp=tempfile.TemporaryDirectory(prefix='toy-session-')
        self.env=os.environ.copy();self.env.update(TOY_HOME=self.temp.name,TOY_NO_UPDATE_CHECK='1')
        # Do not pass GitHub's token into the external CLI.
        for key in ('GH_TOKEN','GITHUB_TOKEN'):self.env.pop(key,None)
        if not self.env.get('TOY_CLI_SESSION_TOKEN'):raise Failure('TOY_SESSION_TOKEN is missing. Configure it using scripts/set_secret.py.')
        p=subprocess.run([self.binary,'--help-json'],capture_output=True,text=True,env=self.env,timeout=20)
        try: helpdata=json.loads(p.stdout)
        except ValueError:raise Failure('CLI help contract unavailable')
        self.help={tuple(x['path']):x for x in helpdata.get('commands',[])}
        self.version=helpdata.get('version','unknown')
        for cmd in ('whoami','mylist','create','update'):
            if (cmd,) not in self.help:raise Failure('Unsupported CLI command contract')
    def close(self):self.temp.cleanup()
    def call(self,args,write=False):
        try:p=subprocess.run([self.binary,*args,'--json'],capture_output=True,text=True,env=self.env,timeout=100)
        except (subprocess.TimeoutExpired,OSError):
            if write:raise Unknown('Request outcome is unknown. Check Bilibili before retrying.') from None
            raise Failure('Toy CLI unavailable or query timed out') from None
        try:data=json.loads(p.stdout)
        except ValueError:data=None
        if p.returncode:
            # Official CLI business errors may be text. Never echo raw responses.
            code=data.get('code') if isinstance(data,dict) else None
            match=re.search(r'\bcode[=:]\s*(\d+)\b',p.stderr)
            if code is None and match:code=int(match.group(1))
            if code in (307001,307029):raise Failure('Toy session expired; log in locally and replace TOY_SESSION_TOKEN.')
            if code is not None:raise Failure(f'Toy rejected the request (code {code}). Inspect the platform; raw responses are not logged.')
            if write:raise Unknown('Request outcome is unknown. Check Bilibili before retrying.')
            raise Failure('Toy query failed; check credentials, network and CLI compatibility')
        if not isinstance(data,dict):
            if write:raise Unknown('Invalid submission response; result is unknown.')
            raise Failure('Invalid CLI JSON response')
        return data
    def account(self):
        uid=self.call(['whoami']).get('uid')
        if not valid_int(uid):raise Failure('CLI did not return a valid current account')
        self.uid=uid
        return hashlib.sha256(str(uid).encode()).hexdigest()[:24]
    def toys(self):
        rows=[];expected=None
        for page in range(1,1001):
            data=self.call(['mylist','--page',str(page),'--size','50'])
            if not isinstance(data.get('list'),list) or not isinstance(data.get('total'),int) or data['total']<0 or data.get('pn')!=page or not valid_int(data.get('ps')):raise Failure('Cannot establish complete Toy pagination')
            if expected is None:expected=data['total']
            elif data['total']!=expected:raise Failure('Toy list changed during pagination. Retry the read.')
            for item in data['list']:
                url=urllib.parse.urlparse(item.get('url',''));match=re.fullmatch(r'/toy/([A-Za-z0-9_-]+)(?:/index\.html|/)?',url.path)
                if url.scheme!='https' or url.hostname!='www.bilibili.com' or not valid_int(item.get('id')) or not match or item.get('user_info',{}).get('mid')!=self.uid:raise Failure('Toy listing contains unverifiable ownership or slug')
                item={**item,'slug':match.group(1)};rows.append(item)
            if len(rows)==expected:
                if len({x['id'] for x in rows})!=len(rows):raise Failure('Duplicate Toy IDs in listing')
                return rows
            if not data['list'] or len(rows)>expected:raise Failure('Toy pagination incomplete')
        raise Failure('Toy pagination exceeded supported size')
    def metadata_flags(self,command,fields,bundle):
        supported={f['name'] for f in self.help[(command,)]['flags']};argv=[]
        for name,value in fields.items():
            if name not in supported:raise Failure('Metadata field unsupported by pinned CLI: '+name)
            if name in {'poster','icon'}:value=str(bundle/value)
            if isinstance(value,bool):argv.append('--'+name+'='+str(value).lower())
            else:argv.extend(['--'+name,value])
        return argv

def resolve_target(gh,toy,cfg,account,sha):
    records=gh.records(cfg['slug'],'binding')
    binding=records[0]['payload'] if records else None
    if binding and binding.get('account')!=account:raise Failure('Stored association belongs to another Toy account. Restore the original account or explicitly reset association records.')
    toyid=cfg.get('toy_id')
    if binding and toyid and binding.get('toy_id')!=toyid:raise Failure('Explicit Toy ID conflicts with stored association')
    if binding:toyid=binding.get('toy_id')
    items=toy.toys();matches=[x for x in items if x['slug']==cfg['slug']]
    if len(matches)>1:raise Failure('More than one Toy matches slug; resolve the target explicitly')
    if toyid:
        chosen=next((x for x in items if x['id']==toyid),None)
        if not chosen or chosen['slug']!=cfg['slug']:raise Failure('Toy ID, slug or account mismatch')
    else:chosen=matches[0] if matches else None
    if chosen and not binding:
        rec=gh.record(sha,cfg['slug'],'binding',account=account,toy_id=chosen['id']);gh.status(rec,'success','Association saved; no content submitted')
    return chosen

def trusted_event():
    if os.environ.get('GITHUB_EVENT_NAME') not in {'push','workflow_dispatch','release'}:raise Failure('Publishing is restricted to push, workflow_dispatch or release; PRs may only check packages.')

def write_operation(args):
    trusted_event()
    event=os.environ.get('GITHUB_EVENT_NAME')
    if args.mode=='submit' and (event not in {'release','workflow_dispatch'} or not args.release_id):raise Failure('Submission requires a published Release and release or manual dispatch event')
    if args.mode=='sync-metadata' and event!='workflow_dispatch':raise Failure('Metadata sync requires manual dispatch')
    if args.mode=='preview' and event=='release':raise Failure('Release cannot silently generate a new preview')
    gh=GitHub();bundle,manifest,cfg=load_bundle(args,args.mode=='submit' and not args.override)
    if args.override and os.environ.get('GITHUB_EVENT_NAME')!='workflow_dispatch':raise Failure('Override is available only through manual dispatch')
    sha=manifest['sha'];toy=Toy()
    try:
        account=toy.account()
        if manifest.get('account') and manifest['account']!=account:raise Failure('Preview account differs from current account')
        chosen=resolve_target(gh,toy,cfg,account,sha)
        if manifest.get('toy_id') and (not chosen or chosen['id']!=manifest['toy_id']):raise Failure('Preview Toy identity changed')
        if args.mode=='sync-metadata' and not chosen:raise Failure('Metadata sync needs an existing Toy')
        if args.mode=='preview':
            if not manifest.get('package_sha'):raise Failure('Preview bundle has no package')
            doctor(bundle/'package.zip',cfg['slug'])
            if chosen:argv=['update',str(chosen['id']),str(bundle/'package.zip')]
            else:argv=['create',str(bundle/'package.zip'),'--slug',cfg['slug'],*toy.metadata_flags('create',{'visibility':'link-only',**cfg['create']},bundle)]
            result=toy.call(argv)
            url=result.get('preview_url')
            if not isinstance(url,str) or not url.startswith('https://'):raise Failure('No valid preview URL returned')
            manifest.update(preview=True,account=account,toy_id=chosen['id'] if chosen else None,preview_run=os.environ['GITHUB_RUN_ID'],cli_version=toy.version)
            save(bundle/'manifest.json',manifest)
            rec=gh.record(sha,cfg['slug'],'preview',account=account,toy_id=manifest['toy_id'],package_sha=manifest['package_sha'],artifact_name='toy-preview-'+sha)
            gh.status(rec,'success','Preview generated; review not submitted')
            output('status','previewed');output('bundle',bundle);output('artifact-name','toy-preview-'+sha);output('package-sha',manifest['package_sha'])
            # Confirmed public preview path contains an opaque capability. Show only via explicit opt-in.
            summary('Preview generated. / 已生成预览。Package SHA-256: `'+manifest['package_sha']+'`')
            if args.expose_preview:
                summary('[Open Toy preview / 打开预览]('+url.replace(')','%29').replace('(','%28')+')')
            else:
                summary('Preview URL withheld. Set expose-preview=true only for content you intend to share; public workflow artifacts are not private storage.')
            return
        kind='metadata' if args.mode=='sync-metadata' else 'submission'
        fingerprint=hashlib.sha256(canonical(cfg['metadata']).encode()).hexdigest() if kind=='metadata' else manifest['package_sha']
        if not fingerprint:raise Failure('No package to submit')
        identity=[args.release_id or 'manual',kind,sha,fingerprint]
        if kind=='metadata' or args.override:identity.append(os.environ.get('GITHUB_RUN_ID',''))
        key=hashlib.sha256(canonical(identity).encode()).hexdigest()
        for old in gh.records(cfg['slug']):
            if old['payload'].get('kind') not in {'submission','metadata'}:continue
            state=gh.state(old)
            if state in {'pending','in_progress','queued','error'}:raise Failure(f"Previous write outcome is unknown (Deployment {old['id']}). Resolve it manually before another write.")
            if old['payload'].get('key')==key and state=='success':
                summary('This exact operation was already accepted; no repeat submission. / 此操作已提交，不重复提审。');output('status','already-submitted');return
        if kind=='metadata':
            if not cfg['metadata']:raise Failure('No explicit metadata fields to sync')
            argv=['update',str(chosen['id']),*toy.metadata_flags('update',cfg['metadata'],bundle),'--yes']
        else:
            doctor(bundle/'package.zip',cfg['slug'])
            if chosen:argv=['update',str(chosen['id']),str(bundle/'package.zip'),'--yes']
            else:argv=['create',str(bundle/'package.zip'),'--slug',cfg['slug'],*toy.metadata_flags('create',{'visibility':'link-only',**cfg['create']},bundle),'--yes']
        # Persist intent before launching the write. If runner dies afterwards, retry is blocked.
        rec=gh.record(sha,cfg['slug'],kind,key=key,account=account,toy_id=chosen['id'] if chosen else None,package_sha=fingerprint,release_id=args.release_id,override=args.override)
        gh.status(rec,'in_progress','Request about to be sent; an interrupted run requires reconciliation')
        try:
            result=toy.call(argv,write=True)
            if not valid_int(result.get('id')) or not isinstance(result.get('status'),str):raise Unknown('Submission response lacks ID or status; check Bilibili before retrying.')
            if chosen and result['id']!=chosen['id']:raise Unknown('Submission returned an unexpected Toy ID; reconcile manually.')
        except Unknown:
            try:gh.status(rec,'error','Result unknown; verify on Bilibili before manual recovery')
            except Failure:pass
            raise
        except Failure:
            gh.status(rec,'failure','CLI explicitly rejected request; no acceptance confirmed')
            raise
        output('toy-id',result['id']);output('status','submitted');output('package-sha',fingerprint)
        summary('Submitted for review / 已提交审核。Toy ID: `'+str(result['id'])+'`. This does not confirm that this version is live.')
        try:
            if not chosen:
                binding=gh.record(sha,cfg['slug'],'binding',account=account,toy_id=result['id']);gh.status(binding,'success','Toy association saved')
            gh.status(rec,'success','Submitted for review; not a confirmation of going live')
        except Failure:
            raise Failure('Bilibili accepted submission but GitHub record update failed. Preserve Toy ID '+str(result['id'])+' and reconcile Deployment '+str(rec['id'])+'; do not resubmit.')
    finally:toy.close()

def resolve_unknown(args):
    trusted_event()
    if os.environ.get('GITHUB_EVENT_NAME')!='workflow_dispatch':raise Failure('Reconciliation must be manually dispatched')
    gh=GitHub();rec=gh.call('deployments/'+str(args.deployment_id));payload=rec.get('payload',{})
    if payload.get('tool')!=TOOL or payload.get('kind') not in {'submission','metadata'}:raise Failure('Not a Toy write record')
    if gh.state(rec) not in {'pending','in_progress','queued','error'}:raise Failure('Record is already resolved')
    if args.resolution=='not-accepted':
        gh.status(rec,'failure','User verified not accepted on Bilibili; manual retry is now allowed')
    elif args.resolution=='accepted':
        toy=Toy()
        try:
            account=toy.account()
            if account!=payload['account']:raise Failure('Account mismatch during reconciliation')
            matches=[x for x in toy.toys() if x['slug']==payload['slug']]
            if len(matches)!=1:raise Failure('Cannot uniquely restore Toy ID')
            if payload.get('toy_id') and matches[0]['id']!=payload['toy_id']:raise Failure('Recovered Toy ID differs from original request')
            bind=gh.record(payload['sha'],payload['slug'],'binding',account=account,toy_id=matches[0]['id']);gh.status(bind,'success','Association recovered after user verification')
            gh.status(rec,'success','User verified this exact request was accepted; no new request sent')
        finally:toy.close()
    else:raise Failure('Choose accepted or not-accepted only after checking Bilibili')
    summary('Unknown result reconciled; no Toy write was sent. / 已记录人工核实结果，未再次提审。')

def plan(args):
    gh=GitHub();event=jsonfile(os.environ['GITHUB_EVENT_PATH']);name=os.environ['GITHUB_EVENT_NAME'];repo=gh.call('');default=repo['default_branch'];operation='preview';build=True;release_id=''
    inputs=event.get('inputs',{})
    if name=='pull_request':operation='check';sha=os.environ['GITHUB_SHA']
    elif name=='push':
        if os.environ.get('GITHUB_REF')!='refs/heads/'+default:raise Failure('Only default-branch push may preview')
        sha=os.environ['GITHUB_SHA']
    elif name=='release' or (name=='workflow_dispatch' and inputs.get('operation') in {'submit','override'}):
        release=event.get('release') if name=='release' else gh.call('releases/tags/'+urllib.parse.quote(inputs.get('release-tag',''),safe=''))
        if not release or release.get('draft') or release.get('prerelease'):raise Failure('Select a published non-prerelease Release')
        tag=release['tag_name'];commit=gh.call('commits/'+urllib.parse.quote(tag,safe=''));sha=commit['sha'];release_id=str(release['id']);operation='submit';build=name=='workflow_dispatch' and inputs.get('operation')=='override'
    elif name=='workflow_dispatch':
        operation=inputs.get('operation','preview')
        if operation=='resolve-unknown':build=False
        if operation not in {'preview','sync-metadata','resolve-unknown'}:raise Failure('Unsupported manual operation')
        ref=inputs.get('source-ref') or default;sha=gh.call('commits/'+urllib.parse.quote(ref,safe=''))['sha']
    else:raise Failure('Unsupported event')
    if not SHA.fullmatch(sha):raise Failure('GitHub returned invalid SHA')
    if name!='pull_request':
        comparison=gh.call('compare/'+sha+'...'+urllib.parse.quote(default,safe=''))
        if comparison['status'] not in {'ahead','identical'}:raise Failure('Source must be in default-branch history before accessing Toy credentials')
    output('source-sha',sha);output('operation',operation);output('build',str(build).lower());output('release-id',release_id);output('override',str(name=='workflow_dispatch' and inputs.get('operation')=='override').lower())
    if operation=='submit' and not build:
        records=gh.pages('deployments?task=toy%3Apreview&sha='+sha)
        for rec in records:
            p=rec.get('payload',{})
            if not isinstance(p,dict) or p.get('tool')!=TOOL or p.get('schema')!=SCHEMA or p.get('sha')!=sha or gh.state(rec)!='success':continue
            run=gh.call('actions/runs/'+str(p['run_id']))
            if run.get('event') not in {'push','workflow_dispatch'} or run.get('conclusion')!='success' or run.get('head_branch')!=default or run.get('head_repository',{}).get('id')!=repo['id'] or run.get('path','').split('@')[0]!=args.workflow_path:continue
            artifacts=gh.pages('actions/runs/'+str(p['run_id'])+'/artifacts','artifacts')
            candidates=[a for a in artifacts if a.get('name')=='toy-preview-'+sha and not a.get('expired')]
            if len(candidates)==1:
                output('artifact-id',candidates[0]['id']);output('preview-run',p['run_id']);output('expected-package-sha',p['package_sha']);return
        raise Failure('No usable successful preview artifact for this Release commit. Generate a preview first, or explicitly dispatch override for this Release.')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['plan','check','preview','submit','sync-metadata','resolve-unknown'])
    parser.add_argument('--config',default='toy.config.json');parser.add_argument('--bundle',default='.toy-state/bundle');parser.add_argument('--source-sha',default='');parser.add_argument('--release-id',default='');parser.add_argument('--override',action='store_true');parser.add_argument('--metadata-only',action='store_true');parser.add_argument('--expose-preview',action='store_true');parser.add_argument('--workflow-path',default='.github/workflows/toy.yml');parser.add_argument('--deployment-id',type=int);parser.add_argument('--resolution',choices=['accepted','not-accepted']);parser.add_argument('--expected-package-sha',default='');parser.add_argument('--preview-run',default='')
    args=parser.parse_args()
    try:
        if args.mode=='plan':plan(args)
        elif args.mode=='check':package(args)
        elif args.mode=='resolve-unknown':resolve_unknown(args)
        else:
            if args.expected_package_sha or args.preview_run:
                _,m,_=load_bundle(args)
                if m.get('package_sha')!=args.expected_package_sha or str(m.get('preview_run'))!=args.preview_run:raise Failure('Downloaded bundle does not match trusted preview record')
            write_operation(args)
    except (Failure,ValueError,KeyError,FileNotFoundError,zipfile.BadZipFile) as exc:
        message=str(exc) if isinstance(exc,Failure) else 'Invalid or missing input/response data; no successful operation can be confirmed.'
        summary('Stopped / 已停止: '+message);output('status','unknown' if isinstance(exc,Unknown) else 'failed');return 1
    return 0
if __name__=='__main__':sys.exit(main())
