"""
Default Configuration Values
=============================

Valores padrão para configurações do PythonKore.
"""

from typing import Dict, Any


DEFAULT_CONFIG: Dict[str, Any] = {
    # Core settings
    'version': '0.1.0',
    'name': 'PythonKore',
    
    # Network settings
    'server': '',
    'username': '',
    'password': '',
    'char': '',
    'master': '',
    'serverType': 0,
    'secureLogin': 0,
    'secureLogin_type': 0,
    'secureLogin_requestCode': '',
    'gameGuard': 0,
    'storageAuto': 0,
    'storageAuto_npc': '',
    'storageAuto_distance': 7,
    'storageAuto_npc_type': 1,
    'storageAuto_npc_steps': '',
    
    # AI settings
    'attackAuto': 2,
    'attackAuto_party': 1,
    'attackAuto_onlyWhenSafe': 0,
    'attackAuto_followTarget': 1,
    'attackAuto_inLockOnly': 1,
    'attackDistance': 1.5,
    'attackMaxDistance': 2.5,
    'attackMaxRouteTime': 5,
    'attackMinPlayerDistance': 2,
    'attackMinPortalDistance': 4,
    'attackUseWeapon': 1,
    'attackNoGiveup': 0,
    'attackCanSnipe': 0,
    'attackCheckLOS': 0,
    'attackLooters': 0,
    'attackChangeTarget': 1,
    
    # Movement settings
    'route_randomWalk': 1,
    'route_randomWalk_maxRouteTime': 120,
    'route_avoidWalls': 1,
    'route_randomWalk_inTown': 0,
    'route_maxWarpFee': 2000,
    'route_maxNpcTries': 5,
    'route_teleport': 1,
    'route_teleport_minDistance': 150,
    'route_teleport_maxTries': 8,
    'route_teleport_notInMaps': '',
    
    # Auto-skills
    'useSelf_skill': '',
    'useSelf_skill_smartHeal': 1,
    'useSelf_skill_smartEncore': 1,
    'partySkill': '',
    'partySkill_target': '',
    'partySkill_maxCastTime': 0,
    'partySkill_minSpCheck': 0,
    'partySkill_maxHpCheck': 0,
    'partySkill_statusCheck': '',
    'partySkill_notWhileSitting': 0,
    'partySkill_notInTown': 0,
    'partySkill_timeout': 0,
    'partySkill_disabled': 0,
    
    # Items
    'itemsTakeAuto': 2,
    'itemsTakeAuto_party': 1,
    'itemsGatherAuto': 2,
    'itemsMaxWeight': 89,
    'itemsMaxWeight_sellOrStore': 48,
    'itemsMaxNum_sellOrStore': 99,
    'cartMaxWeight': 7900,
    'itemsTakeAuto_new': 0,
    
    # Monsters
    'teleportAuto_idle': 0,
    'teleportAuto_portal': 0,
    'teleportAuto_search': 0,
    'teleportAuto_minAggressives': 0,
    'teleportAuto_minAggressivesInLock': 0,
    'teleportAuto_onlyWhenSafe': 0,
    'teleportAuto_maxDmg': 500,
    'teleportAuto_maxDmgInLock': 0,
    'teleportAuto_hp': 0,
    'teleportAuto_sp': 0,
    'teleportAuto_unstuck': 0,
    'teleportAuto_lostTarget': 0,
    'teleportAuto_dropTarget': 0,
    'teleportAuto_dropTargetKS': 0,
    'teleportAuto_attackedWhenSitting': 0,
    'teleportAuto_totalDmg': 0,
    'teleportAuto_totalDmgInLock': 0,
    
    # Sitting
    'sitTown': 0,
    'sitAuto_hp_lower': 40,
    'sitAuto_hp_upper': 100,
    'sitAuto_sp_lower': 0,
    'sitAuto_sp_upper': 0,
    'sitAuto_follow': 0,
    'sitAuto_over_50': 0,
    'sitAuto_idle': 1,
    'sitAuto_look': '',
    'sitAuto_look_from_wall': 0,
    'sitTimeout': 0,
    'sitTimeoutHP': 0,
    'sitTimeoutSP': 0,
    
    # Disconnect
    'dcOnDeath': 0,
    'dcOnDualLogin': 1,
    'dcOnDisconnect': 0,
    'dcOnEmptyArrow': 0,
    'dcOnMaxReconnections': 0,
    'dcOnMute': 0,
    'dcOnPM': 0,
    'dcOnZeny': 0,
    'dcOnStorageOpened': 0,
    'dcOnPlayer': 0,
    
    # Debugging
    'verbose': 1,
    'showDomain': 0,
    'wx_map_enabled': 1,
    'wx_captcha_enabled': 0,
    
    # Interface
    'interface': 'Console',
    'consoleColors': '',
    'showTimeStamps': 1,
    
    # Delays and timeouts
    'ai_attack_waitAfterKill': 0.1,
    'ai_equip_auto': 1,
    'ai_equip_giveup': 0,
    'ai_items_take_end_delay': 0.1,
    'ai_items_take_start_delay': 0.25,
    'ai_items_take_delay': 0.15,
    'ai_move_retry': 3,
    'ai_move_giveup': 3,
    'ai_move_unstuck_count': 5,
    'ai_sit_wait': 1.5,
    'ai_skill_use_giveup': 0,
    'ai_stand_wait': 1.5,
    'ai_teleport_delay': 0.5,
    'ai_teleport_retry': 3,
    'ai_teleport_giveup': 3,
    
    # Party
    'partyAuto': 0,
    'partyAutoShare': 0,
    'partyAutoShareItem': 0,
    'partyAutoShareItemDiv': 0,
    'partySkillDistance': 8,
    'followTarget': '',
    'followBot': 0,
    'followFaceDirection': 0,
    'followDistanceMax': 6,
    'followDistanceMin': 3,
    'followLostStep': 5,
    'followSitAuto': 0,
    'followEmotion': 0,
    'followEmotion_distance': 4,
    'followFaceAuto': 0,
    
    # Guild
    'guild': '',
    'guildAutoDeny': 1,
    
    # PvP
    'attackEquip_topHead': '',
    'attackEquip_midHead': '',
    'attackEquip_lowHead': '',
    'attackEquip_leftHand': '',
    'attackEquip_rightHand': '',
    'attackEquip_leftAccessory': '',
    'attackEquip_rightAccessory': '',
    'attackEquip_robe': '',
    'attackEquip_armor': '',
    'attackEquip_shoes': '',
    'attackEquip_arrow': '',
    
    # Sell
    'sellAuto': 0,
    'sellAuto_npc': '',
    'sellAuto_standpoint': '',
    'sellAuto_distance': 5,
    
    # Buy
    'buyAuto': 0,
    'buyAuto_npc': '',
    'buyAuto_standpoint': '',
    'buyAuto_distance': 5,
} 