# TikTok Seeding Detection Backend

Backend FastAPI cho ứng dụng phát hiện bình luận seeding trên TikTok sử dụng các mô hình như VisoBERT, CafeBert và PhoBert đã được fine-tune - [source](https://github.com/vuminhhieuu/Detecting-seeding-comments-on-Tiktok).

## 🚀 Tính năng

- **Hỗ trợ nhiều kiểu nhập:** Phân tích 1 URL, nhiều URL hoặc tải lên file (JSON/CSV)
- **Phát hiện bằng AI:** Sử dụng mô hình VisoBERT cho tiếng Việt để phân loại bình luận seeding
- **Phân tích chi tiết:** Thống kê, trích xuất từ khóa, báo cáo tỷ lệ seeding
- **Xuất kết quả:** Tải kết quả phân tích dưới dạng file CSV
- **API RESTful:** Dễ sử dụng, có tài liệu chi tiết

## 🛠️ Cài đặt

1. Cài Python 3.8 trở lên
2. Cài đặt các thư viện cần thiết:
```sh
pip install -r requirements.txt
```

## ▶️ Chạy server

```sh
python run.py
```

Server sẽ chạy tại `http://localhost:8000`

## 📚 Tài liệu API

Sau khi chạy, truy cập:
- Swagger: `http://localhost:8000/docs`
- Redoc: `http://localhost:8000/redoc`

## 🌐 Các endpoint chính

- `POST /predict/url` - Phân tích bình luận từ 1 URL TikTok
- `POST /predict/urls` - Phân tích bình luận từ nhiều URL TikTok
- `POST /predict/file` - Phân tích bình luận từ file JSON/CSV tải lên
- `GET /stats` - Thống kê tổng quan
- `GET /download/{analysis_id}` - Tải kết quả phân tích (CSV)

### Endpoint tiện ích

- `GET /` - Thông tin API
- `GET /health` - Kiểm tra trạng thái hệ thống
- `GET /analysis/{analysis_id}` - Xem kết quả phân tích cụ thể
- `DELETE /analysis/{analysis_id}` - Xóa kết quả phân tích

## 📥 Ví dụ request

### Phân tích 1 URL
```sh
curl -X POST "http://localhost:8000/predict/url" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.tiktok.com/@user/video/123"}'
```

### Phân tích nhiều URL
```sh
curl -X POST "http://localhost:8000/predict/urls" \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://www.tiktok.com/@user1/video/123", "https://www.tiktok.com/@user2/video/456"]}'
```

### Phân tích file
```sh
curl -X POST "http://localhost:8000/predict/file" \
  -F "file=@comments.csv"
```

## 📝 Định dạng file

### JSON
```json
[
  {
    "comment_id": "123",
    "comment_text": "Sản phẩm tuyệt vời!",
    "like_count": 45,
    "timestamp": "2024-01-15T10:30:00Z",
    "user_id": "user123"
  }
]
```

### CSV
```csv
comment_id,comment_text,like_count,timestamp,user_id
123,"Sản phẩm tuyệt vời!",45,2024-01-15T10:30:00Z,user123
456,"Video hay quá!",12,2024-01-15T11:15:00Z,user456
```

## 📤 Định dạng phản hồi

```json
{
  "comments": [...],
  "stats": {
    "total": 100,
    "seeding": 25,
    "not_seeding": 75,
    "seeding_percentage": 25.0
  },
  "keywords": {
    "shop": 15,
    "mua": 12,
    "uy tín": 8
  },
  "source": "example.csv",
  "processed_at": "2024-01-15T12:00:00",
  "analysis_id": "analysis_20240115_120000_1234"
}
```

## ⚙️ Cấu hình

### Biến môi trường

- `HUGGINGFACE_TOKEN` - Token Hugging Face để gọi model VisoBERT
- `DEBUG` - Bật chế độ debug (mặc định: False)
- `MAX_BATCH_SIZE` - Số bình luận tối đa mỗi lần phân tích (mặc định: 1000)
- Xem thêm trong file [.env.example](.env.example)

## 🗂️ Cấu trúc dự án

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── models.py            # Định nghĩa dữ liệu
│   └── services/
│       ├── tiktok_service.py    # Lấy bình luận TikTok
│       ├── ml_service.py        # Gọi AI VisoBERT
│       └── data_processor.py    # Xử lý dữ liệu
├── requirements.txt
├── run.py                   # Chạy server
└── README.md
```

## 💡 Lưu ý triển khai

- Để dùng AI thực tế, cần token Hugging Face hợp lệ
- Có thể mở rộng lưu trữ kết quả bằng database (PostgreSQL/MongoDB)
- Có thể triển khai production với Docker, giám sát log, bảo mật API
