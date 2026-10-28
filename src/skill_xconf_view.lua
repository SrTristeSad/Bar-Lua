-- F40: inspecao das listas decodificadas, SEM efeitos no mundo.
local M={}
local page=1
function M.reset() page=1 end
function M.keypressed(key)
  if key=='right' or key=='down' then page=page%3+1;return true end
  if key=='left' or key=='up' then page=(page+1)%3+1;return true end
  if key=='r' then M.reset();return true end
  return false
end
function M.snapshot(report)
  if type(report)~='table' or report.phase~=40 or report.gameplay_enabled~=false
     or report.condition_lists_verified~=true or report.damage_chain_verified~=false then
    return nil,'Relatorio F40 ausente ou incompativel'
  end
  if report.creator_count~=0 or report.target_count~=0 or report.third_count~=0 or report.kind~=10050 then
    return nil,'Contagens ou tipo da habilidade divergentes'
  end
  return {page=page,id=report.skill_id,kind=report.kind,
    records=report.records,decoded=report.decoded,skipped=report.skipped,
    instructions=report.native_instructions,checks=report.checks,
    creator=report.creator_count,target=report.target_count,third=report.third_count,
    enhancement=report.enhancement}
end
function M.draw(report,panel)
  panel.background(panel.x,panel.y,panel.w,panel.h,{0.12,0.16,0.20})
  local function put(msg,dy,color)
    if dy>=0 and dy<panel.h-12 then
      panel.put(tostring(msg),panel.x+17,panel.y+dy,color or {0.9,0.94,0.97},panel.small)
    end
  end
  put('F40 | Listas xconf decodificadas',20,{1,0.83,0.43})
  put('Sem alterar habilidade, dano ou alvos da cena.',48,{1,0.77,0.58})
  local s,err=M.snapshot(report)
  if not s then put(err,100,{1,0.54,0.54});return end
  put('Painel '..s.page..'/3',102,{0.75,1,0.75})
  if s.page==1 then
    put('HeroSkillConfig::load  |  '..s.instructions..' instrucoes',155)
    put(s.checks..' checks ARM64; vinculacao F38 entre CSkill e config.',191)
    put('Vetores de inteiros precedidos por suas contagens.',229)
    put('Registros: '..s.records..' | decodificados: '..s.decoded,270)
    put('Objetos opcionais ainda nao lidos: '..s.skipped,307,{1,0.74,0.5})
  elseif s.page==2 then
    put('Skill '..s.id..' / botao 10039 / codigo 2',153)
    put('HeroSkillConfig +0xB0 | condicoes criador: '..s.creator,195)
    put('HeroSkillConfig +0xC8 | tipo: '..s.kind..' (CSelfSkill)',232)
    put('HeroSkillConfig +0xD0 | condicoes alvo: '..s.target,269)
    put('HeroSkillConfig +0xE8 | terceira lista: '..s.third,306)
    put('EnhanceConfig: '..s.enhancement,344)
  else
    put('As listas do 4010020 estao vazias.',153,{0.75,1,0.75})
    put('Isto NAO comprova que a habilidade seja inerte.',194)
    put('O terceiro vetor nao foi ligado a dano/animacao.',235)
    put('106 linhas com objeto opcional seguem pendentes.',276,{1,0.75,0.5})
    put('Nenhum combate foi adicionado ao Lua Player.',317)
  end
  put('Setas: mudar painel   R: reiniciar',panel.h-68)
  put('Pesquisa, nao gameplay original.',panel.h-39,{1,0.72,0.5})
end
return M
