-- F25: evidências estáticas do ELF original, não executa combate
return {
  version="1.0.1811",
  total_instructions=269,
  total_checks=44,
  functions={
    {name="Entity::getValueByType (contextual)",address="0xe45d5c",instructions=88,checks=13},
    {name="Entity::getValueByType (const)",address="0xe49afc",instructions=92,checks=13},
    {name="Hero::addHurtFromEnemy",address="0xe57678",instructions=89,checks=18},
  },
  hp_offset="0x314",
  last_attacker_offset="0x370",
  supported_scope="modelo isolado de HP; nao altera jogo",
}
