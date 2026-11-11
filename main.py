"""
Mini NPU Simulator (미션 3: AI가 계산하는 방식을 흉내 내는 작은 계산기)

- 모드 1: 3×3 필터 2개(A, B)와 패턴을 직접 입력해 MAC 점수로 판정
- 모드 2: data.json의 필터/패턴을 읽어 일괄 판정 + PASS/FAIL + 성능 분석 + 결과 요약
- 모드 3: (보너스) 2차원 vs 1차원 배열 MAC 속도 비교, 패턴 자동 생성기 사용

외부 라이브러리 없이 표준 라이브러리(json, time, pathlib)만 사용합니다.
"""

import json
import time
from pathlib import Path

# ---------------------------------------------------------
# 설정값 (상수)
# ---------------------------------------------------------
EPSILON = 1e-9        # 두 점수의 차이가 이보다 작으면 "동점"으로 본다
REPEAT_COUNT = 10     # 성능 측정 시 반복 횟수
PERF_SIZES = [3, 5, 13, 25]
DATA_FILE = Path(__file__).parent / "data.json"   # main.py와 같은 폴더의 data.json
LINE = "#" + "-" * 39


# =========================================================
# 1. 데이터 구조: N×N 2차원 리스트
# =========================================================
def create_matrix(n, value=0.0):
    """n×n 크기의 2차원 리스트를 만들어 돌려준다."""
    matrix = []
    for _ in range(n):
        row = [value] * n          # 한 줄(행)에 n개의 값
        matrix.append(row)
    return matrix


def get_value(matrix, row, col):
    """(row, col) 위치의 값을 읽는다."""
    return matrix[row][col]


def set_value(matrix, row, col, value):
    """(row, col) 위치에 값을 저장한다."""
    matrix[row][col] = value


def is_valid_matrix(matrix, n):
    """matrix가 '숫자로만 이루어진 n×n 2차원 리스트'인지 검사한다."""
    if not isinstance(matrix, list) or len(matrix) != n:
        return False
    for row in matrix:
        if not isinstance(row, list) or len(row) != n:
            return False
        for value in row:
            # True/False도 파이썬에서는 숫자로 취급되므로 따로 제외한다
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                return False
    return True


def describe_size(matrix):
    """오류 메시지용으로 행렬의 실제 크기를 '행×열' 글자로 만든다."""
    if not isinstance(matrix, list):
        return "배열 아님"
    if len(matrix) == 0:
        return "0×0"
    col_counts = []
    for row in matrix:
        col_counts.append(len(row) if isinstance(row, list) else -1)
    if min(col_counts) != max(col_counts):
        return f"{len(matrix)}행, 행마다 열 수가 다름"
    return f"{len(matrix)}×{col_counts[0]}"


def print_matrix(matrix):
    """행렬을 보기 좋게 출력한다 (정수처럼 보이는 값은 정수로 표시)."""
    for row in matrix:
        texts = []
        for value in row:
            if value == int(value):
                texts.append(str(int(value)))
            else:
                texts.append(str(value))
        print("  " + " ".join(texts))


# =========================================================
# 2. 패턴 생성기 (보너스 2): N×N 십자가 / X 자동 생성
# =========================================================
def make_cross(n):
    """가운데 행과 가운데 열이 1인 십자가 패턴을 만든다."""
    matrix = create_matrix(n)
    center = n // 2
    for i in range(n):
        set_value(matrix, center, i, 1.0)   # 가운데 가로줄
        set_value(matrix, i, center, 1.0)   # 가운데 세로줄
    return matrix


def make_x(n):
    """두 대각선이 1인 X 패턴을 만든다."""
    matrix = create_matrix(n)
    for i in range(n):
        set_value(matrix, i, i, 1.0)          # 왼쪽 위 → 오른쪽 아래
        set_value(matrix, i, n - 1 - i, 1.0)  # 오른쪽 위 → 왼쪽 아래
    return matrix


# =========================================================
# 3. 라벨 정규화: 여러 표기를 표준 라벨(Cross / X)로 통일
# =========================================================
# 프로그램 안에서 쓰는 표준 라벨 목록 (판정·출력·필터 로드가 모두 이 목록을 따른다)
STANDARD_LABELS = ["Cross", "X"]

# 데이터에 나올 수 있는 표기 → 표준 라벨 매핑 표
# ※ 키는 반드시 '앞뒤 공백 없는 소문자'로 적는다. (입력도 소문자로 바꾼 뒤 찾기 때문)
LABEL_ALIASES = {
    "+": "Cross",
    "cross": "Cross",
    "x": "X",
}


