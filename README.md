# CoW: Code over the Web

CoW is a minimalist online programming environment, with only the
required features so that somebody can program and execute code on a
real Linux box without having to install anything.

User features:

 - support several programming languages (see below)
 - edit multiple files
 - download files
 - full-featured editor thanks to [CodeMirror](http://codemirror.net)
 - automatically compile programs
 - execution in a real terminal thanks to [ttyd](http://github.com/tsl0922/ttyd),
   or (unstable) in a X11 terminal thanks to [Xpra](http://github.com/Xpra-org/xpra)
   (Xpra support is still experimental, see below)
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

Bugs and limitations:

 - young project: expect bugs, regressions, and incompatible updates
 - `xpra` does not work behind a reverse proxy, so it cannot be used
   in production

## Languages supported

### C

CoW supports C through [GCC](http://gcc.gnu.org), with additional features:

 - use ISO C11 standard
 - [get the maximum of GCC](http://airbus-seclab.github.io/c-compiler-security/)
   to capture as many errors as possible
 - customisable compilation: use `// gcc: --your-flags` or `// ldd: --more-flags` 
   in the source code to append compilation/link flags
 - pass command-line arguments: use `// arg: my argv` in the source code
 - set environment variables: use `// env: NAME=VALUE` in the source code,
   several times if needed
 - run arbitrary commands instead of `make`: use `// run: command` in the source code

### Processing

CoW supports [Processing 3](http://processing.org) (Java version)

 - in a multiple-file project, the first file give its name to the sketchbook
 - running a project is _slooooooowww_ because `xpra` takes a while to start
 - using `xpra` currently does not work behind a reverse proxy, so
   **Processing language is disabled by default**

### Python

CoW supports [Python 3](http://www.python.org)

 - execute in a text terminal (graphical interfaces will not work)
 - no third party packages installed appart from what is installed on the host system
 - in a multiple-file project, the first file is assumed to be the main program

### Human Resource Machine

CoW supports [Human Resource Machine](http://tomorrowcorporation.com/humanresourcemachine) though [hrm-interpreter](http://pypi.org/project/hrm-interpreter)

 - text/emoji based interpreter of the HRM language
 - in a multiple-file project, only the first file is interpreted
 - inbox is randomly generated, by default with only numbers,
   customisable using special comments:
   - `-- inbox: 1,A,2,B,3` to provide a specific inbox
   - `-- isize: 5` to specify the size of generated inbox
   - `-- alpha: yes` to allow alphabetic characters in the generated inbox
   - `-- tiles: 0,1,B,U,G` to specify the initial content is the floor tiles

### adding new languages

Just look at `lang/python.py` and `lang/c.py` to see how they are
implemented, it should be easy to add you how language as long as it
works on the CLI and can be called from a `Makefile` (or a script
launched from the `Makefile`).

 - extend `lang.CoWrun` and overwrite:
   - method `add_source` to handle the creation of one source file in
     the project
   - method `add_makefile` to handle the creation of a `Makefile` that
     will compile and run the project
 - extend `lang.CoWzip` to adapt how a project files are zipped into
   one archive (for instance, Python/C do not need any change, while
   Processing need to put files in a subdirectory named from one of
   the source files)
 - add a 32x32 icon as `static/img/YOUR_LANG.png`
 - edit `cow.ini` to add an entry for you language

## Installation

Dependencies:

 - [Python 3](http://python.org)
 - [Flask](http://flask.palletsprojects.com)
 - [Header as Dependencies](http://pypi.org/project/Headers-as-Dependencies)
 - [ttyd](http://github.com/tsl0922/ttyd)
 - [xpra](http://github.com/Xpra-org/xpra)
 - [firejail](http://firejail.wordpress.com)
 - a Linux box with `make` installed
 - a compiler/interpreter for the languages that need to be supported
   - C currently required GCC, but this may change
   - Python is OK because CoW need Python too
   - Processing needs `processing-java` CLI
   - HRM language needs [hrm-interpreter](http://pypi.org/project/hrm-interpreter)
 - for CAS authentication: [Flask-CAS](http://pypi.org/project/Flask-CAS)
 - for production: an Apache or NGINX + uWSGI server
 - for development: [colored tracebacks](http://pypi.org/project/colored-traceback)

### How it works

In order to understand configuration, let's first explain how CoW works:

 - a Flask server exposes one page with the files editor
 - editing and managing files are performed on the client's browser
 - downloading uses the server to package the files into a zip archive
 - running code is performed by sending the source files to the Flask server on which:
   - source code is saved to a temporary directory
   - a `Makefile` is built
   - `make` is launched, within `firejail`, within `ttyd` or `xpra`+`xterm`
   - an URL is returned to the client so it opens a new window to the
     `ttyd`/`xpra` terminal

There's two things to note here:

 - users must allow popups in their browser for CoW
 - `ttyd`/`xpra` must be reachable from the users' browser

This latter point is easy when CoW is run locally since the browser
just connect to `localhost`. But on a server, most ports are usually
not reachable and the HTTP server must be configured to reverse proxy
the connections to `ttyd`/`xpra`. To do so, CoW must be configured to
return recognisable URLs that are forwarded by the HTTP server to the
actual `ttyd`/`xpra` ports on the local server.

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
```

Then create `/home/cow/cow.ini` with:

```ini
[COW]
TMPDIR = /home/cow/tmp
SECRET_KEY = a random string to secure cookies
TTYD_URL = https://your.hostname/ttyd/{port}/{key}/
# XPRA_URL may be set as well but it does not work currently
```

Note how `TTYD_URL` is configured so that the HTTP server can forward
incoming connections to `ttyd`.

Then edit `/var/www/cow.wsgi` to instruct Apache how to run CoW:

```python
PYTHON = "/path/to/python3"
import sys, os
sys.path.insert(0, "/home/cow/cow")
os.environ["COW_CONFIG"] = "/home/cow/cow.ini"
os.chdir("/home/cow/cow")
from app import app as application
```

Finally, create a site for Apache, eg, `/etc/apache2/sites-available/cow.conf`:

```apache
<VirtualHost *>
  ServerName your.hostname

  WSGIDaemonProcess cow user=cow group=cow threads=5
  WSGIScriptAlias / /var/www/cow.wsgi

  # needed since Apache 2.4.48 (26-May-2021)
  ProxyWebsocketFallbackToProxyHttp off

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

Note how URLs as configured in `TTYD_URL` are rewritten and proxyed to
actual `ttyd` instances; websockets are treated separately so that
they are correctly proxyed. Note also that Apache modules `rewrite`,
`proxy`, `proxy_http`, and `proxy_wstunnel` should be enabled.

### Install on NGINX + uWSGI server

NGINX cannot execute Flask applications directly, you will need an
application server for that, and uWSGI is fine. (In principle, it
could also be your HTTP server but I could not configure it correctly
to proxy `ttyd`.)

Create user `cow`, and file `cow.ini` as instructed above.

Configure a new uWSGI server:

```ini
[uwsgi]
env = COW_CONFIG=/home/cow/cow.ini
uid = cow
gid = cow
plugin = python3
pythonpath = /path/to/additional/python/packages
# server location, will be queried by NGINX proxy
uwsgi-socket = 127.0.0.1:9191
chdir = /home/cow/cow
module = app
callable = app
# configure according to the expected workload
processes = 4
threads = 2
offload-threads = 2
```

If uWSGI is installed from a package, it will certainly be
preconfigured to spawn one server for each file in
`/etc/uwsgi/apps-enabled`, and in this case probably it runs under
`www-data` identity or something like that. So you will need to edit
its global configuration file to have it run as `root` so that it will
be able to change this server's identity to `cow`. Under Debian 11,
this global configuration is `/usr/share/uwsgi/conf/default.ini` and
you just need to add:

```ini
[uwsgi]
uid = root
gid = root
```

Take care then to correctly set `uid`/`gid` for every server you'll run.

Finally, create a new NGINX server with:

```
server {
  server_name your.hostname;
  listen 80;
  location ~ ^/ttyd/(\d+)/([^/]+)/ {
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_pass http://127.0.0.1:$1/$2/;
  }
  location / {
    uwsgi_pass 127.0.0.1:9191;
    include uwsgi_params;
  }
}
```

### Xpra in production

In principle, `xpra` could be forwarded by a reverse proxy just like
`ttyd`. But the problem is to forward it authentication. So far, I've
tried to use `--tcp-auth=env` and `--auth=password:value=PASSWORD`, in
which case the password can be passed through the query string
`?password=PASSWORD`. But this does not work so far, I'm working on it.

## Licence

CoW is released under the MIT licence, see file `LICENCE` for more information.
(C) 2021, Franck Pommereau <franck.pommereau@univ-evry.fr>

Third-party utilities are included in CoW for a more convenient installation, they are released under their own licences:

 - `static/jquery.min.js`: [jQuery](http://jquery.com)
 - `static/jqui/`: [jQuery UI](http://jqueryui.com)
 - `statis/cm/`: [CodeMirror](http://codemirror.net)
 - `xpra-html5`: [Xpra HTML5 client](http://github.com/Xpra-org/xpra-html5)
