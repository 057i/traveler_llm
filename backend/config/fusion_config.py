"""
閾诲秴鎮庣粵鏍殣闁板秶鐤?
閸欘垶鈧鐡ラ悾銉窗
1. normalized_weighted - 瑜版帊绔撮崠鏍у閺夊啫閽╅崸鍥风礄閹恒劏宕橀敍灞介挬鐞涒剝鈧嗗厴閸滃苯鍣涵顔解偓褝绱?2. rrf - RRF閾诲秴鎮庨敍鍫熸付缁嬪啿鐣鹃敍灞筋劅閺堫垶鐛欑拠渚婄礆
3. max - MAX閾诲秴鎮庨敍鍫㈢暆閸楁洜娲块幒銉礉娑撳秶鈻堥柌濠囩彯閸掑棴绱?4. hybrid - 濞ｅ嘲鎮庣粵鏍殣閿涘牊娓堕崗銊╂桨閿涘矁顓哥粻妤呭櫤婢堆嶇礆
"""

FUSION_CONFIGS = {
    "normalized_weighted": {
        "rescale_to_original": True,
    },

    "rrf": {
        "k": 60,
    },

    "max": {
        "dense_boost": 1.0,
        "sparse_boost": 1.0,
    },

    "hybrid": {
        "similarity_weight": 0.7,
    }
}

    "normalized_weighted": 0.60,


def get_current_threshold() -> float:
    return FUSION_CONFIGS.get(FUSION_STRATEGY, {})
