-- F38: painel de inspecao, com IDs ficticios e resultados artificiais.
local gate=require('src.skill_condition_gate')
local M={}
local index=1
local cases={
 {name='Criador: lista ausente',creator=nil,target={},fail={}},
 {name='Criador: lista vazia',creator={},target={},fail={}},
 {name='Criador: duas aprovadas',creator={11,12},target={21},fail={}},
 {name='Criador: falha no primeiro',creator={11,12},target={21},fail={[11]=true}},
 {name='Criador: falha no segundo',creator={11,12,13},target={21},fail={[12]=true}},
 {name='Alvo: falha no primeiro',creator={11},target={21,22},fail={[21]=true}},
 {name='Alvo: falha no segundo',creator={11},target={21,22,23},fail={[22]=true}},
 {name='Alvo: lista ausente',creator={11},target=nil,fail={}},
}
function M.reset()index=1 end
function M.keypressed(key)
    if key=='right' or key=='down' then index=index%#cases+1;return true end
    if key=='left' or key=='up' then index=(index-2+#cases)%#cases+1;return true end
    if key=='r' then M.reset();return true end
    return false
end
function M.snapshot(report)
    if type(report)~='table' or report.phase~=38 or report.gameplay_enabled~=false then
        return nil,'Relatorio F38 ausente ou incompativel'
    end
    local c=cases[index]
    local result=gate.evaluate_both(c.creator,c.target,function(id) return not c.fail[id] end,{})
    return {index=index,total=#cases,name=c.name,accepted=result.accepted,phase=result.phase,
        creator=result.creator,target=result.target,skill_id=report.skill_id,
        instructions=report.verified_instructions,checks=report.checkpoints,
        target_noarg=gate.target_noarg()}
end
function M.draw(report,panel)
    panel.background(panel.x,panel.y,panel.w,panel.h,{0.12,0.16,0.20})
    local function put(msg,offset,color)
        if offset>=0 and offset<panel.h-10 then
            panel.put(tostring(msg),panel.x+18,panel.y+offset,color or {0.92,0.94,0.97},panel.small)
        end
    end
    put('F38 | CSkill -> CConditionManager -> CCondition',20,{1,0.82,0.42})
    put('Funcoes nativas auditadas, predicados de exemplo (nao sao do APK).',52,{1,0.72,0.52})
    local s,err=M.snapshot(report)
    if not s then put(err,105,{1,0.5,0.44});return end
    put(string.format('Cenario %d/%d: %s',s.index,s.total,s.name),107,{0.74,1,0.73})
    put('Porta do criador: '..(s.creator.accepted and 'APROVADA' or 'REPROVADA')..' | avaliadas='..s.creator.visited,154)
    if s.target then put('Porta do alvo: '..(s.target.accepted and 'APROVADA' or 'REPROVADA')..' | avaliadas='..s.target.visited,192)
    else put('Porta do alvo: NAO EXECUTADA por falha anterior',192,{1,0.75,0.52}) end
    put('Resultado da demonstracao: '..(s.accepted and 'aprovado' or 'reprovado'),237,{0.75,1,0.77})
    put('Sobrecarga alvo sem argumento: TRUE incondicional',278)
    put('Offsets: CSkill+0x28 criador; CSkill+0x30 alvo',318)
    put('Config: +0xb0 criador; +0xd0 alvo',352)
    put('Botao original 10039 -> habilidade '..s.skill_id,392,{0.76,0.91,1})
    put('Nenhuma condicao especifica foi atribuida a essa habilidade.',423,{1,0.72,0.52})
    put('SEM dano, selecao final ou mudanca na cena.',466,{1,0.72,0.52})
    put('Setas: mudar cenario     R: reiniciar',panel.h-58)
end
return M
