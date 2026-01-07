import platform
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from architects.helpers.managed_mem import ManagedMem
mem_man = ManagedMem()

platform_name = platform.system()
platform_name = mem_man.settr('platform_name', platform_name)
print(mem_man.gettr('platform_name'))
