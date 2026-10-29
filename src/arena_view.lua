-- Bar-Lua playable arena: stand-in 2D art, no external game assets required.
-- Combat rules live in src/arena_game.lua. Original BarbarQ visuals pending.
local View={}
local originalArt=require('src.arena_original_art')
local regular, large, small
local W,H=1280,720
local function fonts()
    if not regular then
        regular=love.graphics.newFont(19)
        large=love.graphics.newFont(43)
        small=love.graphics.newFont(13)
    end
end
local function color(r,g,b,a) love.graphics.setColor(r,g,b,a or 1) end
local function label(value,x,y,font,r,g,b)
    love.graphics.setFont(font or regular)
    color(r or 1,g or 1,b or 1)
    love.graphics.print(value,x,y)
end
local function centered(value,y,font,r,g,b)
    love.graphics.setFont(font)
    label(value,(W-font:getWidth(value))/2,y,font,r,g,b)
end
local function hpbar(x,y,width,hp,maxHp,enemy)
    color(0.05,0.08,0.1,0.92)
    love.graphics.rectangle('fill',x,y,width,8,3,3)
    local ratio=math.max(0,math.min(1,hp/math.max(1,maxHp)))
    if enemy then color(0.97,0.30,0.31) else color(0.39,0.9,0.55) end
    love.graphics.rectangle('fill',x+1,y+1,(width-2)*ratio,6,2,2)
end
local function enemySprite(e)
    local x,y=e.x,e.y
    color(0.01,0.035,0.055,0.35)
    love.graphics.ellipse('fill',x,y+23,25,8)
    if e.hitFlash>0 then color(1,0.91,0.65) else color(0.7,0.23,0.29) end
    love.graphics.circle('fill',x,y,19)
    color(0.24,0.10,0.16)
    love.graphics.polygon('fill',x-15,y-11,x-21,y-30,x-6,y-20)
    love.graphics.polygon('fill',x+15,y-11,x+21,y-30,x+6,y-20)
    color(0.96,0.81,0.64)
    love.graphics.circle('fill',x-7,y-2,4)
    love.graphics.circle('fill',x+7,y-2,4)
    color(0.12,0.10,0.16)
    love.graphics.circle('fill',x-6,y-2,2)
    love.graphics.circle('fill',x+6,y-2,2)
    color(0.18,0.08,0.12)
    love.graphics.rectangle('fill',x-5,y+9,10,3,1,1)
    hpbar(x-24,y-42,48,e.hp,e.maxHp,true)
end
local function playerSprite(g)
    local p=g.player
    local x,y=p.x,p.y
    local flash=p.invulnerable>0 and math.floor(p.invulnerable*17)%2==0
    color(0.01,0.035,0.055,0.42)
    love.graphics.ellipse('fill',x,y+25,29,9)
    local angle=math.atan2 and math.atan2(p.faceY,p.faceX) or math.atan(p.faceY,p.faceX)
    love.graphics.push()
    love.graphics.translate(x,y)
    love.graphics.rotate(angle)
    color(0.19,0.27,0.32)
    love.graphics.ellipse('fill',-1,12,22,21)
    color(0.18,0.59,0.74)
    love.graphics.circle('fill',0,0,21)
    color(0.10,0.29,0.47)
    love.graphics.polygon('fill',2,-15,15,-6,16,13,3,19)
    color(0.95,0.82,0.59)
    love.graphics.circle('fill',6,-7,13)
    color(0.20,0.11,0.12)
    love.graphics.circle('fill',13,-9,2)
    color(0.22,0.16,0.10)
    love.graphics.polygon('fill',-7,-16,-15,-21,-10,-35,0,-27,7,-36,13,-18)
    -- Wooden club: the first playable attack is intentionally provisional.
    color(0.36,0.22,0.12)
    love.graphics.setLineWidth(6)
    love.graphics.line(17,6,38,6)
    color(0.76,0.55,0.30)
    love.graphics.ellipse('fill',39,6,10,8)
    love.graphics.setLineWidth(1)
    love.graphics.pop()
    if flash then
        color(1,1,1,0.28)
        love.graphics.circle('fill',x,y,24)
    end
    if g.attackFlash>0 then
        color(1,0.83,0.33,math.min(1,g.attackFlash/0.17))
        love.graphics.setLineWidth(8)
        love.graphics.arc('line','open',x,y,p.attackRange,angle-0.97,angle+0.97,24)
        love.graphics.setLineWidth(1)
    end
end
local function floor()
    color(0.055,0.11,0.14)
    love.graphics.rectangle('fill',0,0,W,H)
    for y=48,H,52 do
        for x=0,W,52 do
            local t=((math.floor(x/52)+math.floor(y/52))%2==0)
            color(t and 0.077 or 0.083,t and 0.15 or 0.16,t and 0.18 or 0.19)
            love.graphics.rectangle('fill',x,y,50,50)
        end
    end
    color(0.15,0.33,0.34,0.65)
    love.graphics.setLineWidth(5)
    love.graphics.rectangle('line',23,54,W-46,H-78,12,12)
    love.graphics.setLineWidth(1)
    color(0.17,0.33,0.36,0.35)
    love.graphics.circle('line',W/2,H/2,220)
    love.graphics.circle('line',W/2,H/2,126)
    for i=1,16 do
        local a=i*math.pi/8
        local x=W/2+math.cos(a)*218
        local y=H/2+math.sin(a)*218
        color(0.23,0.45,0.45,0.38)
        love.graphics.circle('fill',x,y,3)
    end
