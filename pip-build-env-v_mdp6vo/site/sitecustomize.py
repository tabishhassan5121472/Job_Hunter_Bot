
import os, site, sys

# First, drop system-sites related paths.
original_sys_path = sys.path[:]
known_paths = set()
for path in {'/Users/Tabish/Documents/Personal Data/Make Something that will find a job for me, or collaboration team to work with them and earn money. /jobhunter/venv/lib/python3.14/site-packages'}:
    site.addsitedir(path, known_paths=known_paths)
system_paths = set(
    os.path.normcase(path)
    for path in sys.path[len(original_sys_path):]
)
original_sys_path = [
    path for path in original_sys_path
    if os.path.normcase(path) not in system_paths
]
sys.path = original_sys_path

# Second, add lib directories.
# ensuring .pth file are processed.
for path in ['/Users/Tabish/Documents/Personal Data/Make Something that will find a job for me, or collaboration team to work with them and earn money. /pip-build-env-v_mdp6vo/overlay/lib/python3.14/site-packages', '/Users/Tabish/Documents/Personal Data/Make Something that will find a job for me, or collaboration team to work with them and earn money. /pip-build-env-v_mdp6vo/normal/lib/python3.14/site-packages']:
    assert not path in sys.path
    site.addsitedir(path)
