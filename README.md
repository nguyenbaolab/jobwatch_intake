# jobwatch_intake

Phần nhập tin của Jobwatch. Bạn dán một tin tuyển dụng vào file nháp; chương trình kiểm tra rồi ghi một file JSON cho mỗi tin. Nhãn vàng (đáp án gán tay) nằm ở thư mục khác, để bộ trích xuất không đọc được đáp án.

## Cài và chạy

Cần Python 3.10 trở lên. Trên Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python -m jobwatch_intake .\examples\junior-data-engineer-helsinki.txt --out .\data\jobs --verbose
```

`--out` là thư mục ghi JSON (mặc định `data/jobs`). `--force` ghi đè tin đã có. `--verbose` in log DEBUG của ba bước: đọc, kiểm tra, ghi.

## Định dạng file nháp

Vài dòng `khóa: giá trị`, một dòng chỉ có `---`, rồi nội dung tin. Dòng bắt đầu bằng `#` bị bỏ qua. Dòng `---` đầu tiên ngăn phần đầu và nội dung; `---` sau đó thuộc nội dung. Giá trị rỗng nghĩa là chưa có.

Khóa: `source`, `url`, `language` (`fi`, `en`, `sv`), `title`, `company`, `location`, `published_at`, `deadline`. Ngày dạng `YYYY-MM-DD`. Xem `examples/`.

## Mã thoát

- `0`: đã lưu, hoặc tin đã có sẵn (không ghi đè; dùng `--force` nếu muốn ghi đè).
- `1`: tin không hợp lệ. In `Tin không hợp lệ (N lỗi):` rồi mỗi lỗi một dòng `  - trường: lý do` ra stderr. Lỗi dạng (thiếu trường, sai kiểu, sai ngày, sai ngôn ngữ, trường lạ) in trước. Nếu dạng đúng mà sai luật nghiệp vụ, in đủ lỗi của đợt đó.
- `2`: không đọc được file nháp (không thấy file, sai UTF-8, thiếu dòng `---`, dòng phần đầu không có dấu `:`).

## Cây thư mục

```
pyproject.toml
src/jobwatch_intake/
  __main__.py          python -m jobwatch_intake
  composition.py       ráp adapter vào use case
  domain/              luật nghiệp vụ
  application/         use case SaveJob và các cổng
  adapters/inbound/    file nháp, DTO, dòng lệnh
  adapters/outbound/   file JSON và đồng hồ
tools/make_schemas.py
schemas/               JSON Schema sinh từ DTO
examples/              hai tin giả và nhãn trong examples/labels/
data/jobs/             tin đã lưu (JSON không đưa lên git)
data/labels/           nhãn thật
docs/ARCHITECTURE.md
docs/LABELING.md
tests/
```

## Test

```powershell
python -m pytest -q
```

Sinh lại schema sau khi sửa DTO:

```powershell
python .\tools\make_schemas.py
```

## Tài liệu

- [Kiến trúc](docs/ARCHITECTURE.md)
- [Luật gán nhãn](docs/LABELING.md)
