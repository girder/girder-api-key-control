import cherrypy
import jsonschema
from girder import events, plugin
from girder.exceptions import RestException, ValidationException
from girder.models.setting import Setting
from girder.utility.setting_utilities import validator
from netaddr import AddrFormatError, IPAddress, IPNetwork

PLUGIN_SETTING_WHITELIST = 'api_key_control.whitelist'
_whitelistSchema = {
    'type': 'array',
    'items': {
        'type': 'string'
    }
}


@validator(PLUGIN_SETTING_WHITELIST)
def _validateWhitelist(doc):
    try:
        jsonschema.validate(doc['value'], _whitelistSchema)
    except jsonschema.ValidationError:
        raise ValidationException(
            'Invalid whitelist: must be JSON Array of CIDR strings.')

    try:
        for cidr in doc['value']:
            IPNetwork(cidr)
    except AddrFormatError:
        raise ValidationException('Invalid network notation: ' + cidr)



def _validateIp(event):
    whitelist = Setting().get(PLUGIN_SETTING_WHITELIST, [])
    ip = IPAddress(cherrypy.request.remote.ip)

    if not any(ip in IPNetwork(cidr) for cidr in whitelist):
        raise RestException('API key use disabled on this network.')


class GirderPlugin(plugin.GirderPlugin):
    DISPLAY_NAME = 'API key control'

    def load(self, info):
        events.bind('rest.post.api_key/token.before', _validateIp)
