# CoW: C over the Web

CoW is a minimalist C online programming environment, with only the required features so that somebody can program and execute C code on a real Linux box without having to install anything.

User features:

 - edit multiple files
 - download files
 - full-featured editor thanks to [CodeMirror](http://codemirror.net)
 - automatically compile programs
 - execution in a real terminal thanks to [ttyd](http://github.com/tsl0922/ttyd)
 - possible interaction with the program

![CoW in action](https://raw.githubusercontent.com/fpom/cow/main/misc/demo.gif)

Host features:

 - minimal installation/configuration
 - no files stored on server (except temporarily during compilation/execution)
 - user-code secured using [firejail](http://firejail.wordpress.com)
 - optional CAS authentication (more may be added as long as it'll be outside of CoW)

Development guidelines:

 - keep CoW as simple as possible, with a small and simple code base
 - leverage established third-party projects to provide the most complex features
 - avoid using server as much as possible
 - protect the server from user's programs

## Installation

Dependencies:

 - [Python 3](http://python.org)
 - [Flask](http://flask.palletsprojects.com)
 - [Header as Dependencies](http://pypi.org/project/Headers-as-Dependencies)
 - [ttyd](http://github.com/tsl0922/ttyd)
 - [firejail](http://firejail.wordpress.com)
 - a Linux box with GCC and make
 - for CAS authentication: [Flask-CAS](http://pypi.org/project/Flask-CAS)
 - for production: and Apache or NGINX server
 - for development: [colored tracebacks](http://pypi.org/project/colored-traceback)

### How it works

In order to understand configuration, let's first explain how CoW works:

 - a Flask server exposes one page with the files editor
 - editing, managing files, and downloading is performed on the client's browser
 - running code is performed by sending it's source to the Flask server on which:
   - source code is saved to a temporary directory
   - a `Makefile` is built
   - `make` is launched, within `firejail`, within `ttyd`
   - an URL is returned to the client so it opens a new window to the `ttyd` terminal

There's two things to note here:

 - users must allow popups in their browser for CoW
 - `ttyd` must be reachable from the users' browser

This latter point is easy when CoW is run locally since the browser just connect to `localhost`.
But on a server, most ports are usually not reachable and the HTTP server must be configured to reverse proxy the connections to `ttyd`.
To do so, CoW must be configured to return recognisable URLs that are forwarded by the HTTP server to the actual `ttyd` ports on the local server.

### Run locally

```sh
$ git clone https://github.com/fpom/cow.git
$ cd cow
$ FLASK_APP=app.py flask run
```

### Install on Apache server

```sh
$ adduser cow
$ su - cow
$ git clone https://github.com/fpom/cow.git
$ mkdir tmp
$ cat >config.py <<EOF
TMPDIR = "/home/cow/tmp"
SECRET_KEY = "a random string to secure cookies"
TTYD_URL = "https://your.hostname/ttyd/{port}/{key}/"
EOF
```

Note how `TTYD_URL` is configured so that the HTTP server can forward incoming connections to `ttyd`.

Then edit `/var/www/cow.wsgi` to instruct Apache how to run CoW:

```python
PYTHON = "/path/to/python3"
import sys, os
sys.path.insert(0, "/home/cow/cow")
os.environ["COW_CONFIG"] = "/home/cow/config.py"
os.chdir("/home/cow/cow")
from app import app as application
```

Note how we set `COW_CONFIG` environment variable so that CoW will read the `config.py` we've created earlier.

Finally, create a site for Apache, eg, `/etc/apache2/sites-available/cow.conf`:

```apache
<VirtualHost *>
  ServerName your.hostname

  WSGIDaemonProcess cow user=cow group=cow threads=5
  WSGIScriptAlias / /var/www/cow.wsgi

  RewriteEngine on
  RewriteRule    ^/ttyd/(\d*)/([^/]*)/ws$   ws://localhost:$1/$2/ws [P,L]
  RewriteRule    ^/ttyd/(\d*)/(.*)$         http://localhost:$1/$2  [P,L]
      
  <Directory /var/www>
    WSGIProcessGroup cow
    WSGIApplicationGroup %{GLOBAL}
    Order deny,allow
    Allow from all
    WSGIScriptReloading On
  </Directory>
</VirtualHost>
```

Note how URLs as configured in `TTYD_URL` are rewritten and proxyed to actual `ttyd` instances; websockets are treated separately so that they are correctly proxyed.
Note also that Apache modules `rewrite`, `proxy`, `proxy_http`, and `proxy_wstunnel` should be enabled.

### Install on NGINX server

I don't use such a server now, feel free to contribute installation instructions.

## Licence

CoW is released under the MIT licence, see file `LICENCE` for more information.

Third-party utilities are included in CoW for a more convenient installation, they are released under their own licences:

 - `static/jquery.min.js`: [jQuery](http://jquery.com)
 - `static/jquery.base64.js`: [jQuery base64 plugin](http://plugins.jquery.com/base64)
 - `static/jqui/`: [jQuery UI](http://jqueryui.com)
 - `statis/cm/`: [CodeMirror](http://codemirror.net)
