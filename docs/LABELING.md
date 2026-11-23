# Luật gán nhãn vàng cho tin tuyển dụng

Mục đích: mỗi tin trong bộ 100 tin có một file nhãn mà bạn gán bằng tay. Sau này, kết quả của bộ trích xuất (LLM) được so từng trường với nhãn này. Nhãn sai thì điểm đo sai, nên luật phải cố định trước khi gán tin đầu tiên. Nếu một luật thay đổi giữa chừng, gán lại các tin đã làm.

## Cách làm

1. Lưu tin bằng `python -m jobwatch_intake <file nháp> --out data/jobs` để có `data/jobs/<job_id>.json`.
2. Chép `job_id` đó vào file nhãn `data/labels/<job_id>.json`. Hai tin ví dụ nằm trong `examples/labels/`.
3. Gán nhãn **trước khi** xem kết quả trích xuất của mô hình. Nếu xem trước, bạn sẽ vô thức gán theo mô hình.
4. Khi tin mơ hồ, chọn theo luật bên dưới và ghi lý do vào `notes`. Một dòng là đủ.

Tin gốc và nhãn nằm ở hai thư mục khác nhau để bộ trích xuất chỉ đọc được tin, không đọc được đáp án.

## Tám luật

1. **Chỉ gán điều văn bản nói.** Không suy luận từ tên công ty, ngành hay kinh nghiệm cá nhân. Văn bản không nhắc thì để giá trị mặc định (`not_mentioned`, `unspecified`, `null`, danh sách rỗng).

2. **Ngôn ngữ (finnish, swedish, english) là trường quan trọng nhất.** Mỗi ngôn ngữ có hai phần:
   - `requirement`: `required` nếu tin nói cần, bắt buộc, "vaaditaan", "required", "must", hoặc liệt kê trong phần yêu cầu mà không có từ làm mềm. `preferred` nếu tin nói là lợi thế, "eduksi", "a plus", "nice to have", "useful". `not_mentioned` nếu không nhắc.
   - `level`: `unspecified` khi tin chỉ nói "cần tiếng X" mà không nói mức. Các mức còn lại: `basic` (alkeet, basic), `good` (hyvä, good, đủ để làm việc, "työskentelyyn riittää"), `fluent` (sujuva, erinomainen, fluent, excellent), `native` (äidinkieli, native). Đã `not_mentioned` thì `level` phải là `unspecified`.

3. **Kỹ năng ghi chữ thường, một khái niệm một mục.** `python`, `sql`, `docker`, `azure`. Không ghi "Python-osaaminen" mà ghi `python`. Không ghi mục quá chung như "cloud services" hay "teamwork"; nếu bạn thấy đáng nhớ thì ghi vào `notes`.

4. **required hay preferred cho kỹ năng.** Công cụ mà tin nói bạn sẽ dùng hằng ngày thì tính là `required`, kể cả khi nằm ngoài danh sách yêu cầu. Công cụ có chữ "plus", "eduksi", "nice to have" thì là `preferred`. Một kỹ năng không nằm ở cả hai danh sách.

5. **"A tai B" (A hoặc B).** Ghi cả A và B vào `skills_required` và nêu trong `notes` rằng đó là lựa chọn. Cách này giữ luật đơn giản, chấp nhận mất một chút chính xác.

6. **Số năm kinh nghiệm là mức tối thiểu.** "vähintään 2 vuotta" hay "at least 2 years" cho `2`. "2-4 years" cho `2`. "Kokemusta" mà không có số cho `null`. Không đổi tháng thành năm làm tròn: "6 kuukautta" cho `0` và ghi `notes`.

7. **Thành phố và hình thức làm việc.** `city` là thành phố nơi làm việc, tên tiếng Anh nếu có (Helsinki, Tampere, Turku). Nhiều thành phố thì lấy thành phố đầu tiên và ghi các nơi còn lại vào `notes`. `work_mode`: `onsite`, `hybrid`, `remote`; "pääosin toimistolla" (chủ yếu tại văn phòng) là `onsite`; không nói gì là `unspecified`.

8. **Hạn nộp (`deadline`) theo ISO `YYYY-MM-DD`.** Hạn kiểu Phần Lan `10.12.2026` là ngày.tháng.năm, tức `2026-12-10`. Kiểu Mỹ `12/10/2026` thì xem ngữ cảnh và ghi `notes` nếu không chắc. Tin ghi "jatkuva haku" (tuyển liên tục) hoặc không có hạn thì `null`.

## Ví dụ có giải thích

Hai file `examples/labels/*.json` là hai nhãn mẫu cho hai tin giả trong `examples/`. Đọc ô `notes` của chúng để thấy cách ghi lý do.

## Kiểm tra nhãn

`GoldLabelFileDTO` từ chối nhãn sai dạng (thiếu trường bắt buộc, sai kiểu, sai ngày, trường lạ, gõ nhầm tên trong khối ngôn ngữ). `GoldLabel` từ chối nhãn sai luật nghiệp vụ (kỹ năng rỗng, kỹ năng lặp, kỹ năng nằm ở cả hai danh sách, `not_mentioned` mà có `level`, số năm ngoài 0..30). Lệnh sau chạy cả hai:

```powershell
python -c "import json,sys; from jobwatch_intake.adapters.inbound.dto import GoldLabelFileDTO; print(GoldLabelFileDTO.model_validate(json.load(open(sys.argv[1], encoding='utf-8'))).to_domain().job_id)" data/labels/job-xxxx.json
```

Sinh schema để VS Code báo lỗi lúc gõ: `python tools/make_schemas.py`, rồi thêm vào đầu file nhãn:

```json
"$schema": "../../schemas/gold_label.schema.json"
```

Schema mô tả dạng file. Luật nghiệp vụ nằm trong domain, không nằm trong schema.
