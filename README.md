# b2p
Fork of http://www.beroal.in.ua/prg/bittorrent2player/

The original author is beroal 


<b>Changes:</b>

<ul>
<li>Switched from python2 to python3</li>
<li>Switched from libtorrent 1.1 to 1.2</li>
<li>Logger is deleted</li>
<li>Http respond is just simple m3u playlist</li>
</ul>

<b>Requirements:</b>
<ul>
<li>libtorrent with python binding(>=1.2)</li>
</ul>


# b2p-hook

Lua script for mpv 

<b>Configuration: </b>

You need to edit `b2p-hook.lua`:

`pathscript` - b2p directory path

`savepath` - directory where temporary files will be stored 


 

<b>Usage:</b>

`mpv Big_Buck_Bunny.torrent`

or

`mpv magnet:?xt=urn:btih:a3fbda1961fbc908026ec7cc4569d5fbef840c1e&dn=big_buck_bunny_1080p_surround.avi`


