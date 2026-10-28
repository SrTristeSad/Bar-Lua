-- F34: bancada de predicados do callback; sem inserir hits na partida.
local filter=require('src.sector_filter')
local M={}
local index=1
local scenarios={
    {name='Circulo na frente',candidate={userData=true,mask=1,shape=1,x=60,y=0,radius=10}},
    {name='Circulo atras',candidate={userData=true,mask=1,shape=1,x=-50,y=0,radius=10}},
    {name='Retangulo na borda lateral',candidate={userData=true,mask=1,shape=2,x=35,y=35,width=20,height=20}},
    {name='Entidade tipo 3 atras',candidate={userData=true,mask=1,shape=3,x=-50,y=0}},
    {name='Mascara incompatível',candidate={userData=true,mask=2,shape=1,x=40,y=0,radius=10}},
    {name='Body sem Entity',candidate={userData=false,mask=1,shape=1,x=40,y=0,radius=10}},
}
function M.reset() index=1 end
function M.keypressed(key)
    if key=='right' or key=='down' then index=(index%#scenarios)+1;return true end
    if key=='left' or key=='up' then index=(index-2+#scenarios)%#scenarios+1;return true end
    if key=='r' then M.reset();return true end
    return false
end
function M.snapshot(report)
    if type(report)~='table' or report.phase~=34 or report.conditions_resolved~=false then
        return nil,'relatorio F34 ausente/incompativel'
    end
    local q={cx=0,cy=0,radius=76,heading=0,width=90,mask=1}
    local scene=scenarios[index]
    local result,err=filter.inspect(scene.candidate,q)
    if not result then return nil,err end
    return {name=scene.name,index=index,total=#scenarios,
            result=result,query=q,candidate=scene.candidate,
            instructions=report.verified_instructions,checks=report.checkpoints}
end
function M.draw(report,panel)
    panel.background(panel.x,panel.y,panel.w,panel.h,{0.12,0.16,0.20})
    local function put(s,dy,col)
        if dy<panel.h-16 then panel.put(s,panel.x+19,panel.y+dy,col or {0.92,0.94,0.98},panel.small) end
    end
    put('F34  |  QueryAABB -> ReportFixture -> Filter',22,{1,0.82,0.40})
    put('Apenas candidatos; nenhum dano, alvo definitivo ou hitbox real.',58,{1,0.70,0.53})
    local state,err=M.snapshot(report)
    if not state then put(err or 'Relatorio ausente',96,{1,0.5,0.4});return end
    put(string.format('Cenario %d/%d: %s',state.index,state.total,state.name),104,{0.78,1,0.78})
    local c,q,r=state.candidate,state.query,state.result
    put(string.format('Centro (0,0), raio %d, abertura %d graus, direcao %d',q.radius,q.width,q.heading),137)
    put(string.format('Mascara callback=%d  entidade=%d  forma=%d',q.mask,c.mask,c.shape),169)
    put('Filtro de geometria: '..(r.preselected and 'PASSOU (pre-selecao)' or 'REJEITOU'),208,
        r.preselected and {0.66,1,0.67} or {1,0.68,0.52})
    put('Motivo: '..r.reason,244)
    put('Etapa: '..r.stage,274)
    if r.angle then put(string.format('Angulo calculado: %.2f / meia abertura: %d',r.angle,r.halfwidth),307) end
    put('CCondition posterior: NAO EXECUTADA NESTE MODELO.',366,{1,0.76,0.52})
    put('Candidato aceito nao significa alvo final nem dano.',397,{1,0.76,0.52})
    put('Setas: proximo/anterior cenario   |   R: reiniciar',panel.h-62)
end
return M
