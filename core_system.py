import json
import os
import random
import time
import glob

# 서정우 파트: 태그 시스템 정의 및 효과 매핑 (2.1.3 고도화)
TAGS_DEFINITION = {
    "slash": {"name": "베기", "category": "physical", "desc": "날카로운 베기 (데미지 x1.3)", "power_mult": 1.3},
    "blunt": {"name": "타격", "category": "physical", "desc": "무거운 타격 (25% 확률 기절)", "stun_chance": 0.25},
    "pierce": {"name": "관통", "category": "physical", "desc": "방어 무시 찌르기", "pen_mult": 0.0}, 
    "fire": {"name": "화염", "category": "magical", "desc": "화염 공격 (45% 확률 화상)", "burn_chance": 0.45},
    "ice": {"name": "빙결", "category": "magical", "desc": "빙결 공격 (40% 확률 슬로우)", "slow_chance": 0.4},
    "bolt": {"name": "전격", "category": "magical", "desc": "전격 공격 (25% 확률 마비)", "paralyze_chance": 0.25},
    "dark": {"name": "어둠", "category": "magical", "desc": "어둠 공격 (가한 데미지 20% 흡수)", "drain_hp": 0.2},
    "holy": {"name": "신성", "category": "magical", "desc": "신성 공격 (언데드 특공 x2.5)", "undead_bonus": 2.5},
    "block": {"name": "차단", "category": "defensive", "desc": "차단 (방어력 x3.0)", "def_mult": 3.0},
    "parry": {"name": "반사", "category": "defensive", "desc": "반사 (받은 피해 70% 반사)", "reflect_dmg": 0.7},
    "dodge": {"name": "회피", "category": "defensive", "desc": "회피 (50% 확률 회피)", "evasion_bonus": 0.5},
    "heal": {"name": "치유", "category": "utility", "desc": "회복 (공격력 70%만큼 HP 회복)", "heal_mult": 0.7},
    "buff": {"name": "강화", "category": "utility", "desc": "강화 (공격력 x1.4)", "stat_bonus": 1.4},
    "poison": {"name": "맹독", "category": "status", "desc": "독 (매 턴 8 데미지)", "dot": 8},
    "bleed": {"name": "출혈", "category": "status", "desc": "출혈 (매 턴 12 데미지)", "dot": 12},
    "blind": {"name": "실명", "category": "status", "desc": "실명 (명중률 -70%)", "accuracy_mult": 0.3},
    "vampire": {"name": "흡혈", "category": "passive", "desc": "흡혈 패시브 (가한 데미지 25% 상시 흡수)", "leech": 0.25},
    "berserk": {"name": "광분", "category": "passive", "desc": "광분 (HP 30% 이하 시 공격력 x3.0)", "low_hp_bonus": 3.0},
    "haste": {"name": "가속", "category": "utility", "desc": "가속 (SPD x1.7)", "speed_mult": 1.7},
    "shield": {"name": "보호막", "category": "defensive", "desc": "보호막 (30 피해 흡수)", "shield_amount": 30},
}

class BattleEntity:
    def __init__(self, data):
        self.name = data.get('name', 'Unknown')
        self.personality = data.get('personality', '평범한')
        self.background = data.get('background', '무명')
        self.stats = data['stats'].copy()
        self.skills = data['skills']
        self.tag_weights = data.get('tag_weights', {}) # 캐릭터 고유 태그 가중치 (DNA)
        self.status_effects = []
        self.current_hp = data.get('current_hp', self.stats['hp'])
        self.current_mp = data.get('current_mp', self.stats['mp'])
        self.is_defending = False
        self.is_stunned = False

    def take_damage(self, amount, ignore_def=False):
        actual_def = 0 if ignore_def else self.stats['def']
        if self.is_defending: actual_def *= 2
        damage = max(1, int(amount - actual_def))
        self.current_hp -= damage
        return damage

    def apply_status(self, effect_type, duration, value=0):
        self.status_effects.append({"type": effect_type, "duration": duration, "value": value})

    def process_status_effects(self):
        logs = []
        new_effects = []
        self.is_stunned = False
        for effect in self.status_effects:
            if effect['type'] in ['poison', 'bleed', 'burn', 'fire']:
                dmg = effect.get('value', 5)
                self.current_hp -= dmg
                logs.append(f"  ✨ [{self.name}] {effect['type']} 피해 발생: {dmg}")
            if effect['type'] in ['stun', 'paralyze'] and random.random() < 0.6:
                self.is_stunned = True
                logs.append(f"  🚫 [{self.name}] 상태 이상으로 행동 불능!")
            effect['duration'] -= 1
            if effect['duration'] > 0: new_effects.append(effect)
        self.status_effects = new_effects
        return logs

    def show_info(self):
        print(f"\n" + "="*60)
        print(f" 캐릭터 정보: {self.name} ({self.personality})")
        print(f" 배경: {self.background}")
        print(f" HP: {max(0, self.current_hp)}/{self.stats['hp']} | MP: {max(0, self.current_mp)}/{self.stats['mp']}")
        print(f" ATK: {self.stats['atk']} | DEF: {self.stats['def']} | SPD: {self.stats['spd']}")
        print("-" * 60)
        print(" [기본 태그 가중치 (Character DNA)]")
        # 가중치 정렬하여 출력 (한글 이름 포함)
        sorted_weights = sorted(self.tag_weights.items(), key=lambda x: x[1], reverse=True)
        for i in range(0, len(sorted_weights), 3):
            line = "  ".join([f"{t[0]}({TAGS_DEFINITION[t[0]]['name']}): {t[1]:.2f}" for t in sorted_weights[i:i+3]])
            print(f"  {line}")
        print("-" * 60)
        print(" [보유 스킬]")
        for i, s in enumerate(self.skills):
            tag_descs = [f"{t}({TAGS_DEFINITION[t]['name']})" for t in s['tags']]
            print(f"  {i+1}. {s['name']} (MP {s['mp_cost']})")
            print(f"     ㄴ {', '.join(tag_descs)}")
        print("="*60)

