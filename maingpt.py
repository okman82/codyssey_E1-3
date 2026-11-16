import json

print("=== Mini NPU Simulator ===")

with open("data.json", "r", encoding="utf-8") as file:
    data = json.load(file)

# print("JSON 파이일 읽기 성공!")
# print("파일 버젼 :", data["meta"]["version"])
# print("파일 종류 :", data["meta"]["type"])


# print("첫 번째 문제 정답:", data["patterns"]["size_5_1"]["expected"])
# print("두 번째 문제 정답:", data["patterns"]["size_5_2"]["expected"])


# pattern = data["patterns"]["size_5_1"]["input"]

# print("=== 5*5 x 패턴 ===")

# for row in pattern:
#     print(row)


# print("행 개수 : ", len(pattern))
# print("열 개수 : ", len(pattern[0]))
# print("중앙 값 : ", pattern[2][2])


# print("=== MAC 기초 실습 ===")

# total = 0

# total = total + (2 * 3)
# print("첫 번째 합계:", total)

# total = total + (4 * 5)
# print("두 번째 합계:", total)

# total = total + (1 * 6)
# print("세 번째 합계:", total)



# a = [2, 4, 1]
# b = [3, 5, 6]

# total = 0
# for i in range(len(a)):
#     total = total + (a[i] * b[i])

# print("최종 합계:", total)


# for row in range(3):
#     for col in range(3):
#         print(row, col)



# print("=== 3x3 MAC 실습 ===")

# pattern = [
#     [1, 0, 1],
#     [0, 1, 0],
#     [1, 0, 1]
# ]

# cross_filter = [
#     [0, 1, 0],
#     [1, 1, 1],
#     [0, 1, 0]
# ]

# x_filter = [
#     [1, 0, 1],
#     [0, 1, 0],
#     [1, 0, 1]
# ]        

# cross_score = 0
# x_score = 0

# for row in range(3):
#     for col in range(3):
#         cross_score += pattern[row][col] * cross_filter[row][col]
#         x_score += pattern[row][col] * x_filter[row][col]

# print("십자가 점수 : ", cross_score)
# print("x 점수 : ", x_score)


# if cross_score > x_score:
#     print("최종 판정 :  십자가(+)")
# elif x_score > cross_score:
#     print("최종 판정 : X")
# else:
#     print("최종 판정 : 동점")


print("=== 실제 JSON MAC 계산 =====")

pattern = data["patterns"]["size_5_1"]["input"]

cross_filter = data["filters"]["size_5"]["cross"]
x_filter = data["filters"]["size_5"]["x"]

cross_score = 0
x_score = 0

for row in range(5):
    for col in range(5):
        cross_score += pattern[row][col] * cross_filter[row][col]
        x_score += pattern[row][col] * x_filter[row][col]



print("cross 점수 : ", round(cross_score,2))
print("x 점수 : ", round(x_score,2))

if cross_score > x_score:
    result = "+"
elif x_score > cross_score:
    result = "x"
else:
    result = "tie"

expected = data["patterns"]["size_5_1"]["expected"]    


print("계산 결과 : ", result)
print("JSON 결과 : ", expected)
print("정답 여부:", "PASS" if result == expected else "FAIL")

