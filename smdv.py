#!/usr/bin/env python3

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

""" smdv: a simple markdown viewer """

__version__ = "0.0.1"
__author__ = "Floris Laporte"

# standard library imports
import os
import sys
import time
import socket
import typing
import argparse
import textwrap
import subprocess
import webbrowser
import http.client

# third party imports
import flask
import werkzeug


# add header to html body
def body2html(body: str) -> str:
    """ convert a html body to full html

    Args:
        body: str: the html body

    Returns:
        html: str: the resulting html
    """
    stylesheet = ARGS.md_css_cdn
    if not stylesheet.startswith("http"):
        stylesheet = os.path.abspath(os.path.expanduser(stylesheet)).replace(
            ARGS.home, f"http://127.0.0.1:{ARGS.port}/@static"
        )
    jquery = ARGS.jquery_cdn
    if not jquery.startswith("http"):
        jquery = os.path.abspath(os.path.expanduser(jquery)).replace(
            ARGS.home, f"http://127.0.0.1:{ARGS.port}/@static"
        )
    html = textwrap.dedent(
        f"""
        <!DOCTYPE html>
        <html>
        <head>
        <link rel="stylesheet" href="{stylesheet}">
        <style>
            .markdown-body {{ box-sizing: border-box; min-width: 200px; max-width: 980px; margin: 0 auto; padding: 45px; }}
            @media (max-width: 767px) {{ .markdown-body {{ padding: 15px; }} }}
        </style>
        <script src="{jquery}"></script>
        </head>
        <body>
        <article class="markdown-body" id="content">
        {body}
        </article>
        <script>
            function queryReload() {{
            $.ajax({{
               url: "/@query-reload",
               success: function(data) {{
                  if (data)
                     // $('#content').html(data);
                     // location.reload()
                     location.href = data
                 setTimeout(queryReload, 1000);
               }}
            }});
            }}
            setTimeout(queryReload, 1000);
        </script>
        </body>
        </html>
        """
    )
    return html


# open a new browser
def browser_open(filename: str = ""):
    """ spawn a new browser and open the specified file

    Args:
        filename: str="": the filename to open the browser at.
    """
    if filename.startswith("/"):
        filename = f"{ARGS.home}{filename}"
    url = os.path.abspath(os.path.expanduser(filename)).replace(
        ARGS.home, f"http://127.0.0.1:{ARGS.port}"
    )
    print(f"smdv: opening browser at {url}")
    with open(os.devnull, "w") as NULL:
        if ARGS.browser == "chromium --app":
            subprocess.Popen(["chromium", f"--app={url}"], stdout=NULL, stderr=NULL)
        elif ARGS.browser:
            subprocess.Popen([ARGS.browser, url], stdout=NULL, stderr=NULL)
        elif subprocess.call(["which", "xdg-open"], stdout=NULL, stderr=NULL) == 0:
            subprocess.Popen(["xdg-open", url], stdout=NULL, stderr=NULL)
        else:
            webbrowser.open(url)


