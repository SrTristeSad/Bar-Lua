-- F35: modelos isolados de operacoes de vetor auditadas no ARM64.
-- Os predicados sao EXPLICITAMENTE fornecidos pelo teste; nao sao CCondition reais.
local M = {}

local function clone(items)
    if type(items) ~= 'table' then return nil, 'vetor deve ser uma tabela' end
    local out = {}
    for i=1,#items do out[i] = items[i] end
    return out
end

function M.all_pass(items, predicate)
    if type(items) ~= 'table' or type(predicate) ~= 'function' then
        return nil, 'vetor ou predicado invalido'
    end
    for i=1,#items do
        if not predicate(items[i], i) then return false end
    end
    return true -- CCondition::GetTargetResult retorna verdadeiro para vetor vazio
end

function M.filter_targets(items, predicate)
    if type(predicate) ~= 'function' then return nil, 'predicado nao informado' end
    local out, err = clone(items)
    if not out then return nil,err end
    local i, removed=1,0
    while i <= #out do
        if predicate(out[i],i) then
            i=i+1
        else
            out[i]=out[#out] -- swap-remove original de CCondition::FilterTarget
            out[#out]=nil
            removed=removed+1
        end
    end
    return {items=out,remaining=#out,removed=removed,nonempty=#out>0}
end

-- Representa somente a ordem sequencial de CSelectTargetSector::Filter.
-- Cada predicado e hipotetico, NAO e implementacao de conditioncamp/conditionbuff etc.
function M.apply_chain(items, predicates)
    if type(predicates) ~= 'table' then return nil, 'predicados invalidos' end
    local out,err = clone(items)
    if not out then return nil,err end
    local steps = {}
    for i=1,#predicates do
        if #out==0 then break end -- a camada Sector interrompe ao ficar vazio
        local result, e=M.filter_targets(out,predicates[i])
        if not result then return nil,e end
        out=result.items
        steps[#steps+1]={index=i,remaining=#out,removed=result.removed}
    end
    return {items=out,remaining=#out,steps=steps,final_target=nil,damage_applied=false}
end

-- CTargetsCountCondition::FilterTarget, parte deterministica reproduzida.
-- O modo aleatorio antes de truncar exige RandNum::__NextInt original.
function M.limit_count(items, count, random)
    if type(count)~='number' or count%1~=0 or count<0 then
        return nil,'limite de alvos deve ser inteiro nao negativo'
    end
    local out,err=clone(items)
    if not out then return nil,err end
    local original=#out
    if count >= original then
        return {items=out,remaining=original,random_required=false,limited=false}
    end
    if random and count>0 then
        return nil,'ordenacao aleatoria original ainda nao recuperada'
    end
    for i=original,count+1,-1 do out[i]=nil end
    return {items=out,remaining=#out,random_required=false,limited=true}
end

return M
