"""
Helper functions of UP9
"""
import _thread
import codecs
import copy
import io
import json
import logging
import os
import random
import re
import sys
import threading
import time
import unittest
import uuid
from contextlib import contextmanager
from http.cookiejar import parse_ns_headers, Cookie  # noqa
from urllib import parse as urllib_parse
from urllib.parse import urlencode, unquote

import ddt
import requests
from jsonpath_ng.ext import parse as jsonpath_parse
from lxml import html
from requests.cookies import merge_cookies, cookiejar_from_dict
from requests.structures import CaseInsensitiveDict

import apiritif
from apiritif import http
from apiritif.http import HTTPTarget

# the below block is just to avoid "unused import" in IDE
assert unittest
assert io
assert time
assert http
assert urlencode
assert uuid
assert unquote

TAKE_RANDOM = os.environ.get("UP9_RANDOMIZE_EXTRACTS", False)


class Context(object):
    def __init__(self) -> None:
        super().__init__()
        self.session = requests.Session()
        self.targets = {}
        self.global_headers = {}

    def clear(self):
        self.session = requests.Session()
        self.targets.clear()
        self.global_headers.clear()


_context = Context()


def get_data_from_header(spec, resp):
    header_dict = CaseInsensitiveDict(resp.headers)
    return header_dict.get(spec, "")


def get_data_from_global_header(spec):
    return _context.global_headers.get(spec)


def get_data_from_cookie(spec):
    c_dict = _context.session.cookies.get_dict()
    if spec not in c_dict:
        raise KeyError("Failed to find cookie %r" % spec)
    return c_dict[spec]


def get_first_row_from_dataset(file_name):
    with open(os.path.join("data", file_name)) as dtst_file:
        dataset = json.load(dtst_file)
    row = dataset['rows'][0]
    return tuple(row[x['name']] for x in dataset['parameters'])


def apply_into_json(data, jpath, val):
    jsonpath_expr = jsonpath_parse(jpath)
    jsonpath_expr.update(data, val)


def jsonpath(path, resp):
    if isinstance(resp, str):
        data = json.loads(resp)
    else:
        data = resp.json()

    expr = jsonpath_parse(path)
    vals = [x.value for x in expr.find(data)]
    if vals:
        return random.choice(vals) if TAKE_RANDOM else vals[0]
    else:
        raise KeyError("jsonpath: No values found for %r" % path)


def from_regex(regexp, text):
    pat = re.compile(regexp)
    vals = pat.findall(text)
    if vals:
        return random.choice(vals) if TAKE_RANDOM else vals[0]
    else:
        raise KeyError("regexp: No values found for %r" % regexp)


def cssselect(sel, resp):
    if isinstance(resp, str):
        data = resp
    else:
        data = resp.text

    parts = sel.split(' ')
    if parts[-1].startswith('@'):
        attr = parts[-1][1:]
        parts.pop()
        sel = ' '.join(parts)
    else:
        attr = None

    tree = html.fromstring(data)
    q = tree.cssselect(sel)
    vals = [x.text if attr is None else x.attrib[attr] for x in q]
    if vals:
        return random.choice(vals) if TAKE_RANDOM else vals[0]
    else:
        raise KeyError("cssselect: No values found for %r" % sel)


def url_part(ospec, url):
    logging.debug("Extracting %r from %r", ospec, url)
    flag = ospec[0]
    spec = ospec[1:]

    parse_link = urllib_parse.urlparse(url)
    if flag == '/':
        ind = int(spec)
        path_parts = parse_link.path.split('/')
        return path_parts[ind]
    elif flag == '#':
        get_part = urllib_parse.parse_qs(parse_link.fragment)
    else:
        get_part = urllib_parse.parse_qs(parse_link.query)

    if spec not in get_part:
        raise KeyError("Failed to find element %r inside URL: %s" % (spec, url))
    vals = get_part[spec]
    return random.choice(vals) if TAKE_RANDOM else vals[0]


def clear_session(metadata):
    def decorator(orig_fn):
        def wrapper(*args, **kwargs):
            _do_clear_session(metadata)

            return orig_fn(*args, **kwargs)

        return wrapper

    return decorator


def _do_clear_session(metadata):
    with apiritif.transaction("clear_session: " + json.dumps(metadata)):
        _context.clear()


def dummy_auth(tgt_key, target):
    # a callback to use when auth is suppressed
    # signature should match to authenticate()
    pass


def get_http_target(key, auth_callback=dummy_auth):
    if key in _context.targets:
        return _context.targets[key]

    target = TargetService(key)
    target.additional_headers({"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_1) AppleWebKit/537.36 "
                                             "(KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"})
    target.additional_headers({"Referer": target.address + "/"})
    target.additional_headers({"Accept": "*/*"})
    _context.targets[key] = target

    with apiritif.transaction("authentication"):
        auth_callback(key, target)

    _context.global_headers.update(target.get_additional_headers())
    return target


