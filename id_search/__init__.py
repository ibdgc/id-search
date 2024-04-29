import importlib
import pkgutil
import confuse
import os
from pathlib import Path

config = confuse.Configuration('IBDGCDatabase', __name__)
# Allow config.yaml at project root with highest priority
if os.path.isfile('config.yaml'):
    config.set_file('config.yaml')

loaders = sorted((importlib.import_module(name)
                  for finder, name, ispkg
                  in pkgutil.iter_modules([Path(__file__).parent / 'loaders'],
                                          prefix='ibdgc_db.loaders.')),
                 key=lambda x: getattr(x, 'PRIORITY', float('inf')))
