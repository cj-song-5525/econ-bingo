import streamlit as st
import math
import re

# ==========================================
# 1. 게임 기본 세팅
# ==========================================
st.set_page_config(page_title="경제학 빙고 게임", layout="wide")

TERMS = [
    "수요", "공급", "기회비용", "독점", "과점", "GDP", "인플레이션", 
    "디플레이션", "GNP", "거시경제학", "미시경제학", "대체재", "국채", 
    "고정금리", "변동금리", "비교우위", "보완재", "역선택", "애덤스미스", 
    "이윤", "기준금리", "도덕적해이", "화폐", "빅맥지수", "비트코인", 
    "경제", "명목환율"
]

QUIZZES = [
    {
        "question": "[5라운드 팝퀴즈] 다음 중 '어떤 선택을 함으로써 포기해야 하는 대안들 중에서 가장 가치 있는 것'을 뜻하는 용어는?",
        "options": ["매몰비용", "기회비용", "한계효용", "비교우위"],
        "answer_index": 1
    },
    {
        "question": "[10라운드 팝퀴즈] 다음 중 '한 나라의 화폐가 외국의 화폐와 교환되는 비율'을 뜻하는 용어는?",
        "options": ["수익률", "이자율", "물가상승률", "환율"],
        "answer_index": 3
    },
    {
        "question": "[15라운드 팝퀴즈] 다음 중 '모든 상품의 가격이 전반적으로 꾸준히 오르는 경제 현상'을 뜻하는 용어는?",
        "options": ["인플레이션", "디플레이션", "스태그플레이션", "에그플레이션"],
        "answer_index": 0 
    }
]

# ==========================================
# 2. 서버 메모리 (Cache) 기반 중앙 DB 구축
# ==========================================
@st.cache_resource
def get_global_state():
    return {
        "admin_started": False,
        "game_over": False,  
        "max_per_room": 6,     
        "rooms": {},     
        "players": {}    
    }

db = get_global_state()

def calculate_lines(checked_matrix):
    lines = 0
    for i in range(4):
        if all(checked_matrix[i][j] for j in range(4)): lines += 1
        if all(checked_matrix[j][i] for j in range(4)): lines += 1
    if all(checked_matrix[i][i] for i in range(4)): lines += 1
    if all(checked_matrix[i][3-i] for i in range(4)): lines += 1
    return lines

def assign_room(nickname):
    room_num = 1
    while True:
        if room_num not in db["rooms"]:
            # [버그 수정 완료] quiz_winners를 리스트가 아닌 딕셔너리로 관리하여 우승자를 라운드별로 누적 저장합니다.
            db["rooms"][room_num] = {'players': [], 'turn': 1, 'quiz_active': False, 'quiz_winners': {}, 'quiz_idx': 0}
        
        if len(db["rooms"][room_num]['players']) < db["max_per_room"]:
            db["rooms"][room_num]['players'].append(nickname)
            db["players"][nickname] = {
                'room': room_num,
                'board': [["" for _ in range(4)] for _ in range(4)],
                'checked': [[False for _ in range(4)] for _ in range(4)],
                'ready': False,
                'lines': 0
            }
            break
        room_num += 1

# ==========================================
# 3. 화면 분기 (라우팅 및 로그인 로직) 
# ==========================================
st.title("📊 경제학 빙고 & 팝퀴즈 챌린지")

