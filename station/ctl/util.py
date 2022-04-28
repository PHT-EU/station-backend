from jinja2 import Environment, PackageLoader


def get_template_env():
    return Environment(loader=PackageLoader('station.ctl', 'templates'))
