# ratios: loc_comments=62:16 imports_exports=6:3 calls_definitions=31:4
# === CHECKS ===
# id: scoped_package_extraction_check
#   proves: uchc_package_extraction_complete, uchc_package_extraction_no_authority_transfer
#   call: self::test_scoped_override_preserves_the_package_baseline
#   requires: pytest, git
#   timeout: 60
#   mutates: filesystem
#   cleanup: tmp_path
# id: scoped_package_extraction_rejection_check
#   proves: uchc_package_extraction_complete
#   call: self::test_override_cannot_hide_wrong_source_or_target_bytes
#   requires: pytest, git
#   timeout: 60
#   mutates: filesystem
#   cleanup: tmp_path
# === END CHECKS ===
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess

import pytest

VERIFY = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'tools/verify_package_extraction.py'))['verify']


@pytest.fixture
def package(tmp_path):
    forge, root = tmp_path/'forge', tmp_path/'package'
    forge.mkdir()
    def git(*args):
        return subprocess.check_output(['git','-C',str(forge),'-c','user.name=Fixture',
                                        '-c','user.email=fixture@example.invalid','-c','commit.gpgsign=false',
                                        *args],stderr=subprocess.DEVNULL,text=True).strip()
    git('init','-q')
    directory=forge/'research/english-gonol/english_gonol'
    directory.mkdir(parents=True)
    (directory/'changed.py').write_text('value = 1\n')
    (directory/'unchanged.py').write_text('value = 3\n')
    git('add','.')
    git('commit','-qm','baseline')
    base=git('rev-parse','HEAD')
    (directory/'changed.py').write_text('value = 2\n')
    git('add','.')
    git('commit','-qm','scoped increment')
    increment=git('rev-parse','HEAD')
    files=[]
    for name in ('changed.py','unchanged.py'):
        target=root/'human/english/english_gonol'/name
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes((directory/name).read_bytes())
        digest=sha256(target.read_bytes()).hexdigest()
        item={'source':str((directory/name).relative_to(forge)),
              'target':str(target.relative_to(root)), 'kind':'runtime',
              'source_sha256':digest,'target_sha256':digest,'adaptation':None}
        if name=='changed.py':item['source_commit']=increment
        files.append(item)
    record={'schema':'uchc.package-extraction','version':'1.1.0','source_commit':base,
            'authority_transfer':False,'files':files,'forge_only':[]}
    (root/'docs').mkdir()
    manifest=root/'docs/package-extraction.json'
    manifest.write_text(json.dumps(record))
    return forge,root,manifest,record,increment


def test_scoped_override_preserves_the_package_baseline(package):
    forge,root,_,record,increment=package
    result=VERIFY(forge,root)
    assert result['source_commit']==record['source_commit']
    assert result['runtime_files']==result['files']==2
    assert result['source_commit_overrides']=={'human/english/english_gonol/changed.py':increment}
    assert result['standing']=='exact extraction; graduation gates remain separate'


def test_override_cannot_hide_wrong_source_or_target_bytes(package):
    forge,root,manifest,record,increment=package
    record['files'][0].pop('source_commit')
    manifest.write_text(json.dumps(record))
    with pytest.raises(ValueError,match='producer digest mismatch'):
        VERIFY(forge,root)
    record['files'][0]['source_commit']=increment
    manifest.write_text(json.dumps(record))
    (root/record['files'][0]['target']).write_text('forged = True\n')
    with pytest.raises(ValueError,match='extracted digest mismatch'):
        VERIFY(forge,root)
# ratios: loc_comments=62:16 imports_exports=6:3 calls_definitions=31:4
