-- Geometria TMX recuperada. Nao infere colisao canônica.
local M = {}
function M.rectangles(map)
    local out = {}
    if type(map) ~= 'table' then return out end
    for _,group in ipairs(map.objectgroups or {}) do
        for _,obj in ipairs(group.objects or {}) do
            local x,y,w,h = tonumber(obj.x),tonumber(obj.y),tonumber(obj.width),tonumber(obj.height)
            if obj.shape == 'rectangle' and (obj.rotation or 0) == 0 and
               x and y and w and h and x == x and y == y and
               w > 0 and h > 0 and w < 1e6 and h < 1e6 then
                out[#out+1] = {x=x,y=y,w=w,h=h,id=obj.id,
                                  name=obj.name,group=group.name}
            end
        end
    end
    return out
end
function M.overlaps(rect,x,y,r)
    return x+r > rect.x and x-r < rect.x+rect.w and
           y+r > rect.y and y-r < rect.y+rect.h
end
return M