class CharacterGenerator:
    @staticmethod
    def generate_entity(name, is_player=True):
        tag_weights = {tag: round(random.uniform(0.05, 1.0), 2) for tag in TAGS_DEFINITION}
        skills = []
        available_tags = list(TAGS_DEFINITION.keys())
        weights_list = [tag_weights[tag] for tag in available_tags]
        
        for _ in range(4):
            selected_tags = []
            while len(selected_tags) < 3:
                new_tag = random.choices(available_tags, weights=weights_list, k=1)[0]
                if new_tag not in selected_tags:
                    selected_tags.append(new_tag)
            
            skills.append({
                "name": f"기술-{random.randint(100, 999)}",
                "tags": selected_tags,
                "mp_cost": 10 + (len(selected_tags) * 3)
            })
            
        data = {
            "name": name,
            "personality": random.choice(["냉철한", "용감한", "탐욕스러운", "신비로운", "냉혈한", "자비로운"]),
            "background": random.choice(["북부 성채의 기사", "지하 도시 도굴꾼", "숲의 정령", "왕국 사서", "몰락한 귀족"]),
            "stats": {
                "hp": 150 if is_player else 120,
                "mp": 80,
                "atk": 18 + random.randint(0, 5),
                "def": 10 + random.randint(0, 3),
                "spd": 12 + random.randint(0, 5)
            },
            "tag_weights": tag_weights,
            "skills": skills
        }
        return BattleEntity(data)

class BattleSystem:
    def __init__(self, player, enemy):
        self.player = player
        self.enemy = enemy
        self.turn_count = 1

    def run_battle(self):
        print(f"\n⚔️ 전투 시작: {self.player.name} vs {self.enemy.name}")
        while self.player.current_hp > 0 and self.enemy.current_hp > 0:
            print(f"\n--- [Turn {self.turn_count}] ---")
            for log in self.player.process_status_effects(): print(log)
            for log in self.enemy.process_status_effects(): print(log)
            if self.player.current_hp <= 0 or self.enemy.current_hp <= 0: break
            
            entities = [self.player, self.enemy]
            entities.sort(key=lambda x: x.stats['spd'], reverse=True)
            for attacker in entities:
                if attacker.is_stunned: continue
                defender = self.enemy if attacker == self.player else self.player
                if attacker.current_hp <= 0 or defender.current_hp <= 0: continue
                if attacker == self.player: self.player_turn()
                else: self.enemy_turn()
                time.sleep(0.4)
            self.turn_count += 1
        return self.player.current_hp > 0

    def player_turn(self):
        print(f"\n[{self.player.name}의 행동] HP: {self.player.current_hp} | MP: {self.player.current_mp}")
        print("사용 가능한 스킬:")
        for i, s in enumerate(self.player.skills):
            effect_summary = ", ".join([TAGS_DEFINITION[t]['desc'] for t in s['tags']])
            print(f"{i+1}. {s['name']:10} (MP {s['mp_cost']}) [{effect_summary}]")
        print("0. 일반 공격 / H. 도움말 / I. 내 정보")
        
        while True:
            cmd = input(">> ").upper()
            if cmd == 'H': show_help(); continue
            if cmd == 'I': self.player.show_info(); continue
            try:
                if cmd == '0': self.execute_attack(self.player, self.enemy, None); break
                idx = int(cmd) - 1
                if 0 <= idx < len(self.player.skills):
                    skill = self.player.skills[idx]
                    if self.player.current_mp >= skill['mp_cost']:
                        self.player.current_mp -= skill['mp_cost']
                        self.execute_attack(self.player, self.enemy, skill); break
                    else: print("MP 부족!")
                else: print("범위 밖 입력.")
            except: print("잘못된 입력.")

    def enemy_turn(self):
        usable = [s for s in self.enemy.skills if s['mp_cost'] <= self.enemy.current_mp]
        if usable and random.random() < 0.7:
            skill = random.choice(usable)
            self.enemy.current_mp -= skill['mp_cost']
            self.execute_attack(self.enemy, self.player, skill)
        else: self.execute_attack(self.enemy, self.player, None)

    def execute_attack(self, attacker, defender, skill):
        print(f"\n>>> [{attacker.name}]의 차례")
        if skill:
            print(f"📢 [{skill['name']}] 발동!")
            final_power = attacker.stats['atk']
            ignore_def = False
            
            if 'berserk' in skill['tags'] and attacker.current_hp <= attacker.stats['hp'] * 0.3:
                final_power *= 3.0
                print("  🔥 [Berserk] 체력 저하로 위력 3배 폭발!")

            for tag in skill['tags']:
                eff = TAGS_DEFINITION[tag]
                if 'power_mult' in eff: final_power *= eff['power_mult']
                if 'pen_mult' in eff: ignore_def = True; print(f"  🎯 [{tag}] 방어 무시 타격!")
                if 'burn_chance' in eff and random.random() < eff['burn_chance']:
                    defender.apply_status('burn', 3, 7); print(f"  🔥 [{tag}] 화상 부여!")
                if 'stun_chance' in eff and random.random() < eff['stun_chance']:
                    defender.apply_status('stun', 1); print(f"  💫 [{tag}] 기절 부여!")
                if 'heal_mult' in eff:
                    heal = int(attacker.stats['atk'] * eff['heal_mult'])
                    attacker.current_hp = min(attacker.stats['hp'], attacker.current_hp + heal)
                    print(f"  💚 [{tag}] {heal} 회복!")
            
            dmg = defender.take_damage(int(final_power), ignore_def)
            print(f"  💥 피해량: {dmg} (적 HP: {max(0, defender.current_hp)})")
            
            if 'dark' in skill['tags'] or 'vampire' in skill['tags']:
                drain = int(dmg * 0.25)
                attacker.current_hp = min(attacker.stats['hp'], attacker.current_hp + drain)
                print(f"  🩸 [흡혈] {drain} HP 흡수!")
        else:
            dmg = defender.take_damage(attacker.stats['atk'])
            print(f"👊 일반 공격! => {dmg} 피해 (적 HP: {max(0, defender.current_hp)})")

