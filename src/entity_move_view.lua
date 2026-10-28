-- F10: pesquisa das duas rotas do método ARM64 Entity::move.
local model = require('src.entity_move')
local M = {dx = 1, dy = 0, x = 0, y = 0, flags = 0, body_type = 2}
function M.reset()
    M.dx, M.dy, M.x, M.y, M.flags, M.body_type = 1, 0, 0, 0, 0, 2
end
function M.keypressed(key)
    if key == 'left' then M.dx = M.dx - 0.25
    elseif key == 'right' then M.dx = M.dx + 0.25
    elseif key == 'up' then M.dy = M.dy + 0.25
    elseif key == 'down' then M.dy = M.dy - 0.25
    elseif key == 'g' then M.flags = (math.floor(M.flags/32)%2 == 1) and M.flags-32 or M.flags+32
    elseif key == 't' then M.body_type = (M.body_type == 0) and 2 or 0
    elseif key == 'z' then M.dx, M.dy = 0, 0
    elseif key == 'r' then M.reset()
    elseif key == 'return' then
        local p = M.values()
        if p.kind == 'set_transform' then M.x, M.y = p.x, p.y end
        M.flags = p.flags
    else return false end
    return true
end
function M.values()
    return model.plan({x=M.x,y=M.y,flags=M.flags,body_type=M.body_type,angle=0},M.dx,M.dy)
end
function M.draw(_, panel)
    local x,y,w,h=panel.x,panel.y,panel.w,panel.h
    local p = M.values()
    panel.background(x,y,w,h,{0.12,0.16,0.20})
    local c={1,0.86,0.5}
    panel.put('F10 · Entity::move / Box2D — laboratório de inspeção',x+12,y+14,c,panel.small)
    panel.put(string.format('Componentes: dx=%.5f, dy=%.5f',M.dx,M.dy),x+12,y+48,nil,panel.small)
    panel.put(string.format('Posição no laboratório: (%.5f, %.5f)',M.x,M.y),x+12,y+76,nil,panel.small)
    panel.put(string.format('Bit 5: %s | body_type: %d | estado bruto: %d',tostring(math.floor(M.flags/32)%2==1),M.body_type,M.flags),x+12,y+104,nil,panel.small)
    panel.put('Caminho ELF: '..p.kind,x+12,y+139,{0.55,0.98,0.69},panel.small)
    panel.put(string.format('Posição resultante: (%.6f, %.6f)',p.x,p.y),x+12,y+169,nil,panel.small)
    panel.put(p.reason,x+12,y+199,nil,panel.small)
    local cx,cy=x+w/2,y+math.max(310,math.min(h-120,365))
    local scale=55
    love.graphics.setColor(0.30,0.36,0.45)
    love.graphics.line(cx-160,cy,cx+160,cy)
    love.graphics.line(cx,cy-105,cx,cy+105)
    love.graphics.setColor(0.40,0.80,1)
    love.graphics.circle('fill',cx,cy,6)
    love.graphics.setColor(0.50,1,0.60)
    love.graphics.circle('fill',cx+(p.x-M.x)*scale,cy-(p.y-M.y)*scale,6)
    panel.put('Azul: posição anterior   Verde: destino SetTransform (sem física)',x+12,y+h-81,nil,panel.small)
    panel.put('←→ ajusta dx | ↑↓ ajusta dy | G bit 5 | T tipo | Z zero | R reset',x+12,y+h-53,nil,panel.small)
    panel.put('Enter aplica apenas o destino; nenhuma colisão, IA ou rede é simulada.',x+12,y+h-27,{0.88,0.85,0.72},panel.small)
end
return M
