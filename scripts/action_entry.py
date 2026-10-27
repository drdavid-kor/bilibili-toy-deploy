#!/usr/bin/env python3
"""Read Action inputs as data, never interpolate them into a shell."""
import os,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def value(name,default=''):return os.environ.get('INPUT_'+name.upper().replace('-','_'),default)
mode=value('mode','check')
args=[sys.executable,str(root/'scripts/toy_action.py'),mode]
for name in ('config','bundle','source-sha','release-id','workflow-path','deployment-id','resolution','expected-package-sha','preview-run'):
    v=value(name)
    if v:args.extend(['--'+name,v])
for name in ('override','metadata-only','expose-preview'):
    v=value(name,'false')
    if v not in ('true','false',''):raise SystemExit('Boolean input must be true or false: '+name)
    if v=='true':args.append('--'+name)
if mode in ('preview','submit','sync-metadata','resolve-unknown'):
    sys.path.insert(0,str(root/'scripts'))
    from install_cli import download_verified
    dest=Path(os.environ.get('RUNNER_TEMP','/tmp'))/'bilibili-toy-cli'/'toy'
    try:download_verified(value('toy-version','v0.6.4'),dest)
    except Exception:raise SystemExit('Could not install and verify official Toy CLI')
    os.environ['TOY_BINARY']=str(dest)
raise SystemExit(subprocess.run(args).returncode)
