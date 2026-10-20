#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Create the GitHub-ready CHIPIX ZIP and verify every archived file hash."""
import argparse
import hashlib
import json
from pathlib import Path
import stat
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main(output):
    manifest=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
    version=manifest['version']
    wheel=ROOT/manifest['wheel']
    if not wheel.is_file():
        raise SystemExit('Build the ChimeraX wheel before packaging the ZIP.')
    with zipfile.ZipFile(wheel) as archive:
        metadata=archive.read(next(p for p in archive.namelist() if p.endswith('/METADATA'))).decode()
        if f'Name: {manifest["bundle"]}\n' not in metadata or f'Version: {version}\n' not in metadata:
            raise SystemExit('Wheel identity does not match manifest.json')
    (ROOT/'dist/SHA256SUMS').write_text(digest(wheel.read_bytes())+'  '+wheel.name+'\n',encoding='utf-8')
    rules=manifest['release']
    files=[]
    for path in sorted(ROOT.rglob('*')):
        if not path.is_file():
            continue
        relative=path.relative_to(ROOT)
        if any(part in rules['exclude_parts'] or part.endswith('.egg-info') for part in relative.parts):
            continue
        if path.suffix in rules['exclude_suffixes'] or path.name in rules['exclude_names']:
            continue
        if len(relative.parts)>1 and relative.parts[0] not in rules['include_roots']:
            continue
        files.append((relative,path))
    output=Path(output).resolve()
    output.mkdir(parents=True,exist_ok=True)
    target=output/f'CHIPIX-{version}.zip'
    prefix=f'CHIPIX-{version}/'
    checksums=[]
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for relative,path in files:
            data=path.read_bytes()
            name=relative.as_posix()
            checksums.append(f'{digest(data)}  {name}')
            entry=zipfile.ZipInfo(prefix+name,date_time=(2026,1,1,0,0,0))
            entry.create_system=3
            mode=0o755 if path.stat().st_mode & stat.S_IXUSR else 0o644
            entry.external_attr=(stat.S_IFREG|mode)<<16
            entry.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(entry,data)
        archive.writestr(prefix+rules['checksum_file'],'\n'.join(checksums)+'\n')
    with zipfile.ZipFile(target) as archive:
        if archive.testzip() is not None:
            raise SystemExit('ZIP integrity check failed')
        for line in archive.read(prefix+rules['checksum_file']).decode().splitlines():
            expected,name=line.split('  ',1)
            if digest(archive.read(prefix+name))!=expected:
                raise SystemExit(f'ZIP checksum mismatch: {name}')
    result={'name':manifest['release_name'],'zip':str(target),'bytes':target.stat().st_size,
            'sha256':digest(target.read_bytes()),'files':len(files)+1}
    (output/'SHA256SUMS').write_text(result['sha256']+'  '+target.name+'\n',encoding='utf-8')
    (output/'CHIPIX-1.0.0-release.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',default=str(ROOT.parent/'releases'))
    main(parser.parse_args().output)
