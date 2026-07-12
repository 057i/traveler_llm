"""
韫囶偊鈧喎鍨垫慨瀣缁€杞扮伐閺佺増宓侀懘姘拱
濞ｈ濮炴稉鈧禍娑氥仛娓氬姊惧〒鍛婃珯閻愯鏆熼幑顔煎煂閸氭垿鍣洪弫鐗堝祦鎼?"""
import sys
import os


from app.core.milvus_rag_client import get_rag_engine
from app.models.schemas import Destination, Season, TravelType
from loguru import logger


def create_sample_destinations():
    destinations = [
        Destination(
            name="娑撳绨规禍姘剁烦濠€?,
            location="濞村嘲宕￠惇浣风瑏娴滄艾绔?,
            description="娑撳绨规禍姘剁烦濠€鐐Ц娑擃厼娴楅張鈧紘搴ｆ畱濞撮攱鍝楁稊瀣╃閿涘本瀚㈤張?閸忣剟鍣烽梹璺ㄦ畱闁惧墎娅ч懝鍙夌煓濠娾晪绱濆ù閿嬫寜濞撳懏绶㈠﹢娑滄憫閿涘矂鈧倸鎮庡〒鍛婂惖閵嗕焦缍斿鏉戞嫲閸氬嫮顫掑缈犵瑐鏉╂劕濮╅妴鍌濈箹闁插本鐨甸崐娆忕杹娴滅尨绱濋崗銊ュ嬀楠炲啿娼庡鏃€淇?5鎼达讣绱濋弰顖氬閸嬪洩鍎ㄩ崷鑸偓鍌氭噯鏉堣婀佹禍鏃€妲︾痪褔鍘惔妤冨參閿涘矂鈧倸鎮庣€硅泛娑甸弮鍛埗閸滃矁婀濋張鍫熸⒕鐞涘被鈧?,
            tags=["濞撮攱鍝?, "鎼达箑浜?, "濞兼粍鎸?, "娴滄梹妲﹂柊鎺戠暗", "閻戭厼鐢?],
            best_season=[Season.WINTER, Season.SPRING],
            budget_range=[3000, 10000],
            suitable_for=[TravelType.FAMILY, TravelType.COUPLE],
            duration_days=5,
            rating=4.8
        ),
        Destination(
            name="閸栨ぞ鍚弫鍛唫",
            location="閸栨ぞ鍚敮鍌欑閸╁骸灏?,
            description="閸栨ぞ鍚弫鍛唫閺勵垯鑵戦崶鑺ユ濞撳懍琚辨禒锝囨畱閻ㄥ洤顔嶇€诡偅顔栭敍灞炬Ц娑撴牜鏅稉濠勫箛鐎涙顫夊Ο鈩冩付婢堆佲偓浣风箽鐎涙ɑ娓剁€瑰本鏆ｉ惃鍕躬鐠愩劎绮ㄩ弸鍕綔瀵よ櫣鐡氱紘銈冣偓鍌涘閺?80鎼囱冪紦缁涙埊绱?707闂傚瓨鍩х仦瀣剁礉閺勵垯鑵戦崶钘夊綔娴狅絽顔傚宄扮紦缁涙垹娈戠划鎯у磿閵嗗倿鈧倸鎮庢禍鍡毿掓稉顓炴禇閸樺棗褰堕弬鍥у閿涘矁顫囩挧蹇撳綔瀵よ櫣鐡氶懝鐑樻钩閵?,
            tags=["閸樺棗褰?, "閺傚洤瀵?, "閸欍倕缂撶粵?, "娑撴牜鏅柆妞鹃獓", "閸楁氨澧挎＃?],
            best_season=[Season.SPRING, Season.AUTUMN],
            budget_range=[500, 2000],
            suitable_for=[TravelType.FAMILY, TravelType.FRIENDS, TravelType.SOLO],
            duration_days=2,
            rating=4.9
        ),
        Destination(
            name="閺夘厼绐炵憲鎸庣",
            location="濞存瑦鐫欓惇浣规線瀹哥偛绔?,
            description="閺夘厼绐炵憲鎸庣閺勵垯鑵戦崶鍊熸啿閸氬秶娈戞搴㈡珯閸氬秷鍎ㄩ崠鐚寸礉娴犮儳顫呯紘搴ｆ畱濠€鏍у帨鐏炶精澹婇崪灞肩船婢舵氨娈戦崥宥堝劏閸欍倛鎶楅梻璇叉倳娑擃厼顦婚妴鍌濄偪濠€鏍у磩閺咁垰瀵橀幏顒佹焽濡椼儲鐣梿顏傗偓渚€娴勫畡鏉款樅閻撗呯搼閵嗗倹妲€涳絽褰茬挧蹇斉懞鎲嬬礉婢跺繐顒滈懡鐤С閻╂稑绱戦敍宀€顫愮€涳絾顢囬懞閬嶎棟妫ｆ瑱绱濋崘顒€顒滈崣顖濈セ闂嗩亝娅欓妴鍌炩偓鍌氭値娴兼垿妫藉顐ｎ劄閵嗕礁鎼ч懠韬测偓浣界セ閺咁垬鈧?,
            tags=["濠€鏍ㄧˇ", "妞嬪孩娅?, "閸欍倛鎶?, "娴兼垿妫?, "閹藉嫬濂?],
            best_season=[Season.SPRING, Season.AUTUMN],
            budget_range=[1000, 3000],
            suitable_for=[TravelType.COUPLE, TravelType.FAMILY, TravelType.SOLO],
            duration_days=3,
            rating=4.7
        ),
        Destination(
            name="閹存劙鍏橀悢濠勫皸閸╁搫婀?,
            location="閸ユ稑绐涢惇浣瑰灇闁棄绔?,
            description="閹存劙鍏樻径褏鍞洪悮顐ょ畳閼茶尙鐖虹粚璺虹唨閸︾増妲告稉鏍櫕閽佹鎮曢惃鍕亣閻斿﹦灏楁潻浣告勾娣囨繃濮㈤崺鍝勬勾閵嗕胶顫栭惍鏃傜畳閼叉彃鐔€閸﹁埇鈧礁鍙曟导妤佹殌閼叉彃鐔€閸︽澘鎷伴弫娆掑仜閺冨懏鐖堕崺鍝勬勾閵嗗倸褰叉禒銉ㄧ箮鐠烘繄顬囩憴鍌滄箙婢堆呭敽閻氼偓绱濇禍鍡毿掓径褏鍞洪悮顐ゆ畱閻㈢喐妞挎稊鐘斥偓褋鈧倸鐔€閸︽壆骞嗘晶鍐х喘缂囧函绱濋柅鍌氭値娴滄彃鐡欏〒绋挎嫲閸斻劎澧块悥鍗炪偨閼板懌鈧?,
            tags=["閸斻劎澧块崶?, "婢堆呭敽閻?, "娴滄彃鐡?, "缁夋垶娅?, "閻㈢喐鈧?],
            best_season=[Season.SPRING, Season.AUTUMN],
            budget_range=[800, 2500],
            suitable_for=[TravelType.FAMILY, TravelType.FRIENDS],
            duration_days=2,
            rating=4.8
        ),
        Destination(
            name="瀵姴顔嶉悾灞芥禇鐎硅埖锛庨弸妤€鍙曢崶?,
            location="濠€鏍у础閻礁绱剁€瑰墎鏅敮?,
            description="瀵姴顔嶉悾灞芥禇鐎硅埖锛庨弸妤€鍙曢崶顓濅簰閻欘剛澹掗惃鍕叾閼昏京鐖炲畝鈺佸槻閺嬫婀寸挩宀冩啿缁夊府绱濋幏銉︽箒3000婢舵艾楠囨總鍥у槻閹亞鐓堕妴鍌滄暩瑜颁究鈧﹪妯嬮崙陇鎻妴瀣╄厬閸濆牆鍩勭捄顖欑肮鐏炶京娈戦崢鐔风€风亸鍗炴躬鏉╂瑩鍣烽妴鍌氬讲娑旀ê娼楁稉鏍櫕閺堚偓闂€璺ㄦ畱缁便垽浜鹃敍灞肩秼妤犲瞼骞撻悹鍐╃垽闁挾娈戦崚鐑樼负閿涘本顐剧挧蹇庣隘濞村嘲顨岀憴鍌樷偓鍌炩偓鍌氭値閸犳粍顐介惂璇插寳閸滃本鎲氳ぐ杈╂畱濞撶顓归妴?,
            tags=["鐏炲崬娓?, "濡喗鐏?, "婵傚洤鍢?, "缁便垽浜?, "閹恒垽娅?],
            best_season=[Season.SPRING, Season.AUTUMN],
            budget_range=[2000, 5000],
            suitable_for=[TravelType.FRIENDS, TravelType.SOLO],
            duration_days=4,
            rating=4.7
        ),
        Destination(
            name="濡楀倹鐏勫鎾寸潤",
            location="楠炶儻銈挎竟顔芥閼奉亝涓嶉崠鐑橆攪閺嬫绔?,
            description="濡楀倹鐏勫鎾寸潤娴犮儱鍖楀瀵告暢婢垛晙绗呴懓宀勬閸氬稄绱濇稉銈呭摵瀹勬澘鑲犻崣鐘茬П閿涘矂顥撻崗澶岊潊娑撳鈧倷绠婚懜瑙勭埗鐟欏牊绱﹀Ч鐕傜礉閸欘垯浜掗惇瀣煂鐠烇繝钃熺仦渚库偓浣风瘈妞诡剛鏁剧仦杈╃搼閽佹鎮曢弲顖滃仯閵嗗倹閮ㄩ柅鏃堫棑閺咁垰顩ч悽浼欑礉鐞氼偉鐛曟稉铏规闁插瞼鏁惧濞库偓鍌炩偓鍌氭値娴兼垿妫藉〒姝岊潔閵嗕焦鎲氳ぐ鍗炴嫲娴ｆ捇鐛欑仦杈ㄦ寜閺傚洤瀵查妴?,
            tags=["鐏炶鲸鎸?, "濞撴瓕鍩?, "妞嬪孩娅?, "閹藉嫬濂?, "閸犫偓閺傤垳澹?],
            best_season=[Season.SPRING, Season.AUTUMN],
            budget_range=[1500, 4000],
            suitable_for=[TravelType.FAMILY, TravelType.COUPLE, TravelType.FRIENDS],
            duration_days=3,
            rating=4.8
        ),
        Destination(
            name="娑撹姤鐫欓崣銈呯厔",
            location="娴滄垵宕￠惇浣烽檮濮圭喎绔?,
            description="娑撹姤鐫欓崣銈呯厔閺勵垯鑵戦崶鎴掔箽鐎涙ɑ娓剁€瑰本鏆ｉ惃鍕毌閺佺増鐨弮蹇撳綔閸╁簼绠ｆ稉鈧敍灞炬箒800婢舵艾鍕鹃崢鍡楀蕉閵嗗倸褰滈崺搴″敶鐏忓繑藟濞翠焦鎸夐敍灞藉綔瀵よ櫣鐡氶弸妤冪彌閿涘瞼鎾肩憲鎸庢閺傚洤瀵插ù鎾冲袱閵嗗倸顧侀弲姘辨畱閸欍倕鐓勯悘顖滀紑闂冩垹寮烽敍宀勫幁閸氀傜閺壜ゎ敎閻戭參妞嗛棃鐐插殥閵嗗倿鈧倸鎮庢担鎾荤崣濮樻垶妫岄弬鍥у閵嗕椒绱ら梻鎻掑閸嬪洤鎷伴弬鍥閺冨懓顢戦妴?,
            tags=["閸欍倕鐓?, "濮樻垶妫岄弬鍥у", "閺傚洩澹?, "鐎广垺鐖?, "閹便垻鏁撳ú?],
            best_season=[Season.SPRING, Season.AUTUMN],
            budget_range=[2000, 5000],
            suitable_for=[TravelType.COUPLE, TravelType.SOLO, TravelType.FRIENDS],
            duration_days=5,
            rating=4.6
        ),
        Destination(
            name="闂堟帒鐭濆畷鍌氬寳",
            location="鐏炲彉绗㈤惇渚€娼氬畝娑樼",
            description="瀹曞倸鍖楅弰顖欒厬閸ヨ姤鎹ｅ畝鍝ュ殠缁楊兛绔存妯哄槻閿涘本婀佸ù铚傜瑐缁楊兛绔撮崥宥呭寳娑斿袨閵嗗倸鍖楀ù椋庢祲鏉╃儑绱濇搴㈡珯娴兼绶ㄩ敍宀勪壕閺佹瑦鏋冮崠鏍ㄧ箒閸樻哎鈧倸褰叉禒銉у焽鐏炶精顫囧ù鍑ょ礉閸濅礁鐨惧畷鍌氬寳缂佽儻灏敍灞藉棘鐟欏倿浜鹃弫娆忣唫鐟欏倶鈧倸顦寸€涳絾鐨甸崐娆忓櫝閻栨枻绱濋弰顖炰缉閺嗘垼鍎ㄩ崷鑸偓鍌炩偓鍌氭値閻ц鍖楅妴浣侯殟缁傚繐鎷版导鎴︽＝鎼达箑浜ｉ妴?,
            tags=["鐏炲崬娓?, "濞撮攱娅?, "闁挻鏆€", "闁寧娈?, "閼艰埖鏋冮崠?],
            best_season=[Season.SUMMER, Season.AUTUMN],
            budget_range=[1000, 3000],
            suitable_for=[TravelType.FAMILY, TravelType.FRIENDS, TravelType.SOLO],
            duration_days=2,
            rating=4.5
        ),
        Destination(
            name="鐟楀灝鐣ㄩ崗鐢糕攬娣?,
            location="闂勬洝銈块惇浣姐偪鐎瑰绔?,
            description="缁夛箑顫愰惃鍥у徍妞诡兛绻庨崡姘卞⒖妫ｅ棙妲告稉鏍櫕閺傚洤瀵查柆妞鹃獓閿涘矁顫︾懢澶夎礋娑撴牜鏅粭顒€鍙撴径褍顨屾潻骞库偓鍌氬徍妞诡兛绻庣憴鍕佺€瑰繐銇囬敍灞炬殶闁插繋绱径姘剧礉濮ｅ繋閲滄穱鎴犳畱闂堛垽鍎寸悰銊﹀剰闁棄鎮囨稉宥囨祲閸氬被鈧倸褰叉禒銉ょ啊鐟欙絿袝娴狅絽宸婚崣鍙夋瀮閸栨牭绱濋幇鐔峰綀閸欍倓鍞崘娑楃皑閸旀盯鍣洪妴鍌炩偓鍌氭値閸樺棗褰堕弬鍥у閻栧崬銈介懓鍛嫲鐎硅泛娑甸弮鍛埗閵?,
            tags=["閸樺棗褰?, "閸楁氨澧挎＃?, "娑撴牜鏅柆妞鹃獓", "閼板啫褰?, "閺傚洤瀵?],
            best_season=[Season.SPRING, Season.AUTUMN],
            budget_range=[800, 2500],
            suitable_for=[TravelType.FAMILY, TravelType.FRIENDS, TravelType.SOLO],
            duration_days=2,
            rating=4.9
        ),
        Destination(
            name="閸橈箓妫Η鎾存爱鐏?,
            location="缁傚繐缂撻惇浣稿傅闂傘劌绔?,
            description="姒ф挻姘仦鎸庢Ц娑撯偓鎼囱呯法娑撶晫娈戝ù铚傜瑐閼哄崬娲亸蹇撶煗閿涘苯鐭濇稉濠傜紦缁涙垿顥撻弽鐓庮樋閺嶅嚖绱濋張澶夌閸ヨ棄缂撶粵鎴濆触鐟欏牅绠ｇ粔鑸偓鍌涚梾閺堝婧€閸斻劏婧呴敍宀€骞嗘晶鍐ㄧ暔闂堟瑤绱紘搴涒偓鍌氬讲娴犮儲鏋佸銉︽崳鏉堢櫢绱濋崣鍌濐潎閸氬嫬绱￠崚顐㈩暘閿涘苯鎼х亸婵嗙秼閸︽壆绶ㄦ鐔粹偓鍌炩偓鍌氭値閺傚洩澹撻棃鎺戝嬀閵嗕焦鍎忔笟锝呮嫲鐎硅泛娑甸弮鍛埗閵?,
            tags=["濞村嘲鐭?, "瀵よ櫣鐡?, "閺傚洩澹?, "濞寸兘鐭?, "濠曨偅顒?],
            best_season=[Season.SPRING, Season.AUTUMN],
            budget_range=[1500, 4000],
            suitable_for=[TravelType.COUPLE, TravelType.FAMILY, TravelType.FRIENDS],
            duration_days=3,
            rating=4.7
        )
    ]

    return destinations


def main():
    """娑撹鍤遍弫?""
    try:
        logger.info("瀵偓婵鍨垫慨瀣缁€杞扮伐閺佺増宓?..")

        # 閼惧嘲褰?RAG 瀵洘鎼?        rag_engine = get_rag_engine()

        # 閸掓稑缂撶粈杞扮伐閺佺増宓?        destinations = create_sample_destinations()
        logger.info(f"閸掓稑缂撴禍?{len(destinations)} 娑擃亞銇氭笟瀣珯閻?)

        # 濞ｈ濮為崚鏉挎倻闁插繑鏆熼幑顔肩氨
        success = rag_engine.add_destinations(destinations)

        if success:
            logger.success(f"閴?閹存劕濮涘ǎ璇插 {len(destinations)} 娑擃亝娅欓悙鐟板煂閸氭垿鍣洪弫鐗堝祦鎼存搫绱?)
            logger.info("閻滄澘婀崣顖欎簰瀵偓婵绁寸拠鏇熷腹閼芥劕濮涢懗鎴掔啊")
        else:
            logger.error("閴?濞ｈ濮為弫鐗堝祦婢惰精瑙?)
            return False

        return True

    except Exception as e:
        logger.error(f"閸掓繂顫愰崠鏍ㄦ殶閹诡喖銇戠拹? {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