def normalize_label(label):
    """매핑 표에서 표준 라벨을 찾아 돌려준다. 표에 없는 표기면 None."""
    text = str(label).strip().lower()   # 앞뒤 공백 제거 + 소문자로 통일
    return LABEL_ALIASES.get(text)      # 없으면 None


# =========================================================
# 4. MAC 연산 (Multiply-Accumulate)
# =========================================================
def mac(pattern, filter_matrix):
    """같은 위치끼리 곱하고(Multiply) 모두 더한(Accumulate) 점수를 돌려준다."""
    n = len(pattern)
    total = 0.0
    for i in range(n):              # 행
        for j in range(n):          # 열
            total += pattern[i][j] * filter_matrix[i][j]
    return total


def flatten(matrix):
    """(보너스 1) 2차원 리스트를 길이 N²의 1차원 리스트로 펼친다."""
    flat = []
    for row in matrix:
        for value in row:
            flat.append(value)
    return flat


def mac_flat(flat_pattern, flat_filter):
    """(보너스 1) 1차원 리스트로 MAC 연산을 한다. 반복문이 1개로 줄어든다."""
    total = 0.0
    for k in range(len(flat_pattern)):
        total += flat_pattern[k] * flat_filter[k]
    return total


# =========================================================
# 5. 점수 비교 정책 (epsilon 기반 동점 처리)
# =========================================================
def judge(scores):
    """scores = {"라벨": 점수, ...} 에서 점수가 가장 높은 라벨을 돌려준다.
    1등과 점수 차이가 EPSILON보다 작은 다른 라벨이 있으면 동점(UNDECIDED).
    라벨이 2개든 3개 이상이든 같은 방식으로 동작한다."""
    # ① 가장 높은 점수 찾기
    best_label = None
    best_score = None
    for label, score in scores.items():
        if best_score is None or score > best_score:
            best_label = label
            best_score = score

    # ② 1등과 거의 같은 점수가 또 있으면 판정 불가
    for label, score in scores.items():
        if label != best_label and abs(best_score - score) < EPSILON:
            return "UNDECIDED"
    return best_label


# =========================================================
# 6. 성능 측정
# =========================================================
def measure_average_ms(mac_function, pattern, filter_matrix, repeat=REPEAT_COUNT):
    """mac_function을 repeat번 실행하고 1회 평균 시간(ms)을 돌려준다.
    입력/출력/파일 읽기는 빼고 '연산 함수 호출'만 시간을 잰다."""
    start = time.perf_counter()
    for _ in range(repeat):
        mac_function(pattern, filter_matrix)
    end = time.perf_counter()
    return (end - start) * 1000 / repeat     # 초 → 밀리초, 그리고 평균


def run_performance(sizes):
    """크기별 평균 연산 시간과 연산 횟수(N²) 표를 출력한다."""
    print(f"{'크기':<10}{'평균 시간(ms)':>14}{'연산 횟수(N²)':>14}")
    print("-" * 40)
    for n in sizes:
        pattern = make_cross(n)      # 같은 모양의 데이터로 크기만 바꿔 측정
        filter_matrix = make_x(n)
        avg_ms = measure_average_ms(mac, pattern, filter_matrix)
        size_text = f"{n}×{n}"
        print(f"{size_text:<10}{avg_ms:>14.4f}{n * n:>14}")


def section(title):
    """구역 제목을 출력한다."""
    print(LINE)
    print(f"# {title}")
    print(LINE)


# =========================================================
# 7. 모드 1: 사용자 입력 (3×3)
# =========================================================
def input_matrix(title, n=3):
    """n줄을 한 줄씩 입력받아 n×n 행렬을 만든다. 잘못된 줄은 다시 입력받는다."""
    print(f"{title} ({n}줄 입력, 공백 구분)")
    matrix = []
    while len(matrix) < n:
        parts = input().split()        # 공백 기준으로 나누기
        if len(parts) != n:
            print(f"입력 형식 오류: 각 줄에 {n}개의 숫자를 공백으로 구분해 입력하세요. "
                  f"({len(matrix) + 1}번째 줄을 다시 입력)")
            continue
        try:
            row = [float(p) for p in parts]
        except ValueError:
            print(f"입력 형식 오류: 숫자만 입력하세요. ({len(matrix) + 1}번째 줄을 다시 입력)")
            continue
        matrix.append(row)
    return matrix


