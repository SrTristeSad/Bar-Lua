-- F36: painel de comparacao de predicados; configuracoes de exemplo ficticias.
local rules=require('src.concrete_conditions')
local M={}
local idx=1
local samples={
    {label='Camp: mesmo time',kind='camp',a={1,3,2,2}},
    {label='Camp: equipes distintas',kind='camp',a={2,3,1,2}},
    {label='Camp: time 3 (ID 2)',kind='camp',a={5,3,2,4}},
    {label='Camp: negacao do time 3',kind='camp',a={5,4,2,4}},
    {label='Camp: referencia ausente',kind='camp',a={1,4,1,nil}},
    {label='EntityKind: tipo igual',kind='entity',a={3,8,8}},
    {label='EntityKind: tipo diferente',kind='entity',a={4,8,8}},
    {label='EntityKind: entidade ausente',kind='entity',a={4,nil,8}},
    {label='Buff: estado presente e ativo',kind='buff',a={2,true,1}},
    {label='Buff: estado ausente',kind='buff',a={2,true,nil}},
    {label='Buff: alvo ausente',kind='buff',a={2,false,nil}},
}
function M.reset()idx=1 end
function M.keypressed(key)
    if key=='right' or key=='down' then idx=idx%#samples+1;return true end
    if key=='left' or key=='up' then idx=(idx-2+#samples)%#samples+1;return true end
    if key=='r' then idx=1;return true end
    return false
end
function M.snapshot(report)
    if type(report)~='table' or report.phase~=36 then
        return nil,'Relatorio F36 nao encontrado'
    end
    local s=samples[idx]
    local result,error
    if s.kind=='camp' then result,error=rules.camp(s.a[1],s.a[2],s.a[3],s.a[4])
    elseif s.kind=='entity' then result,error=rules.entity_kind(s.a[1],s.a[2],s.a[3])
    else result,error=rules.buff_state(s.a[1],s.a[2],s.a[3]) end
    return {name=s.label,index=idx,total=#samples,result=result,error=error,kind=s.kind,
        arguments=s.a,functions=report.functions,checks=report.checkpoints}
end
function M.draw(report,panel)
    panel.background(panel.x,panel.y,panel.w,panel.h,{0.12,0.16,0.20})
    local function line(t,y,c)
        if y<panel.h-12 then panel.put(t,panel.x+16,panel.y+y,c or {0.95,0.96,0.98},panel.small) end
    end
    line('F36 | Camp / EntityKind / Buff (ARM64)',20,{1,0.82,0.4})
    line('Somente testes de predicados: sem alvo final e sem dano.',55,{1,0.70,0.53})
    local state,err=M.snapshot(report)
    if not state then line(err,100,{1,0.55,0.5});return end
    line(string.format('Exemplo %d/%d: %s',state.index,state.total,state.name),110,{0.76,1,0.8})
    local args={}
    for i=1,(state.kind=="camp" and 4 or 3) do args[i]=tostring(state.arguments[i]) end
    line('Parametros do modelo: '..table.concat(args,', '),155)
    line('Resultado: '..tostring(state.result),205,state.result and {0.7,1,0.73} or {1,0.7,0.62})
    line('Funcoes nativas auditadas: '..state.functions..'   checks: '..state.checks,253)
    line('Camp: compara ID de equipe em Entity +0x17C',305)
    line('EntityKind: compara tipo interno em Entity +0x20',337)
    line('Buff: interpreta byte de StateDetails +0x4',369)
    line('Contextos de combate/skill ainda nao reproduzidos.',409,{1,0.70,0.53})
    line('Setas: mudar exemplo    R: reiniciar',panel.h-59)
end
return M
