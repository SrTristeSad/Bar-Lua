-- F36: predicados especificos demonstrativos, extraidos das instrucoes ARM64.
-- Recebem CAMP/KIND/BUFF ja resolvidos: NAO leem memoria de Entity nem aplicam dano.
local M = {}

local function integer(v)
    return type(v)=='number' and v==v and v%1==0
end

local function invert_if_other_contain(equal, contain)
    -- O ARM64 executa cset(ne) e eor do resultado booleano com o teste.
    if contain==3 then return equal end
    return not equal
end

-- CCampCondition::GetTargetResult / GetCreatorResult:
-- tipos 1/2 comparam os campos camp +0x17C; 3..8 testam ID 0..5.
function M.camp(kind, contain, subject, reference)
    if not integer(kind) or not integer(contain) then return nil,'tipo invalido' end
    if not integer(subject) then return false end
    local yes
    if kind==1 or kind==2 then
        if not integer(reference) then return false end
        yes = (kind==1 and subject==reference) or (kind==2 and subject~=reference)
    elseif kind>=3 and kind<=8 then
        yes = subject==(kind-3)
    else
        return false
    end
    return invert_if_other_contain(yes, contain)
end

-- CEntityKindTypeCondition::GetTargetResult/GetCreatorResult:
-- campo +0x20 do Entity com inteiro configurado; NULL retorna falso.
function M.entity_kind(contain, actual, expected)
    if not integer(contain) or not integer(expected) then return nil,'configuracao invalida' end
    if not integer(actual) then return false end
    return invert_if_other_contain(actual==expected,contain)
end

-- CBuffCondition::GetTargetResult: Entity::getStateDetails(id) retorna ponteiro
-- opcional, byte +0x4 = flag. XOR com (ContainType == 2).
-- flag=nil significa ausência do registro, entity_present=false significa GetEntity NULL.
function M.buff_state(contain, entity_present, flag)
    if not integer(contain) then return nil,'contain invalido' end
    if not entity_present then return false end
    if flag==nil then return contain==2 end
    if not integer(flag) or flag<0 or flag>255 then return nil,'byte de estado invalido' end
    if contain==2 then return flag~=1 end
    return flag~=0
end

return M
