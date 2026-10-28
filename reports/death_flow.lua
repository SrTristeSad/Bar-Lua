-- F26: dados estáticos auditados do ELF; sem executar morte ou combate
return {
  version="1.0.1811",
  total_instructions=377,
  total_checks=29,
  first_callback="Entity::onDied",
  callback_flag="0x1bc",
  hero_die_logic="Hero::dieLogic",
  score_fraction=0.75,
  functions={
    {name="Hero::addHurtFromEnemy",address="0xe57678",instructions=89,checks=5},
    {name="Entity::onDied",address="0xe4b554",instructions=3,checks=3},
    {name="Entity::dieLogic",address="0xe4d1f8",instructions=185,checks=7},
    {name="Hero::dieLogic",address="0xe5988c",instructions=100,checks=14},
  },
}
