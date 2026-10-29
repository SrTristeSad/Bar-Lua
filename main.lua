-- Bar-Lua: prototipo de arena jogavel + laboratorio de engenharia reversa.
-- O modo jogavel ainda usa mecanicas e visuais temporarios, nao e port 1:1.
local modes = {"Mapas TMX", "Imagens", "Atlas .plist/.bplist", "Configurações", "Animações", "Cenas .csb", "ELF ARM64", "Fluxo ARM64", "Movimento ARM64", "Entity / Box2D", "Contatos ARM64", "Colisores ARM64", "Filtros Box2D", "Teste de movimento", "Habilidades (dados)", "Combate ARM64", "Núcleo de dano ARM64", "HP / Vida ARM64", "Morte / Score ARM64", "Renascimento ARM64", "ReInit ARM64", "Atributos por nível", "Escopo de setor (AABB)", "Filtro de alvos (ARM64)", "Condicoes ARM64", "Predicados ARM64", "Comparacoes ARM64", "Portas de skill ARM64", "Esquema de habilidade", "Listas xconf de habilidade", "Funções CSelfSkill ARM64"}
local tabLabels = {"Mapa", "Img", "Atlas", "Cfg", "Anim", "CSB", "ELF", "Fluxo", "Mov", "Ent", "Cont", "Colis", "Filtro", "Teste", "Skill", "Comb", "Dano", "Vida", "Morte", "Renas", "ReInit", "Níveis", "Escopo", "Alvos", "Cond", "Pred", "Comp", "Gate", "SkillCfg", "Listas", "SelfFn"}
local animationView = require("src.animation_view")
local sceneView = require("src.scene_view")
local nativeView = require("src.native_view")
local flowView = require("src.flow_view")
local movementView = require("src.movement_view")
local entityMoveView = require("src.entity_move_view")
local contactView = require("src.contact_view")
local colliderView = require("src.collider_view")
local filterView = require("src.filter_view")
local playtest = require("src.playtest")
local arenaGame = require("src.arena_game")
local arenaView = require("src.arena_view")
local skillView = require("src.skill_view")
local combatView = require("src.combat_view")
local damageMathView = require("src.damage_math_view")
local heroHurtView = require("src.hero_hurt_view")
local deathView = require("src.death_view")
local rebornView = require("src.reborn_view")
local reinitView = require("src.reinit_view")
local levelAttributesView = require("src.level_attributes_view")
local sectorScopeView = require("src.sector_scope_view")
local sectorFilterView = require("src.sector_filter_view")
local conditionView = require("src.condition_view")
local concreteConditionsView = require("src.concrete_conditions_view")
local compareConditionsView = require("src.compare_conditions_view")
local skillConditionGateView = require("src.skill_condition_gate_view")
local heroSkillSchemaView = require("src.hero_skill_schema_view")
local skillXconfView = require("src.skill_xconf_view")
local selfSkillFlowView = require("src.self_skill_flow_view")
local sceneResources = require("src.scene_resources")
local spriteGeometry = require("src.sprite_geometry")
local mode, selected, search, zoom = 1, 1, "", 1
local lists = {{}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}}
local maps, atlases, animations, scenes, nativeCatalog, flowCatalog, contactCatalog, colliderCatalog, filterCatalog = {}, {}, {}, {}, {}, {}, {}, {}, {}
local sceneResourceIndex = nil
local skillCatalog = {links={},tables={}}
local skillTrace = {}
local combatCatalog = {}
local damageReport = {}
local heroHurtReport = {}
local deathReport = {}
local rebornReport = {}
local reinitReport = {}
local heroLevelCatalog = {groups={}}
local heroAttrReport = {}
local heroSchemaReport = {}
local heroSemanticReport = {}
local sectorScopeReport = {}
local sectorFilterReport = {}
local conditionReport = {}
local concreteConditionsReport = {}
local compareConditionsReport = {}
local skillConditionGateReport = {}
local heroSkillSchemaReport = {}
local skillXconfReport = {}
local selfSkillFlowReport = {}
local imageIndex = {}
local textures, quads = {}, {}
local position = {x = 0, y = 0}
local arenaState, gameplayActive = nil, true
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
    animationView.reset()
    sceneView.reset()
    filterView.reset()
    sectorScopeView.reset()
    sectorFilterView.reset()
    conditionView.reset()
    concreteConditionsView.reset()
    compareConditionsView.reset()
    skillConditionGateView.reset()
    heroSkillSchemaView.reset()
    skillXconfView.reset()
    if mode == 14 then
        for i, m in ipairs(lists[14]) do
            if m.name == 'petisland_01' then selected = i; break end
        end
        local m = lists[14][selected]
        if m then
            local hero = playtest.findHero(animations)
            local ok = playtest.start(m,hero,atlases)
            if not ok then status = playtest.state().error or 'Teste indisponível' end
        end
    end
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
    local tabwidth = (w - 28) / #modes
    for i, name in ipairs(modes) do
        local x = 14 + (i - 1) * tabwidth
        if i == mode then background(x - 3, 49, tabwidth - 6, 31, {0.28, 0.37, 0.46}) end
        local label = tabLabels[i]
        put(label, x + math.max(2, (tabwidth-small:getWidth(label)) / 2), 55, {0.94, 0.94, 1}, small)
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
    put("↑↓: selecionar  •  Ctrl+L: níveis  •  Ctrl+I: reInit  •  Ctrl+P: teste  •  Ctrl+E: escopo  •  Ctrl+Q: alvos", 13, h - BOTTOM + 7, {0.85, 0.90, 0.96}, small)
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

