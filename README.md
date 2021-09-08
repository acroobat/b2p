# b2p
Fork of http://www.beroal.in.ua/prg/bittorrent2player/

<b>Requirements:</b>
<ul>
<li>libtorrent with python binding(>=2.0)</li>
</ul>

<b>Installation:</b>

`pip install git+https://github.com/acroobat/b2p.git`

<b>Usage:</b>

`b2p --hash-file="Big_Buck_Bunny.torrent" --save-path="/tmp"`

To play with vlc

`vlc http://localhost:17580` 


# b2p-hook

Lua script for mpv

<b>Installation: </b> 

Copy `b2p-hook.lua` into `~/.config/mpv/scripts/`

<b>Configuration: </b>

`pathscript` - b2p directory path

`savepath` - directory where temporary files will be stored 

`deletefiles` - whether to delete files


 

<b>Usage:</b>

`mpv Big_Buck_Bunny.torrent`

or

`mpv magnet:?xt=urn:btih:a3fbda1961fbc908026ec7cc4569d5fbef840c1e&dn=big_buck_bunny_1080p_surround.avi`


