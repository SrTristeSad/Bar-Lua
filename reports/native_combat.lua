-- Fase 23: metadados auditados do ELF ARM64, não dados de execução.
return {
  {name="CDamageFunction::Run()", address="0xe52ff8", instructions=30, checks={
    "damage_run_target",
  }},
  {name="CDamageFunction::Run(target)", address="0xe53070", instructions=70, checks={
    "get_damage_value",
    "hero_hurt",
    "resolve_target_entity",
  }},
  {name="CDamageFunction::GetDamageValue", address="0xe52950", instructions=332, checks={
    "random_number",
    "read_parameter",
  }},
  {name="CDamageFunction::GetParamValue", address="0xe52e94", instructions=89, checks={
  }},
  {name="CSelectTargetSector::GetSelectTargets", address="0xe63e14", instructions=158, checks={
    "physical_query",
    "stick_direction",
    "trig_cosine",
    "trig_sine",
  }},
  {name="CSelectTargetNearest::GetSelectTargets", address="0xe63990", instructions=153, checks={
  }},
  {name="CMultiTargetSkill::Update", address="0xe65f2c", instructions=131, checks={
    "bind_function_entity",
  }},
  {name="Entity::skill_update", address="0xe4a28c", instructions=122, checks={
    "release_skill",
  }},
}
