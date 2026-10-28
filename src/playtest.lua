-- Fase 18: primeiro ambiente controlável de INVESTIGAÇÃO, não BarbarQ jogável.
-- Recursos visuais do APK, pose aproximada da F5, corpo Box2D real via love.physics.
-- A velocidade, o raio, os obstáculos de validação e os 30 fps NÃO foram
-- recuperados da versão nativa; nunca usá-los como mecânica canônica.
local codec = require('src.movement_codec')
local pose = require('src.pose')
local resolver = require('src.sprite_resolver')
local geometry = require('src.sprite_geometry')
local mapObjects = require('src.map_objects')
local M = {}
local state = {world = nil, body = nil, map = nil, hero = nil, lookup = nil,
               running = false, directions = 0, time = 0, cameraX = 0, cameraY = 0,
               collisionDebug = true, ready = false, steps = 0, lastContacts = 0,
               contactCount = 0, textureMisses = 0, error = nil,
               mapObjectFixtures = {}, mapObjectRects = {}, mapCollision = false,
               showMapObjects = true, mapObjectMessage = nil}
local ACCUMULATOR_LIMIT, STEP = 0.12, 1/60
local SPEED_CENTI, PIXELS_PER_METER, RADIUS = 300, 30, 18
local function validMap(map)
    return type(map)=='table' and type(map.width)=='number' and map.width>0 and
           type(map.height)=='number' and map.height>0 and
           type(map.tilewidth)=='number' and map.tilewidth>0 and
           type(map.tileheight)=='number' and map.tileheight>0
end
function M.findHero(animations)
    for _, a in ipairs(animations or {}) do
        if a.path == 'character/babarian/babarian.bexportjson' then return a end
    end
end
function M.movement(hero, running, variant)
    if not hero then return nil end
    local name = (running and 'walk_' or 'stand_') .. tostring(variant or 0)
    for _, animation in ipairs(hero.animations or {}) do
        for _, move in ipairs(animation.movements or {}) do
            if move.name == name and move.duration > 0 then return move end
        end
    end
    return nil
end
function M.inputVector(up, down, left, right)
    local x = (right and 1 or 0) - (left and 1 or 0)
    local y = (down and 1 or 0) - (up and 1 or 0)
    local magnitude = math.sqrt(x*x+y*y)
    if magnitude == 0 then return 0,0,false end
    return x/magnitude, y/magnitude, true
end
function M.reset()
    state.world = nil; state.body = nil; state.map = nil
    state.ready = false; state.running = false; state.time = 0
    state.steps = 0; state.accum = 0; state.lastContacts = 0
    state.contactCount = 0; state.error = nil; state.textureMisses = 0
    state.mapObjectFixtures = {}; state.mapObjectRects = {}
    state.mapCollision = false; state.showMapObjects = true
    state.mapObjectMessage = nil
end
local function staticBox(world,x,y,w,h)
    local body = love.physics.newBody(world,x,y,'static')
    local fixture = love.physics.newFixture(body,love.physics.newRectangleShape(w,h),1)
    fixture:setFilterData(1,3,0)
    return body,fixture
