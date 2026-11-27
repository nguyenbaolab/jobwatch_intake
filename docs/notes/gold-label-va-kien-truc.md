# Gold label và eval runner trong Clean Architecture

Ghi chú học, Tuần 1, v0.1, Ngày 3. Đọc cùng `docs/EVAL_RULES.md`.

Quy ước trong file:
- **Đã có:** Cursor thấy trong repo (báo cáo khảo sát ngày 3).
- **Đề xuất:** chưa có code, tên file và tên class chỉ là gợi ý.

---

## 1. Gold label là gì

Gold label (nhãn vàng) là **đáp án do người thật điền** cho một tin tuyển dụng.
Nó là chuẩn để chấm extractor. Ta coi nó là đúng, kể cả khi người gán nhãn có lúc nhầm.

| Trong bài thi | Trong Jobwatch |
|---|---|
| Đề thi | Tin tuyển dụng |
| Đáp án do giáo viên soạn | **Gold label** |
| Bài làm của học sinh | **Prediction**: output của extractor (LLM) |
| Giáo viên chấm bài | **Eval runner** |
| Bảng điểm | Báo cáo accuracy từng trường |

**Vì sao cần:** có gold thì mới *đo* được LLM giỏi đến đâu.
Khi đổi prompt hay đổi model, ta biết điểm tăng hay giảm bằng số, không bằng cảm giác.

---

## 2. Ví dụ một tin

**Tin tuyển dụng (đề thi):**

> Etsimme Python-kehittäjää Helsinkiin. Hybridityö. Vähintään 3 vuoden kokemus. Hyvä suomen kielen taito.

Tạm dịch: Tìm lập trình viên Python ở Helsinki. Làm hybrid. Tối thiểu 3 năm kinh nghiệm. Tiếng Phần Lan tốt.

**Gold label:** người gán nhãn đọc tin và điền vào `labels/job-a1abfcca01d0.json`:

```json
{
  "job_id": "job-a1abfcca01d0",
  "labeler": "an",
  "labeled_at": "2026-11-26",
  "skills_required": ["python"],
  "experience_years_min": 3,
  "city": "helsinki",
  "work_mode": "hybrid",
  "finnish": {"requirement": "required", "level": "good"}
}
```

**Prediction:** LLM đọc cùng tin và điền cùng các trường:

```json
{
  "job_id": "job-a1abfcca01d0",
  "skills_required": ["Python"],
  "experience_years_min": 3,
  "city": "Helsinki",
  "work_mode": "onsite",
  "finnish": {"requirement": "required", "level": "fluent"}
}
```

**Chấm từng trường** (theo luật trong `EVAL_RULES.md`):

| Trường | Gold | Prediction | Kết quả |
|---|---|---|---|
| `skills_required` | [python] | [Python] | ✓ (sau `lower`, so set) |
| `experience_years_min` | 3 | 3 | ✓ |
| `city` | helsinki | Helsinki | ✓ (sau `strip` + `lower`) |
| `work_mode` | hybrid | onsite | ✗ |
| `finnish.requirement` | required | required | ✓ |
| `finnish.level` | good | fluent | ✗ |

Một tin chỉ cho đúng/sai từng ô. **Accuracy một trường** cần nhiều tin: số tin đúng ở trường đó / tổng số tin.

---

## 3. Đặt vào Clean Architecture

**Nguyên tắc:** luật nằm ở trong, đọc/ghi file nằm ở ngoài.
Tầng trong không biết file JSON hay CLI tồn tại.
Phụ thuộc chỉ chỉ vào trong: adapters → application → domain.

| Tầng | Vai trò | Đã có | Đề xuất (ngày 4) |
|---|---|---|---|
| **domain** | Đáp án trông thế nào; luật chấm. Thuần logic, không I/O. | `domain/gold_label.py`: `GoldLabel`, luật đáp án hợp lệ (`_clean_skills`, kiểm `not_mentioned` + `level`) | `domain/scoring.py`: so một trường, chính sách null, accuracy và precision/recall (mục 3–5 của `EVAL_RULES.md`). `Extraction`: `job_id` cộng các trường được chấm; prediction xấu không bị từ chối. |
| **application** | Kịch bản: lấy đáp án, lấy bài làm, ghép, gọi luật chấm, trả bảng điểm | `application/ports.py`: chỉ có `JobRepository`, `Clock` | Use case `EvaluateExtractor` nhận `list[GoldLabel]` do CLI truyền vào. Chỉ một port: `PredictionSource`. |
| **adapters/outbound** | Nơi use case gọi ra để lấy prediction | chưa có reader nhãn cho eval | Extractor giả cài `PredictionSource`: nhận gold, trả `Extraction` y hệt trong bộ nhớ. Hôm nay chưa đọc `predictions/*.json`. |
| **adapters/inbound** | Cửa vào cho người dùng | `adapters/inbound/dto.py`: `GoldLabelFileDTO` chuyển JSON thành `GoldLabel`; `adapters/inbound/cli.py`: lệnh lưu tin | CLI `eval` đọc `labels/`, dùng `GoldLabelFileDTO`, kiểm `job_id` tên file trùng JSON (lệch thì dừng), truyền `list[GoldLabel]`, in bảng điểm. |
| **composition** | Lắp các mảnh lại | có cho lệnh lưu tin | Nối `EvaluateExtractor` với extractor giả. |

Lý do đổi (ngày 4): bỏ port `GoldLabelSource` — gold là đầu vào người dùng đưa qua CLI nên thuộc inbound; prediction là thứ use case gọi ra ngoài lấy nên thuộc outbound.

### Luồng chạy (đề xuất)

```
CLI eval                          (adapters/inbound)
  → đọc labels/*.json             (GoldLabelFileDTO; job_id tên file trùng JSON, lệch thì dừng)
  → list[GoldLabel]
  → EvaluateExtractor             (application)
      → PredictionSource          (port)
          → extractor giả         (adapters/outbound, trong bộ nhớ)
      → ghép theo job_id
      → so từng ô, tính điểm      (domain/scoring.py)
  → in bảng điểm                  (adapters/inbound)
```

### Vì sao luật chấm nằm ở domain

- **Luật chấm là ý nghĩa nghiệp vụ.** "null/null có tính đúng không" là quyết định về đo lường, không phải chuyện kỹ thuật.
- **Test dễ.** Đưa vào hai object Python, kiểm tra kết quả, không cần file. Ví dụ 3 tin ở mục 7 của `EVAL_RULES.md` thành unit test thẳng cho `scoring.py`.
- **Đổi nguồn dữ liệu không đụng luật.** Prediction sau này đến từ API hay database thì chỉ viết thêm một adapter.

---

## 4. Ngày 3 và ngày 4 làm gì

| Ngày | Việc | Kết quả |
|---|---|---|
| 3 | Viết luật chấm (thiết kế cho `domain/scoring.py`) | `docs/EVAL_RULES.md` + ghi chú này |
| 4 | Code các phần "Đề xuất" ở mục 3; chạy với 3 extractor giả | Runner ra đúng các số tính tay ở mục 7 của `EVAL_RULES.md` |

---

## 5. Tự kiểm tra

Trả lời được mà không nhìn file là đạt:

1. Gold label khác prediction ở điểm nào? Ai tạo ra mỗi loại?
2. Vì sao một tin đơn lẻ không cho ra "accuracy"?
3. Luật "null/null tính đúng" nằm ở tầng nào? Vì sao không đặt trong adapter đọc file?
4. Muốn đọc prediction từ API thay vì file, phải sửa tầng nào, và tầng nào giữ nguyên?