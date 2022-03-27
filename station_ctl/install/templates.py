from jinja2 import Environment, PackageLoader



def render_init_sql(db_user: str, env: Environment = None):
    if not env:
        env = _get_template_env()
    template = env.get_template('init.sql.tmpl')
    return template.render(db_user=db_user)


def _get_template_env():
    return Environment(loader=PackageLoader('station_ctl', 'templates'))
