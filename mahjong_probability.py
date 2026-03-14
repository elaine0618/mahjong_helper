import random
from collections import Counter
import itertools

class MahjongProbabilityCalculator:
    """
    危险度计算类
    """
    
    def __init__(self):
        pass
    
    def calculate_risk_probability(self, tile_key, tile_counts, player_wind='东', round_wind='东'):
        """
        计算打出某张牌的风险概率
        
        参数:
            tile_key: 牌型键值，如 '1m', '2s', '3p', '1z'
            tile_counts: 当前牌局中所有牌的数量统计
            player_wind: 玩家自风，默认东
            round_wind: 场风，默认东
            
        返回:
            风险概率 (0-100)
        """
        # 获取当前牌的数量
        current_count = tile_counts.get(tile_key, 0)
        
        # 计算剩余牌数
        remaining = max(0, 4 - current_count)
        
        # 基础风险：剩余牌越多，听牌率越高
        base_risk = remaining * 8
        
        # 牌的危险程度评估
        danger_score = self._evaluate_tile_danger(tile_key, tile_counts, player_wind, round_wind)
        
        # 役种可能性评估
        yaku_potential = self._evaluate_yaku_potential(tile_key, tile_counts)
        
        # 听牌形状评估
        tenpai_shape = self._evaluate_tenpai_shapes(tile_key, tile_counts)
        
        # 顺子可能性评估
        sequence_potential = self._evaluate_sequence_potential(tile_key, tile_counts)
        
        # 牌局进度评估
        progress_factor = self._evaluate_game_progress(tile_counts)
        
        # 综合计算风险
        risk = base_risk + danger_score + yaku_potential + tenpai_shape + sequence_potential + progress_factor
        
        # 模拟对手的听牌状态和牌局动态
        total_discarded = sum(tile_counts.values())
        if total_discarded < 8:  # 早巡
            random_factor = random.randint(-5, 5)
        elif total_discarded < 16:  # 中巡
            random_factor = random.randint(-3, 8)
        else:  # 晚巡
            random_factor = random.randint(0, 10)
        risk += random_factor
        
        # 限制在0-100之间
        risk = max(0, min(100, risk))
        
        return int(risk)
    
    def _evaluate_tile_danger(self, tile_key, tile_counts, player_wind, round_wind):
        """评估牌本身的危险程度"""
        danger = 0
        
        # 字牌评估
        if tile_key.endswith('z'):
            # 风牌
            if tile_key in ['1z', '2z', '3z', '4z']:
                tile_wind = {'1z': '东', '2z': '南', '3z': '西', '4z': '北'}[tile_key]
                if tile_counts.get(tile_key, 0) == 3:
                    danger -= 10
                elif tile_wind == player_wind:
                    danger += 5
                elif tile_wind != round_wind:
                    danger += 15
                else:
                    danger += 25
            
            # 三元牌
            elif tile_key in ['5z', '6z', '7z']:
                if tile_counts.get(tile_key, 0) == 3:
                    danger -= 10
                else:
                    danger += 20
        
        else:
            # 数牌评估
            num = int(tile_key[0])
            suit = tile_key[1]
            
            # 边张（1,9）相对安全
            if num == 1 or num == 9:
                danger -= 5
            # 中张（4,5,6）危险度较高
            elif num in [4, 5, 6]:
                danger += 10
            # 其他数牌（2,3,7,8）
            else:
                danger += 5
            
            # 检查是否已经打出多张相同牌
            count = tile_counts.get(tile_key, 0)
            if count == 3:
                danger += 15  # 绝张，非常危险
            elif count == 2:
                danger += 5   # 还剩2张，中等危险
        
        return danger
    
    def _evaluate_sequence_potential(self, tile_key, tile_counts):
        """评估这张牌被用于顺子的可能性"""
        if tile_key.endswith('z'):
            return 0
        
        num = int(tile_key[0])
        suit = tile_key[1]
        potential = 0
        
        # 检查这张牌可能组成的顺子

        # 前一种顺子（如345）
        if num >= 3:
            if (tile_counts.get(f"{num-2}{suit}", 0) >= 1 and 
                tile_counts.get(f"{num-1}{suit}", 0) >= 1):
                potential += 5
        
        # 中一种顺子（如456）
        if 2 <= num <= 8:
            if (tile_counts.get(f"{num-1}{suit}", 0) >= 1 and 
                tile_counts.get(f"{num+1}{suit}", 0) >= 1):
                potential += 8
        
        # 后一种顺子（如567）
        if num <= 7:
            if (tile_counts.get(f"{num+1}{suit}", 0) >= 1 and 
                tile_counts.get(f"{num+2}{suit}", 0) >= 1):
                potential += 5
        
        return potential
    
    def _evaluate_game_progress(self, tile_counts):
        """评估牌局进度对风险的影响"""
        total_discarded = sum(tile_counts.values())
        
        # 早巡（0-8张）：安全牌多，风险降低
        if total_discarded < 8:
            return -5
        # 中巡（8-16张）：正常
        elif total_discarded < 16:
            return 0
        # 晚巡（>16张）：危险，可能有人听牌
        else:
            return 10
    
    def _evaluate_yaku_potential(self, tile_key, tile_counts):
        """评估形成役种的可能性"""
        potential = 0
        
        # 断幺九可能性
        if not tile_key.endswith('z') and tile_key[0] not in ['1', '9']:
            potential += 5
        
        # 清一色可能性
        if not tile_key.endswith('z'):
            suit = tile_key[1]
            same_suit_count = sum(tile_counts.get(f"{i}{suit}", 0) for i in range(1, 10))
            if same_suit_count > 10:
                potential += 10
            elif same_suit_count > 6:
                potential += 5
        
        # 混一色可能性
        if not tile_key.endswith('z'):
            suit = tile_key[1]
            same_suit_count = sum(tile_counts.get(f"{i}{suit}", 0) for i in range(1, 10))
            zi_count = sum(tile_counts.get(f"{i}z", 0) for i in range(1, 8))
            if same_suit_count > 8 and zi_count > 2:
                potential += 8
        
        # 对对和可能性
        pairs = 0
        for key, count in tile_counts.items():
            if count >= 2:
                pairs += 1
        if pairs >= 3:
            potential += 5
        
        # 七对子可能性
        if pairs >= 4:
            potential += 8
        
        return potential
    
    def _evaluate_tenpai_shapes(self, tile_key, tile_counts):
        """评估可能的听牌形状"""
        shape_score = 0
        
        if tile_key.endswith('z'):
            return shape_score  # 字牌不考虑顺子
        
        num = int(tile_key[0])
        suit = tile_key[1]
        
        # === 1. 两面听牌（最危险）===
        if 2 <= num <= 8:
            left = tile_counts.get(f"{num-1}{suit}", 0)
            right = tile_counts.get(f"{num+1}{suit}", 0)
            
            if left >= 1 and right >= 1:
                shape_score += 15
            elif left >= 2 or right >= 2:
                shape_score += 8
        
        # === 2. 坎张听牌（中等危险）===
        if 3 <= num <= 7:
            left2 = tile_counts.get(f"{num-2}{suit}", 0)
            right2 = tile_counts.get(f"{num+2}{suit}", 0)
            
            if left2 >= 1 and tile_counts.get(f"{num-1}{suit}", 0) >= 1:
                shape_score += 12
            if right2 >= 1 and tile_counts.get(f"{num+1}{suit}", 0) >= 1:
                shape_score += 12
        
        # === 3. 边张听牌（较安全）===
        if num == 3:
            if tile_counts.get(f"1{suit}", 0) >= 1 and tile_counts.get(f"2{suit}", 0) >= 1:
                shape_score += 5
        if num == 7:
            if tile_counts.get(f"8{suit}", 0) >= 1 and tile_counts.get(f"9{suit}", 0) >= 1:
                shape_score += 5
        
        # === 4. 单骑听牌 ===
        if tile_counts.get(tile_key, 0) == 3:
            shape_score += 10
        
        # === 5. 双碰听牌 ===
        if tile_counts.get(tile_key, 0) == 2:
            shape_score += 8
        
        return shape_score
    
    def calculate_discard_advice(self, hand_tiles, tile_counts, player_wind='东', round_wind='东'):
        """
        计算手牌中每张牌的打出的建议
        
        参数:
            hand_tiles: 手牌列表，每张牌的键值
            tile_counts: 当前牌局中所有牌的数量统计
            player_wind: 玩家自风
            round_wind: 场风
            
        返回:
            每张牌的危险度
        """
        results = []
        
        for tile_key in hand_tiles:
            risk = self.calculate_risk_probability(tile_key, tile_counts, player_wind, round_wind)
            
            # 颜色配置
            if risk < 20:
                color = "#00FF00"
            elif risk < 40:
                color = "#ADFF2F"
            elif risk < 60:
                color = "#FFFF00"
            elif risk < 80:
                color = "#FFA500"
            else:
                color = "#FF0000"
            
            results.append({
                'tile_key': tile_key,
                'risk': risk,
                'color': color
            })
        
        return results


def calculate_tile_risk(tile_key, tile_counts, player_wind='东', round_wind='东'):
    """
    简化版的单张牌风险计算函数
    供主程序直接调用
    """
    calculator = MahjongProbabilityCalculator()
    return calculator.calculate_risk_probability(tile_key, tile_counts, player_wind, round_wind)


def get_discard_advice(hand_tiles, tile_counts, player_wind='东', round_wind='东'):
    """
    获取手牌危险度
    """
    calculator = MahjongProbabilityCalculator()
    return calculator.calculate_discard_advice(hand_tiles, tile_counts, player_wind, round_wind)