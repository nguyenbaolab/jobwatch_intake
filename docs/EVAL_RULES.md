# EVAL_RULES — Luật chấm extractor (v0.1)

Trạng thái: bản thiết kế, chưa có code. Ngày 4 sẽ code runner theo file này.
Mọi mục "Đề xuất" cần tôi duyệt: đánh [x] khi đồng ý, sửa nếu không.

## 1. Đầu vào

- **Gold:** mỗi tin một file JSON, đúng định dạng `GoldLabel` (`domain/gold_label.py`).
- **Prediction (output extractor):** mỗi tin một file `predictions/<job_id>.json`.
  Cùng tên trường với các trường được chấm ở mục 3. Không có `labeler`, `labeled_at`, `notes`.
  - [x] Đề xuất: khi prediction thiếu key, lấy default giống `GoldLabelFileDTO`. DTO đó là class mới ở outbound, vì outbound không được import inbound.
  - Lý do: một nguồn sự thật cho "giá trị rỗng"; extractor không bị phạt chỉ vì bỏ key.

## 2. Ghép gold với prediction

- [x] Ghép theo `job_id`, không theo thứ tự file.
- [x] Gold có, prediction **không có**: mọi trường của tin đó tính **SAI**, vẫn nằm trong mẫu số.
  Runner liệt kê tin đó trong mục `missing_predictions`.
  - Lý do: extractor bỏ cả tin là lỗi thật; loại khỏi mẫu số sẽ làm điểm đẹp giả.
- [x] Prediction có, gold **không có**: bỏ qua khi tính điểm, liệt kê trong `unlabeled_predictions`.

## 3. Trường được chấm và quy tắc so sánh

| Trường | Kiểu | Quy tắc |
|---|---|---|
| `experience_years_min` | int hoặc null | exact match |
| `city` | str hoặc null | `strip()` + `lower()` hai bên rồi so bằng |
| `work_mode` | enum | exact match |
| `deadline` | date hoặc null | exact match (so ngày, ISO `YYYY-MM-DD`) |
| `finnish.requirement`, `swedish.requirement`, `english.requirement` | enum | exact match |
| `finnish.level`, `swedish.level`, `english.level` | enum | exact match |
| `skills_required`, `skills_preferred` | list[str] | chuẩn hoá từng phần tử (`strip` + `lower`), chuyển sang **set**, so set |

**Không chấm:** `job_id` (dùng để ghép), `labeler`, `labeled_at`, `notes`.

- [x] Ngôn ngữ chấm tách làm 2 trường con (`requirement` và `level`).
  - Lý do: đúng "required" nhưng sai level vẫn là đúng một nửa thông tin. Gộp lại sẽ che mất điều đó.
- [x] Skills so dạng **set**.
  - Lý do: gold lưu `tuple` (giữ thứ tự), nhưng thứ tự skill trong tin không mang nghĩa.
  - **Bẫy:** không được so `tuple == tuple`.

## 4. Chính sách null

Định nghĩa **giá trị rỗng**: `None`, `[]`, `"unspecified"`, `"not_mentioned"`.

| Gold | Prediction | Kết quả |
|---|---|---|
| rỗng | rỗng (cùng giá trị) | ĐÚNG |
| rỗng | có giá trị | SAI (bịa thông tin) |
| có giá trị | rỗng | SAI (bỏ sót) |
| có giá trị | có giá trị | so theo mục 3 |

- [x] Đề xuất: **null là một giá trị**; không loại ô nào khỏi mẫu số.
  - Lý do: tin tuyển dụng thường không ghi số năm, deadline, thành phố. Nói đúng "không có" cũng là một kỹ năng cần đo.
  - Nếu loại null khỏi mẫu số, lỗi bịa giá trị không bao giờ bị phạt.
- [x] Để chống "extractor lười ăn điểm" (trả rỗng mọi nơi), mỗi trường báo **2 con số**:
  - `acc_all`: tính trên mọi tin.
  - `acc_gold_nonempty`: chỉ tính trên các tin mà gold **không** rỗng.
  - Nếu `acc_all` cao mà `acc_gold_nonempty` thấp, extractor đang thắng nhờ đoán "không có".

