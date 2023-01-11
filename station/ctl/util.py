import os

from jinja2 import Environment, FileSystemLoader, PackageLoader


def get_template_env():
    env_template_dir = os.getenv("PHT_TEMPLATE_DIR")
    if env_template_dir:
        loader = FileSystemLoader(env_template_dir)
    else:
        loader = PackageLoader('station.ctl', 'templates')
    return Environment(loader=loader)
