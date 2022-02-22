import os
import sys

import requests
from requests import HTTPError

from flamingo.tools import run, _err, _warn


class FlamingoAPI:
    _API_URL = None

    @classmethod
    def api(cls):
        if not cls._API_URL:
            if 'FLAMINGO_URL' not in os.environ:
                sys.exit(f"Environment variable 'FLAMINGO_URL' must be set with the Flamingo server endpoint")
            cls._API_URL = os.environ['FLAMINGO_URL']
        return cls._API_URL

    @classmethod
    def list_apps(cls):
        return cls._list(endpoint='/apps')

    @classmethod
    def get_app(cls, name, environment):
        apps = list(cls._list(endpoint='/apps', name=name, environment_name=environment))
        return apps

    @classmethod
    def update_app(cls, app_id, data):
        return cls._patch(endpoint=f'/apps/{app_id}', data=data)

    @classmethod
    def list_envs(cls, app_id):
        return cls._detail(endpoint=f'/apps/{app_id}/vars')['results']

    @classmethod
    def set_envs(cls, app_id, key_values):
        return cls._post(endpoint=f'/apps/{app_id}/vars', data=key_values)

    @classmethod
    def unset_envs(cls, app_id, keys):
        return cls._delete(endpoint=f'/apps/{app_id}/vars', data=keys)

    @classmethod
    def apply_app(cls, app_id):
        return cls._post(endpoint=f'/apps/{app_id}/apply')

    @classmethod
    def info(cls):
        out, _ = run('gcloud', 'auth', 'list')

        email = None
        for row in out.splitlines():
            if row.startswith('*'):
                email = row.split(' ')[-1].strip()
                break

        return {
            'email': email,
            'endpoint': cls.api(),
        }

    @classmethod
    def list_buildpacks(cls):
        return cls._list(endpoint='/build-packs')

    @classmethod
    def get_buildpack(cls, name):
        buildpacks = list(cls._list(endpoint='/build-packs', name=name))
        return buildpacks

    @classmethod
    def _headers(cls, url):
        stream = os.popen('gcloud auth print-identity-token')
        output = stream.read().strip()
        return {'Authorization': f"Bearer {output}"}

    @classmethod
    def _detail(cls, endpoint, **kwargs):
        url = f"{cls.api()}{endpoint}"
        response = requests.get(url=url, params=kwargs, headers=cls._headers(url=url))
        response.raise_for_status()
        return response.json()

    @classmethod
    def _list(cls, endpoint, **kwargs):
        page = 1
        while True:
            try:
                results = cls._detail(endpoint=endpoint, page=page, **kwargs)['results']
                yield from results
                page += 1
            except HTTPError as e:
                if e.response.status_code == 404:
                    break
                raise

    @classmethod
    def _post(cls, endpoint, data=None):
        url = f"{cls.api()}{endpoint}"
        response = requests.post(url=url, json=data, headers=cls._headers(url=url))
        response.raise_for_status()
        return response.json()

    @classmethod
    def _patch(cls, endpoint, data):
        url = f"{cls.api()}{endpoint}"
        response = requests.patch(url=url, json=data, headers=cls._headers(url=url))
        response.raise_for_status()
        return response.json()

    @classmethod
    def _delete(cls, endpoint, data=None):
        url = f"{cls.api()}{endpoint}"
        response = requests.delete(url=url, json=data, headers=cls._headers(url=url))
        response.raise_for_status()
        return response.json()


def _parse_app_name(application):
    try:
        name, environment = application.rsplit('-', 1)
    except ValueError:
        _err(f"Application name must be in the format <name>-<env>, not {application}")
        return None

    apps = FlamingoAPI.get_app(name=name, environment=environment)

    if len(apps) > 1:
        _err("Duplicated apps found!!")
        return None

    if len(apps) == 0:
        _warn(f"No app named {name} in the environment {environment}")
        return None

    return apps[0]


def _parse_buildpack_name(name):
    buildpacks = FlamingoAPI.get_buildpack(name=name)

    if len(buildpacks) > 1:
        _err("Duplicated build packs found!!")
        return None

    if len(buildpacks) == 0:
        _warn(f"No buildpack named {name} found.")
        return None

    return buildpacks[0]
