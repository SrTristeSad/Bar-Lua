-- Inspecao geométrica de cenas Cocos Studio (.csb) decodificadas.
-- Nao reproduz fielmente layout, ancoragem responsiva, fontes nem ações do Cocos.
local M = {nodeIndex = 1, showGuides = true, showHidden = false}
local current, nodes = nil, {}

local function flatten(n, px, py, sx, sy, depth, inheritedVisible)
    if depth > 70 or #nodes >= 12000 then return end
    local p = n.props or {}
    local pos = p.position or {0, 0}
    local sc = p.scale or {1, 1}
    local pointX, pointY = px + pos[1] * sx, py + pos[2] * sy
    local scaleX, scaleY = sx * sc[1], sy * sc[2]
    local visible = inheritedVisible and p.visible ~= false
    nodes[#nodes+1] = {node = n, x = pointX, y = pointY,
        sx = scaleX, sy = scaleY, visible = visible, depth = depth}
    for _, child in ipairs(n.children or {}) do
        flatten(child, pointX, pointY, scaleX, scaleY, depth+1, visible)
    end
end

local function ensure(scene)
    if current == scene then return end
    current, nodes, M.nodeIndex = scene, {}, 1
    if scene and scene.root then flatten(scene.root, 0, 0, 1, 1, 0, true) end
end

function M.reset()
    current, nodes, M.nodeIndex = nil, {}, 1
end

function M.next(scene, direction)
    ensure(scene)
    M.nodeIndex = math.max(1, math.min(#nodes, M.nodeIndex + direction))
end

function M.toggleGuides() M.showGuides = not M.showGuides end
function M.toggleHidden() M.showHidden = not M.showHidden end
function M.inspect(scene)
    ensure(scene)
    return nodes[M.nodeIndex], #nodes
end

local function trunc(s, n)
    s = tostring(s or '')
    return #s <= n and s or s:sub(1, n-3)..'...'
end

function M.draw(scene, ctx)
    ensure(scene)
    local g, x, y, w, h = love.graphics, ctx.x, ctx.y, ctx.w, ctx.h
    ctx.background(x, y, w, h, {0.11, 0.15, 0.19})
    if #nodes == 0 then ctx.put('Cena sem nós recuperados.', x+20, y+20); return end
    local root = scene.root.props or {}
    local size = root.size or {960, 540}
    local sw, sh = size[1] > 0 and size[1] or 960, size[2] > 0 and size[2] or 540
    local frameH = math.max(80, h-153)
    local scale = math.max(0.02, math.min((w-55)/sw, (frameH-42)/sh, 2.0))
    local ox, oy = x + w/2 - sw*scale/2, y+46 + (frameH-sh*scale)/2 + sh*scale
    local function world(x0,y0) return ox + x0*scale, oy - y0*scale end
    g.setColor(0.23, 0.30, 0.36)
    g.rectangle('fill', ox, oy-sh*scale, sw*scale, sh*scale)
    g.setScissor(x, y+40, w, frameH)
    local maxImageDraws = 800
    for i, entry in ipairs(nodes) do
        if entry.visible or M.showHidden then
            local n,p = entry.node, entry.node.props or {}
            local size0, anchor = p.size or {0,0}, p.anchor or {0.5,0.5}
            local ww, hh = size0[1]*math.abs(entry.sx)*scale, size0[2]*math.abs(entry.sy)*scale
            local cx,cy=world(entry.x,entry.y)
            local left, top = cx-anchor[1]*ww, cy-(1-anchor[2])*hh
            -- Testa apenas texturas avulsas no APK; plist/atlas em outra etapa.
            local r = n.resource
            if entry.visible and maxImageDraws>0 and r and r.path and r.path~='' then
                local image = ctx.resolveImage(r.path, r.type)
                if image then
                    local iw,ih = image:getDimensions()
                    if ww > 1 and hh > 1 then
                        g.setColor(1,1,1,(p.opacity or 255)/255)
                        g.draw(image,left,top,0,ww/iw,hh/ih)
                        maxImageDraws=maxImageDraws-1
                    end
                end
            end
            if M.showGuides and ww>1 and hh>1 then
                if i==M.nodeIndex then g.setColor(1,0.78,0.24,1)
                elseif entry.visible then g.setColor(0.38,0.78,0.88,0.23)
                else g.setColor(1,0.4,0.4,0.16) end
                g.rectangle('line',left,top,ww,hh)
            end
            if i==M.nodeIndex then
                g.setColor(1,0.79,0.25)
                g.circle('fill',cx,cy,3)
            end
        end
    end
    g.setScissor()
    local selected=nodes[M.nodeIndex]
    local n, p = selected.node, selected.node.props or {}
    ctx.put(trunc(scene.name or scene.path,80)..'   |   '..#nodes..' nós   |   '..sw..' × '..sh, x+10,y+10,{0.96,0.98,1},ctx.small)
    ctx.background(x+8,y+h-105,w-16,100,{0.08,0.12,0.16})
    local prefix=string.rep('· ',math.min(8,selected.depth))
    ctx.put(M.nodeIndex..'/'..#nodes..' '..prefix..trunc(n.class..'  '..(p.name or ''),65),x+16,y+h-100,{1,0.82,0.40},ctx.small)
    ctx.put(string.format('Posição (%.1f, %.1f)  |  Tamanho %.1f × %.1f  |  z=%d  |  visível=%s',
        selected.x,selected.y,(p.size or {0,0})[1],(p.size or {0,0})[2],p.z or 0,tostring(selected.visible)),
        x+16,y+h-77,{0.84,0.9,0.96},ctx.small)
    local res = n.resource
    if res then ctx.put('Recurso: '..trunc(res.path,95),x+16,y+h-56,{0.82,0.86,0.93},ctx.small)
    elseif n.text then ctx.put('Texto: '..trunc(n.text,95),x+16,y+h-56,{0.82,0.86,0.93},ctx.small)
    else ctx.put('Tag: '..tostring(p.action_tag or 0)..'  |  origem: '..tostring((p.anchor or {})[1] or 0.5),x+16,y+h-56,{0.72,0.78,0.86},ctx.small) end
    ctx.put('Tab: próximo nó  ·  Shift+Tab: anterior  ·  G: guias  ·  V: ocultos',x+16,y+h-27,{0.86,0.91,0.96},ctx.small)
end

return M