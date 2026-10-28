-- F37: predicados isolados; argumentos sao valores ja resolvidos de CSkillEntity / Entity.
-- Nao executa ParseValueInfo, nao consulta entidades reais nem aplica dano.
local M={}
local function number(v) return type(v)=='number' and v==v and v~=math.huge and v~=-math.huge end
local function integer(v) return number(v) and v%1==0 end

-- modo 1: igualdade entre IDs primarios do CSkillEntity (offset +0x0).
-- modo 3: alvo Entity +0x30 comparado a origem Entity +0x188.
-- modo inesperado: retorno somente por ContainType == 3.
function M.skill_entity(mode,contain,candidate,creator)
    if not integer(mode) or not integer(contain) then return nil,'configuracao invalida' end
    if mode~=1 and mode~=3 then return contain==3 end
    if not integer(candidate) or not integer(creator) then return nil,'campos da entidade nao resolvidos' end
    local eq = candidate==creator
    return (contain==3) == eq
end

-- CCompareValueCondition::Operate: o operando e percentual (100 == 1).
-- Codigos 0/1/2/3 = adicao/subtracao/multiplicacao/divisao.
function M.operate(value,code,parameter)
    if not number(value) or not integer(code) or not number(parameter) then
        return nil,'numero/operacao invalida'
    end
    local p=parameter/100
    if code==0 then return value+p
    elseif code==1 then return value-p
    elseif code==2 then return value*p
    elseif code==3 then
        if p==0 then return nil,'divisao por zero nao demonstrada' end
        return value/p
    end
    return value
end

-- Operandos de GetResult ja foram resolvidos pelo chamador com
-- SParseValueInfo + Entity::getValueByType; NUNCA inferir ValueType por ID.
-- O codigo 1001 no original obtem valor de SParseValueInfo e divide por 100.
-- 'op' opcional: tabela {code=0..3,parameter=<inteiro percentual>}.
-- comparadores: 3 aprox ==, 4 aprox !=, 5 >, 6 >=, 7 <, 8 <=.
function M.compare(left,right,comparator,epsilon,left_op,right_op)
    if not number(left) or not number(right) or not integer(comparator) or not number(epsilon) or epsilon<=0 then
        return nil,'parametros invalidos'
    end
    -- O original retorna falso quando algum valor e sentinela -1.
    if left==-1 or right==-1 then return false end
    local a,b=left,right
    if left_op then
        if type(left_op)~='table' then return nil,'operacao esquerda invalida' end
        local err;a,err=M.operate(a,left_op.code,left_op.parameter)
        if a==nil then return nil,err end
    end
    if right_op then
        if type(right_op)~='table' then return nil,'operacao direita invalida' end
        local err;b,err=M.operate(b,right_op.code,right_op.parameter)
        if b==nil then return nil,err end
    end
    if comparator==3 then return math.abs(a-b)<=epsilon
    elseif comparator==4 then return math.abs(a-b)>epsilon
    elseif comparator==5 then return a>b
    elseif comparator==6 then return a>=b
    elseif comparator==7 then return a<b
    elseif comparator==8 then return a<=b
    end
    return false
end
return M
