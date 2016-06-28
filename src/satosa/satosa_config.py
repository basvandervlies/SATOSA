"""
This module contains methods to load, verify and build configurations for the satosa proxy.
"""
import logging
import os

import yaml

from satosa.exception import SATOSAConfigurationError

logger = logging.getLogger(__name__)


class SATOSAConfig(object):
    """
    A configuration class for the satosa proxy. Verifies that the given config holds all the
    necessary parameters.
    """
    sensitive_dict_keys = ["STATE_ENCRYPTION_KEY", "USER_ID_HASH_SALT"]
    mandatory_dict_keys = ["BASE", "BACKEND_MODULES", "FRONTEND_MODULES",
                           "INTERNAL_ATTRIBUTES", "COOKIE_STATE_NAME"] + sensitive_dict_keys

    def __init__(self, config):
        """
        Reads a given config and builds the SATOSAConfig.

        :type config: str | dict
        :rtype: satosa.satosa_config.SATOSAConfig

        :param config: Can be a file path or a dictionary
        :return: A verified SATOSAConfig
        """
        parsers = [self._load_dict, self._load_yaml]
        for parser in parsers:
            self.__dict__["_config"] = parser(config)
            if self._config is not None:
                break

        # Load sensitive config from environment variables
        for key in SATOSAConfig.sensitive_dict_keys:
            val = os.environ.get("SATOSA_{key}".format(key=key))
            if val:
                self._config[key] = val

        self._verify_dict(self._config)

        for parser in parsers:
            _internal_attributes = parser(self._config["INTERNAL_ATTRIBUTES"])
            if _internal_attributes is not None:
                self._config["INTERNAL_ATTRIBUTES"] = _internal_attributes
                break
        if not self._config["INTERNAL_ATTRIBUTES"]:
            raise SATOSAConfigurationError("Coudl not load attribute mapping from 'INTERNAL_ATTRIBUTES.")

    def _verify_dict(self, conf):
        """
        Check that the configuration contains all necessary keys.

        :type conf: dict
        :rtype: None
        :raise ValueError: if the configuration is incorrect

        :param conf: config to verify
        :return: None
        """
        if not conf:
            raise ValueError("Missing configuration or unknown format")

        for key in SATOSAConfig.mandatory_dict_keys:
            if key not in conf:
                raise ValueError("Missing key '%s' in config" % key)

    def __getattr__(self, item):
        """
        Returns data bound to the key 'item'.

        :type item: str
        :rtype object

        :param item: key to data
        :return: data bound to key 'item'
        """
        if self._config and item in self._config:
            return self._config[item]
        raise AttributeError("'module' object has no attribute '%s'" % item)

    def __setattr__(self, key, value):
        """
        Inserts value into internal dict

        :type key: str
        :type value: object

        :param key: key
        :param value: data
        :return: None
        """
        if key != "_config":
            if self._config is not None:
                self._config[key] = value

    def __iter__(self):
        return iter(self._config)

    def _load_dict(self, config):
        """
        Load config from dict

        :type config: dict
        :rtype: dict

        :param config: config to load
        :return: Loaded config
        """
        if isinstance(config, dict):
            return config

        return None

    def _load_yaml(self, config_file):
        """
        Load config from yaml file or string

        :type config_file: str
        :rtype: dict

        :param config_file: config to load. Can be file path or yaml string
        :return: Loaded config
        """
        try:
            with open(config_file) as f:
                return yaml.safe_load(f.read())
        except yaml.YAMLError as error:
            logger.debug("Could not parse config as YAML: {}", str(error))

        return None
