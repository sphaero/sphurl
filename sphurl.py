#!/usr/bin/python
# Sphurl
# Copyright (C) 2016  Arnaud Loonstra
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import json
from webob import Request, Response, exc

ROOT_DOMAIN="z25.org"
HTACCESS=".htaccess"

# The double {{ is specifically for str.format to not pick them up!
HTACCESS_HEAD = """### THIS FILE IS GENERATED!!! DON'T EDIT ###
Options +FollowSymLinks
RewriteEngine On
RewriteCond %{{HTTP_HOST}} {0}$ [NC]
""".format(ROOT_DOMAIN)
HTACCESS_FOOT = """RewriteRule ^$ http://www.{0}$1 [R=301,L]
""".format(ROOT_DOMAIN)


def read_file_lines(file):
    with open(file) as f:
        return f.readlines()

def rewrite_rules_to_dict(rules):
    d = {}
    for entry in rules:
        if entry.startswith("RewriteRule") and \
                not (entry.startswith("RewriteRule ^$")):
            short = entry.split('^')[1].split('$')[0]
            long = entry.split(' ')[2]
            d[short] = long
    return d

def read_htaccess():
	file_list = read_file_lines(HTACCESS)
	return rewrite_rules_to_dict(file_list)

def write_htaccess(rules):
	with open(HTACCESS, 'w') as f:
		f.write(HTACCESS_HEAD)
		for key, val in rules.items():
			f.write("RewriteRule ^{0}$ {1} [R=301,L]\n".format(key, val))
		f.write(HTACCESS_FOOT)


class AppieRestObject(object):
    """
    template class for a simple REST object for Appie

    Inherit this class and override the methods you need
    """
    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, environ, start_response):
        req = Request(environ)
        method = req.method
        try:
            handle_method = getattr(self, 'handle_'+method)
        except:
            raise exc.HTTPInternalServerError('No %s method on resource: %s' %(method,object))
        resp = handle_method(req)
        return resp(environ, start_response)

    def handle_GET(self, req, *args, **kwargs):
        return exc.HTTPMethodNotAllowed()

    def handle_POST(self, req, *args, **kwargs):
        return exc.HTTPMethodNotAllowed()

    def handle_PUT(self, req, *args, **kwargs):
        return exc.HTTPMethodNotAllowed()

    def handle_DELETE(self, req, *args, **kwargs):
        return exc.HTTPMethodNotAllowed()

class Z25Url(AppieRestObject):
	
	def handle_GET(self, req, *args, **kwargs):
		if req.content_type == "application/json":			
			rules = read_htaccess()
			return Response(json.dumps(rules), content_type="application/json")
		else:
			with open('index.html') as f:
				d = f.read()
				return Response(d)

	def handle_PUT(self, req, *args, **kwargs):
		cur_rules = read_htaccess()
		new_data = json.loads(req.body)
		if new_data.keys()[0] in cur_rules.keys():
			cur_rules[new_data.keys()[0]] = new_data[new_data.keys()[0]]
			write_htaccess(cur_rules)
			return Response("null")
		return exc.HTTPMethodNotAllowed()

	def handle_POST(self, req, *args, **kwargs):
		cur_rules = read_htaccess()
		new_url = req.body
		new_id = int(max(cur_rules.keys()))
		new_id += 1
		new_id = str(new_id).zfill(3)
		cur_rules[new_id] = new_url
		write_htaccess(cur_rules)
		return Response(json.dumps(new_id))
		
	def handle_DELETE(self, req, *args, **kwargs):
		cur_rules = read_htaccess()
		del_id = req.body
		cur_rules.pop(del_id)
		write_htaccess(cur_rules)
		return Response("null")

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    httpd = make_server('', 8000, Z25Url())
    print("Serving on port 8000...")
    # Serve until process is killed
    httpd.serve_forever()

