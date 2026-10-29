-- BarbarQ Lua: playable vertical slice (prototype rules, NOT verified 1:1).
-- Deterministic pure-Lua combat model. Rendering and input are separate.
local Game = {}
local TAU = math.pi * 2
local function clamp(value, minimum, maximum)
    return math.max(minimum, math.min(maximum, value))
end
local function distance(x, y)
    return math.sqrt(x*x + y*y)
end
local function pushEffect(g, x, y, label, color)
    g.effects[#g.effects + 1] = {x=x, y=y, text=label, color=color, age=0, duration=0.7}
end

function Game.spawnWave(g)
    local count = 2 + g.wave
    g.enemies = {}
    for i = 1, count do
        local angle = (i - 1) * TAU / count + g.wave * 0.38
        local radius = 235 + (i % 2) * 40
        local x = clamp(g.width/2 + math.cos(angle)*radius, 45, g.width-45)
        local y = clamp(g.height/2 + math.sin(angle)*radius, 65, g.height-45)
        local hp = 105 + g.wave*20
        g.enemies[#g.enemies+1] = {
            x=x, y=y, radius=17, hp=hp, maxHp=hp,
            speed=64 + g.wave*10,
            damage=10 + g.wave*3,
            attackRange=39, cooldown=(i-1)*0.22,
            hitFlash=0, alive=true
        }
    end
    g.phase = 'playing'
    g.message = 'ONDA '..g.wave
    g.messageTimer = 1.3
end

function Game.new()
    local g = {
        width=1280, height=720, wave=1, maxWaves=3,
        score=0, kills=0, elapsed=0, phase='playing',
        enemies={}, effects={}, message='', messageTimer=0,
        attackFlash=0, hitCount=0, nextWaveTimer=0,
        player={
            x=640, y=360, radius=18,
            maxHp=300, hp=300,
            speed=220, damage=59,
            attackRange=94, attackCooldown=0.42,
            cooldown=0, invulnerable=0,
            faceX=1, faceY=0
        }
    }
    Game.spawnWave(g)
    return g
end

function Game.togglePause(g)
    if g.phase == 'paused' then
        g.phase = g.pausedPhase or 'playing'
        g.pausedPhase = nil
    elseif g.phase == 'playing' or g.phase == 'between' then
        g.pausedPhase = g.phase
        g.phase = 'paused'
    end
end

local function countAlive(g)
    local count=0
    for _, e in ipairs(g.enemies) do
        if e.alive then count=count+1 end
    end
    return count
end
function Game.aliveEnemies(g)
    return countAlive(g)
end

function Game.attack(g)
    if g.phase ~= 'playing' then return false, 0 end
    local p=g.player
    if p.cooldown > 0 then return false, 0 end
    p.cooldown=p.attackCooldown
    g.attackFlash=0.17
    local hits=0
    for _,e in ipairs(g.enemies) do
        if e.alive then
            local dx,dy=e.x-p.x,e.y-p.y
            local d=distance(dx,dy)
            local inRange=d <= p.attackRange+e.radius
            local towards=d < 0.00001 or (dx*p.faceX+dy*p.faceY)/d >= 0.45
            if inRange and towards then
                e.hp=math.max(0,e.hp-p.damage)
                e.hitFlash=0.2
                hits=hits+1
                pushEffect(g,e.x,e.y-27,'-'..p.damage,{1,0.84,0.28})
                if e.hp==0 then
                    e.alive=false
                    g.kills=g.kills+1
                    g.score=g.score+100
                    pushEffect(g,e.x,e.y-48,'+100',{0.53,1,0.65})
                else
                    local nx,ny=dx/math.max(d,0.00001),dy/math.max(d,0.00001)
                    e.x=clamp(e.x+nx*14, e.radius, g.width-e.radius)
                    e.y=clamp(e.y+ny*14, e.radius, g.height-e.radius)
                end
            end
        end
    end
    g.hitCount=hits
    if countAlive(g)==0 then
        if g.wave>=g.maxWaves then
            g.phase='won'
            g.message='VITORIA!'
        else
            g.phase='between'
            g.nextWaveTimer=1.5
            g.message='ONDA CONCLUIDA'
            g.messageTimer=1.5
        end
    end
    return true,hits
end

function Game.update(g, dt, input)
    if type(dt)~='number' or dt~=dt or dt<0 or dt==math.huge then return end
    if g.phase=='paused' or g.phase=='won' or g.phase=='lost' then return end
    dt=math.min(dt,0.05)
    local p=g.player
    input=input or {}
    g.elapsed=g.elapsed+dt
    p.cooldown=math.max(0,p.cooldown-dt)
    p.invulnerable=math.max(0,p.invulnerable-dt)
    g.attackFlash=math.max(0,g.attackFlash-dt)
    g.messageTimer=math.max(0,g.messageTimer-dt)
    for i=#g.effects,1,-1 do
        local effect=g.effects[i]
        effect.age=effect.age+dt
        if effect.age>=effect.duration then table.remove(g.effects,i) end
    end
    if g.phase=='between' then
        g.nextWaveTimer=g.nextWaveTimer-dt
        if g.nextWaveTimer<=0 then
            g.wave=g.wave+1
            Game.spawnWave(g)
        end
        return
    end
    local mx=(input.right and 1 or 0)-(input.left and 1 or 0)
    local my=(input.down and 1 or 0)-(input.up and 1 or 0)
    local m=distance(mx,my)
    if m>0 then
        mx,my=mx/m,my/m
        p.faceX,p.faceY=mx,my
        p.x=clamp(p.x+mx*p.speed*dt,p.radius+16,g.width-p.radius-16)
        p.y=clamp(p.y+my*p.speed*dt,p.radius+45,g.height-p.radius-16)
    end
    for _,e in ipairs(g.enemies) do
        if e.alive then
            e.hitFlash=math.max(0,e.hitFlash-dt)
            e.cooldown=math.max(0,e.cooldown-dt)
            local dx,dy=p.x-e.x,p.y-e.y
            local d=distance(dx,dy)
            if d > e.attackRange then
                local delta=math.min(e.speed*dt,d-e.attackRange)
                if d>0 then
                    e.x=clamp(e.x+dx/d*delta,e.radius+12,g.width-e.radius-12)
                    e.y=clamp(e.y+dy/d*delta,e.radius+45,g.height-e.radius-12)
                end
            elseif e.cooldown<=0 then
                e.cooldown=1.2
                if p.invulnerable<=0 then
                    p.hp=math.max(0,p.hp-e.damage)
                    p.invulnerable=0.45
                    pushEffect(g,p.x,p.y-34,'-'..e.damage,{1,0.39,0.39})
                    if p.hp==0 then
                        g.phase='lost'
                        g.message='DERROTA'
                        break
                    end
                end
            end
        end
    end
end

return Game