if "nickname" not in st.session_state:
    st.subheader("입장하기")
    
    col1, col2 = st.columns(2)
    with col1:
        nickname = st.text_input("닉네임을 입력하세요 (한글 7글자 이내)")
    with col2:
        admin_pw = st.text_input("관리자 비밀번호 (학생은 비워두세요)", type="password")
        
    if st.button("접속"):
        if nickname == "admin":
            if admin_pw == "2556":
                st.session_state["nickname"] = "admin"
                st.rerun()
            else:
                st.error("관리자 비밀번호가 일치하지 않습니다.")
        else:
            if not re.match(r'^[가-힣]{1,7}$', nickname):
                st.warning("⚠️ 닉네임은 공백, 숫자, 영문 없이 '한글 7글자 이내'로만 작성해주세요.")
            else:
                if nickname not in db["players"]:
                    if db["admin_started"]:
                        st.error("이미 게임이 시작되어 새로 접속할 수 없습니다.")
                    else:
                        assign_room(nickname)
                        st.session_state["nickname"] = nickname
                        st.rerun()
                else:
                    st.success("기존 데이터가 복구되었습니다. 게임을 이어서 진행합니다!")
                    st.session_state["nickname"] = nickname
                    st.rerun()

# [B] 관리자 화면
elif st.session_state["nickname"] == "admin":
    st.sidebar.success("👨‍🏫 관리자 모드 접속 중")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("게임 통제 센터")
        
        if not db["admin_started"]:
            new_max = st.selectbox(
                "👥 1개 조(방)당 최대 인원 설정", 
                [3, 4, 5, 6, 7, 8], 
                index=[3, 4, 5, 6, 7, 8].index(db["max_per_room"])
            )
            db["max_per_room"] = new_max
            st.caption(f"현재 {new_max}명씩 자동으로 방이 배정됩니다.")
            
            if st.button("🚀 전체 게임 시작 (신규 접속 차단)", use_container_width=True):
                db["admin_started"] = True
                db["game_over"] = False
                st.rerun()
                
        else:
            if not db["game_over"]:
                st.success("▶️ 현재 실시간으로 게임이 진행 중입니다.")
                if st.button("🛑 게임 최종 종료 (학생 화면 잠금 및 순위 동결)", type="primary", use_container_width=True):
                    db["game_over"] = True
                    st.rerun()
            else:
                st.error("🏁 게임이 정상적으로 종료되었습니다. 최종 순위를 확인하세요.")
                if st.button("🔄 전체 데이터 초기화 (다음 수업/새 게임 준비)", use_container_width=True):
                    db["admin_started"] = False
                    db["game_over"] = False
                    db["rooms"] = {}
                    db["players"] = {}
                    st.rerun()

    with col2:
        if st.button("🔄 실시간 순위 업데이트", type="primary", use_container_width=True):
            st.rerun()

    st.markdown("---")
    
    room_cols = st.columns(max(1, len(db["rooms"])))
    for idx, (room_id, room_data) in enumerate(db["rooms"].items()):
        with room_cols[idx % len(room_cols)]:
            st.markdown(f"### 🚪 {room_id}조 (현재 {room_data['turn']}턴)")
            
            # [버그 수정 완료] 팝퀴즈 우승자가 덮어씌워지지 않고, 라운드별로 누적되어 표시됩니다.
            if room_data["quiz_winners"]:
                for q_idx, winner in room_data["quiz_winners"].items():
                    round_num = (q_idx + 1) * 5
                    st.success(f"🎁 {round_num}R 퀴즈 우승: {winner}")
                
            for p in room_data['players']:
                p_data = db["players"][p]
                status = "✔️완료" if p_data['ready'] else "대기중"
                lines = p_data['lines']
                
                if lines >= 3:
                    st.markdown(f"**👑 {p} : BINGO!! ({lines}줄 완성)**")
                elif db["admin_started"]:
                    st.markdown(f"- {p} : {lines}줄 완성")
                else:
                    st.markdown(f"- {p} : {status}")

