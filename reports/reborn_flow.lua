-- F27: metadados validados; nao executa morte/respawn reais
return {
  version="1.0.1811",
  total_instructions=391,
  total_checks=39,
  flag_offset="0x1bc",
  die_logic_virtual_offset="0x98",
  respawn_virtual_offset="0x50",
  source="Hero::update,Hero::reborn,Hero::resetReviveData",
  functions={
    {name="Hero::update",address="0xe58e84",instructions=225,checks=16},
    {name="Hero::reborn",address="0xe57ee0",instructions=69,checks=13},
    {name="Entity::reborn",address="0xe4d4dc",instructions=1,checks=1},
    {name="Hero::resetReviveData",address="0xe57bd0",instructions=96,checks=9},
  },
}
