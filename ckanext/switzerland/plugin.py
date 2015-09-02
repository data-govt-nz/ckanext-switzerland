import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import pylons
import json
import pprint
import logging
log = logging.getLogger(__name__)

from ckanext.switzerland import validators


LANGUAGE_PRIORITIES = ['de', 'en', 'fr', 'it'] 

class OgdchPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IValidators)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'switzerland')
    
    # IValidators

    def get_validators(self):
        return {
            'multiple_text': validators.multiple_text,
            'multiple_text_output': validators.multiple_text_output,
            'list_of_dicts': validators.list_of_dicts,
            }


class OgdchPackagePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IPackageController, inherit=True)

    # IPackageController

    def before_view(self, pkg_dict):
        desired_lang_code = pylons.request.environ['CKAN_LANG']
        for key, value in pkg_dict.iteritems():
            if isinstance(value, dict):
                pkg_dict[key] = self.get_language_value(value, desired_lang_code, default_value=value)
        for resource in pkg_dict['resources']:
            if not resource['name'] and resource['title']:
                resource['name'] = resource['title']
            for key, value in resource.iteritems():
                if isinstance(value, dict):
                    resource[key] = self.get_language_value(value, desired_lang_code, default_value=value)
        return pkg_dict

    def get_language_value(self, lang_dict, desired_lang_code, default_value=''):
        try:
            if lang_dict[desired_lang_code]:
                return lang_dict[desired_lang_code]
        except KeyError:
            pass

        lang_idx = LANGUAGE_PRIORITIES.index(desired_lang_code)
        for i in range(0,len(LANGUAGE_PRIORITIES)):
            try:
                # choose next language according to priority
                lang_code = LANGUAGE_PRIORITIES[lang_idx-i]
                if str(lang_dict[lang_code]):
                    return lang_dict[lang_code]
            except (KeyError, IndexError, ValueError):
                continue
        return default_value

    def before_index(self, pkg_dict):
        extract_title = LangToString('title')
        validated_dict = json.loads(pkg_dict['validated_data_dict'])
        
        log.debug(pprint.pformat(validated_dict['title']))

        pkg_dict['res_name'] = map(extract_title, validated_dict[u'resources'])
        pkg_dict['title_string'] = extract_title(validated_dict)
        pkg_dict['notes'] = LangToString('notes')(validated_dict)

        pkg_dict['title_de'] = validated_dict['title']['de']
        pkg_dict['title_fr'] = validated_dict['title']['fr']
        pkg_dict['title_it'] = validated_dict['title']['it']
        pkg_dict['title_en'] = validated_dict['title']['en']
        log.debug(pprint.pformat(pkg_dict))
        return pkg_dict
   
    def before_search(self, search_params):
        log.debug(pprint.pformat(search_params))
        return search_params


class LangToString(object):
    def __init__(self, attribute):
        self.attribute = attribute

    def __call__(self, data_dict):
        lang = data_dict[self.attribute]
        return (
            '%s - %s - %s - %s'
            % (lang['de'], lang['fr'], lang['it'], lang['en'])
        )
