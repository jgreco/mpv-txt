local utils = require 'mp.utils'
local msg = require 'mp.msg'
local options = require 'mp.options'

local function exec(args)
    local ret = utils.subprocess({args = args})
    return ret.status, ret.stdout, ret, ret.killed_by_us
end

mp.add_hook("on_load", 10, function ()
    local url = mp.get_property("stream-open-filename", "")
    msg.debug("stream-open-filename: "..url)
    if (url:find("%.txt$") == nil) then
        msg.debug("did not find a text file")
        return
    end

    -- find text2media
    local text2media_py = mp.find_config_file("text2media.py")
    if (text2media_py == nil) then
        msg.error("text2media.py is missing, should be in ~/.config/mpv/")
        return
    end

    _,filename = utils.split_path(url)
    stat,out = exec({text2media_py, filename, url})
    mp.set_property("stream-open-filename", out:gsub("\n", ""))
    return
end)