def mode_user_input():
    section("[1] 필터 입력")
    filter_a = input_matrix("필터 A")
    filter_b = input_matrix("필터 B")
    print("✓ 필터 저장 완료")
    print("[필터 A]")
    print_matrix(filter_a)
    print("[필터 B]")
    print_matrix(filter_b)

    section("[2] 패턴 입력")
    pattern = input_matrix("패턴")

    section("[3] MAC 결과")
    score_a = mac(pattern, filter_a)
    score_b = mac(pattern, filter_b)

    # 두 필터 점수를 계산하는 구간만 10회 반복해 평균 시간 측정
    start = time.perf_counter()
    for _ in range(REPEAT_COUNT):
        mac(pattern, filter_a)
        mac(pattern, filter_b)
    avg_ms = (time.perf_counter() - start) * 1000 / REPEAT_COUNT

    verdict = judge({"A": score_a, "B": score_b})
    print(f"A 점수: {score_a}")
    print(f"B 점수: {score_b}")
    print(f"연산 시간(평균/{REPEAT_COUNT}회): {avg_ms:.4f} ms")
    if verdict == "UNDECIDED":
        print(f"판정: 판정 불가 (|A-B| < {EPSILON})")
    else:
        print(f"판정: {verdict}")

    section(f"[4] 성능 분석 (평균/{REPEAT_COUNT}회)")
    run_performance([3])


