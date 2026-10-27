-- Fase 6: avaliação de poses, displays e matrizes afins 2D.
-- Aproximação de investigação. Trocas de display são discretas;
-- não reproduz easing, pivôs, cores ou temporização original do Cocos Studio.
local M = {}

local function value(t, key, default)
    local v = t and t[key]
    return type(v) == 'number' and v or default
end

local function interpolated(a, b, percent)
    return {
        x = value(a, 'x', 0) + (value(b, 'x', 0) - value(a, 'x', 0)) * percent,
        y = value(a, 'y', 0) + (value(b, 'y', 0) - value(a, 'y', 0)) * percent,
        scale_x = value(a, 'scale_x', 1) + (value(b, 'scale_x', 1) - value(a, 'scale_x', 1)) * percent,
        scale_y = value(a, 'scale_y', 1) + (value(b, 'scale_y', 1) - value(a, 'scale_y', 1)) * percent,
        skew_x = value(a, 'skew_x', 0) + (value(b, 'skew_x', 0) - value(a, 'skew_x', 0)) * percent,
        skew_y = value(a, 'skew_y', 0) + (value(b, 'skew_y', 0) - value(a, 'skew_y', 0)) * percent,
    }
end

function M.sample(keys, frame, tween)
    if not keys or #keys == 0 then return nil end
    if frame <= keys[1].at then return interpolated(keys[1], keys[1], 0) end
    local first, nextKey = keys[1], nil
    for i = 2, #keys do
        local candidate = keys[i]
        if candidate.at > frame then nextKey = candidate; break end
        first = candidate
    end
    if not nextKey or not tween then return interpolated(first, first, 0) end
    local span = nextKey.at - first.at
    if span <= 0 then return interpolated(first, first, 0) end
    return interpolated(first, nextKey, math.max(0, math.min(1, (frame - first.at) / span)))
end

function M.affine(p)
    local x, y = value(p, 'x', 0), value(p, 'y', 0)
    local sx, sy = value(p, 'scale_x', 1), value(p, 'scale_y', 1)
    local kx, ky = value(p, 'skew_x', 0), value(p, 'skew_y', 0)
    return {a = sx * math.cos(ky), b = sx * math.sin(ky),
            c = -sy * math.sin(kx), d = sy * math.cos(kx),
            tx = x, ty = y}
end

function M.multiply(parent, child)
    if not parent then return child end
    return {
        a = parent.a * child.a + parent.c * child.b,
        b = parent.b * child.a + parent.d * child.b,
        c = parent.a * child.c + parent.c * child.d,
        d = parent.b * child.c + parent.d * child.d,
        tx = parent.a * child.tx + parent.c * child.ty + parent.tx,
        ty = parent.b * child.tx + parent.d * child.ty + parent.ty,
    }
end

function M.apply(matrix, x, y)
    return matrix.a * x + matrix.c * y + matrix.tx,
           matrix.b * x + matrix.d * y + matrix.ty
end

-- Seleção discreta de textura: base 0, -1 = oculto.
function M.displayAt(bone, track, frame)
    local selected = bone and bone.initial_display or 0
    for _, key in ipairs(track and track.keys or {}) do
        if key.at > frame then break end
        if type(key.display_index) == 'number' then selected = key.display_index end
    end
    return selected
end

-- Renderização de trás para frente; empates conservam a ordem de origem.
function M.ordered(nodes)
    local sorted = {}
    for i, node in ipairs(nodes) do
        sorted[#sorted + 1] = {index = i, node = node}
    end
    table.sort(sorted, function(a, b)
        local za = a.node.bone.layer_order or 0
        local zb = b.node.bone.layer_order or 0
        if za == zb then return a.index < b.index end
        return za < zb
    end)
    local result = {}
    for i, entry in ipairs(sorted) do result[i] = entry.node end
    return result
end

function M.evaluate(armature, movement, frame, tween, withBind)
    local bones = armature and armature.bones or {}
    local byName, tracks = {}, {}
    for _, bone in ipairs(bones) do byName[bone.name] = bone end
    for _, track in ipairs(movement and movement.tracks or {}) do tracks[track.bone] = track end
    local composed, visiting, result = {}, {}, {}
    local function world(name)
        if composed[name] then return composed[name] end
        local bone = byName[name]
        if not bone or visiting[name] then return nil end
        visiting[name] = true
        local sampled = M.sample(tracks[name] and tracks[name].keys, frame, tween) or {}
        local base = withBind and bone.bind or nil
        local p = {
            x = value(base, 'x', 0) + value(sampled, 'x', 0),
            y = value(base, 'y', 0) + value(sampled, 'y', 0),
            scale_x = value(base, 'scale_x', 1) * value(sampled, 'scale_x', 1),
            scale_y = value(base, 'scale_y', 1) * value(sampled, 'scale_y', 1),
            skew_x = value(base, 'skew_x', 0) + value(sampled, 'skew_x', 0),
            skew_y = value(base, 'skew_y', 0) + value(sampled, 'skew_y', 0),
        }
        local localMatrix = M.affine(p)
        local parent = bone.parent
        if parent and parent ~= '' and parent ~= name and byName[parent] then
            local parentMatrix = world(parent)
            if parentMatrix then localMatrix = M.multiply(parentMatrix, localMatrix) end
        end
        visiting[name] = nil
        composed[name] = localMatrix
        return localMatrix
    end
    for _, bone in ipairs(bones) do
        result[#result + 1] = {
            name = bone.name, bone = bone, matrix = world(bone.name),
            animated = tracks[bone.name] ~= nil,
            display_index = M.displayAt(bone, tracks[bone.name], frame)
        }
    end
    return result
end

return M