end
local function hud(g)
    local p=g.player
    color(0.035,0.073,0.1,0.95)
    love.graphics.rectangle('fill',0,0,W,54)
    color(0.24,0.51,0.55)
    love.graphics.line(0,53,W,53)
    label('BAR-LUA  |  ARENA ALFA',24,12,regular,0.95,0.86,0.6)
    label(string.format('ONDA %d/%d   INIMIGOS %d',g.wave,g.maxWaves,
        require('src.arena_game').aliveEnemies(g)),480,13,regular)
    label(string.format('PONTOS %d',g.score),1035,13,regular,0.81,0.96,0.73)
    color(0.035,0.073,0.1,0.93)
    love.graphics.rectangle('fill',0,H-53,W,53)
    hpbar(25,H-34,255,p.hp,p.maxHp,false)
    label(string.format('VIDA %d/%d',p.hp,p.maxHp),292,H-42,regular,0.85,1,0.88)
    label(string.format('ABATES %d',g.kills),490,H-42,regular)
    local cooldown=p.cooldown>0 and string.format('ATAQUE %.1fs',p.cooldown) or 'ATAQUE PRONTO'
    label(cooldown,760,H-42,regular,p.cooldown>0 and 1 or 0.62,p.cooldown>0 and 0.73 or 1,0.60)
    label('WASD / SETAS mover   ESPAÇO (segurar) / J / CLIQUE mirar e atacar',25,H-66,small,0.77,0.9,0.95)
    label('P pausa    R reinicia    ESC laboratório',960,H-66,small,0.77,0.9,0.95)
end
local function overlay(g)
    local text,subtitle
    if g.phase=='paused' then
        text='PAUSADO';subtitle='P para continuar'
    elseif g.phase=='won' then
        text='VITORIA!';subtitle=string.format('%d pontos   |   R para jogar novamente',g.score)
    elseif g.phase=='lost' then
        text='DERROTA';subtitle=string.format('%d abates   |   R para tentar novamente',g.kills)
    elseif g.phase=='between' then
        text='ONDA CONCLUIDA';subtitle='Prepare-se para a próxima onda'
    elseif g.messageTimer>0 then
        text=g.message
    end
    if not text then return end
    if g.phase~='playing' then
        color(0.015,0.04,0.06,0.72)
        love.graphics.rectangle('fill',0,0,W,H)
    end
    centered(text,285,large,1,0.86,0.41)
    if subtitle then centered(subtitle,354,regular,0.89,0.95,0.96) end
end
function View.draw(g,w,h,original)
    if not g then return end
    fonts()
    w=w or love.graphics.getWidth()
    h=h or love.graphics.getHeight()
    local scale=math.min(w/W,h/H)
    local left,top=(w-W*scale)/2,(h-H*scale)/2
    love.graphics.push()
    color(0.02,0.04,0.06)
    love.graphics.rectangle('fill',0,0,w,h)
    love.graphics.translate(left,top)
    love.graphics.scale(scale,scale)
    floor()
    local camera=original and originalArt.camera(original,g.player) or {scale=1,x=0,y=0}
    love.graphics.push()
    love.graphics.translate(camera.x,camera.y)
    love.graphics.scale(camera.scale,camera.scale)
    if original and original.map then originalArt.drawMap(original,g.player) end
    local actors={}
    for _,e in ipairs(g.enemies) do
        if e.alive then actors[#actors+1]={y=e.y,enemy=e} end
    end
    actors[#actors+1]={y=g.player.y,player=true}
    table.sort(actors,function(a,b)return a.y<b.y end)
    for _,a in ipairs(actors) do
        if a.player then
            local drawn=original and originalArt.drawHero(original,g.player,g.elapsed,g.player.cooldown>0,false)
            if not drawn then playerSprite(g) end
        else
            local drawn=original and originalArt.drawHero(original,a.enemy,g.elapsed,(a.enemy.attackVisual or 0)>0,true)
            if not drawn then
                enemySprite(a.enemy)
            else
                hpbar(a.enemy.x-24,a.enemy.y-45,48,a.enemy.hp,a.enemy.maxHp,true)
            end
        end
    end
    for _,effect in ipairs(g.effects) do
        label(effect.text,effect.x-16,effect.y-effect.age*34,regular,
              effect.color[1],effect.color[2],effect.color[3])
    end
    love.graphics.pop()
    hud(g)
    overlay(g)
    local message=original and original.usesOriginalMap and original.usesOriginalHero and
        ('ARTE DO APK: mapa e heroi | visuais de inimigos: '..tostring(#(original.enemyAssets or {}))..' candidatos | mecanicas alfa') or
        'ALFA: instale cache e assets_original para usar arte BarbarQ | combate provisório'
    label(message,22,56,small,1,0.72,0.45)
    love.graphics.pop()
    color(1,1,1)
end
return View
