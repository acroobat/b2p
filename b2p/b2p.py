#!/usr/bin/python3
__credits__ = """Copyright (c) 2011 Roman Beslik <rabeslik@gmail.com>
Licensed under GNU LGPL 2.1 or later.  See <http://www.fsf.org/>.

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
"""

import http.server
from socketserver import ThreadingMixIn
import urllib.request, urllib.parse, urllib.error
from mimetypes import guess_type as guess_mime_type
from distutils.util import strtobool
import libtorrent

import threading
import os
import os.path as fs
import sys
import io
import getopt
import base64
import binascii
import time

class reference(object):
    pass

def split_path_list(path):
    r = []
    while True:
        y, x = fs.split(path)
        if y==path:
            break;
        path = y
        r.append(x)
    return r

class piece_server(object):
    def __init__(self):
        super(piece_server, self).__init__()
        self.lock = threading.Lock()
        self.array = []
    def init(self):
        self.torrent_handle.prioritize_pieces(self.torrent_info.num_pieces() * [0])
    def push(self, read_piece_alert):
        if (self.torrent_handle == read_piece_alert.handle):
            self.lock.acquire()
            try:
                def f(record):
                    _, _, piece = record
                    return piece == read_piece_alert.piece
                for record in filter(f, self.array):
                    event, channel, _ = record
                    channel.append(read_piece_alert.buffer)
                    event.set()
                self.array = [record for record in self.array if not(f(record))]
            finally:
                self.lock.release()
    def pop(self, piece):
        event = threading.Event()
        channel = []
        self.lock.acquire()
        try:
            piece_par = round(self.torrent_info.metadata_size() / 10000) + 1
            def bound_in_torrent(start):
                return min(self.torrent_info.num_pieces(), start+piece_par)
            bound0 = bound_in_torrent(piece)
            phave = piece
            while phave < bound0 and self.torrent_handle.have_piece(phave):
                phave += 1
            bound1 = bound_in_torrent(phave)
            p = phave
            while p < bound1:
                if p==phave:
                    priority = 7
                else:
                    priority = 1
                self.torrent_handle.piece_priority(p, priority)
                p += 1
            self.array.append((event, channel, piece))
            self.torrent_handle.set_piece_deadline(piece, 0, libtorrent.deadline_flags_t.alert_when_available)
        finally:
            self.lock.release()
        event.wait()
        return channel[0]

class alert_client(threading.Thread):
    def __init__(self):
        super(alert_client, self).__init__()
        self.daemon = True
    def run(self):
        while(True):
            self.torrent_session.wait_for_alert(1000)
            a = self.torrent_session.pop_alerts()
            try:
                s = self.torrent_handle.status()     
                state_str = ['queued', 'checking', 'downloading metadata', 'downloading', 'finished', 'seeding', 'allocating', 'checking fastresume']
                print('\r%.2f%% complete (down: %.1f kb/s up: %.1f kB/s peers: %d) %s' % (s.progress * 100, s.download_rate / 1000, s.upload_rate / 1000, s.num_peers, state_str[s.state]), end=' ')
                sys.stdout.flush()
            except RuntimeError:
                pass
            if a:
                if (type(a[0]) == libtorrent.read_piece_alert):
                    self.piece_server.push(a[0])

class torrent_file_bt2p(object):
    def write(self, dest, rangespec, startpos, endpos):
        request_done = False
        while (not(request_done)):
            piece_slice = self.map_file(startpos)
            data = self.piece_server.pop(piece_slice.piece)
            if data is None:
                request_done = True
            else:
                available_length = rangespec
                end = piece_slice.start + available_length
                if (end>=len(data)):
                    end = len(data)
                    available_length = len(data)-piece_slice.start
                dest.write(data[piece_slice.start:end])
                startpos += available_length
                request_done = startpos>endpos

class torrent_read_bt2p(object):
    def write_html(self, s):
        return """#EXTM3U"""+s
    def write_html_index(self):
        t = {}
        error = []
        for f in self.torrent_info.files():
            t0 = t
            level = 0
            xs = split_path_list(f.path)
            level_n = len(xs)
            for x in reversed(xs):
                key_found = x in t0
                if level+1 >= level_n:
                    if key_found:
                        error.append("duplicate file: "+f.path)
                    else:
                        t0[x] = ("file", f)
                else:
                    if key_found:
                        tag, t1 = t0[x]
                        if not (tag == "dir"):
                            error.append("file and directory: "+f.path)
                            break
                        t0 = t1
                    else:
                        t1 = {}
                        t0[x] = ("dir", t1)
                        t0 = t1
                level += 1
        def flat(t, level):
            r = []
            for x, y in sorted(iter(t.items()), key = lambda x: x[0]):
                tag, z = y
                if "file"==tag:
                    f = z
                    r.append("""
#EXTINF:-1,
http://localhost:17580"""+urllib.request.pathname2url("/"+f.path)+"""""")
                elif "dir"==tag:
                    r.append(flat(z, level+1))
                else:
                    pass
            return "".join(r)
        file_tree_s = flat(t, 0)
        return self.write_html(file_tree_s)

#   def init(self):
#       self.info_hash = self.torrent_info.info_hash()
    def find_file(self, http_path):
        p = urllib.request.url2pathname(http_path)
        for i, f0 in enumerate(self.torrent_info.files()):
            if "/"+f0.path == p:
                f1 = torrent_file_bt2p()
                f1.size = f0.size
                f1.map_file = lambda offset: self.torrent_info.map_file(i, offset, 1)
                f1.content_type = guess_mime_type(f0.path)
                return f1
        return None

