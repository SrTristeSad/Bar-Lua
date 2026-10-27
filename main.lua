-- Bar-Lua | laboratório de engenharia reversa do BarbarQ 1.0.1811.
-- NÃO é o jogo: apenas visualização fiel de dados originais decodificados.
local modes = {"Mapas TMX", "Imagens", "Atlas .plist/.bplist", "Configurações"}
local mode, selected, search, zoom = 1, 1, "", 1
local lists = {{}, {}, {}, {}}
local maps, atlases = {}, {}
local textures, quads = {}, {}
local position = {x = 0, y = 0}
local frameIndex = 1
local atlasClick = nil
local font, small, titlefont
local status, currentImage, currentImagePath = "", nil, nil
local SIDE, TOP, BOTTOM = 310, 92, 58

local function readLua(file)
    if not love.filesystem.getInfo(file) then return {} end
    local chunk, err = love.filesystem.load(file)
    if not chunk then status = tostring(err); return {} end
    local ok, data = pcall(chunk)
    if not ok or type(data) ~= "table" then status = tostring(data); return {} end
    return data
end

local function scan(folder, ext, target)
    if not love.filesystem.getInfo(folder, "directory") then return end
    for _, name in ipairs(love.filesystem.getDirectoryItems(folder)) do
        local path = folder .. "/" .. name
        local info = love.filesystem.getInfo(path)
        if info and info.type == "directory" then
            scan(path, ext, target)
        elseif info and info.type == "file" then
            local extension = path:match("%.([^%.]+)$")
            if extension and ext[extension:lower()] then target[#target+1] = path end
        end
    end
end

local function resetImage()
    currentImage, currentImagePath = nil, nil
    frameIndex, atlasClick = 1, nil
end

local function setMode(index)
    mode = index
    selected, search, zoom = 1, "", 1
    position.x, position.y = 0, 0
    resetImage()
end

local function visibleList()
    local result, needle = {}, search:lower()
    for _, item in ipairs(lists[mode]) do
        local label = type(item) == "table" and (item.path or item.name) or item
        if needle == "" or label:lower():find(needle, 1, true) then
            result[#result+1] = item
        end
    end
    return result
end

local function imageFor(path)
    if not path then return nil end
    local full = "assets_original/" .. path
    local cached = textures[full]
    if cached ~= nil then return cached or nil end
    local ok, img = pcall(love.graphics.newImage, full)
    if not ok then
        textures[full] = false
        return nil
    end
    img:setFilter("nearest", "nearest")
    textures[full] = img
    return img
end

local function selectedItem()
    return visibleList()[selected]
end

local function activeMap()
    return mode == 1 and selectedItem() or nil
end

local function put(s, x, y, c, f)
    c = c or {0.91, 0.93, 0.97}
    love.graphics.setColor(c)
    love.graphics.setFont(f or font)
    love.graphics.print(tostring(s), x, y)
end

local function background(x, y, w, h, color)
    love.graphics.setColor(color)
    love.graphics.rectangle("fill", x, y, w, h)
end

local function getPanel(w, h)
    return SIDE + 10, TOP + 10, w - SIDE - 20, h - TOP - BOTTOM - 15
end

local function drawShell(w, h, list)
    background(0, 0, w, h, {0.06, 0.08, 0.11})
    background(0, 0, w, TOP, {0.12, 0.16, 0.20})
    put("Bar-Lua  •  BarbarQ 1.0.1811  •  pesquisa, NÃO jogável", 14, 10, {1, 1, 1}, titlefont)
    for i, name in ipairs(modes) do
        local x = 14 + (i - 1) * 155
        if i == mode then background(x - 3, 49, 145, 31, {0.28, 0.37, 0.46}) end
        put("F" .. i .. "  " .. name, x, 55, {0.94, 0.94, 1}, small)
    end
    background(0, TOP, SIDE, h - TOP, {0.10, 0.13, 0.17})
    put("Filtrar: " .. search .. "_", 12, TOP + 10, {1, 0.82, 0.44}, small)
    put(#list .. " itens", 12, TOP + 36, {0.66, 0.77, 0.85}, small)
    local visible = math.max(1, math.floor((h - TOP - BOTTOM - 73) / 26))
    local first = math.max(1, math.min(selected - math.floor(visible / 2), math.max(1, #list - visible + 1)))
    for i = first, math.min(#list, first + visible - 1) do
        local y = TOP + 65 + (i - first) * 26
        if i == selected then background(6, y - 2, SIDE - 12, 25, {0.24, 0.32, 0.40}) end
        local item = list[i]
        local label = type(item) == "table" and (item.name or item.path) or item
        label = label:gsub("^assets_original/", "")
        if #label > 41 then label = "…" .. label:sub(-38) end
        put(label, 13, y, i == selected and {1, 1, 1} or {0.74, 0.80, 0.84}, small)
    end
    background(0, h - BOTTOM, w, BOTTOM, {0.12, 0.16, 0.20})
    put("↑↓: escolher atlas  •  [ ]: sprite  •  F1–F4: painel  •  Esc: limpar", 13, h - BOTTOM + 7, {0.85, 0.90, 0.96}, small)
    put(status, 13, h - BOTTOM + 29, {0.72, 0.80, 0.87}, small)
end

local function expandRuns(layer, width, height)
    if layer.tiles then return layer.tiles end
    local tiles, pos = {}, 1
    for _, run in ipairs(layer.runs) do
        for _ = 1, run[2] do tiles[pos] = run[1]; pos = pos + 1 end
    end
    if pos ~= width * height + 1 then error("Camada TMX corrompida: contagem de GIDs") end
    layer.tiles = tiles
    return tiles
end

local function tileQuad(ts, gid, img)
    local tilesetId = gid - ts.firstgid
    local cols = ts.columns
    if cols <= 0 then cols = math.floor((img:getWidth() - ts.margin * 2 + ts.spacing) / (ts.tilewidth + ts.spacing)) end
    if cols <= 0 or tilesetId < 0 then return nil end
    local key = ts.image .. ":" .. tilesetId
    if quads[key] then return quads[key] end
    local x = ts.margin + (tilesetId % cols) * (ts.tilewidth + ts.spacing)
    local y = ts.margin + math.floor(tilesetId / cols) * (ts.tileheight + ts.spacing)
    if x + ts.tilewidth > img:getWidth() or y + ts.tileheight > img:getHeight() then return nil end
    quads[key] = love.graphics.newQuad(x, y, ts.tilewidth, ts.tileheight, img:getDimensions())
    return quads[key]
end

local function drawMap(map, x, y, w, h)
    background(x, y, w, h, {0.14, 0.18, 0.18})
    -- Exibe apenas tiles visíveis: mapas 128x128 não geram 16.384 draw calls por quadro.
    local scale = zoom
    local tw, th = map.tilewidth, map.tileheight
    local worldW, worldH = map.width * tw, map.height * th
    local viewW, viewH = w / scale, h / scale
    position.x = math.max(0, math.min(worldW, position.x))
    position.y = math.max(0, math.min(worldH, position.y))
    local left = position.x - viewW / 2
    local top = position.y - viewH / 2
    if worldW >= viewW then left = math.max(0, math.min(left, worldW - viewW)) end
    if worldH >= viewH then top = math.max(0, math.min(top, worldH - viewH)) end
    local c1, c2 = math.max(0, math.floor(left / tw)), math.min(map.width - 1, math.ceil((left + viewW) / tw))
    local r1, r2 = math.max(0, math.floor(top / th)), math.min(map.height - 1, math.ceil((top + viewH) / th))
    love.graphics.setScissor(x, y, w, h)
    for _, layer in ipairs(map.layers) do
        local cells = expandRuns(layer, map.width, map.height)
        for row = r1, r2 do
            for col = c1, c2 do
                local gid = cells[row * map.width + col + 1] or 0
                -- Tiled: três flags de espelhamento nos bits 31..29; nesta etapa elas são removidas.
                gid = gid % 536870912
                if gid > 0 then
                    local ts
                    for ti = #map.tilesets, 1, -1 do
                        if gid >= map.tilesets[ti].firstgid then ts = map.tilesets[ti]; break end
                    end
                    if ts then
                        local img = imageFor(ts.image)
                        if img then
                            local quad = tileQuad(ts, gid, img)
                            if quad then
                                love.graphics.setColor(1, 1, 1)
                                love.graphics.draw(img, quad, x + (col * tw - left) * scale, y + (row * th - top) * scale, 0,
                                    scale * tw / ts.tilewidth, scale * th / ts.tileheight)
                            end
                        end
                    end
                end
            end
        end
    end
    love.graphics.setScissor()
    -- Retículo de depuração da câmera; NÃO representa personagem/colisão do BarbarQ.
    love.graphics.setColor(0.96, 0.83, 0.32, 0.95)
    love.graphics.circle("line", x + (position.x - left) * scale, y + (position.y - top) * scale, 11)
    love.graphics.line(x + (position.x - left) * scale - 14, y + (position.y - top) * scale,
        x + (position.x - left) * scale + 14, y + (position.y - top) * scale)
    put(string.format("%s  |  %dx%d tiles  |  célula %dx%d  |  zoom %.2fx", map.name, map.width, map.height, tw, th, zoom), x + 12, y + 10, {1, 1, 1}, small)
    put("WASD: deslocar câmera  •  roda do mouse: zoom  •  retículo = depuração", x + 12, y + h - 27, {1, 1, 1}, small)
end

local function drawImage(item, x, y, w, h)
    local path = type(item) == "string" and item:gsub("^assets_original/", "") or item.image
    if path ~= currentImagePath then
        currentImagePath, currentImage = path, imageFor(path)
    end
    background(x, y, w, h, {0.16, 0.19, 0.22})
    if not currentImage then put("Textura ausente: " .. (path or "?"), x + 22, y + 45); return end
    local iw, ih = currentImage:getDimensions()
    local fit = math.min((w - 40) / iw, (h - 100) / ih, 2) * zoom
    love.graphics.setColor(1, 1, 1)
    love.graphics.draw(currentImage, x + w / 2, y + h / 2, 0, fit, fit, iw / 2, ih / 2)
    put(string.format("%s  |  %d×%d  |  zoom %.2fx", path, iw, ih, zoom), x + 12, y + h - 30, {1, 1, 1}, small)
end

local function atlasViewport(img, x, y, w, h)
    local iw, ih = img:getDimensions()
    local fit = math.min((w - 24) / iw, (h - 80) / ih, 2) * zoom
    return x + w / 2 - iw * fit / 2, y + h / 2 - ih * fit / 2, fit
end

local function spriteQuad(atlas, f, img)
    local iw, ih = img:getDimensions()
    if f.x < 0 or f.y < 0 or f.w < 1 or f.h < 1 or
       f.x + f.w > iw or f.y + f.h > ih then return nil end
    local key = atlas.path .. ":" .. f.x .. ":" .. f.y .. ":" .. f.w .. ":" .. f.h
    if not quads[key] then
        quads[key] = love.graphics.newQuad(f.x, f.y, f.w, f.h, iw, ih)
    end
    return quads[key]
end

local function drawAtlas(atlas, x, y, w, h)
    background(x, y, w, h, {0.15, 0.18, 0.21})
    atlasClick = nil
    if w < 240 or h < 180 then return end
    local img = imageFor(atlas.image)
    if not img then
        put("Textura não presente neste APK:", x + 20, y + 35, {1, 0.7, 0.48}, small)
        put(atlas.image, x + 20, y + 59, {1, 1, 1}, small)
        put("Os metadados do atlas foram preservados.", x + 20, y + 83, nil, small)
        return
    end
    local iw, ih = img:getDimensions()
    local leftWidth = math.max(130, math.floor(w * 0.52))
    local xx, yy, scale = atlasViewport(img, x, y, leftWidth, h)
    love.graphics.setScissor(x, y + 40, leftWidth, h - 45)
    love.graphics.setColor(1, 1, 1)
    love.graphics.draw(img, xx, yy, 0, scale, scale)
    local n = #atlas.frames
    if n > 0 then
        frameIndex = math.max(1, math.min(n, frameIndex))
        local f = atlas.frames[frameIndex]
        love.graphics.setColor(1, 0.83, 0.26, 1)
        love.graphics.setLineWidth(2)
        love.graphics.rectangle("line", xx + f.x * scale, yy + f.y * scale, f.w * scale, f.h * scale)
        love.graphics.setLineWidth(1)
    end
    love.graphics.setScissor()
    atlasClick = {atlas = atlas, x = xx, y = yy, scale = scale,
                  minx = x, miny = y + 40, maxx = x + leftWidth, maxy = y + h - 5}
    background(x + leftWidth + 5, y + 42, w - leftWidth - 13, h - 85, {0.10, 0.14, 0.17})
    put(string.format("%s  |  %d sprites  |  %dx%d", atlas.kind or "plist", n, iw, ih),
        x + 12, y + 12, {1, 1, 1}, small)
    if n == 0 then return end
    local f = atlas.frames[frameIndex]
    local rightX = x + leftWidth + 18
    local rightW = w - leftWidth - 35
    put(string.format("Sprite %d / %d", frameIndex, n), rightX, y + 57, {1, 0.83, 0.42}, small)
    local label = f.name
    if #label > 35 then label = "..." .. label:sub(-32) end
    put(label, rightX, y + 83, {1, 1, 1}, small)
    local quad = spriteQuad(atlas, f, img)
    if quad then
        local sw, sh = f.w, f.h
        local previewHeight = math.max(15, h - 210)
        local sf = math.min(rightW / sw, previewHeight / sh, 4)
        love.graphics.setColor(1, 1, 1)
        love.graphics.draw(img, quad, rightX + rightW / 2 - sw * sf / 2,
            y + 119 + (previewHeight - sh * sf) / 2, 0, sf, sf)
    end
    put(string.format("Atlas: (%d,%d)  %dx%d", f.x, f.y, f.w, f.h),
        rightX, y + h - 74, {0.75, 0.85, 0.92}, small)
    put(string.format("Origem: %dx%d   Desloc.: %.1f, %.1f", f.source_w or f.w,
        f.source_h or f.h, f.offset_x or 0, f.offset_y or 0),
        rightX, y + h - 51, {0.75, 0.85, 0.92}, small)
    put("[ ] muda sprite • clique no atlas", x + 12, y + h - 25,
        {0.87, 0.89, 0.94}, small)
end

local function drawConfig(path, x, y, w, h)
    background(x, y, w, h, {0.15, 0.18, 0.21})
    local data = love.filesystem.read(path)
    if not data then put("Configuração indisponível.", x + 12, y + 12); return end
    put(path, x + 12, y + 12, {1, 0.82, 0.46}, small)
    local fontWidth = math.max(20, math.floor((w - 36) / 7.3))
    local lines = 0
    for line in (data .. "\n"):gmatch("(.-)\r?\n") do
        if lines >= math.floor((h - 68) / 18) then break end
        local label = #line > fontWidth and line:sub(1, fontWidth) .. "…" or line
        put(label, x + 13, y + 39 + lines * 18, {0.82, 0.89, 0.92}, small)
        lines = lines + 1
    end
    put("Leitura dos dados originais (campos ainda não interpretados).", x + 12, y + h - 27, {0.75, 0.83, 0.89}, small)
end

function love.load()
    love.graphics.setDefaultFilter("nearest", "nearest")
    font, small, titlefont = love.graphics.newFont(16), love.graphics.newFont(13), love.graphics.newFont(21)
    maps = readLua("cache/maps.lua")
    atlases = readLua("cache/atlases.lua")
    for _, map in ipairs(maps) do lists[1][#lists[1]+1] = map end
    scan("assets_original", {png = true, jpg = true, jpeg = true}, lists[2])
    for _, atlas in ipairs(atlases) do lists[3][#lists[3]+1] = atlas end
    scan("assets_original/configdata", {txt = true}, lists[4])
    table.sort(lists[2]); table.sort(lists[4])
    if #maps == 0 then
        status = "Execute o extrator do APK e o preparador Python conforme README."
    else
        status = string.format("Recursos locais: %d mapas, %d imagens, %d atlas, %d configs.",
            #maps, #lists[2], #atlases, #lists[4])
        for i, item in ipairs(maps) do if item.name == "petisland_01" then selected = i; break end end
        local map = activeMap()
        if map then position.x = map.width * map.tilewidth / 2; position.y = map.height * map.tileheight / 2 end
    end
end

function love.update(dt)
    local map = activeMap()
    if map then
        local speed = 500 / zoom * math.min(dt, 0.08)
        if love.keyboard.isDown("w") or love.keyboard.isDown("up") then position.y = position.y - speed end
        if love.keyboard.isDown("s") or love.keyboard.isDown("down") then position.y = position.y + speed end
        if love.keyboard.isDown("a") then position.x = position.x - speed end
        if love.keyboard.isDown("d") then position.x = position.x + speed end
    end
end

function love.draw()
    local w, h = love.graphics.getDimensions()
    local list = visibleList()
    drawShell(w, h, list)
    local x, y, pw, ph = getPanel(w, h)
    if pw <= 10 or ph <= 10 then return end
    local item = list[selected]
    if mode == 1 and item then drawMap(item, x, y, pw, ph)
    elseif mode == 2 and item then drawImage(item, x, y, pw, ph)
    elseif mode == 3 and item then drawAtlas(item, x, y, pw, ph)
    elseif mode == 4 and item then drawConfig(item, x, y, pw, ph)
    else
        local message = (mode == 1 or mode == 3) and "Sem dados preparados. Execute tools/preparar_recursos.py." or "Nenhum recurso encontrado. Extraia o APK para assets_original."
        put(message, x + 18, y + 40)
    end
end

function love.keypressed(key)
    local n = key:match("^f([1-4])$")
    if n then setMode(tonumber(n)); return end
    local list = visibleList()
    if key == "escape" then search, selected = "", 1
    elseif key == "backspace" then search = search:sub(1, -2); selected = 1
    elseif key == "down" and mode ~= 1 then selected = math.min(#list, selected + 1)
    elseif key == "up" and mode ~= 1 then selected = math.max(1, selected - 1)
    elseif key == "pageup" then selected = math.max(1, selected - 10)
    elseif key == "pagedown" then selected = math.min(#list, selected + 10)
    elseif key == "home" then selected = #list > 0 and 1 or 0
    elseif key == "end" then selected = #list
    elseif mode == 3 and (key == "[" or key == "leftbracket") then
        local atlas = selectedItem()
        if atlas then frameIndex = math.max(1, frameIndex - 1) end
        return
    elseif mode == 3 and (key == "]" or key == "rightbracket") then
        local atlas = selectedItem()
        if atlas then frameIndex = math.min(#atlas.frames, frameIndex + 1) end
        return
    end
    if mode ~= 1 then resetImage() end
end

function love.textinput(text)
    -- WASD no mapa é controle da câmera, não texto de busca.
    if mode == 3 and (text == "[" or text == "]") then return end
    if mode ~= 1 and #search < 80 and text:match("%g") then search = search .. text; selected = 1; resetImage() end
end

function love.wheelmoved(_, dy)
    if dy ~= 0 then zoom = math.max(0.12, math.min(8, zoom * (dy > 0 and 1.18 or 1 / 1.18))) end
end

function love.mousepressed(x, y, button)
    if button ~= 1 then return end
    if mode == 3 and atlasClick and atlasClick.atlas == selectedItem() then
        local a = atlasClick
        if x >= a.minx and x < a.maxx and y >= a.miny and y <= a.maxy then
            local tx = (x - a.x) / a.scale
            local ty = (y - a.y) / a.scale
            -- Seleciona o último frame sobreposto, se houver.
            for index, f in ipairs(a.atlas.frames) do
                if tx >= f.x and tx < f.x + f.w and ty >= f.y and ty < f.y + f.h then
                    frameIndex = index
                end
            end
            return
        end
    end
    if x > SIDE or y < TOP + 65 then return end
    local _, h = love.graphics.getDimensions()
    local list = visibleList()
    local visible = math.max(1, math.floor((h - TOP - BOTTOM - 73) / 26))
    local first = math.max(1, math.min(selected - math.floor(visible / 2), math.max(1, #list - visible + 1)))
    local idx = first + math.floor((y - (TOP + 65)) / 26)
    if idx >= 1 and idx <= #list then
        selected = idx
        resetImage()
        local map = activeMap()
        if map then position.x, position.y = map.width * map.tilewidth / 2, map.height * map.tileheight / 2 end
    end
end