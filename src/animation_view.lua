-- Laboratório visual de keyframes Cocos Studio, não renderizador definitivo.
-- Coordenadas, escala e indexação foram recuperadas do APK. Hierarquia,
-- tweening, skew, orientações especiais e blending aguardam validação.
local pose = require("src.pose")
local M = {movement = 1, time = 0, running = true, interpolate = true, useBind = true}
local spriteLookup
local lastAnimation

local function dirname(path)
    return path:match("^(.*)/[^/]+$") or ""
end

local function findMovements(asset)
    if not asset or not asset.animations then return {} end
    local result = {}
    for _, animation in ipairs(asset.animations) do
        for _, movement in ipairs(animation.movements or {}) do
            result[#result + 1] = {name = animation.name .. " / " .. movement.name, data = movement}
        end
    end
    return result
end

local function active(asset)
    local movements = findMovements(asset)
    if #movements == 0 then return nil, movements end
    M.movement = math.max(1, math.min(M.movement, #movements))
    return movements[M.movement], movements
end

function M.reset()
    M.movement, M.time, M.running = 1, 0, true
    lastAnimation = nil
end

function M.update(dt)
    if M.running then
        -- 30 quadros/s é a frequência da PRÉVIA, não a velocidade certificada do jogo.
        M.time = M.time + math.min(dt, 0.08) * 30
    end
end

function M.toggle()
    M.running = not M.running
end

function M.toggleInterpolate()
    M.interpolate = not M.interpolate
end

function M.toggleBind()
    M.useBind = not M.useBind
end

function M.step(asset, delta)
    local item = active(asset)
    if item then
        M.running = false
        local duration = math.max(1, item.data.duration)
        M.time = (math.floor(M.time) + delta) % duration
    end
end

function M.changeMovement(asset, delta)
    local _, moves = active(asset)
    if #moves == 0 then return end
    M.movement = ((M.movement - 1 + delta) % #moves) + 1
    M.time = 0
end

local function indexAtlases(atlases)
    local lookup = {}
    -- Entrada específica do diretório tem prioridade. Nomes globais só são
    -- usados quando não há colisão, evitando associações arbitrárias.
    local glob, ambiguous = {}, {}
    for _, atlas in ipairs(atlases) do
        local folder = dirname(atlas.path)
        for _, f in ipairs(atlas.frames) do
            local key = folder .. "/" .. f.name
            lookup[key] = {atlas = atlas, frame = f}
            if glob[f.name] then ambiguous[f.name] = true
            else glob[f.name] = {atlas = atlas, frame = f} end
        end
    end
    for name in pairs(ambiguous) do glob[name] = nil end
    return lookup, glob
end

local function spriteBox(matrix, f)
    -- Bounding box calculada com a transformação afim, incluindo skew.
    local ox, oy = f.offset_x or 0, f.offset_y or 0
    local x1, y1 = -f.w / 2 + ox, -f.h / 2 + oy
    local x2, y2 = x1 + f.w, y1 + f.h
    local minx, maxx, miny, maxy = math.huge, -math.huge, math.huge, -math.huge
    for _, p in ipairs({{x1,y1},{x1,y2},{x2,y1},{x2,y2}}) do
        local tx, ty = pose.apply(matrix, p[1], p[2])
        minx, maxx = math.min(minx, tx), math.max(maxx, tx)
        miny, maxy = math.min(miny, ty), math.max(maxy, ty)
    end
    return minx, miny, maxx, maxy
end

function M.draw(asset, atlases, ctx)
    local x, y, w, h = ctx.x, ctx.y, ctx.w, ctx.h
    local put, background = ctx.put, ctx.background
    background(x, y, w, h, {0.13, 0.17, 0.20})
    if not asset then return end
    if lastAnimation ~= asset then M.time = 0; M.movement = 1; lastAnimation = asset end
    local selected, moves = active(asset)
    put(asset.path, x + 12, y + 10, {1, 0.86, 0.55}, ctx.small)
    if not selected then
        put("Sem movimentos nesta animação.", x + 12, y + 45, nil, ctx.small)
        return
    end
    local movement = selected.data
    local duration = math.max(1, movement.duration)
    local frameIndex = math.floor(M.time) % duration
    local ntracks = #movement.tracks
    put(string.format("Movimento %d/%d: %s", M.movement, #moves, selected.name),
        x + 12, y + 38, {1, 1, 1}, ctx.small)
    put(string.format("Quadro %d / %d  •  %d trilhas  •  %s", frameIndex, duration,
        ntracks, M.running and "reproduzindo" or "pausado"),
        x + 12, y + 61, {0.78, 0.88, 0.96}, ctx.small)
    put(string.format("Prévia: %s  |  base: %s  |  troca de display ainda não interpretada",
        M.interpolate and "interpolada" or "discreta", M.useBind and "ligada" or "desligada"),
        x + 12, y + h - 105, {1, 0.73, 0.49}, ctx.small)

    if not spriteLookup then
        local global
        spriteLookup, global = indexAtlases(atlases)
        M.global = global
    end
    local folder = dirname(asset.path)
    local poses = {}
    local missing = 0
    -- Os nomes das armaduras observadas no APK podem divergir de nomes
    -- de animações; a seleção da primeira armadura continua provisória.
    local armature = asset.armatures and asset.armatures[1]
    local nodes = pose.evaluate(armature, movement, frameIndex, M.interpolate, M.useBind)
    for _, node in ipairs(nodes) do
        local name = node.bone.displays and node.bone.displays[1]
        -- Só renderizamos o primeiro display: o campo binário que identifica
        -- mudanças de display ainda não foi mapeado com segurança.
        local sprite = name and (spriteLookup[folder .. "/" .. name] or M.global[name])
        if sprite and not sprite.frame.rotated then
            local image = ctx.imageFor(sprite.atlas.image)
            if image then
                local quad = ctx.spriteQuad(sprite.atlas, sprite.frame, image)
                if quad and node.matrix then
                    poses[#poses + 1] = {matrix = node.matrix, image = image,
                        quad = quad, f = sprite.frame}
                else missing = missing + 1 end
            else missing = missing + 1 end
        else missing = missing + 1 end
    end
    local px, py, pw, ph = x + 12, y + 92, w - 24, h - 214
    if pw < 80 or ph < 90 then return end
    background(px, py, pw, ph, {0.08, 0.115, 0.14})
    if #poses == 0 then
        put("Nenhuma pose com textura correspondente nesta animação.", px + 14, py + 25, nil, ctx.small)
    else
        local minx, miny, maxx, maxy = math.huge, math.huge, -math.huge, -math.huge
        for _, item in ipairs(poses) do
            local a, b, c, d = spriteBox(item.matrix, item.f)
            minx, miny, maxx, maxy = math.min(minx, a), math.min(miny, b),
                math.max(maxx, c), math.max(maxy, d)
        end
        local midx, midy = (minx + maxx) / 2, (miny + maxy) / 2
        local scale = math.min((pw - 40) / math.max(maxx - minx, 1),
            (ph - 40) / math.max(maxy - miny, 1), 3)
        love.graphics.setScissor(px, py, pw, ph)
        for _, item in ipairs(poses) do
            local m, f = item.matrix, item.f
            love.graphics.push()
            love.graphics.translate(px + pw / 2, py + ph / 2)
            love.graphics.scale(scale, -scale) -- Cocos +Y para cima; LÖVE +Y para baixo.
            love.graphics.translate(-midx, -midy)
            local transform = love.math.newTransform()
            transform:setMatrix(m.a, m.b, m.c, m.d, m.tx, m.ty)
            love.graphics.applyTransform(transform)
            love.graphics.setColor(1, 1, 1)
            love.graphics.draw(item.image, item.quad,
                -f.w / 2 + (f.offset_x or 0), -f.h / 2 + (f.offset_y or 0))
            love.graphics.pop()
        end
        love.graphics.setScissor()
    end
    put(string.format("Componentes com sprite: %d/%d  |  não resolvidos: %d", #poses, ntracks, missing),
        x + 12, y + h - 124, {0.78, 0.87, 0.94}, ctx.small)
    local barx, bary, barw = x + 15, y + h - 74, math.max(1, w - 30)
    background(barx, bary, barw, 13, {0.28, 0.35, 0.41})
    love.graphics.setColor(1, 0.80, 0.31)
    love.graphics.rectangle("fill", barx, bary, (frameIndex / duration) * barw, 13)
    put("Espaço: pausa  •  ← →: quadro  •  Tab: movimento", x + 12,
        y + h - 44, {0.82, 0.90, 0.94}, ctx.small)
    put("I: interpolação  •  B: pose-base  •  30 quadros/s (não validado)", x + 12,
        y + h - 23, {0.65, 0.76, 0.83}, ctx.small)
end

return M