-- Resolve referencias de imagens CSB aos PNGs avulsos ou frames de atlas.
-- Nao tenta adivinhar um sprite homonimo: entradas duplicadas sao ambiguas.
local M = {}

local function normalize(s)
    return (s or ''):gsub('\\', '/'):gsub('^%./', ''):lower()
end
local function keyFor(atlas, frame)
    local stem = normalize(atlas.path):gsub('%.b?plist$', '')
    return stem .. '/' .. normalize(frame.name)
end
local function insert(index, key, item)
    if index[key] == nil then index[key] = item
    elseif index[key] ~= item then index[key] = false end
end

function M.build(atlases, imageIndex)
    local index = {frames = {}, images = {}}
    for _, atlas in ipairs(atlases or {}) do
        for _, frame in ipairs(atlas.frames or {}) do
            insert(index.frames, keyFor(atlas, frame), {atlas = atlas, frame = frame})
        end
    end
    for path, actual in pairs(imageIndex or {}) do
        insert(index.images, normalize(path), actual)
    end
    return index
end

function M.find(index, resource)
    if type(resource) ~= 'table' or type(resource.path) ~= 'string' or resource.path == '' then return nil end
    -- O APK usa ResourceData.type=0 para referencia por caminho. Nunca tratar
    -- um tipo desconhecido como uma imagem aleatoria do atlas.
    if resource.type ~= 0 and resource.type ~= nil then return nil end
    local name = normalize(resource.path)
    local path = index.images[name]
    if path then return {kind = 'image', path = path} end
    local frame = index.frames[name]
    if frame then return {kind = 'atlas', atlas = frame.atlas, frame = frame.frame} end
    return nil
end
return M
