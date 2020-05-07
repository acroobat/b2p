# b2p
Fork from dead http://www.beroal.in.ua/prg/bittorrent2player/

The original author is beroal 


<b>Difference:</b>

<ul>
<li>Swithed from python2 to python3</li>
<li>Switched from libtorrent 1.1 to 1.2</li>
<li>Logger is deleted</li>
<li>Http request is just simple m3u playlist</li>
</ul>

<b>Requirement</b>
<ul>
<li>libtorrent with python bindings(>=1.2)</li>
</ul>


# b2p-hook

Lua script for mpv 

<b>Configuration: </b>

You need to edit in `b2p-hook.lua`:

`pathscript` - b2p directory path

`savepath` - directory where temporary files will be stored 


 

<b>Usage:</b>

`mpv myfile.torrent` or `mpv magnet://mymagnet`


## Hope it works
