-- F38: modelo puro da ordem de verificacao observada em CSkill.
-- Recebe predicados ficticios; nao resolve CCondition nem aplica combate.
local M={}

function M.evaluate(conditions, evaluator, context)
    if conditions == nil then
        return {accepted=true, visited=0, reason='lista ausente', failed_id=nil}
    end
    if type(conditions)~='table' or type(evaluator)~='function' then
        return nil,'lista/evaluator invalidos'
    end
    for i, id in ipairs(conditions) do
        if type(id)~='number' then return nil,'id de condicao invalido' end
        local result=evaluator(id,context)
        if result~=true and result~=false then return nil,'resultado de condicao invalido' end
        if not result then
            return {accepted=false, visited=i, reason='condicao reprovada',failed_id=id}
        end
    end
    return {accepted=true,visited=#conditions,reason='todas aprovadas',failed_id=nil}
end

function M.target_noarg()
    -- A sobrecarga nativa sem argumento retorna 1, nao percorre condicoes.
    return true
end

function M.evaluate_both(creator_ids,target_ids,evaluator,context)
    local creator,err=M.evaluate(creator_ids,evaluator,context)
    if not creator then return nil,err end
    if not creator.accepted then
        return {creator=creator,target=nil,accepted=false,phase='creator'}
    end
    local target,err2=M.evaluate(target_ids,evaluator,context)
    if not target then return nil,err2 end
    return {creator=creator,target=target,accepted=target.accepted,phase=target.accepted and 'pass' or 'target'}
end
return M