## 5. Công thức

**Accuracy một trường:**

    acc_all           = số ô ĐÚNG / số tin trong gold
    acc_gold_nonempty = số ô ĐÚNG trong nhóm gold không rỗng / số tin có gold không rỗng
    (nhóm rỗng: báo "n/a", không báo 0%)

**Skills (thêm, cộng dồn kiểu micro qua mọi tin):**

    TP        = tổng số skill có ở cả gold và prediction
    precision = TP / tổng số skill extractor đưa ra
    recall    = TP / tổng số skill trong gold
    F1        = 2·TP / (tổng skill prediction + tổng skill gold)

- Tin có `[]` ở cả hai bên chỉ đóng góp 0 vào mọi tổng, nên không có phép chia 0/0 ở từng tin.
- Nếu cả tổng cũng bằng 0, báo "n/a".

**Điểm tổng:**
- [x] v0.1 **không có** điểm tổng.
  - Lý do: một con số trung bình che mất trường nào yếu. Thêm macro average ở bản sau nếu cần.

## 6. Output của runner

1. **Bảng từng trường:** `field | n | correct | acc_all | n_nonempty | acc_gold_nonempty`
2. **Skills:** `precision | recall | F1` cho từng list.
3. **Danh sách ô sai:** `job_id | field | gold | prediction` để debug.
4. `missing_predictions`, `unlabeled_predictions`.

## 7. Ví dụ chạy tay (kết quả mong đợi, dùng làm test đầu tiên)

Gold:

| job | experience_years_min | work_mode | city | skills_required |
|---|---|---|---|---|
| J1 | 3 | hybrid | helsinki | [python, sql] |
| J2 | null | remote | null | [react] |
| J3 | 5 | onsite | espoo | [java, spring, sql] |

Prediction:

| job | experience_years_min | work_mode | city | skills_required |
|---|---|---|---|---|
| J1 | 3 | hybrid | "Helsinki" | [sql, python] |
| J2 | 2 | remote | null | [react, typescript] |
| J3 | null | onsite | espoo | [java] |

So từng ô:

| job | experience_years_min | work_mode | city | skills_required (set) |
|---|---|---|---|---|
| J1 | ✓ | ✓ | ✓ (nhờ lower) | ✓ (bỏ qua thứ tự) |
| J2 | ✗ bịa | ✓ | ✓ null/null | ✗ |
| J3 | ✗ bỏ sót | ✓ | ✓ | ✗ |

Điểm mong đợi:

| field | acc_all | acc_gold_nonempty |
|---|---|---|
| experience_years_min | 1/3 = 0.33 | 1/2 = 0.50 (J1, J3) |
| work_mode | 3/3 = 1.00 | 3/3 = 1.00 |
| city | 3/3 = 1.00 | 2/2 = 1.00 (J1, J3) |
| skills_required | 1/3 = 0.33 | 1/3 = 0.33 |

Skills micro:
- TP = 2 + 1 + 1 = 4
- precision = 4/5 = 0.80
- recall = 4/6 = 0.67
- F1 = 8/11 = 0.73

## 8. Ba extractor giả cho ngày 4

| Extractor giả | Kết quả mong đợi | Nếu khác, nghĩa là |
|---|---|---|
| Trả lại đúng gold | 100% mọi trường | lỗi ghép `job_id` hoặc lỗi chuẩn hoá |
| Trả rỗng mọi trường | `acc_gold_nonempty` = 0% mọi trường | luật rỗng ở mục 4 bị code sai |
| Đúng gold nhưng đảo thứ tự skill | giống hệt extractor "đúng gold" | đang so `tuple` thay vì `set` |

## 9. Giới hạn đã biết (chưa xử lý ở v0.1)

- Tên thành phố khác ngôn ngữ (Helsinki / Helsingfors) bị tính SAI.
- Skill đồng nghĩa (js / javascript) bị tính SAI.
- Chưa đo độ tin cậy của chính gold (một người gán nhãn).