end
function M.start(map, hero, atlases)
    M.reset()
    if not validMap(map) then state.error = 'Mapa TMX inválido ou ausente'; return false end
    if not love.physics then state.error = 'LÖVE2D sem módulo love.physics'; return false end
    if not hero then state.error = 'Animação original babarian ausente'; return false end
    state.map, state.hero = map, hero
    state.mapObjectRects = mapObjects.rectangles(map)
    state.lookup = resolver.index(atlases)
    state.cameraX, state.cameraY = map.width*map.tilewidth/2, map.height*map.tileheight/2
    local ok, err = pcall(function()
        love.physics.setMeter(PIXELS_PER_METER)
        state.world = love.physics.newWorld(0,0,true)
        state.world:setCallbacks(function(a,b)
            if a and b then state.contactCount = state.contactCount + 1 end
        end)
        local x,y = state.cameraX,state.cameraY
        state.body = love.physics.newBody(state.world,x,y,'dynamic')
        state.body:setFixedRotation(true)
        local fixture = love.physics.newFixture(state.body,love.physics.newCircleShape(RADIUS),1)
        fixture:setFriction(0)
        fixture:setRestitution(0)
        fixture:setFilterData(1,3,0) -- Estado collidable da F17, NÃO dimensão canônica
        state.fixture = fixture
        local w,h = map.width * map.tilewidth, map.height * map.tileheight
        if w>2*RADIUS and h>2*RADIUS then
            local t=18
            staticBox(state.world,w/2,-t/2,w,t)
            staticBox(state.world,w/2,h+t/2,w,t)
            staticBox(state.world,-t/2,h/2,t,h)
            staticBox(state.world,w+t/2,h/2,t,h)
        end
        -- Objetos TMX recuperados sao apenas SENSORES de pesquisa por padrao.
        -- Os arquivos nao dizem que sejam obstaculos jogaveis.
        for _,rect in ipairs(state.mapObjectRects) do
            local rb = love.physics.newBody(state.world,rect.x+rect.w/2,rect.y+rect.h/2,'static')
            local rf = love.physics.newFixture(rb,love.physics.newRectangleShape(rect.w,rect.h),1)
            rf:setFilterData(1,3,0)
            rf:setSensor(true)
            state.mapObjectFixtures[#state.mapObjectFixtures+1] = rf
        end
        -- Corpo de depuração deliberadamente ARTIFICIAL, não obstáculo do mapa original.
        if w>360 and h>260 then
            state.obstacle = {x=math.min(w-RADIUS*5,x+116),y=y,w=58,h=72}
            staticBox(state.world,state.obstacle.x,state.obstacle.y,58,72)
        end
    end)
    if not ok then state.error = tostring(err); M.reset(); state.error=tostring(err); return false end
    state.ready = true
    return true
end
function M.update(dt, keys)
    if not state.ready then return end
    dt = math.max(0,math.min(dt or 0, ACCUMULATOR_LIMIT))
    local nx,ny,moving = M.inputVector(keys('w') or keys('up'),keys('s') or keys('down'),
        keys('a') or keys('left'),keys('d') or keys('right'))
    state.running = moving
    -- O codec original identifica cálculo trigonométrico e divisão por 100.
    -- 300 centésimos e 30 pixels por metro são calibração do TESTE, não do APK.
    local direction = moving and math.floor(math.deg(math.atan(ny,nx))) or 0
    local vx,vy = codec.move_vector(moving and SPEED_CENTI or 0,0,0,direction,true,false)
    -- codec quantiza direções por graus inteiros; preservamos normalização diagonal.
    -- Vetor do controle é autoritativo para o sinal e a magnitude da prévia.
    if moving then vx,vy = nx * math.sqrt(vx*vx+vy*vy), ny * math.sqrt(vx*vx+vy*vy) end
    state.body:setLinearVelocity(vx*PIXELS_PER_METER,vy*PIXELS_PER_METER)
    state.accum = math.min((state.accum or 0)+dt, ACCUMULATOR_LIMIT)
    while state.accum >= STEP do
        state.world:update(STEP)
        state.accum = state.accum - STEP
        state.steps = state.steps + 1
    end
    state.cameraX,state.cameraY = state.body:getPosition()
    if moving then state.time = state.time + dt*30 else state.time = state.time + dt*30 end
end
function M.playerPosition()
    if not state.ready then return nil end
    return state.body:getPosition()
end
function M.setVariant(number)
    if type(number)~='number' or number<0 or number>4 then return false end
    state.directions = math.floor(number)
    state.time = 0
    return true
end
function M.toggleMapObjects()
    state.showMapObjects = not state.showMapObjects
    return state.showMapObjects
end
function M.toggleMapCollision()
    if not state.ready or #state.mapObjectFixtures == 0 then
        state.mapObjectMessage = 'Este mapa nao contem retangulos TMX testaveis'
        return false
    end
    if not state.mapCollision then
        local x,y = state.body:getPosition()
        for _,rect in ipairs(state.mapObjectRects) do
            if mapObjects.overlaps(rect,x,y,RADIUS) then
                state.mapObjectMessage = 'Saia do retangulo TMX antes de ativar a colisao de teste'
                return false
            end
        end
    end
    state.mapCollision = not state.mapCollision
    for _,f in ipairs(state.mapObjectFixtures) do f:setSensor(not state.mapCollision) end
    state.mapObjectMessage = state.mapCollision and
        'Fisica experimental ON (NAO confirma obstaculo original)' or
        'Objetos TMX sem colisao (sensor)'
    return true
end
function M.toggleDebug() state.collisionDebug = not state.collisionDebug end
function M.state() return state end

function M.draw(panel, camera, context)
    local put = context.put
    if not state.ready then
        put('Laboratório indisponível: '..(state.error or 'selecione um mapa'),panel.x+15,panel.y+70)
        return
    end
    local centerX,centerY=state.body:getPosition()
    local x=panel.x+(centerX-camera.left)*camera.scale
    local y=panel.y+(centerY-camera.top)*camera.scale
    love.graphics.setScissor(panel.x,panel.y,panel.w,panel.h)
    local drawn, unresolved = 0, 0
    local movement = M.movement(state.hero,state.running,state.directions)
    local armature = state.hero.armatures and state.hero.armatures[1]
    if movement and armature then
        local frame = state.time % movement.duration
        local nodes = pose.ordered(pose.evaluate(armature,movement,frame,true,true))
        for _,node in ipairs(nodes) do
            local di=node.display_index
            local spriteName=di and di>=0 and node.bone.displays and node.bone.displays[di+1]
            local sprite=spriteName and resolver.find(state.lookup,state.hero,spriteName)
            if sprite and node.matrix then
                local image=context.imageFor(sprite.atlas.image)
                local quad=image and context.spriteQuad(sprite.atlas,sprite.frame,image)
                if quad then
                    love.graphics.push()
                    love.graphics.translate(x,y)
                    love.graphics.scale(camera.scale,-camera.scale)
                    local m=node.matrix
                    local t=love.math.newTransform()
                    t:setMatrix(m.a,m.b,m.c,m.d,m.tx,m.ty)
                    love.graphics.applyTransform(t)
                    love.graphics.setColor(1,1,1)
                    geometry.draw(image,quad,sprite.frame)
                    love.graphics.pop()
                    drawn=drawn+1
                else unresolved=unresolved+1 end
            elseif di ~= -1 then unresolved=unresolved+1 end
        end
    end
    state.textureMisses=unresolved
    if state.showMapObjects then
        for _,rect in ipairs(state.mapObjectRects) do
            love.graphics.setColor(state.mapCollision and 1 or 0.25,
                state.mapCollision and 0.65 or 0.80, 1, 0.75)
            love.graphics.rectangle('line',
                panel.x+(rect.x-camera.left)*camera.scale,
                panel.y+(rect.y-camera.top)*camera.scale,
                rect.w*camera.scale,rect.h*camera.scale)
        end
    end
    if state.collisionDebug then
        love.graphics.setColor(0.17,1,0.62,0.86)
        love.graphics.setLineWidth(2)
        love.graphics.circle('line',x,y,RADIUS*camera.scale)
        love.graphics.setLineWidth(1)
        if state.obstacle then
            local o=state.obstacle
            love.graphics.setColor(1,0.39,0.22,0.7)
            love.graphics.rectangle('line',panel.x+(o.x-o.w/2-camera.left)*camera.scale,
                panel.y+(o.y-o.h/2-camera.top)*camera.scale,o.w*camera.scale,o.h*camera.scale)
        end
    end
    love.graphics.setScissor()
    put(string.format('F14 TESTE Box2D | mapa: %s | personagem: babarian | %s_%d',
        state.map.name,state.running and 'walk' or 'stand',state.directions),
        panel.x+10,panel.y+38,{1,0.87,0.44},context.small)
    put(string.format('Posição (px): %.1f, %.1f | corpos de teste | contatos: %d',centerX,centerY,state.contactCount),
        panel.x+10,panel.y+60,{1,1,1},context.small)
    put('WASD: andar | O: objetos TMX | K: colisao TESTE | C: debug | R: reiniciar',
        panel.x+10,panel.y+panel.h-50,{1,1,1},context.small)
    put(string.format('Pose original: %d partes visíveis, %d não resolvidas; geometria e 30 fps PROVISÓRIOS',
        drawn,unresolved),panel.x+10,panel.y+panel.h-27,{1,0.77,0.45},context.small)
    put(string.format('Objetos TMX: %d | teste fisico: %s | %s',
        #state.mapObjectRects,state.mapCollision and 'ativo' or 'inativo',
        state.mapObjectMessage or 'sem semantica de colisao confirmada'),
        panel.x+10,panel.y+82,{0.69,0.91,1},context.small)
end
return M