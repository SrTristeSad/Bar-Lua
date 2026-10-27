-- Fase 10: resolve referências EXPLÍCITAS de ProjectNode para cenas CSB.
-- O caminho vem do FlatBuffers original: não infere rotas ou callbacks.
local M = {}
local function normalize(path)
    if type(path) ~= 'string' or #path > 512 then return nil end
    path = path:gsub('\\', '/'):lower():gsub('^%./', ''):gsub('^assets_original/', '')
    if path == '' or path == '.csb' or not path:match('%.csb$') then return nil end
    if path:sub(1,1)=='/' or path:find('//',1,true) then return nil end
    for part in path:gmatch('[^/]+') do
        if part == '.' or part == '..' then return nil end
    end
    return path
end
M.normalize = normalize
function M.build(scenes)
    local index = {}
    for _, scene in ipairs(scenes or {}) do
        local key=normalize(scene.path)
        if key then
            if index[key] == nil then index[key]=scene else index[key]=false end
        end
    end
    return index
end
function M.find(index, reference)
    local key = normalize(reference)
    if not key then return nil, 'Referência vazia ou inválida' end
    if not index then return nil, 'Catálogo indisponível' end
    local result = index[key]
    if result == false then return nil, 'Caminho ambíguo' end
    if not result then return nil, 'Cena não encontrada no APK' end
    return result
end
return M
