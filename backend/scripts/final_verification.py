"""
閺堚偓缂佸牓鐛欑拠浣圭ゴ鐠?- 妤犲矁鐦夐幍鈧張澶夋叏婢跺秵妲搁崥锔炬晸閺?"""
print("=" * 80)
print("閺堚偓缂佸牓鐛欑拠浣圭ゴ鐠?)
print("=" * 80)

tests = [
    {
        "name": "Milvus鏉╃偞甯?,
        "status": "瀵板懏绁寸拠?,
        "description": "妤犲矁鐦塎ilvus閺堝秴濮熷锝呯埗鏉╂劘顢?
    },
    {
        "name": "濞ｅ嘲鎮庡Λ鈧槐銏犲瀻閺?,
        "status": "瀵板懏绁寸拠?,
        "description": "妤犲矁鐦夐崚鍡樻殶娴?.01閹绘劕宕岄崚?.2-0.4"
    },
    {
        "name": "Province/City閹绘劕褰?,
        "status": "瀵板懏绁寸拠?,
        "description": "妤犲矁鐦塸rovince閸滃畱ity鐎涙顔屽锝団€橀幓鎰絿"
    },
    {
        "name": "瀹搞儰缍斿ù浣哥暚閺佸瓨鈧?,
        "status": "瀵板懏绁寸拠?,
        "description": "妤犲矁鐦?娑擃亣濡悙鐟板弿闁劍顒滅敮鍛婂⒔鐞?
    },
    {
        "name": "閸撳秶顏紒鎾寸亯閺勫墽銇?,
        "status": "瀵板懏绁寸拠?,
        "description": "妤犲矁鐦夐崜宥囶伂濮濓絿鈥橀弰鍓с仛AI閸ョ偛顦?
    }
]

print("\n瀵板懘鐛欑拠渚€銆嶉惄?")
for i, test in enumerate(tests, 1):
    print(f"{i}. [{test['status']}] {test['name']}")
    print(f"   閹诲繗鍫? {test['description']}")
    print()

print("=" * 80)
print("鐠囩兘鍣搁崥顖氭倵缁旑垱婀囬崝鈥蹭簰鎼存梻鏁ら幍鈧張澶夋叏婢?")
print("=" * 80)
print("""
cd E:\\婢堆勀侀崹瀣磻閸欐叚\娴狅絿鐖淺\缂冩垹鐝痋\travel_proj\\backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
""")

print("=" * 80)
print("闁插秴鎯庨崥搴礉閸︺劌澧犵粩顖涚ゴ鐠囨洑浜掓稉瀣叀鐠?")
print("=" * 80)
print("1. 娑撳绔荤仦杈ㄦ⒕濞撳憡鏁鹃悾?)
print("2. 鐟楁寧绠规搴㈡珯")
print("3. 娑撳﹥鎹ｆ径鏍ㄥ摋")
print()
print("妫板嫭婀＄紒鎾寸亯:")
print("- 鏉╂柨娲朅I閸ョ偛顦查敍鍫滅瑝閸愬秵妯夌粈?濞屸剝婀侀幍鎯у煂閻╃鍙ч惃鍕⒕濞撻晲淇婇幁?閿?)
print("- 閸掑棙鏆熼崷?.2-0.4閼煎啫娲?)
print("- 鏉╂柨娲栭惄绋垮彠閺咁垳鍋ｉ幒銊ㄥ礃")
print("=" * 80)