# [C] 학생 화면
else:
    nickname = st.session_state["nickname"]
    p_data = db["players"][nickname]
    my_room_id = p_data["room"]
    room_data = db["rooms"][my_room_id]
    
    is_frozen = db["game_over"]
    if is_frozen:
        st.error("🏁 교수님이 게임을 종료했습니다! 칠판(화면)을 통해 최종 등수를 확인하세요.")
    
    st.sidebar.write(f"👤 **{nickname}** 님 (소속: {my_room_id}조)")

    if not p_data["ready"]:
        st.info("아래 16칸에 원하는 경제학 용어를 선택하여 빙고판을 완성하세요. (중복 선택 불가)")
        
        selected_count = 0
        for i in range(4):
            cols = st.columns(4)
            for j in range(4):
                current_val = p_data['board'][i][j]
                sel = cols[j].selectbox(
                    f"({i+1},{j+1})", 
                    options=["선택하세요"] + TERMS, 
                    key=f"cell_{i}_{j}",
                    index=TERMS.index(current_val)+1 if current_val else 0
                )
                if sel != "선택하세요":
                    p_data['board'][i][j] = sel
                    selected_count += 1
        
        if selected_count == 16:
            flat_board = [item for sublist in p_data['board'] for item in sublist]
            if len(set(flat_board)) == 16:
                if st.button("✅ 준비 완료", type="primary"):
                    p_data["ready"] = True
                    st.rerun()
            else:
                st.error("중복된 용어가 있습니다. 모두 다른 용어로 채워주세요.")
                
    elif not db["admin_started"]:
        st.warning("교수님이 게임을 시작할 때까지 잠시 대기해주세요.")
        
    elif room_data["quiz_active"]:
        st.error("🚨 스피드 팝퀴즈 발생! 빙고판이 잠시 사라집니다.")
        quiz = QUIZZES[room_data["quiz_idx"]]
        st.subheader(quiz["question"])
        
        for idx, option in enumerate(quiz["options"]):
            if st.button(f"{idx + 1}. {option}", use_container_width=True, disabled=is_frozen):
                if idx == quiz["answer_index"]:
                    # [버그 수정 완료] 현재 진행 중인 퀴즈의 인덱스에 우승자를 안전하게 저장
                    room_data["quiz_winners"][room_data["quiz_idx"]] = nickname
                    room_data["quiz_active"] = False 
                    st.success("정답입니다! 퀴즈 우승자로 기록되었습니다.")
                    st.rerun()
                else:
                    st.warning("오답입니다. 다른 친구들에게 기회가 넘어갑니다!")

    else:
        p_data["lines"] = calculate_lines(p_data["checked"])
        
        # [UX 개선] 학생들이 직관적으로 턴을 업데이트할 수 있도록 사이드바에서 메인 화면 정중앙으로 이동
        st.button("🔄 현재 진행 상황 동기화 (새로고침)", use_container_width=True)
        
        if p_data["lines"] >= 3:
            st.balloons()
            st.success(f"🎉 BINGO! 총 {p_data['lines']}줄을 완성했습니다!")
        else:
            st.info(f"현재 {p_data['lines']}줄 완성!")
            
        current_turn_player = room_data['players'][(room_data['turn'] - 1) % len(room_data['players'])]
        
        if current_turn_player == nickname:
            st.warning("📣 내 차례입니다! 친구들이 체크할 수 있도록 단어를 외치고 아래에서 [다음 턴으로 넘기기]를 누르세요.")
            if st.button("⏭️ 다음 턴으로 넘기기 (클릭 시 턴 종료)", type="primary", disabled=is_frozen):
                room_data['turn'] += 1
                if room_data['turn'] - 1 in [5, 10, 15]:
                    room_data["quiz_active"] = True
                    room_data["quiz_idx"] = ((room_data['turn'] - 1) // 5) - 1
                st.rerun()
        else:
            st.info(f"현재 **{current_turn_player}** 님의 차례입니다. 호명된 단어를 내 빙고판에서 클릭하여 지우세요.")

        st.markdown("---")
        
        for i in range(4):
            cols = st.columns(4)
            for j in range(4):
                word = p_data['board'][i][j]
                is_checked = p_data['checked'][i][j]
                
                btn_text = f"✅ ~{word}~" if is_checked else word
                
                if cols[j].button(btn_text, key=f"btn_{i}_{j}", use_container_width=True, disabled=is_frozen):
                    p_data['checked'][i][j] = not is_checked 
                    st.rerun()