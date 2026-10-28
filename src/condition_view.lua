-- F35: bancada SEM dano, SEM CCondition real e sem manipulacao da partida.
local rules=require('src.condition_rules')
local M={}
local index=1
local scenarios={
    {name='Filtro base: exclusao por swap',kind='base',items={1,2,3,4},predicate=function(v) return v%2==0 end},
    {name='Filtro base: todos passam',kind='base',items={2,4,6},predicate=function(v) return v%2==0 end},
    {name='Filtro base: nenhum candidato',kind='base',items={},predicate=function(v) return v>0 end},
    {name='Pacote: condicoes hipoteticas em serie',kind='chain',items={1,2,3,4,5},predicates={function(v) return v>1 end,function(v) return v%2==0 end}},
    {name='Pacote: para quando lista esvazia',kind='chain',items={1,2},predicates={function() return false end,function() error('nao deveria executar') end}},
    {name='Quantidade: conserva dois primeiros',kind='count',items={11,22,33,44},count=2,random=false},
    {name='Quantidade: sorteio ainda desconhecido',kind='count',items={11,22,33,44},count=2,random=true},
}
function M.reset() index=1 end
function M.keypressed(key)
    if key=='right' or key=='down' then index=(index%#scenarios)+1;return true end
    if key=='left' or key=='up' then index=(index-2+#scenarios)%#scenarios+1;return true end
    if key=='r' then M.reset(); return true end
    return false
end
function M.snapshot(report)
    if type(report)~='table' or report.phase~=35 or report.predicates_resolved~=false then
        return nil,'relatorio F35 ausente/incompativel'
    end
    local s=scenarios[index]
    local result,err
    if s.kind=='base' then result,err=rules.filter_targets(s.items,s.predicate)
    elseif s.kind=='chain' then result,err=rules.apply_chain(s.items,s.predicates)
    else result,err=rules.limit_count(s.items,s.count,s.random) end
    local src={}
    for _,v in ipairs(s.items) do src[#src+1]=tostring(v) end
    local dst={}
    for _,v in ipairs((result or {}).items or {}) do dst[#dst+1]=tostring(v) end
    return {index=index,total=#scenarios,name=s.name,kind=s.kind,
        original=table.concat(src,', '),remaining=result and table.concat(dst,', ') or '(nao calculado)',
        result=result,error=err,instructions=report.verified_instructions,checks=report.checkpoints}
end
function M.draw(report,panel)
    panel.background(panel.x,panel.y,panel.w,panel.h,{0.12,0.16,0.20})
    local function put(s,dy,color)
        if dy<panel.h-12 then
            panel.put(s,panel.x+18,panel.y+dy,color or {0.92,0.94,0.97},panel.small)
        end
    end
    put('F35 | CCondition / CPackCondition / TargetsCount',20,{1,0.82,0.42})
    put('Predicados demonstrativos. Nao representam efeitos reais das habilidades.',55,{1,0.70,0.53})
    local s,err=M.snapshot(report)
    if not s then put(err or 'Relatorio indisponivel',95,{1,0.50,0.44});return end
    put(string.format('Exemplo %d/%d: %s',s.index,s.total,s.name),110,{0.74,1,0.73})
    put('Candidatos iniciais: ['..s.original..']',152)
    put('Restantes: ['..s.remaining..']',183)
    if s.error then put('Nao reproduzido: '..s.error,222,{1,0.70,0.53})
    else put('Restantes: '..tostring(s.result.remaining),222,{0.72,0.95,0.76}) end
    put('Base: swap-removal, ordem dos candidatos pode mudar.',283)
    put('Pacote: lista e contexto compartilhados; filtros executados em ordem.',315)
    put('Count: sorteio original nao reconstruido.',349,{1,0.70,0.53})
    put('NENHUM alvo e validado para combate nem sofre dano.',393,{1,0.70,0.53})
    put('Setas: trocar exemplo   R: reiniciar',panel.h-59)
end
return M
