-- Collision and group steering for the playable BarbarQ Lua alpha.
-- Circle radii, steering and wall margins are ALPHA rules, not native BarbarQ.
-- Pure Lua; no love.physics dependency, so Windows and CI share identical math.
local M={}
local EPS=1e-8
local function clamp(value,min,max)
    return math.max(min,math.min(max,value))
end
local function project(a,w,h,padding)
    local r=a.radius or 0
    local minX=r+padding
    local minY=r+padding+30
    a.x=clamp(a.x,minX,math.max(minX,w-minX))
    a.y=clamp(a.y,minY,math.max(minY,h-r-padding))
end
M.project=project

local function separate(a,b,aShare)
    local dx,dy=b.x-a.x,b.y-a.y
    local minDist=(a.radius or 0)+(b.radius or 0)
    local d2=dx*dx+dy*dy
    if d2>=minDist*minDist then return false end
    local distance=math.sqrt(d2)
    local nx,ny
    if distance<EPS then
        -- Deterministic recovery from coincident positions.
        nx,ny=1,0
    else
        nx,ny=dx/distance,dy/distance
    end
    local penetration=minDist-distance
    aShare=aShare or 0.5
    a.x=a.x-nx*penetration*aShare
    a.y=a.y-ny*penetration*aShare
    b.x=b.x+nx*penetration*(1-aShare)
    b.y=b.y+ny*penetration*(1-aShare)
    return true
end
M.separate=separate

function M.solve(g,iterations)
    local enemies=g.enemies or {}
    iterations=iterations or 8
    for _=1,iterations do
        local changes=0
        local p=g.player
        project(p,g.width,g.height,16)
        for _,e in ipairs(enemies) do
            if e.alive then
                project(e,g.width,g.height,12)
                if separate(p,e,0.3) then changes=changes+1 end
            end
        end
        for i=1,#enemies do
            local a=enemies[i]
            if a.alive then
                for j=i+1,#enemies do
                    local b=enemies[j]
                    if b.alive and separate(a,b,0.5) then changes=changes+1 end
                end
            end
        end
        project(p,g.width,g.height,16)
        for _,e in ipairs(enemies) do
            if e.alive then project(e,g.width,g.height,12) end
        end
        if changes==0 then break end
    end
end

function M.steer(e,p,enemies)
    local dx,dy=p.x-e.x,p.y-e.y
    local distance=math.sqrt(dx*dx+dy*dy)
    if distance<EPS then return 0,0,0 end
    local fx,fy=dx/distance,dy/distance
    local ax,ay=0,0
    for _,other in ipairs(enemies) do
        if other~=e and other.alive then
            local sx,sy=e.x-other.x,e.y-other.y
            local d2=sx*sx+sy*sy
            local soft=(e.radius or 17)+(other.radius or 17)+54
            if d2<soft*soft then
                local d=math.sqrt(d2)
                if d<EPS then
                    -- Stable order-based fallback using distinct skin indexes.
                    sx=(e.skin or 1)<(other.skin or 2) and -1 or 1
                    sy=0
                    d=1
                end
                local weight=(soft-math.min(d,soft))/soft
                ax=ax+(sx/d)*weight
                ay=ay+(sy/d)*weight
            end
        end
    end
    local magnitude=math.sqrt(ax*ax+ay*ay)
    if magnitude>1 then ax,ay=ax/magnitude,ay/magnitude end
    local vx,vy=fx+ax*0.78,fy+ay*0.78
    local n=math.sqrt(vx*vx+vy*vy)
    if n<EPS then return fx,fy,distance end
    return vx/n,vy/n,distance
end
return M
