-- F29: leitura apenas dos slots numericos de HeroConfig recuperados do APK.
-- F30 identificou 0x44 como HP inicial; F31 identificou 0x48 como velocidade-base.
local M={}
M.slots={'0x38','0x3c','0x40','0x44','0x48','0x4c','0x50','0x54'}
local function level(group,number)
    if type(group)~='table' or type(group.levels)~='table' or type(number)~='number'
        or number%1~=0 or number<1 then return nil end
    return group.levels[number]
end
function M.value(group,number,slot)
    local row=level(group,number)
    if not row or type(row.values)~='table' then return nil,'nivel indisponivel' end
    for _,known in ipairs(M.slots) do
        if slot==known then return row.values[slot] end
    end
    return nil,'slot invalido'
end
function M.diff(group,old_level,new_level)
    local old,new=level(group,old_level),level(group,new_level)
    if not old or not new then return nil,'nivel nao recuperado' end
    local diff={}
    for _,slot in ipairs(M.slots) do
        local a,b=old.values[slot],new.values[slot]
        if type(a)~='number' or type(b)~='number' then
            return nil,'slot ausente: '..slot
        end
        diff[slot]=b-a
    end
    return diff
end
return M