# app factory
def create_app() -> flask.Flask:
    """ flask app factory

    Returns:
        app: flask.Flask: the flask app.
    """

    app = flask.Flask(__name__, static_folder=ARGS.home, static_url_path="/@static")

    @app.route("/<path:path>/@edit")
    def edit(path: str) -> werkzeug.wrappers.Response:
        """ edit markdown file

        Args:
            path: str: the path of the file to edit with neovim

        Returns:
            flask.redirect to the view route of the file to edit.
        """
        neovim_remote_open(os.path.join(ARGS.home, path))
        return flask.redirect(f"/{path}")

    @app.route("/@query-reload")
    def query_reload() -> str:
        """ query the server to see if the current page needs a reload

        Returns:
            html: str: the html representation for the perhaps reloaded file.
        """
        if os.path.exists("/tmp/smdv"):
            with open("/tmp/smdv", "r") as file:
                content = file.read()
            os.remove("/tmp/smdv")
            content = content.replace(ARGS.home, "")
            if content == "":
                content = "/"
            return content
        else:
            return ""

    @app.route("/@server-stop")
    def request_server_stop():
        """ kill current running flask server """
        func = flask.request.environ.get("werkzeug.server.shutdown")
        if func is None:
            return f"could not stop server on port {ARGS.port}."
        func()
        return "smdv: server successfully stopped."

    @app.route("/<path:path>.md")
    def view_md(path: str) -> str:
        """ view markdown file

        Args:
            path: the path of the markdown file to view.

        Returns:
            html: str: the html representation for the requested markdown file.
        """
        path = os.path.join(ARGS.home, path + ".md")
        if ARGS.interactive:
            neovim_remote_open(path)
        html = md2html(path=path)
        return html

    @app.route("/<path:path>.ipynb")
    def view_ipynb(path: str) -> str:
        """ view jupyter notebook file

        Args:
            path: the path of the jupyter notebook to view.

        Returns:
            html: str: the html representation for the requested jupyter notebook file.

        """
        path = os.path.join(ARGS.home, path + ".ipynb")
        if ARGS.interactive:
            neovim_remote_open(path)
        with open(path, "r") as file:
            try:
                html = subprocess.check_output(
                    ["jupyter", "nbconvert", path, "--to", "html", "--stdout"]
                )
            except subprocess.CalledProcessError:
                return flask.abort(500)
        return html

    @app.route("/")
    @app.route("/<path:path>")
    def view_other(path: str = "") -> typing.Union[str, werkzeug.wrappers.Response]:
        """ view file/directory

        Args:
            path: str="": the path of the file or directory to show

        Returns:
            html: str: the html representation for the requested file or directory.

        Note:
            This is the default route. Any filetype that has no route of its own
            will be opened here.
        """
        path = os.path.join(ARGS.home, path)
        if ARGS.interactive:
            neovim_remote_open(path)
        if not os.path.exists(path):
            flask.abort(404)
        elif os.path.isdir(path):
            return dir2html(path)
        elif not is_binary_file(path):
            with open(path, "r") as file:
                content = file.read()
            return md2html(content=f"```\n{content}\n```", path=path)
        else:
            return flask.redirect(
                path.replace(ARGS.home, f"http://127.0.0.1:{ARGS.port}/@static")
            )

    return app


# convert a directory path to html
def dir2html(path: str, full: bool = True) -> str:
    """ convert markdown to html using the github flavored markdown [gfm] spec of pandoc

    Args:
        path: str: the directory path to convert to html
        full: bool: wether to do a full conversion of the html (True),
            or just to return the body

    Returns:
        html: str: the resulting html
    """
    if path.endswith("/"):
        path = path[:-1]
    url = lambda path: path.replace(ARGS.home, f"http://127.0.0.1:{ARGS.port}").replace(
        " ", "%20"
    )
    if ARGS.home == os.path.expanduser("~"):
        displayed_path = path.replace(os.path.expanduser("~"), "~")
    else:
        displayed_path = path.replace(os.path.dirname(ARGS.home) + "/", "")
    filenames = {f"<h1>{displayed_path}/</h1>": None}
    if path != ARGS.home:
        filenames.update({"<b>⬆️  ..</b>": url(os.path.dirname(path))})
    listdir = sorted([p for p in os.listdir(path)], key=str.upper)
    md_html = ""
    for readme in ["README.md", "Readme.md", "readme.md"]:
        if readme in listdir:
            md_html = md2html(path=os.path.join(path, readme), full=False)
    listdir = [os.path.join(path, p) for p in listdir]
    listdir = [p for p in listdir if os.path.isdir(p)] + [
        p for p in listdir if not os.path.isdir(p)
    ]
    filenames.update(
        {
            (
                f"<b>📁  {os.path.basename(p)}</b>"
                if os.path.isdir(p)
                else f"📄  {os.path.basename(p)}"
            ): url(p)
            for p in listdir
        }
    )
    html = "<br>\n".join(
        [f"<a href={u}>{p}</a>" if u is not None else p for p, u in filenames.items()]
    )
    if not full:
        return html
    if md_html:
        html = html + "<br><br><hr><br>" + md_html
    html = body2html(html)

    return html


# check if a file is a binary
def is_binary_file(filename) -> bool:
    """ check if a file can be considered a binary file

    Args:
        filename: str: the filename of the file to check

    Returns:
        is_binary_string: bool: the truth value indicating wether the file is
            binary or not.
    """
    textchars = (
        bytearray([7, 8, 9, 10, 12, 13, 27])
        + bytearray(range(0x20, 0x7F))
        + bytearray(range(0x80, 0x100))
    )
    is_binary_string = lambda bytes: bool(bytes.translate(None, textchars))

    if is_binary_string(open(filename, "rb").read(1024)):
        return True
    else:
        return False