def show_help():
    print("\n=== 태그(Tag) 효과 사전 ===")
    for tag, info in TAGS_DEFINITION.items():
        print(f"[{tag:10}] : {info['desc']}")
    print("-" * 40)

class DataManager:
    @staticmethod
    def save(entity):
        if not os.path.exists('characters'): os.makedirs('characters')
        filename = f"characters/{entity.name}.json"
        data = {
            "name": entity.name, "personality": entity.personality, "background": entity.background,
            "stats": entity.stats, "skills": entity.skills, "tag_weights": entity.tag_weights,
            "current_hp": entity.current_hp, "current_mp": entity.current_mp
        }
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"💾 '{entity.name}' 저장 완료.")

    @staticmethod
    def list_characters():
        if not os.path.exists('characters'): return []
        return [os.path.basename(f).replace(".json", "") for f in glob.glob("characters/*.json")]

    @staticmethod
    def load(name):
        filename = f"characters/{name}.json"
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return BattleEntity(data)
        return None

def main_menu():
    current_player = None
    while True:
        status = f" [접속: {current_player.name}]" if current_player else " [미접속]"
        print(f"\n=== 🏰 DungeonAndAI: Core System{status} ===")
        print("1. 새 캐릭터 생성 (DNA 기반)")
        print("2. 캐릭터 선택")
        print("3. 캐릭터 정보 (가중치 포함)")
        print("4. 배틀 시작")
        print("5. 도움말")
        print("6. 종료")
        choice = input("선택: ")

        if choice == '1':
            name = input("이름: ")
            current_player = CharacterGenerator.generate_entity(name)
            DataManager.save(current_player)
        elif choice == '2':
            chars = DataManager.list_characters()
            if not chars: print("캐릭터가 없습니다."); continue
            for i, n in enumerate(chars): print(f"{i+1}. {n}")
            try:
                c_idx = int(input("선택: ")) - 1
                current_player = DataManager.load(chars[c_idx])
                print(f"'{current_player.name}' 캐릭터로 변경되었습니다.")
            except: print("오류 발생.")
        elif choice == '3':
            if current_player: current_player.show_info()
            else: print("캐릭터를 먼저 선택하세요.")
        elif choice == '4':
            if not current_player: print("캐릭터를 먼저 선택하세요."); continue
            enemy = CharacterGenerator.generate_entity("어둠의 기사", is_player=False)
            battle = BattleSystem(current_player, enemy)
            if battle.run_battle(): DataManager.save(current_player)
        elif choice == '5': show_help()
        elif choice == '6': break

if __name__ == "__main__":
    main_menu()
