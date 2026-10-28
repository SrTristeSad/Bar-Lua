-- F41: plano de construção baseado no terceiro vetor de HeroSkillConfig.
-- NÃO invoca CFunction nem reproduz efeitos, temporizadores ou dano real.
local M = {}
function M.plan(skillId, selectorId, functionIds, categories)
  assert(type(skillId)=='number' and type(selectorId)=='number','IDs inválidos')
  assert(type(functionIds)=='table' and type(categories)=='table','listas inválidas')
  local objects = {}
  for i,id in ipairs(functionIds) do
    assert(type(id)=='number' and id>=0 and id==math.floor(id),'ID de função inválido')
    local category=categories[id]
    if type(category)~='string' or category=='' then
      return nil,'função sem tabela: '..tostring(id)
    end
    objects[#objects+1]={order=i,id=id,category=category}
  end
  return {
    skill_id=skillId,selector_id=selectorId,
    constructor=(selectorId==10050) and 'CSelfSkill' or 'CMultiTargetSkill',
    objects=objects, count=#objects, executed=false, damage_applied=false,
    target_selection_verified=false
  }
end
function M.binding_steps(plan)
  assert(type(plan)=='table' and type(plan.objects)=='table','plano inválido')
  local steps={}
  for _,f in ipairs(plan.objects) do
    steps[#steps+1]={function_id=f.id, step='Init'}
    steps[#steps+1]={function_id=f.id, step='SetCreatorEntity'}
    steps[#steps+1]={function_id=f.id, step='SetTargetEntitys'}
    steps[#steps+1]={function_id=f.id, step='SetEntity'}
  end
  return steps
end
return M
