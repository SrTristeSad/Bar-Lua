-- Laboratório visual de keyframes Cocos Studio, não renderizador definitivo.
-- Coordenadas, escala e indexação foram recuperadas do APK. Hierarquia,
-- tweening, skew, orientações especiais e blending aguardam validação.
local M = {movement = 1, time = 0, running = true}
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

local function atFrame(track, frameIndex)
    local best
    for _, key in ipairs(track.keys or {}) do
        if key.at > frameIndex then break end
        best = key
    end
    return best
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
    put("Prévia experimental: sem interpolação, hierarquia/skew ou blending Cocos.",
        x + 12, y + h - 102, {1, 0.73, 0.49}, ctx.small)

    if not spriteLookup then
        local global
        spriteLookup, global = indexAtlases(atlases)
        M.global = global
    end
    local boneByName = {}
    for _, armature in ipairs(asset.armatures or {}) do
        for _, bone in ipairs(armature.bones or {}) do
            boneByName[bone.name] = bone
        end
    end
    local folder = dirname(asset.path)
    local poses = {}
    local missing = 0
    for _, track in ipairs(movement.tracks) do
        local bone = boneByName[track.bone]
        local key = atFrame(track, frameIndex)
        local name = bone and bone.displays and bone.displays[1]
        local sprite = name and (spriteLookup[folder .. "/" .. name] or M.global[name])
        if key and sprite and not sprite.frame.rotated then
            local image = ctx.imageFor(sprite.atlas.image)
            if image then
                local quad = ctx.spriteQuad(sprite.atlas, sprite.frame, image)
                if quad then poses[#poses + 1] = {key = key, image = image, quad = quad, f = sprite.frame} end
            end
        else
            missing = missing + 1
        end
    end
    local px, py, pw, ph = x + 12, y + 92, w - 24, h - 214
    if pw < 80 or ph < 90 then return end
    background(px, py, pw, ph, {0.08, 0.115, 0.14})
    if #poses == 0 then
        put("Nenhuma pose com textura correspondente nesta animação.", px + 14, py + 25, nil, ctx.small)
    else
        local minx, miny, maxx, maxy = math.huge, math.huge, -math.huge, -math.huge
        for _, pose in ipairs(poses) do
            local k, f = pose.key, pose.f
            local sw, sh = math.abs(k.scale_x) * f.w, math.abs(k.scale_y) * f.h
            minx = math.min(minx, k.x - sw / 2)
            maxx = math.max(maxx, k.x + sw / 2)
            miny = math.min(miny, k.y - sh / 2)
            maxy = math.max(maxy, k.y + sh / 2)
        end
        local midx, midy = (minx + maxx) / 2, (miny + maxy) / 2
        local scale = math.min((pw - 40) / math.max(maxx - minx, 1),
            (ph - 40) / math.max(maxy - miny, 1), 3)
        love.graphics.setScissor(px, py, pw, ph)
        for _, pose in ipairs(poses) do
            local k, f = pose.key, pose.f
            love.graphics.setColor(1, 1, 1)
            love.graphics.draw(pose.image, pose.quad,
                px + pw / 2 + (k.x - midx) * scale,
                py + ph / 2 - (k.y - midy) * scale,
                0, scale * k.scale_x, scale * k.scale_y, f.w / 2, f.h / 2)
        end
        love.graphics.setScissor()
    end
    put(string.format("Componentes com sprite: %d/%d  |  não resolvidos: %d", #poses, ntracks, missing),
        x + 12, y + h - 124, {0.78, 0.87, 0.94}, ctx.small)
    local barx, bary, barw = x + 15, y + h - 74, math.max(1, w - 30)
    background(barx, bary, barw, 13, {0.28, 0.35, 0.41})
    love.graphics.setColor(1, 0.80, 0.31)
    love.graphics.rectangle("fill", barx, bary, (frameIndex / duration) * barw, 13)
    put("Espaço: pausa  •  ← →: quadro  •  Tab / Shift+Tab: movimento", x + 12,
        y + h - 44, {0.82, 0.90, 0.94}, ctx.small)
    put("Velocidade fixa de inspeção: 30 quadros/s (não validada).", x + 12,
        y + h - 23, {0.65, 0.76, 0.83}, ctx.small)
end

return M