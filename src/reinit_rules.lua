-- F28: reproduz SOMENTE a aritmética das atribuições do ramo incremental
-- de Hero::reInit(int, false) do BarbarQ 1.0.1811.
-- Deslocamentos são metadados ARM64, não nomes semânticos de atributos.
local M={}
local MIN,MAX=-2147483648,2147483647
local delta_fields={
    {'0xc0','0x38'}, {'0x32c','0x3c'}, {'0x330','0x40'},
    {'0x310','0x44'}, {'0x314','0x44'}, {'0x328','0x48'},
    {'0x318','0x4c'}, {'0x31c','0x4c'}, {'0x1b8','0x50'},
}
M.fields=delta_fields
local function int(n)
    return type(n)=='number' and n==math.floor(n) and n>=MIN and n<=MAX
end
function M.configId(base_id,level)
    if not int(base_id) or not int(level) or level<1 then
        return nil,'IDs e nível devem ser inteiros válidos; nível >= 1'
    end
    local n=base_id+(level-1)*10000
    if not int(n) then return nil,'overflow int32 não modelado' end
    return n
end
-- Os testes devem passar flags explicitamente; a falta de informação não
-- pode assumir que ramos condicionais do executável ficaram desligados.
function M.applySimpleDelta(old_config,new_config,entity,flags)
    if type(old_config)~='table' or type(new_config)~='table' or
       type(entity)~='table' or type(flags)~='table' then
       return nil,'configs, entity e flags obrigatórios'
    end
    if flags.extra_204_active~=false or flags.nested_88_active~=false then
       return nil,'ramos opcionais +0x204/+0x88 não reproduzidos'
    end
    local result={}
    for k,v in pairs(entity) do result[k]=v end
    for _,pair in ipairs(delta_fields) do
        local dst,src=pair[1],pair[2]
        local before,after,current=old_config[src],new_config[src],entity[dst]
        if not int(before) or not int(after) or not int(current) then
            return nil,'campo não inteiro ou ausente: '..dst..' / '..src
        end
        local next_value=current+(after-before)
        if not int(next_value) then return nil,'overflow int32 em '..dst end
        result[dst]=next_value
    end
    -- Esta atribuição é direta no ARM64, não um delta.
    result['0xe0']=new_config['0x48']
    return result
end
-- O ramo de lista compara IDs da configuração nova com os da anterior.
-- Operação apenas sobre listas já decodificadas; parsing e addSkill omitidos.
function M.newSkillIds(old_ids,new_ids)
    if type(old_ids)~='table' or type(new_ids)~='table' then
        return nil,'listas de IDs obrigatórias'
    end
    local old={}
    for _,v in ipairs(old_ids) do
        if not int(v) then return nil,'ID anterior inválido' end
        old[v]=true
    end
    local out={}
    for _,v in ipairs(new_ids) do
        if not int(v) then return nil,'ID novo inválido' end
        if not old[v] then out[#out+1]=v end
    end
    return out
end
return M