local function drawMap(map, x, y, w, h, withoutReticle)
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
    if not withoutReticle then
    love.graphics.setColor(0.96, 0.83, 0.32, 0.95)
    love.graphics.circle("line", x + (position.x - left) * scale, y + (position.y - top) * scale, 11)
    love.graphics.line(x + (position.x - left) * scale - 14, y + (position.y - top) * scale,
        x + (position.x - left) * scale + 14, y + (position.y - top) * scale)
    end
    put(string.format("%s  |  %dx%d tiles  |  célula %dx%d  |  zoom %.2fx", map.name, map.width, map.height, tw, th, zoom), x + 12, y + 10, {1, 1, 1}, small)
    if not withoutReticle then
        put("WASD: deslocar câmera  •  roda do mouse: zoom  •  retículo = depuração", x + 12, y + h - 27, {1, 1, 1}, small)
    end
    return {left=left,top=top,scale=scale}
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
        local sw, sh = spriteGeometry.size(f)
        local previewHeight = math.max(15, h - 210)
        local sourceW, sourceH = f.source_w or sw, f.source_h or sh
        local sf = math.max(0.01, math.min(rightW / math.max(sourceW, sw, 1),
            previewHeight / math.max(sourceH, sh, 1), 4))
        love.graphics.push()
        love.graphics.translate(rightX + rightW / 2, y + 119 + previewHeight / 2)
        love.graphics.scale(sf, -sf)
        love.graphics.setLineWidth(1 / sf)
        local lx, ly, rx, ry = spriteGeometry.sourceBounds(f)
        love.graphics.setColor(0.9, 0.72, 0.25, 0.55)
        love.graphics.rectangle("line", lx, ly, rx - lx, ry - ly)
        love.graphics.setColor(1, 1, 1)
        spriteGeometry.draw(img, quad, f)
        local bx, by, ex, ey = spriteGeometry.bounds(f)
        love.graphics.setColor(0.2, 0.94, 0.62, 0.85)
        love.graphics.rectangle("line", bx, by, ex - bx, ey - by)
        love.graphics.pop()
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
    animations = readLua("cache/animations.lua")
    scenes = readLua("cache/scenes.lua")
    nativeCatalog = readLua("reports/native_findings.lua")
    flowCatalog = readLua("reports/native_flow.lua")
    contactCatalog = readLua("reports/native_contacts.lua")
    colliderCatalog = readLua("reports/native_colliders.lua")
    filterCatalog = readLua("reports/native_filters.lua")
    skillCatalog = readLua("cache/skill_catalog.lua")
    skillTrace = readLua("cache/skill_trace.lua")
    combatCatalog = readLua("reports/native_combat.lua")
    damageReport = readLua("reports/damage_math.lua")
    heroHurtReport = readLua("reports/entity_damage_flow.lua")
    deathReport = readLua("reports/death_flow.lua")
    rebornReport = readLua("reports/reborn_flow.lua")
    reinitReport = readLua("reports/reinit_flow.lua")
    heroLevelCatalog = readLua("cache/hero_levels.lua")
    heroAttrReport = readLua("reports/hero_attr_arm64.lua")
    heroSchemaReport = readLua("reports/hero_schema.lua")
    heroSemanticReport = readLua("reports/hero_semantics.lua")
    sectorScopeReport = readLua("reports/sector_scope.lua")
    sectorFilterReport = readLua("reports/sector_filter.lua")
    conditionReport = readLua("reports/condition_flow.lua")
    concreteConditionsReport = readLua("reports/concrete_conditions.lua")
    compareConditionsReport = readLua("reports/compare_conditions.lua")
    skillConditionGateReport = readLua("reports/skill_condition_gate.lua")
    heroSkillSchemaReport = readLua("reports/hero_skill_schema.lua")
    skillXconfReport = readLua("reports/skill_xconf40.lua")
    selfSkillFlowReport = readLua("reports/self_skill_flow.lua")
    for _, map in ipairs(maps) do lists[1][#lists[1]+1] = map end
    scan("assets_original", {png = true, jpg = true, jpeg = true}, lists[2])
    for _, atlas in ipairs(atlases) do lists[3][#lists[3]+1] = atlas end
    scan("assets_original/configdata", {txt = true}, lists[4])
    for _, entry in ipairs(animations) do lists[5][#lists[5]+1] = entry end
    for _, entry in ipairs(scenes) do lists[6][#lists[6]+1] = entry end
    for _, entry in ipairs(nativeCatalog) do lists[7][#lists[7]+1] = entry end
    for _, entry in ipairs(flowCatalog) do lists[8][#lists[8]+1] = entry end
    lists[9][1] = {name="Hero::move_update (vetores)"}
    lists[10][1] = {name="Entity::move (Box2D)"}
    for _,entry in ipairs(contactCatalog) do lists[11][#lists[11]+1] = entry end
    for _,entry in ipairs(colliderCatalog) do lists[12][#lists[12]+1] = entry end
    for _,entry in ipairs(filterCatalog) do lists[13][#lists[13]+1] = entry end
    for _,map in ipairs(maps) do lists[14][#lists[14]+1] = map end
    for _,row in ipairs(skillCatalog.links or {}) do lists[15][#lists[15]+1] = row end
    for _,row in ipairs(combatCatalog) do lists[16][#lists[16]+1] = row end
    lists[17][1] = {name="GetDamageValue: núcleo matemático"}
    lists[18][1] = {name="Hero::addHurtFromEnemy (HP)"}
    lists[19][1] = {name="onDied / dieLogic (morte e pontuação)"}
    lists[20][1] = {name="update / reborn (renascimento)"}
    lists[21][1] = {name="reInit / atributos por nível"}
    for _,row in ipairs(heroLevelCatalog.groups or {}) do lists[22][#lists[22]+1]=row end
    lists[23][1]={name="Busca AABB / ValueType 3"}
    lists[24][1]={name="ReportFixture / candidatos"}
    lists[25][1] = {name="CCondition: filtros de alvo"}
    lists[26][1] = {name="Camp / EntityKind / Buff"}
    lists[27][1] = {name="SkillEntity / ValueCompare"}
    lists[28][1] = {name="CSkill: portas de criador e alvo"}
    lists[29][1] = {name="HeroSkillConfig: esquema nativo"}
    lists[30][1] = {name="HeroSkillConfig: vetores xconf"}
    lists[31][1] = {name="CSelfSkill: funcoes e ciclo de vida"}
    for _, path in ipairs(lists[2]) do
        imageIndex[path:gsub("^assets_original/", ""):lower()] = path:gsub("^assets_original/", "")
    end
    sceneResourceIndex = sceneResources.build(atlases, imageIndex)
    sceneView.setCatalog(scenes)
    table.sort(lists[2]); table.sort(lists[4])
    if #maps == 0 then
        status = "Execute o extrator do APK e o preparador Python conforme README."
    else
        status = string.format("Recursos: %d mapas, %d imagens, %d atlas, %d configs, %d animações, %d cenas CSB.",
            #maps, #lists[2], #atlases, #lists[4], #animations, #scenes)
        for i, item in ipairs(maps) do if item.name == "petisland_01" then selected = i; break end end
        local map = activeMap()
        if map then position.x = map.width * map.tilewidth / 2; position.y = map.height * map.tileheight / 2 end
    end
    arenaState = arenaGame.new()
end

function love.update(dt)
    if gameplayActive then
        local kb = love.keyboard
        arenaGame.update(arenaState, dt, {
            up=kb.isDown("w","up"), down=kb.isDown("s","down"),
            left=kb.isDown("a","left"), right=kb.isDown("d","right")
        })
        return
    end
    if mode == 14 then
        playtest.update(dt, function(key) return love.keyboard.isDown(key) end)
        local px,py = playtest.playerPosition()
        if px then position.x,position.y=px,py end
    end
    if mode == 5 then animationView.update(dt) end
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
    if gameplayActive then
        arenaView.draw(arenaState, love.graphics.getDimensions())
        return
    end
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
    elseif mode == 5 and item then
        animationView.draw(item, atlases, {x = x, y = y, w = pw, h = ph,
            put = put, background = background, imageFor = imageFor,
            spriteQuad = spriteQuad, small = small})
    elseif mode == 6 and item then
        sceneView.draw(item, {x=x, y=y, w=pw, h=ph,
            put=put, background=background, small=small,
            resolveResource=function(resource)
                local found = sceneResources.find(sceneResourceIndex, resource)
                if not found then return nil end
                if found.kind == 'image' then
                    local image = imageFor(found.path)
                    return image and {kind='image',image=image} or nil
                end
                local image = imageFor(found.atlas.image)
                local quad = image and spriteQuad(found.atlas, found.frame, image)
                return quad and {kind='atlas',image=image,quad=quad,frame=found.frame} or nil
            end})
    elseif mode == 7 and item then
        nativeView.draw(item, {x=x, y=y, w=pw, h=ph,
            put=put, background=background, small=small})
    elseif mode == 8 and item then
        flowView.draw(item, {x=x, y=y, w=pw, h=ph,
            put=put, background=background, small=small})
    elseif mode == 9 then
        movementView.draw(item, {x=x, y=y, w=pw, h=ph, put=put, background=background, small=small})
    elseif mode == 10 then
        entityMoveView.draw(item, {x=x, y=y, w=pw, h=ph, put=put, background=background, small=small})
    elseif mode == 11 then
        contactView.draw(item, {x=x, y=y, w=pw, h=ph, put=put, background=background, small=small})
    elseif mode == 12 then
        colliderView.draw(item, {x=x, y=y, w=pw, h=ph, put=put, background=background, small=small})
    elseif mode == 13 then
        filterView.draw(item, {x=x, y=y, w=pw, h=ph, put=put, background=background, small=small})
    elseif mode == 15 then
        skillView.draw(item,{x=x,y=y,w=pw,h=ph,put=put,background=background,small=small},skillCatalog.tables,skillTrace)
    elseif mode == 31 then
        selfSkillFlowView.draw(selfSkillFlowReport,{x=x,y=y,w=pw,h=ph,put=put,background=background,small=small})
    elseif mode == 30 then
        skillXconfView.draw(skillXconfReport,{x=x,y=y,w=pw,h=ph,put=put,background=background,small=small})
    elseif mode == 29 then
        heroSkillSchemaView.draw(heroSkillSchemaReport,{x=x,y=y,w=pw,h=ph,put=put,background=background,small=small})
    elseif mode == 28 then
        skillConditionGateView.draw(skillConditionGateReport,{x=x,y=y,w=pw,h=ph,put=put,background=background,small=small})
    elseif mode == 27 then
        compareConditionsView.draw(compareConditionsReport,{x=x,y=y,w=pw,h=ph,put=put,background=background,small=small})
    elseif mode == 26 then
        concreteConditionsView.draw(concreteConditionsReport,{x=x,y=y,w=pw,h=ph,put=put,background=background,small=small})
    elseif mode == 25 then
        conditionView.draw(conditionReport,{x=x,y=y,w=pw,h=ph,put=put,background=background,small=small})
    elseif mode == 24 then
        sectorFilterView.draw(sectorFilterReport,{x=x,y=y,w=pw,h=ph,put=put,background=background,small=small})
    elseif mode == 23 then
        sectorScopeView.draw(sectorScopeReport,{x=x,y=y,w=pw,h=ph,put=put,background=background,small=small})
    elseif mode == 22 then
        levelAttributesView.draw(item,heroAttrReport,{x=x,y=y,w=pw,h=ph,put=put,background=background,small=small},heroSchemaReport,heroSemanticReport)
    elseif mode == 21 then
        reinitView.draw(reinitReport,{x=x,y=y,w=pw,h=ph,put=put,background=background,small=small})
    elseif mode == 20 then
        rebornView.draw(rebornReport,{x=x,y=y,w=pw,h=ph,put=put,background=background,small=small})
    elseif mode == 19 then
        deathView.draw(deathReport,{x=x,y=y,w=pw,h=ph,put=put,background=background,small=small})
    elseif mode == 18 then
        heroHurtView.draw(heroHurtReport,{x=x,y=y,w=pw,h=ph,put=put,background=background,small=small})
    elseif mode == 17 then
        damageMathView.draw(damageReport,{x=x,y=y,w=pw,h=ph,put=put,background=background,small=small})
    elseif mode == 16 then
        combatView.draw(item,{x=x,y=y,w=pw,h=ph,put=put,background=background,small=small})
    elseif mode == 14 and item then
        local camera = drawMap(item,x,y,pw,ph,true)
        playtest.draw({x=x,y=y,w=pw,h=ph},camera,
            {put=put,small=small,imageFor=imageFor,spriteQuad=spriteQuad})
    else
        local message = (mode == 1 or mode == 3) and "Sem dados preparados. Execute tools/preparar_recursos.py." or "Nenhum recurso encontrado. Extraia o APK para assets_original."
        put(message, x + 18, y + 40)
    end
end

function love.keypressed(key)
    if gameplayActive then
        if key == "escape" then gameplayActive = false
        elseif key == "space" or key == "j" then arenaGame.attack(arenaState)
        elseif key == "r" then arenaState = arenaGame.new()
        elseif key == "p" then arenaGame.togglePause(arenaState)
        end
        return
    end
    if (key == "return" or key == "kpenter") and love.keyboard.isDown("lctrl","rctrl") then
        arenaState = arenaGame.new()
        gameplayActive = true
        return
    end
    if key == 'p' and love.keyboard.isDown('lctrl','rctrl') then setMode(14); return end
    if key == 'h' and love.keyboard.isDown('lctrl','rctrl') then setMode(15); return end
    if key == 'd' and love.keyboard.isDown('lctrl','rctrl') then setMode(16); return end
    if key == 'm' and love.keyboard.isDown('lctrl','rctrl') then setMode(17); return end
    if key == 'v' and love.keyboard.isDown('lctrl','rctrl') then setMode(18); return end
    if key == 'n' and love.keyboard.isDown('lctrl','rctrl') then setMode(19); return end
    if key == 'b' and love.keyboard.isDown('lctrl','rctrl') then setMode(20); return end
    if key == 'i' and love.keyboard.isDown('lctrl','rctrl') then setMode(21); return end
    if key == 'l' and love.keyboard.isDown('lctrl','rctrl') then setMode(22); return end
    if key == 'e' and love.keyboard.isDown('lctrl','rctrl') then setMode(23); return end
    if key == 'q' and love.keyboard.isDown('lctrl','rctrl') then setMode(24); return end
    if key == 'j' and love.keyboard.isDown('lctrl','rctrl') then setMode(25); return end
    if key == 'u' and love.keyboard.isDown('lctrl','rctrl') then setMode(26); return end
    if key == 'y' and love.keyboard.isDown('lctrl','rctrl') then setMode(27); return end
    if key == 'g' and love.keyboard.isDown('lctrl','rctrl') then setMode(28); return end
    if key == 's' and love.keyboard.isDown('lctrl','rctrl') then setMode(29); return end
    if key == 'k' and love.keyboard.isDown('lctrl','rctrl') then setMode(30); return end
    if key == 't' and love.keyboard.isDown('lctrl','rctrl') then setMode(31); return end
    if mode == 14 then
        if key == 'r' then
            local ok=playtest.start(selectedItem(),playtest.findHero(animations),atlases)
            if not ok then status=playtest.state().error or 'Erro físico' end
            return
        elseif key == 'o' then playtest.toggleMapObjects();return
        elseif key == 'g' then playtest.toggleMapCollision();return
        elseif key == 'j' then playtest.triggerAttack(1);return
        elseif key == 'k' then playtest.triggerAttack(2);return
        elseif key == 'l' then playtest.triggerAttack(3);return
        elseif key == 'c' then playtest.toggleDebug();return
        elseif key:match('^[1-5]$') then playtest.setVariant(tonumber(key)-1);return
        elseif key == 'up' or key == 'down' or key == 'left' or key == 'right' then return end
    end
    -- A maioria dos teclados não possui F13; Ctrl+F12 abre a aba 13.
    if key == "f12" and love.keyboard.isDown("lctrl", "rctrl") then setMode(13); return end
    local n = tonumber(key:match("^f(%d+)$"))
    if n and n >= 1 and n <= #modes then setMode(n); return end
    if mode == 17 and damageMathView.keypressed(key) then return end
    if mode == 18 and heroHurtView.keypressed(key) then return end
    if mode == 19 and deathView.keypressed(key) then return end
    if mode == 20 and rebornView.keypressed(key) then return end
    if mode == 21 and reinitView.keypressed(key) then return end
    if mode == 22 and levelAttributesView.keypressed(key) then return end
    if mode == 23 and sectorScopeView.keypressed(key) then return end
    if mode == 24 and sectorFilterView.keypressed(key) then return end
    if mode == 25 and conditionView.keypressed(key) then return end
    if mode == 26 and concreteConditionsView.keypressed(key) then return end
    if mode == 27 and compareConditionsView.keypressed(key) then return end
    if mode == 28 and skillConditionGateView.keypressed(key) then return end
    if mode == 29 and heroSkillSchemaView.keypressed(key) then return end
    if mode == 30 and skillXconfView.keypressed(key) then return end
    if mode == 31 and selfSkillFlowView.keypressed(key) then return end
    if mode == 13 and filterView.keypressed(key) then return end
    if mode == 10 and entityMoveView.keypressed(key) then return end
    if mode == 9 and movementView.keypressed(key) then return end
    local list = visibleList()
    if mode == 6 then
        if key == "tab" then sceneView.next(selectedItem(), love.keyboard.isDown("lshift", "rshift") and -1 or 1); return end
        if key == "return" or key == "kpenter" then
            local ok, reason = sceneView.openReference(selectedItem())
            if not ok then status = reason or 'A subcena não está disponível' end
            return
        end
        if key == "backspace" and sceneView.depth(selectedItem())>0 then
            sceneView.back(selectedItem()); return
        end
        if key == "h" then sceneView.cycleButton(selectedItem()); return end
        if key == "g" then sceneView.toggleGuides(); return end
        if key == "v" then sceneView.toggleHidden(); return end
        if key == "t" then sceneView.toggleText(); return end
    end
    if mode == 5 then
        if key == "space" then animationView.toggle(); return end
        if key == "i" then animationView.toggleInterpolate(); return end
        if key == "b" then animationView.toggleBind(); return end
        if key == "p" then animationView.toggleGuides(); return end
        if key == "left" then animationView.step(selectedItem(), -1); return end
        if key == "right" then animationView.step(selectedItem(), 1); return end
        if key == "tab" then
            animationView.changeMovement(selectedItem(), love.keyboard.isDown("lshift", "rshift") and -1 or 1)
            return
        end
    end
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
    if mode == 5 then animationView.reset() end
    if mode == 6 then sceneView.reset() end
end

function love.textinput(text)
    if gameplayActive then return end
    -- WASD no mapa é controle da câmera, não texto de busca.
    if mode == 3 and (text == "[" or text == "]") then return end
    if mode == 5 and (text:lower() == "i" or text:lower() == "b" or text:lower() == "p") then return end
    if mode == 6 and (text:lower() == "g" or text:lower() == "v" or text:lower() == "t") then return end
    if mode == 9 or mode == 10 or mode == 13 or mode == 14 or mode == 16 or mode == 17 or mode == 18 or mode == 19 or mode == 20 or mode == 21 or mode == 22 or mode == 23 or mode == 24 or mode == 25 or mode == 26 or mode == 27 or mode == 28 or mode == 29 or mode == 30 then return end
    if mode ~= 1 and #search < 80 and text:match("%g") then search = search .. text; selected = 1; resetImage(); if mode == 5 then animationView.reset() end; if mode == 6 then sceneView.reset() end end
end

function love.wheelmoved(_, dy)
    if gameplayActive then return end
    if dy ~= 0 then zoom = math.max(0.12, math.min(8, zoom * (dy > 0 and 1.18 or 1 / 1.18))) end
end

function love.mousepressed(x, y, button)
    if gameplayActive then
        if button == 1 then arenaGame.attack(arenaState) end
        return
    end
    if button ~= 1 then return end
    -- Todas as abas são acessíveis por clique no cabeçalho, inclusive F13.
    if y >= 49 and y < 80 and x >= 14 then
        local w = love.graphics.getDimensions()
        local i = math.floor((x - 14) / ((w - 28) / #modes)) + 1
        if i >= 1 and i <= #modes then setMode(i); return end
    end
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
    if mode == 6 and x >= SIDE then
        sceneView.pick(selectedItem(), x, y)
        return
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
        if mode == 5 then animationView.reset() end
        if mode == 6 then sceneView.reset() end
        if mode == 14 then
            local ok=playtest.start(selectedItem(),playtest.findHero(animations),atlases)
            if not ok then status=playtest.state().error or 'Erro físico' end
        end
        local map = activeMap()
        if map then position.x, position.y = map.width * map.tilewidth / 2, map.height * map.tileheight / 2 end
    end
end
