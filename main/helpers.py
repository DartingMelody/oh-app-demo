import ohapi
from django.conf import settings
from openhumans.models import OpenHumansMember
import logging

logger = logging.getLogger(__name__)
OH_OAUTH2_REDIRECT_URI = '{}/complete'.format(settings.OPENHUMANS_APP_BASE_URL)
OH_BASE_URL = settings.OPENHUMANS_OH_BASE_URL


def get_create_member(data):
    '''
    use the data returned by `ohapi.api.oauth2_token_exchange`
    and return an oh_member object
    '''
    oh_id = ohapi.api.exchange_oauth2_member(
        access_token=data['access_token'])['project_member_id']
    try:
        oh_member = OpenHumansMember.objects.get(oh_id=oh_id)
        logger.debug('Member {} re-authorized.'.format(oh_id))
        oh_member.access_token = data['access_token']
        oh_member.refresh_token = data['refresh_token']
        oh_member.token_expires = OpenHumansMember.get_expiration(
            data['expires_in'])
    except OpenHumansMember.DoesNotExist:
        oh_member = OpenHumansMember.create(
            oh_id=oh_id,
            data=data)
        logger.debug('Member {} created.'.format(oh_id))
    oh_member.save()
    return oh_member


def oh_client_info():
    client_info = {
        'client_id': settings.OPENHUMANS_CLIENT_ID,
        'client_secret': settings.OPENHUMANS_CLIENT_SECRET,
    }
    return client_info


def oh_code_to_member(code):
    """
    Exchange code for token, use this to create and return OpenHumansMember.
    If a matching OpenHumansMember already exists in db, update and return it.
    """
    if not (settings.OPENHUMANS_CLIENT_SECRET and
            settings.OPENHUMANS_CLIENT_ID and code):
        logger.error('OPENHUMANS_CLIENT_SECRET or ID or code are unavailable')
        return None
    params = {
        'client_id': settings.OPENHUMANS_CLIENT_ID,
        'client_secret': settings.OPENHUMANS_CLIENT_SECRET,
        'code': code,
        'base_url': OH_BASE_URL,
    }
    if settings.OPENHUMANS_REDIRECT_URI:
        params['redirect_uri'] = settings.OPENHUMANS_REDIRECT_URI
    data = ohapi.api.oauth2_token_exchange(**params)
    if 'error' in data:
        logger.debug('Error in token exchange: {}'.format(data))
        return None

    if 'access_token' in data:
        return get_create_member(data)
    else:
        logger.warning('Neither token nor error info in OH response!')
        return None