# main smdv function
def main():
    """ The main smdv function """
    try:
        # Arguments
        parse_args(sys.argv[1:])

        # ARGS.nvim_address = "127.0.0.1:9999"
        # if asked to stop server, stop server and exit
        if ARGS.stop:
            server_stop()
            exit(0)

        # if asked the status of the server, return status and exit
        if ARGS.status:
            server_status()
            exit(0)

        # cleanup filename
        filename = ARGS.filename
        if filename is None:
            filename = ARGS.home
        full_filename = os.path.abspath(os.path.expanduser(filename))
        filename = full_filename.replace(ARGS.home, "")
        if filename == "":
            filename = "/"

        # sync current filename and exit (requires a running server)
        if ARGS.sync:
            with open("/tmp/smdv", "w") as file:
                file.write(full_filename)
            exit(0)

        # kill other instance of smdv at this port if there is one running:
        if socket_in_use(f"127.0.0.1:{ARGS.port}"):
            subprocess.call(["python3", __file__, "--port", f"{ARGS.port}", "--stop"])
            time.sleep(1)  # give some time to kill the old server

        # open a browser at the current filename. Most browsers will wait for
        # a few miliseconds to get a reply from the server...
        browser_open(filename)

        # ... this is just in time to start the server:
        server_start()

    except Exception as e:
        print(f"{e.__class__.__name__}: {str(e)}", file=sys.stderr)
        exit(1)


# convert markdown content or path to html
def md2html(content: str = "", path: str = "", full=True) -> str:
    """ convert markdown to html using the github flavored markdown [gfm] spec of pandoc

    Args:
        content: str: the markdown string to convert
        path: str: the file path of the file to convert

    Returns:
        html: str: the resulting html

    Note:
        if content is given, it will display that in stead of the
        content in the file given by path.

    """
    if path.endswith("/"):
        path = path[:-1]

    dirpath = os.path.dirname(path)
    if path and not content:
        with open(path, "r") as file:
            content = file.read()
    if path and full:
        path = path.replace(ARGS.home, "")
        if ARGS.home == os.path.expanduser("~"):
            displayed_path = (ARGS.home + path).replace(os.path.expanduser("~"), "~")
        else:
            displayed_path = (ARGS.home + path).replace(
                os.path.dirname(ARGS.home) + "/", ""
            )
        content = (
            f"# {displayed_path}\n"
            f"[🖊 edit]({f'{os.path.basename(path)}/@edit'})&nbsp;&nbsp;&nbsp;&nbsp;"
            f"[📁 dir]({f'{os.path.dirname(path)}'})\n"
            f"{content}"
        )

    md_out = subprocess.Popen(
        ["printf", content.encode()], stdout=subprocess.PIPE
    ).stdout
    # sed_out = subprocess.Popen(["sed", f"s/\[\(.*\)\](\(.*\))/\[\1\](X\2)/g"], stdout=subprocess.PIPE).stdout
    html_out = (
        subprocess.check_output(
            ["pandoc", "--from", "gfm", "--to", "html"], stdin=md_out
        )
        .decode()
        .strip()
    )
    if path:  # fix urls.
        curdir = os.path.dirname(path).replace(ARGS.home, "")
        html_out = html_out.replace(
            '<img src="', f'<img src="/@static{curdir}/'
        ).replace("@static//", "@static/")
    if not full:
        return html_out
    html = body2html(html_out)
    return html


# open file in neovim
def neovim_remote_open(filename: str = ""):
    """ Open file in neovim using neovim-remote

    Args:
        filename: str="": the filename to open in neovim
    """
    path = os.path.abspath(os.path.expanduser(filename))
    if not os.path.exists(path):
        return
    socket = ARGS.nvim_address.strip()
    if not ":" in socket:  # unix socket
        dirname = os.path.dirname(socket)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
    if socket_in_use(socket):
        subprocess.Popen(["nvr", "-s", "--nostart", "--servername", socket, path])
    else:
        subprocess.Popen(
            [ARGS.terminal, "-e", "nvr", "-s", "--servername", socket, path]
        )


