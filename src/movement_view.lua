-- F13: laboratório dos cálculos de direção, NÃO jogador ou física do BarbarQ.
local codec = require('src.movement_codec')
local M = {}
local function reset()
    M.angle, M.facing, M.speed, M.secondarySpeed = 90, 0, 100, 50
    M.primary, M.secondary = true, false
end
reset()
M.reset = reset

function M.keypressed(key)
    if key == 'left' then M.angle = (M.angle - 4) % 360
    elseif key == 'right' then M.angle = (M.angle + 4) % 360
    elseif key == 'up' then M.speed = math.min(1000, M.speed + 10)
    elseif key == 'down' then M.speed = math.max(0, M.speed - 10)
    elseif key == 'a' then M.secondarySpeed = math.max(0, M.secondarySpeed - 10)
    elseif key == 'z' then M.secondarySpeed = math.min(1000, M.secondarySpeed + 10)
    elseif key == 'q' then M.facing = (M.facing - 15) % 360
    elseif key == 'e' then M.facing = (M.facing + 15) % 360
    elseif key == 'j' then M.primary = not M.primary
    elseif key == 'k' then M.secondary = not M.secondary
    elseif key == 'r' then reset()
    else return false end
    return true
end

function M.values()
    local x, y = codec.move_vector(M.speed, M.secondarySpeed, M.facing,
                                   M.angle, M.primary, M.secondary)
    local encoded = codec.quantize_degrees(M.angle)
    return {x=x, y=y, encoded=encoded, display_angle=encoded*4,
            speed=M.speed, secondary_speed=M.secondarySpeed}
end

local function arrow(cx,cy,dx,dy,scale,rgb)
    love.graphics.setColor(rgb)
    local ax, ay = cx + dx*scale, cy - dy*scale
    love.graphics.line(cx,cy,ax,ay)
    love.graphics.circle('fill',ax,ay,4)
end

function M.draw(_,panel)
    local x,y,w,h=panel.x,panel.y,panel.w,panel.h
    panel.background(x,y,w,h,{0.12,0.16,0.20})
    local v=M.values()
    panel.put('Movimento ARM64 — laboratório, NÃO física/combate original',x+14,y+15,{1,0.84,0.48},panel.small)
    panel.put('Hero::move_update(float) | dois vetores com cosDeg/sinDeg',x+14,y+44,nil,panel.small)
    panel.put(string.format('Direção %d° | código: %d | visual: %d°',M.angle,v.encoded,v.display_angle),x+14,y+73,nil,panel.small)
    panel.put(string.format('Primário: %s, velocidade int=%d /100',tostring(M.primary),M.speed),x+14,y+98,nil,panel.small)
    panel.put(string.format('Secundário: %s, velocidade int=%d /100; ângulo %d°',tostring(M.secondary),M.secondarySpeed,M.facing),x+14,y+123,nil,panel.small)
    panel.put(string.format('Entity::move(x=%.5f, y=%.5f) — componentes calculados',v.x,v.y),x+14,y+148,{0.68,1,0.76},panel.small)
    local centerX,centerY=x+w/2,y+math.max(255,math.min(h-117,300))
    love.graphics.setColor(0.28,0.33,0.39)
    love.graphics.line(centerX-145,centerY,centerX+145,centerY)
    love.graphics.line(centerX,centerY-125,centerX,centerY+125)
    local s=math.min(100,math.max(30,w/8))
    local a=math.rad(M.angle)
    local b=math.rad(M.facing)
    arrow(centerX,centerY,M.primary and M.speed/100*math.cos(a) or 0,
          M.primary and M.speed/100*math.sin(a) or 0,s,{0.43,0.73,1})
    arrow(centerX,centerY,M.secondary and M.secondarySpeed/100*math.cos(b) or 0,
          M.secondary and M.secondarySpeed/100*math.sin(b) or 0,s,{1,0.75,0.36})
    arrow(centerX,centerY,v.x,v.y,s,{0.48,1,0.59})
    panel.put('Azul = vetor 1 | laranja = vetor 2 | verde = soma',x+14,y+h-76,nil,panel.small)
    panel.put('←→ ângulo | ↑↓ velocidade | J/K flags | A/Z vel. 2 | Q/E giro 2 | R reset',x+14,y+h-52,nil,panel.small)
    panel.put('Não gera pacotes, não movimenta entidades nem simula colisões.',x+14,y+h-28,{0.76,0.87,0.92},panel.small)
end
return M
