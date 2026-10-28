-- F37: painel de predicados relacionais e numericos. Exemplos sem vinculo com skills reais.
local rules=require('src.compare_conditions')
local M={}
local index=1
local samples={
 {name='SkillEntity modo 1: igual',what='entity',args={1,3,77,77}},
 {name='SkillEntity modo 1: negado',what='entity',args={1,4,77,77}},
 {name='SkillEntity modo 3: criador',what='entity',args={3,3,10,10}},
 {name='SkillEntity modo 3: nao criador',what='entity',args={3,4,11,10}},
 {name='Compare: igualdade tolerada',what='cmp',args={12,12.00005,3}},
 {name='Compare: diferente alem tolerancia',what='cmp',args={12,12.0002,4}},
 {name='Compare: maior estrito',what='cmp',args={15,12,5}},
 {name='Compare: maior/igual',what='cmp',args={12,12,6}},
 {name='Compare: menor estrito',what='cmp',args={9,12,7}},
 {name='Compare: menor/igual',what='cmp',args={12,12,8}},
 {name='Compare: operacao porcentual 0 (soma)',what='cmp',args={10,12,6},left_op={code=0,parameter=200}},
 {name='Compare: sentinela -1',what='cmp',args={-1,10,5}},
}
function M.reset()index=1 end
function M.keypressed(key)
    if key=='right' or key=='down' then index=index%#samples+1;return true end
    if key=='left' or key=='up' then index=(index-2+#samples)%#samples+1;return true end
    if key=='r' then index=1;return true end
    return false
end
function M.snapshot(report)
    if type(report)~='table' or report.phase~=37 then return nil,'Relatorio F37 indisponivel' end
    local s=samples[index]
    local result,err
    if s.what=='entity' then
        result,err=rules.skill_entity(s.args[1],s.args[2],s.args[3],s.args[4])
    else
        result,err=rules.compare(s.args[1],s.args[2],s.args[3],report.epsilon,s.left_op,s.right_op)
    end
    return {index=index,total=#samples,label=s.name,kind=s.what,result=result,error=err,
        functions=report.functions,checks=report.checkpoints,epsilon=report.epsilon,
        params=s.args}
end
function M.draw(report,panel)
    panel.background(panel.x,panel.y,panel.w,panel.h,{0.12,0.16,0.20})
    local function line(text,y,color)
        if y<panel.h-15 then panel.put(text,panel.x+16,panel.y+y,color or {0.95,0.97,1},panel.small) end
    end
    line('F37 | Comparacao de valores / SkillEntity',20,{1,0.82,0.4})
    line('Modelo isolado, nenhum ataque causa dano.',54,{1,0.69,0.53})
    local s,err=M.snapshot(report)
    if not s then line(err,100,{1,0.6,0.5});return end
    line(string.format('Exemplo %d/%d: %s',s.index,s.total,s.label),110,{0.75,1,0.82})
    local p={} for _,v in ipairs(s.params) do p[#p+1]=tostring(v) end
    line('Entradas (ja resolvidas): '..table.concat(p,', '),158)
    line('Resultado: '..tostring(s.result),204,s.result and {0.75,1,0.75} or {1,0.72,0.65})
    line('Tolerancia igualdade: '..string.format('%.8g',s.epsilon),248)
    line('Funcoes auditadas: '..s.functions..'  verificacoes: '..s.checks,290)
    line('Modos 1/3: ID do CSkillEntity / relacao com criador.',337)
    line('Comparadores 3..8: ~=, !=, >, >=, <, <=.',372)
    line('Operacoes 0..3: +, -, *, / com parametro /100.',407)
    line('Sem associacao confirmada com habilidade 4010020.',448,{1,0.69,0.53})
    line('Setas: mudar exemplo    R: reiniciar',panel.h-58)
end
return M
