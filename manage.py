#!/usr/bin/env python
import os
import sys

#import pydevd
#pydevd.patch_django_autoreload(
#    patch_remote_debugger=True, #Note that the remote debugger patch setting should be False on a regular run
#    patch_show_console=True
#)

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dayz_icrc.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