class TargetService(HTTPTarget):
    def __init__(self, target_key, base_path=None, use_cookies=True, additional_headers=None, keep_alive=True,
                 auto_assert_ok=False, timeout=60, allow_redirects=False):
        self.target_key = target_key
        self.access_key = None
        address = os.getenv(target_key, None)
        if address is None:
            with open(os.path.join("data", "target_services.json")) as fp:
                services = json.load(fp)
                if target_key not in services:
                    raise KeyError("Service %r is not found in target URL mapping" % target_key)
                address = services[target_key]

        timeout = float(os.getenv("UP9_HTTP_TIMEOUT", str(timeout)))
        super().__init__(address, base_path, use_cookies, additional_headers, keep_alive, auto_assert_ok, timeout,
                         allow_redirects, _context.session)

        self.additional_headers({"x-abuse-info": "UP9.com generated tests"})

    def request(self, method, path,
                params=None, headers=None, cookies=None, data=None, json=None, files=None,
                allow_redirects=None, timeout=None):

        headers = self._headers_from_token_map(headers, method, path)

        overall_to = timeout if timeout is not None else self._timeout
        with timeout_scope(overall_to * 1.1 if overall_to is not None else None):  # prevent hang on slow or large dwnl
            resp = super().request(method, path, params, headers, cookies, data, json, files, allow_redirects, timeout)

        if resp.headers.get('content-type', '').startswith('text/html'):
            self.additional_headers({"Referer": resp.url})
        return resp

    def _headers_from_token_map(self, headers, method, path):
        token_map = json.loads(os.getenv("UP9_AUTH_HEADERS_CONFIG", "[]"))
        for item in token_map:
            same_method = item['method'].lower() == method.lower()
            same_target = item['target'] == self.target_key
            patt = re.sub(r'{[^}]+}', '[^/]+', item['path'])
            same_path = re.match(patt, path)
            if same_target and same_method and same_path:
                hdrs = copy.copy(item['headers'])
                hdrs.update(headers if headers else {})
                headers = hdrs
        return headers

    def get_additional_headers(self):
        return self._additional_headers


_JSON_METADATA_ATTR = "%json_metadata_file_path"


def data_driven_tests(cls):
    ddt.ddt(cls)
    for name, func in list(cls.__dict__.items()):
        if hasattr(func, _JSON_METADATA_ATTR):
            file_attr = getattr(func, _JSON_METADATA_ATTR)

            with codecs.open(file_attr, 'r', 'utf-8') as f:
                data = json.load(f)

            _add_tests_from_data(cls, name, func, data)
            delattr(cls, name)  # removes original test method
    return cls


def json_dataset(value):
    def wrapper(func):
        setattr(func, _JSON_METADATA_ATTR, value)
        return func

    return wrapper


def _add_tests_from_data(cls, name, func, data):
    for i, row in enumerate(data['rows']):
        value = tuple(row[x['name']] for x in data['parameters'])
        test_name = ddt.mk_test_name(name, value, i)
        ddt.add_test(cls, test_name, test_name, func, value)
        if i >= int(os.getenv('UP9_LIMIT_DATASET', sys.maxsize)):
            logging.info("Interrupting dataset because of limit")
            break


def merge_cookies_into_session(cookies_input):
    jar = _context.session.cookies
    if isinstance(cookies_input, list):
        for item in cookies_input:
            cookie = Cookie(
                0, item['name'], item['value'], None, False, item['domain'], True,
                bool(item['domain'].startswith(".")), item['path'], True, item['secure'], None, False, "",
                "", [],
            )
            jar.set_cookie(cookie)
    else:
        attrs_set = parse_ns_headers(cookies_input.split('; '))
        merge_cookies(jar, cookiejar_from_dict({x[0][0]: x[0][1] for x in attrs_set}))


class _Timeout(threading.Thread):
    def __init__(self, timeout):
        super().__init__(daemon=True)
        self.timeout = timeout
        self.canceled = False
        self.msg = None
        logging.debug("%s Created timeout", id(self))

    def run(self) -> None:
        if self.timeout is None:
            return

        start = time.time()
        passed = 0
        while not self.canceled and passed < self.timeout:
            passed = time.time() - start
            remaining = self.timeout - passed
            if remaining > 1:
                logging.debug("%s Sleeping 1s", id(self))
                time.sleep(1)
            elif remaining > 0:
                logging.debug("%s Sleeping rest of %s", id(self), remaining)
                time.sleep(remaining)
            else:
                logging.debug("%s Timeout exhausted: %s", id(self), self.timeout)

        if not self.canceled:
            self.msg = "Timeout of %.3fs has expired" % self.timeout
            _thread.interrupt_main()
        else:
            logging.debug("%s Canceled timeout", id(self))


@contextmanager
def timeout_scope(to):
    def wrapper():
        watcher = _Timeout(to)
        watcher.start()
        try:
            yield
        except KeyboardInterrupt:
            if watcher.msg:
                raise TimeoutError(watcher.msg)
            else:
                raise
        finally:
            watcher.canceled = True

    yield from wrapper()
