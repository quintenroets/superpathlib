from package_utils.context import Context

from superpathlib.models import Config, Options, Secrets

context = Context(Options, Config, Secrets)
