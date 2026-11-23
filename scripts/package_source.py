"""Create a reproducible source-only ZIP; never include the runtime database or keys."""
from pathlib import Path
import zipfile
import check_release

def main():
 if check_release.main():raise SystemExit(1)
 root=check_release.ROOT
 destination=root.parent/'placement-portal-source.zip'
 with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED) as archive:
  for path in sorted(check_release.files()):
   relative=Path(root.name)/path.relative_to(root)
   info=zipfile.ZipInfo(relative.as_posix(),date_time=(2026,11,22,0,0,0))
   info.compress_type=zipfile.ZIP_DEFLATED
   archive.writestr(info,path.read_bytes())
 print('Source archive:',destination)

if __name__=='__main__':main()
