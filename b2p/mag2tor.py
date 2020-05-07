import libtorrent as lt
import time
import sys
import base64
import binascii

ses = lt.session()
ses.listen_on(6881, 6891)

magnet = lt.parse_magnet_uri(sys.argv[1])
e = str(magnet.info_hash)
if len(e) == 40:
    info_hash = binascii.unhexlify(e)
elif len(e) == 32:
    info_hash = base64.b32decode(e)
else:
    raise Exception("Unable to parse infohash")

trackers = magnet.trackers
h = ses.add_torrent({'info_hash': info_hash, 'trackers': trackers})
dots=0
while not h.has_metadata():
    dots += 1
    sys.stdout.write('.')
    sys.stdout.flush()
    time.sleep(1)
if (dots): sys.stdout.write('\n')
ses.pause()
tinf = h.get_torrent_info()
f = open('/tmp/b2pgen' + '.torrent', 'wb')
f.write(lt.bencode(
    lt.create_torrent(tinf).generate()))
f.close()
ses.remove_torrent(h)
