-- Conformance adapter for the wadamesh MECP app (deploy/apps/mecp/1.0/mecp.lua).
-- Loads the app unmodified with a stub wada SDK, takes its local decode() from
-- app.on_message's upvalues, and maps the rendered text back to the harness
-- record. Mapping is representation-only ("2 people" -> pax 2); the app exposes
-- no codes/freetext structure, so only valid/severity/pax/gps/timestamp are compared.
--
--   lua5.4 adapter.lua <path/to/mecp.lua>
--   stdin: <id>\t<hex utf-8 input>     stdout: one JSON record per line
local path = assert(arg[1], "usage: adapter.lua <mecp.lua>")

local nop = function() end
local stub = setmetatable({}, { __index = function() return nop end })
wada = { ui = setmetatable({ colors = {} }, { __index = function() return nop end }),
         sys = stub, mesh = stub, store = stub }
local app = assert(loadfile(path))()

local decode
for i = 1, 255 do
  local name, value = debug.getupvalue(app.on_message, i)
  if not name then break end
  if name == "decode" then decode = value end
end
assert(decode, "decode() not found among app.on_message upvalues")

local function q(s)
  if s == nil then return "null" end
  return '"' .. s:gsub('[%c"\\]', function(c)
    return c == '"' and '\\"' or c == "\\" and "\\\\" or string.format("\\u%04x", c:byte())
  end) .. '"'
end

-- "MAYDAY: Injury, 2 people, at 48.6520,20.1305 \"note\""
local function record(text)
  local s, sev = decode(text)
  if not s then return '{"valid":false}' end
  local words = s:match("^.-: (.*)$") or ""
  local note_at = words:find(' "', 1, true) or (words:sub(1, 1) == '"' and 1)
  if note_at then words = words:sub(1, note_at - 1) end
  local pax, gps, ts = "null", "null", "null"
  for w in (words .. ", "):gmatch("(.-), ") do
    local n = w:match("^(%d+) people$")
    if n and pax == "null" then pax = tostring(tonumber(n)) end
    local h, m = w:match("^at (%d%d):(%d%d)$")
    if h and ts == "null" then ts = q(h .. ":" .. m) end
    local lat, lon = w:match("^at (%-?[%d.]+),(%-?[%d.]+)$")
    if lat and gps == "null" then
      gps = string.format('{"lat":%s,"lon":%s}', tonumber(lat), tonumber(lon))
    end
  end
  return string.format('{"valid":true,"severity":%d,"pax":%s,"gps":%s,"timestamp":%s}',
                       sev, pax, gps, ts)
end

for line in io.lines() do
  local id, hex = line:match("^([^\t]+)\t(%x*)$")
  if id then
    local text = hex:gsub("%x%x", function(h) return string.char(tonumber(h, 16)) end)
    local ok, rec = pcall(record, text)
    io.write('{"id":', q(id), ",", ok and ('"result":' .. rec) or ('"error":' .. q(tostring(rec))), "}\n")
  end
end