# =========================================================
# 8. 모드 2: data.json 분석
# =========================================================
def load_json(path):
    """JSON 파일을 읽어 딕셔너리로 돌려준다. 실패하면 None."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"오류: {path.name} 파일을 찾을 수 없습니다. ({path})")
    except json.JSONDecodeError as e:
        print(f"오류: {path.name}의 JSON 형식이 올바르지 않습니다. ({e})")
    return None


def get_size_from_key(key):
    """'size_5' 또는 'size_13_2' 같은 키에서 크기 N(정수)을 꺼낸다. 실패하면 None."""
    parts = key.split("_")
    if len(parts) < 2 or parts[0] != "size" or not parts[1].isdigit():
        return None
    return int(parts[1])


def load_filters(raw_filters):
    """filters 부분을 읽어 {N: {"Cross": 행렬, "X": 행렬, ...}} 형태로 만든다.
    STANDARD_LABELS의 필터가 하나라도 없으면 그 크기는 사용하지 않는다."""
    filters = {}
    if not isinstance(raw_filters, dict):
        print("✗ filters 항목이 없거나 형식이 잘못되었습니다.")
        return filters

    for size_key, group in raw_filters.items():
        n = get_size_from_key(size_key)
        if n is None or not isinstance(group, dict):
            print(f"✗ {size_key}: 키 또는 형식 오류로 건너뜀")
            continue

        loaded = {}
        for label_key, matrix in group.items():
            label = normalize_label(label_key)          # 'cross' → 'Cross', 'x' → 'X'
            if label is None:
                print(f"✗ {size_key}: 알 수 없는 필터 이름 '{label_key}'")
            elif not is_valid_matrix(matrix, n):
                print(f"✗ {size_key}: {label} 필터 크기 오류 ({describe_size(matrix)})")
            else:
                loaded[label] = matrix

        missing = []
        for label in STANDARD_LABELS:
            if label not in loaded:
                missing.append(label)

        label_text = ", ".join(STANDARD_LABELS)
        if not missing:
            filters[n] = loaded
            print(f"✓ {size_key} 필터 로드 완료 ({label_text})")
        else:
            print(f"✗ {size_key} 필터 로드 실패 (없는 필터: {', '.join(missing)})")
    return filters


def analyze_pattern(key, case, filters):
    """패턴 1개를 판정해 출력하고, 실패하면 사유 문자열을, 통과하면 None을 돌려준다."""
    print(f"--- {key} ---")

    # ① 키 규칙 검사: size_{N}_{idx}
    n = get_size_from_key(key)
    if n is None or len(key.split("_")) != 3:
        reason = "키 형식 오류 (size_{N}_{idx} 형식이 아님)"
        print(f"FAIL: {reason}")
        return reason

    # ② 스키마 검사: input, expected가 있는지
    if not isinstance(case, dict) or "input" not in case or "expected" not in case:
        reason = "스키마 오류 (input 또는 expected 없음)"
        print(f"FAIL: {reason}")
        return reason

    # ③ 해당 크기의 필터가 있는지
    if n not in filters:
        reason = f"size_{n} 필터가 없음"
        print(f"FAIL: {reason}")
        return reason

    # ④ 패턴 크기/값 검사
    pattern = case["input"]
    if not is_valid_matrix(pattern, n):
        actual = describe_size(pattern)
        if actual == f"{n}×{n}":
            reason = "값 오류 (숫자가 아닌 값이 있음)"
        else:
            reason = f"크기 불일치 (필터 {n}×{n}, 패턴 {actual})"
        print(f"FAIL: {reason}")
        return reason

    # ⑤ expected 라벨 정규화: '+' → Cross, 'x' → X
    expected = normalize_label(case["expected"])
    if expected is None:
        reason = f"알 수 없는 expected 라벨 '{case['expected']}'"
        print(f"FAIL: {reason}")
        return reason

    # ⑥ 표준 라벨마다 MAC 연산 → 판정 → PASS/FAIL
    scores = {}
    for label in STANDARD_LABELS:
        scores[label] = mac(pattern, filters[n][label])
        print(f"{label} 점수: {scores[label]}")
    verdict = judge(scores)
    if verdict == expected:
        print(f"판정: {verdict} | expected: {expected} | PASS")
        return None

    if verdict == "UNDECIDED":
        reason = "동점(UNDECIDED) 처리 규칙에 따라 FAIL"
    else:
        reason = f"판정({verdict})이 expected({expected})와 다름"
    print(f"판정: {verdict} | expected: {expected} | FAIL")
    return reason


def mode_json_analysis():
    data = load_json(DATA_FILE)
    if data is None:
        return

    section("[1] 필터 로드")
    filters = load_filters(data.get("filters"))

    section("[2] 패턴 분석 (라벨 정규화 적용)")
    patterns = data.get("patterns")
    if not isinstance(patterns, dict):
        print("✗ patterns 항목이 없거나 형식이 잘못되었습니다.")
        patterns = {}

    failures = []          # (케이스 이름, 실패 사유) 목록
    for key, case in patterns.items():
        reason = analyze_pattern(key, case, filters)
        if reason is not None:
            failures.append((key, reason))

    section(f"[3] 성능 분석 (평균/{REPEAT_COUNT}회)")
    run_performance(PERF_SIZES)

    section("[4] 결과 요약")
    total = len(patterns)
    print(f"총 테스트: {total}개")
    print(f"통과: {total - len(failures)}개")
    print(f"실패: {len(failures)}개")
    if failures:
        print("실패 케이스:")
        for key, reason in failures:
            print(f"- {key}: {reason}")


# =========================================================
# 9. 모드 3 (보너스): 2차원 vs 1차원 성능 비교
# =========================================================
def mode_bonus_compare():
    section(f"[보너스] 2차원 vs 1차원 MAC 비교 (평균/{REPEAT_COUNT}회)")
    print(f"{'크기':<10}{'2차원(ms)':>12}{'1차원(ms)':>12}{'차이(%)':>10}")
    print("-" * 44)
    for n in PERF_SIZES:
        pattern = make_cross(n)            # 패턴 생성기로 같은 입력 준비
        filter_matrix = make_x(n)
        flat_pattern = flatten(pattern)    # 펼치는 시간은 측정에서 제외
        flat_filter = flatten(filter_matrix)

        time_2d = measure_average_ms(mac, pattern, filter_matrix)
        time_1d = measure_average_ms(mac_flat, flat_pattern, flat_filter)
        diff = (time_2d - time_1d) / time_2d * 100 if time_2d > 0 else 0
        size_text = f"{n}×{n}"
        print(f"{size_text:<10}{time_2d:>12.4f}{time_1d:>12.4f}{diff:>9.1f}%")
    print("※ 차이(%)가 양수면 1차원 방식이 더 빠르다는 뜻입니다.")


# =========================================================
# 10. 프로그램 시작
# =========================================================
def main():
    print("=== Mini NPU Simulator ===")
    while True:
        print()
        print("[모드 선택]")
        print("1. 사용자 입력 (3x3)")
        print("2. data.json 분석")
        print("3. 보너스: 2차원/1차원 성능 비교")
        print("0. 종료")
        choice = input("선택: ").strip()

        if choice == "1":
            mode_user_input()
        elif choice == "2":
            mode_json_analysis()
        elif choice == "3":
            mode_bonus_compare()
        elif choice == "0":
            print("프로그램을 종료합니다.")
            break
        else:
            print("0, 1, 2, 3 중에서 선택하세요.")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):     # Ctrl+C, Ctrl+D 로 끝내도 오류 화면 없이 종료
        print("\n프로그램을 종료합니다.")