class http_responder_bt2p(http.server.BaseHTTPRequestHandler):
    def read_from_torrent(self, torrent_file):
        file_size = torrent_file.size
        hr = self.headers.get("Range")
        if not (hr is None):
            startpos = ''.join(filter(lambda i: i.isdigit(), hr)) 
            rangespec = file_size-int(startpos)
            self.send_header("Content-Length", rangespec)
            self.send_header("Content-Range", "bytes "+startpos+"-"+str(file_size-1)+"/"+str(file_size))
            self.end_headers()
            torrent_file.write(self.wfile, rangespec, int(startpos), file_size-1)
    def do_GET(self):
        try:
            if "/"==self.path:
                s = self.server.torrent.write_html_index()
                self.send_header("Content-Length", str(len(s)))
                self.end_headers()
                sd = s.encode()
                self.wfile.write(sd)
            elif "/?exit=yes"==self.path:
                self.torrent_session.remove_torrent(self.torrent_handle, strtobool(self.delete_files))
                t = threading.Thread(target=self.http_server.shutdown)
                t.daemon = True
                t.start()
               # sys.exit()
            else:
                torrent_file = self.server.torrent.find_file(self.path)
                if not torrent_file:
                    self.send_response(404)
                    self.end_headers()
                else:
                    torrent_file.piece_server = self.server.piece_server
                    self.read_from_torrent(torrent_file)
        except IOError as e:
            pass

class http_server_bt2p(ThreadingMixIn, http.server.HTTPServer):
    pass

def error_exit(exit_code, message):
    sys.stderr.write(message+"\n")
    sys.exit(exit_code)

def main_default(options):
    if not ("domain-name" in options):
        options["domain-name"] = "127.0.0.1"
    if not ("port" in options):
        options["port"] = 17580
    if not ("delete-files" in options):
        options["delete-files"] = True
    if not ("save-path" in options):
        error_exit(226, "\"--save-path\" is mandatory")
    if not ("hash-file" in options):
        error_exit(226, "\"--hash-file\" is mandatory")

def main_torrent_descr(options):
    main_default(options)
    sett = {'enable_lsd': True,
    'enable_dht': True,
    'enable_upnp': True,
    'enable_natpmp': True,}
    torrent_session = libtorrent.session(sett)
    alert_mask = (
        libtorrent.alert.category_t.storage_notification
        | libtorrent.alert.category_t.status_notification
    )

    torrent_session.apply_settings({'alert_mask': alert_mask})
    torrent_session.listen_on(6881, 6891)
    torrent_session.dht_nodes=[ ('router.bittorrent.com',6881), ('router.utorrent.com',6881), ('dht.transmissionbt.com',6881), ('dht.libtorrent.org',25401), ('dht.aelitis.com',6881)]
    torrent_session.start_dht()
    torrent_session.start_lsd()
    torrent_session.add_extension('ut_metadata')
    torrent_session.add_extension('ut_pex_plugin')
    torrent_session.add_extension('smart_ban_plugin')

    
    torrent_descr = {"save_path": options["save-path"]}
    if "hash-file" in options:
        if options["hash-file"].startswith('magnet:?'):
            magnet = libtorrent.parse_magnet_uri(options["hash-file"])
            e = str(magnet.info_hash)
            if len(e) == 40:
                info_hash = binascii.unhexlify(e)
            elif len(e) == 32:
                info_hash = base64.b32decode(e)
            else:
                raise Exception("Unable to parse infohash")

            trackers = magnet.trackers
            torrent_handle = torrent_session.add_torrent({'info_hash': info_hash, 'trackers': trackers, "save_path": options["save-path"]})
            dots=0
            while not torrent_handle.has_metadata():
                dots += 1
                sys.stdout.write('.')
                sys.stdout.flush()
                time.sleep(1)
            if (dots): sys.stdout.write('\n')
            torrent_info = torrent_handle.get_torrent_info()
        else:   
            torrent_info = libtorrent.torrent_info(options["hash-file"])
            torrent_descr["ti"] = torrent_info
            torrent_handle = torrent_session.add_torrent(torrent_descr)
    
    piece_par_ref0 = reference()
    
    piece_server0 = piece_server()
    piece_server0.torrent_handle = torrent_handle
    piece_server0.torrent_info = torrent_info
    piece_server0.init()

    alert_client0 = alert_client()
    alert_client0.torrent_session = torrent_session
    alert_client0.torrent_handle = torrent_handle
    alert_client0.piece_server = piece_server0
    alert_client0.start()
    
    r = torrent_read_bt2p()
    r.torrent_handle = torrent_handle
    r.torrent_info = torrent_info
    #r.init()
    
    http_server = http_server_bt2p((options["domain-name"], options["port"]), http_responder_bt2p)
    http_server.daemon_threads = True
    http_server.torrent = r
    http_server.piece_server = piece_server0
    
    http_responder_bt2p.torrent_session = torrent_session
    http_responder_bt2p.torrent_handle = torrent_handle
    http_responder_bt2p.delete_files = options["delete-files"]
    http_responder_bt2p.http_server = http_server
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        print("An exception occurred")

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        crude_options, args = getopt.getopt(argv[1:], ""
            , ["save-path=", "domain-name=", "port="
            , "hash-file=", "delete-files="])
    except getopt.error as error:
        error_exit(221, "the option "+error.opt+" is incorrect because "+error.msg)
    if []!=args:
        error_exit(222, "only options are allowed, not arguments")
    options = {}
    for o, a in crude_options:
        if "--hash-file"==o:
            options["hash-file"] = a
        elif "--save-path"==o:
            options["save-path"] = a
        elif "--domain-name"==o:
            options["domain-name"] = a
        elif "--port"==o:
            options["port"] = a
        elif "--delete-files"==o:
            options["delete-files"] = a
        else:
            error_exit(223, "an unknown option is given")
    main_torrent_descr(options)

if __name__ == "__main__":
    main()
