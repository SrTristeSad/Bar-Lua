-- F20: prévia, SEM dano/rede/cooldown/área de acerto.
-- Durações do bexportjson são contagens de quadros; 30 fps é convenção de inspeção.
local M = {}
local function lookup(hero, name)
    for _,anim in ipairs((hero and hero.animations) or {}) do
        for _,move in ipairs(anim.movements or {}) do
            if move.name==name and type(move.duration)=='number' and move.duration>0 then
                return move
            end
        end
    end
end
function M.new(hero, fps)
    return {hero=hero, fps=fps or 30, action=nil, elapsed=0, variant=0}
end
function M.begin(state, number, variant)
    if not state or state.action then return false end
    if type(number)~='number' or number<1 or number>3 or number%1~=0 then return false end
    if type(variant)~='number' or variant<0 or variant>4 or variant%1~=0 then return false end
    local action=lookup(state.hero,('attack%d_%d'):format(number,variant))
    if not action then return false end
    state.action=action
    state.variant=variant
    state.elapsed=0
    return true
end
function M.update(state, dt)
    if not state or not state.action then return false end
    if type(dt)~='number' or dt~=dt or dt<0 or dt==math.huge then return false end
    state.elapsed=state.elapsed+dt
    if state.elapsed*state.fps >= state.action.duration then
        state.action=nil
        state.elapsed=0
        return true
    end
    return false
end
function M.sample(state)
    if not state or not state.action then return nil end
    return state.action, math.min(state.elapsed*state.fps, state.action.duration-0.0001)
end
function M.cancel(state)
    if state then state.action=nil;state.elapsed=0 end
end
return M
