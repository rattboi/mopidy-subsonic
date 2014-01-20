from __future__ import unicode_literals

import os

from mopidy import ext, config

__version__ = '0.3'


class SubsonicExtension(ext.Extension):

    dist_name = 'Mopidy-Subsonic'
    ext_name = 'subsonic'
    version = __version__

    def get_default_config(self):
        conf_file = os.path.join(os.path.dirname(__file__), 'ext.conf')
        return config.read(conf_file)

    def get_config_schema(self):
        schema = super(SubsonicExtension, self).get_config_schema()
        schema['hostname'] = config.Hostname()
        schema['port'] = config.Port()
        schema['username'] = config.String()
        schema['password'] = config.Secret()
        schema['ssl'] = config.Boolean()
        return schema

    def setup(self, registry):
        from .actor import SubsonicBackend
        registry.add('backend', SubsonicBackend)
