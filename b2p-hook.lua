local utils = require 'mp.utils'
local msg = require 'mp.msg'
local pathscript = '/home/damir/b2p'
local savepath = '/home/damir/files'

local b2p_is_running = false


mp.add_hook("on_load", 50, function ()
    local url = mp.get_property("stream-open-filename")
    if (url:find("b2p://") == 1) then 
            url = url:sub(7)
    end
	if (url:find("magnet:") == 1) then
    utils.subprocess({ args = { 'python', pathscript.. '/mag2tor.py', url}})
    url = "/tmp/b2pgen.torrent"
	end
	if(url:find("[%a%d%p]+%.torrent") == 1) then 
	if(url:find("http") == 1) then
    utils.subprocess({ args = { 'curl', '-s', url, '-o', '/tmp/b2pgen.torrent' }})
    url = "/tmp/b2pgen.torrent"
	end
       local res = utils.subprocess({ args = { "pgrep", "-f", pathscript.. '/b2p3.py' }})
	    local out = (res["stdout"])
        if (out:find("[%d]+") == 1) then
       utils.subprocess({ args = { 'killall', '-9', out}})
       end

        utils.subprocess_detached({ args = { 'python', pathscript.. '/b2p3.py', '--save-path='..savepath ,'--piece-par=10', '--hash-file=' ..url}})
       utils.subprocess({ args = { 'curl', '-s', "http://localhost:17580", '--retry', '10', '--retry-connrefused', '10', '--retry-delay', '2'}})
        mp.set_property("stream-open-filename", "http://localhost:17580")
        b2p_is_running = true
    end
end) 

mp.add_hook("on_unload", 10, function ()
	if (b2p_is_running) then
      rar = mp.get_property("playlist")
	  rar = rar:gsub('[%p%c%s]', '')
	if not (rar:find("filenamehttplocalhost17580") == 1) then
    os.execute("kill -9 $(pgrep -f 'python " .. pathscript.. "/b2p3.py')") 
    b2p_is_running = false
	  end
      end
end)

function my_fn()
    if (b2p_is_running) then
       os.execute("kill -9 $(pgrep -f 'python " .. pathscript.. "/b2p3.py')") 
end
end

mp.register_event("shutdown", my_fn)
