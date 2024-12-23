import sys
import os


project_home = '/home/servicioszmg1138/mysite'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

os.chdir(project_home)

from app import application

