local utils = require 'mp.utils'
local msg = require 'mp.msg'

local opts = {
    threads = 4,
    supported_extensions=[[
    ["txt", "epub", "mobi", "azw3", "azw4", "pdf", "docx", "odt"]
    ]],
    ebook_convert_options="",
    editor_cleanup=false,
    gui_progress=true,
}
(require 'mp.options').read_options(opts)
opts.supported_extensions = utils.parse_json(opts.supported_extensions)

local function exec(args)
    local ret = utils.subprocess({args = args})
    return ret.status, ret.stdout, ret, ret.killed_by_us
end

local function findl(str, patterns)
    for i,p in pairs(patterns) do
        if str:find("%."..p.."$") then
            return true
        end
    end
    return false
end

mp.add_hook("on_load", 10, function ()
    local url = mp.get_property("stream-open-filename", "")
    msg.debug("stream-open-filename: "..url)
    if (findl(url, opts.supported_extensions) == false) then
        msg.debug("did not find a supported file")
        return
    end

    -- find text2media
    local text2media_py = mp.find_config_file("text2media.py")
    if (text2media_py == nil) then
        msg.error("text2media.py is missing, should be in ~/.config/mpv/")
        return
    end

    -- build text2media command and run
    command = {text2media_py, "--cleanup", "--threads", opts.threads,   url}
    if (opts.editor_cleanup) then table.insert(command, "--editor-cleanup") end
    if (opts.gui_progress) then table.insert(command, "--gui-progress") end
    stat,out = exec(command)

    mp.set_property("stream-open-filename", out:gsub("\n", ""))
    return
end)
