-- Bar-Lua Fase 7: geometria do SpriteFrame em coordenadas +Y para cima.
-- Atlas usam +Y para baixo; offsets são relativos ao centro da fonte.
-- O APK 1.0.1811 não contém quadros rotacionados; suporte rotated é experimental.
local M = {}
local function num(x, default)
    return type(x) == 'number' and x or default
end
function M.size(f)
    if f.rotated then return f.h, f.w end
    return f.w, f.h
end
function M.center(f, anchorX, anchorY)
    local w, h = M.size(f)
    local srcW = num(f.source_w, w)
    local srcH = num(f.source_h, h)
    local x = num(f.offset_x, 0) + (0.5 - num(anchorX, 0.5)) * srcW
    local y = num(f.offset_y, 0) + (0.5 - num(anchorY, 0.5)) * srcH
    return x, y
end
function M.bounds(f, anchorX, anchorY)
    local w, h = M.size(f)
    local x, y = M.center(f, anchorX, anchorY)
    return x - w / 2, y - h / 2, x + w / 2, y + h / 2
end
function M.placement(f, anchorX, anchorY)
    local x, y = M.center(f, anchorX, anchorY)
    if f.rotated then
        -- Hipótese: armazenado em rotação horária de 90 graus.
        return x - f.h / 2, y - f.w / 2, math.pi / 2, 1, -1
    end
    return x - f.w / 2, y + f.h / 2, 0, 1, -1
end
function M.draw(image, quad, frame, anchorX, anchorY)
    local x, y, r, sx, sy = M.placement(frame, anchorX, anchorY)
    love.graphics.draw(image, quad, x, y, r, sx, sy)
end
function M.sourceBounds(f, anchorX, anchorY)
    local w, h = M.size(f)
    local sw = num(f.source_w, w)
    local sh = num(f.source_h, h)
    local ax, ay = num(anchorX, 0.5), num(anchorY, 0.5)
    return -ax * sw, -ay * sh, (1 - ax) * sw, (1 - ay) * sh
end
return M
