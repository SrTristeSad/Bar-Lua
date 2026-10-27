-- Índice de atlas do BarbarQ para o visualizador de engenharia reversa.
-- Evita escolher um sprite ambiguamente quando duas texturas usam o mesmo nome.
local M = {}
local function lower(s) return (s or ''):gsub('\\', '/'):lower() end
local function dirname(path) return (path or ''):match('^(.*)/[^/]+$') or '' end
local function basename(path) return (path or ''):match('[^/]+$') or '' end
local function alias(path)
    -- Referências CocosStudio mencionam .plist; os arquivos originais
    -- neste APK foram empacotados como .bplist.
    return lower(path):gsub('%.bplist$', '.plist')
end
local function add(map, key, item)
    local previous = map[key]
    if previous == nil then map[key] = item
    elseif previous ~= item then map[key] = false end -- ambíguo
end

function M.index(atlases)
    local res = {byFolder = {}, global = {}, byAtlas = {}}
    for _, atlas in ipairs(atlases or {}) do
        local path = alias(atlas.path)
        local folder = dirname(path)
        local bucket = res.byAtlas[path] or {}
        res.byAtlas[path] = bucket
        for _, frame in ipairs(atlas.frames or {}) do
            local sprite = {atlas = atlas, frame = frame}
            local name = lower(frame.name)
            add(bucket, name, sprite)
            add(res.byFolder, folder .. '/' .. name, sprite)
            add(res.global, name, sprite)
        end
    end
    return res
end

function M.find(index, asset, display)
    if type(display) ~= 'string' or display == '' then return nil end
    local name = lower(display)
    local folder = dirname(lower(asset.path))
    -- O arquivo .bexportjson especifica explicitamente os atlas usados.
    -- Resolver primeiro pelo atlas declarado elimina colisões globais.
    for _, ref in ipairs(asset.atlas_files or {}) do
        local key = alias(folder .. '/' .. ref)
        local specific = index.byAtlas[key]
        if specific and specific[name] then return specific[name] end
    end
    local localMatch = index.byFolder[folder .. '/' .. name]
    if localMatch then return localMatch end
    local global = index.global[name]
    if global then return global end
    return nil
end
return M