# argument parser
def parse_args(args: tuple):
    """ populate the global argument object ARGS

    Args:
        args: tuple: the arguments to parse

    Populates:
        ARGS: the global argument object which is used everywhere else.

    """
    global ARGS

    ## Argument parser
    parser = argparse.ArgumentParser(description="simple markdown viewer")
    parser.add_argument(
        "filename",
        type=str,
        nargs="?",
        default="",
        help="path or file to open with smdv",
    )
    parser.add_argument(
        "-H",
        "--home",
        default=os.path.abspath(os.path.expanduser("~")),
        help="set the root folder of the smdv server",
    )
    parser.add_argument(
        "-t",
        "--terminal",
        default=os.environ.get("TERMINAL", ""),
        help="default terminal to spawn (uses $TERMINAL by default)",
    )
    parser.add_argument(
        "-b",
        "--browser",
        default=os.environ.get("BROWSER", ""),
        help="default browser to spawn (uses $BROWSER by default)",
    )
    parser.add_argument(
        "-p", "--port", default="9876", help="port on which smdv is served."
    )
    parser.add_argument(
        "--md-css-cdn",
        default="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/3.0.1/github-markdown.css",
        help="location of [github flavored] markdown css cdn (can be a local file)",
    )
    parser.add_argument(
        "--jquery-cdn",
        default="https://code.jquery.com/jquery-3.4.1.min.js",
        help="location of jquery cdn (can be a local file)",
    )
    parser.add_argument(
        "-v",
        "--nvim-address",
        default="127.0.0.1:9877",
        help="address or socket to communicate with neovim (requires neovim-remote)",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        default=False,
        help="launch in interactive mode: each displayed page will also be displayed in neovim (requires neovim-remote)",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--start", action="store_true", default=False, help="check server status"
    )
    group.add_argument(
        "--stop",
        action="store_true",
        default=False,
        help="stop server; useful for a backgrounded process. ",
    )
    group.add_argument(
        "--status", action="store_true", default=False, help="check server status"
    )
    parser.add_argument(
        "-s",
        "--sync",
        action="store_true",
        default=False,
        help="sync new filename in current browser (requires a running server)",
    )

    ARGS = parser.parse_args(args=args)
    ARGS.home = os.path.abspath(os.path.expanduser(ARGS.home))
    if not ARGS.filename:
        ARGS.filename = ARGS.home


# start the smdv server
def server_start():
    """ start the smdv server """
    print(f"smdv: server started at http://127.0.0.1:{ARGS.port}")
    old_stdout, old_stderr = sys.stdout, sys.stderr
    with open(os.devnull, "w") as devnul:
        sys.stdout, sys.stderr = devnul, devnul
        create_app().run(debug=False, port=ARGS.port, threaded=True)
    sys.stdout, sys.stderr = old_stdout, old_stderr


# get status for the smdv server
def server_status() -> str:
    """ request the smdv server status

    Returns:
        status: str: the smdv server status
    """
    connection = http.client.HTTPConnection("127.0.0.1", ARGS.port)
    try:
        connection.connect()
        status = "server running"
    except ConnectionRefusedError:
        status = "server stopped"
    finally:
        connection.close()
    print(f"smdv: {status}")
    return status


# stop the smdv server
def server_stop():
    """ stop the smdv server """
    print("smdv: stopping server...")
    connection = http.client.HTTPConnection("127.0.0.1", ARGS.port)
    try:
        connection.connect()
        connection.request("GET", "/@server-stop")
        response = connection.getresponse().read().decode()
    except ConnectionRefusedError:
        response = "smdv: no server to stop."
    finally:
        connection.close()
    if (
        response == "smdv: server successfully stopped."
        or response == "smdv: no server to stop."
    ):
        print(response)
    else:
        raise RuntimeError(response)


# check if a socket is in use
def socket_in_use(address: str) -> bool:
    """ check if a socket is in use

    Args:
        address: str: the address of the unix/inet socket

    Returns:
        in_use: bool: wether the socket is in use or not.
    """

    if ":" in address:  # inet socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host, port = address.split(":")
        result = sock.connect_ex((host, int(port)))
        if result == 0:
            return True
        else:
            return False
        sock.close()
    else:  # unix socket
        if os.path.exists(address):
            return True
        return False


if __name__ == "__main__":
    main()
