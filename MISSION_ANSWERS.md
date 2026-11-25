# Day 14 — Ghi chú bài làm

## Part 1 — Localhost và production

Các rủi ro thường gặp gồm secret hard-code, cấu hình cố định theo máy, lưu state trong RAM, thiếu health/readiness, thiếu giới hạn truy cập, và không xử lý shutdown. Config qua environment giúp tái sử dụng image; health kiểm tra process sống còn readiness kiểm tra khả năng nhận tải.

Trong mẫu develop: key và database URL được hard-code; key bị in ra log; DEBUG và reload bật; bind localhost, port 8000 cố định; không có health check. Đây là key giả của bài tập.

| Thành phần | Develop | Production | Lý do |
|---|---|---|---|
| Config | Giá trị cố định | Biến môi trường | Cùng image chạy ở nhiều môi trường |
| Health | Không có | /health và /ready | Phát hiện process chết hoặc instance chưa sẵn sàng |
| Log | print, có cả key giả | Log có cấu trúc | Dễ tra cứu và hạn chế lộ secret |
| Shutdown | Không quản lý | Lifespan và dự kiến graceful | Giảm mất request khi dừng |

Đã chạy server develop local và gọi bằng curl:

```text
POST /ask?question=Hello
HTTP/1.1 200 OK
{"answer":"Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn đã được nhận."}
```

## Part 2 — Docker

Multi-stage tách môi trường cài/build khỏi runtime. Copy requirements trước source cho phép Docker tái sử dụng cache dependencies khi chỉ đổi code. Docker image inspect đo được develop 1.590,51 MiB (1.667.775.798 bytes), production 228,71 MiB (239.815.702 bytes), giảm 85,62% so với develop. Container develop trả HTTP 200 với POST /ask?question=Hello; container production trả HTTP 200 với GET /health.

Exercise 2.1: base image là python:3.11; working directory là /app. Copy requirements trước giúp cache lớp cài dependencies. CMD cung cấp lệnh/tham số mặc định có thể thay bằng đối số khi chạy container; ENTRYPOINT xác định chương trình chính, đối số chạy thường được chuyển cho chương trình đó.

Compose 2.4: client → Nginx → agent; agent được cấu hình địa chỉ Redis và Qdrant; các service nằm trên mạng nội bộ. Đã chạy stack và gọi qua Nginx: GET /health HTTP 200, POST /ask với câu hỏi Hello HTTP 200 và có answer.

## Part 3 — Cloud

Railway dùng TOML khai báo Docker builder và healthcheck; Render dùng YAML khai báo web service và các biến môi trường. Cloud Build chạy test, build và push image, rồi triển khai Cloud Run; service manifest mô tả tài nguyên, scaling, secrets và probes. Đã deploy Part 6 lên Render và kiểm tra /health 200, /ready 200, POST /ask thiếu key 401, có key hợp lệ 200. URL và bằng chứng nằm trong [DEPLOYMENT.md](DEPLOYMENT.md).

## Part 4 — API security

API key xác thực client; rate limit giới hạn tốc độ gọi; cost guard giới hạn tổng chi phí. Cần cả hai vì traffic ít vẫn có thể tốn nhiều tiền trên mỗi request.

Đã chạy các server local và gọi qua curl; token được che:

```text
Develop, thiếu key:
HTTP/1.1 401 Unauthorized
{"detail":"Missing API key. Include header: X-API-Key: <your-key>"}

Develop, key đúng:
HTTP/1.1 200 OK
{"question":"Hello","answer":"Agent đang hoạt động tốt! (mock response) Hỏi thêm câu hỏi đi nhé."}

Production, thiếu token:
HTTP/1.1 401 Unauthorized
www-authenticate: Bearer
{"detail":"Authentication required. Include: Authorization: Bearer <token>"}

Production, token hợp lệ:
HTTP/1.1 200 OK
{"question":"Hello","answer":"Đây là câu trả lời từ AI agent (mock). Trong production, đây sẽ là response từ OpenAI/Anthropic.","usage":{"requests_remaining":9,"budget_remaining_usd":2.1e-05}}

Production, sau 10 request hợp lệ trong cửa sổ:
HTTP/1.1 429 Too Many Requests
x-ratelimit-limit: 10
x-ratelimit-remaining: 0
retry-after: 59
{"detail":{"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_after_seconds":59}}
```

Develop dùng header X-API-Key và từ chối key sai hoặc thiếu. Đổi key bằng cách thay giá trị environment và triển khai lại; cần phân phối key mới an toàn cho client. Bản production cấp JWT sau khi xác thực, sau đó kiểm tra chữ ký, hạn và role. Rate limiter mẫu dùng sliding window: student 10/phút, admin có limiter riêng 100/phút, không phải miễn giới hạn.

Cost guard Part 6 tính chi phí mô phỏng theo token, cộng vào Redis bằng INCRBYFLOAT và kiểm tra tổng ngày UTC trước request tiếp theo. Vì không đặt trước chi phí mỗi request, nhiều request đồng thời có thể vượt ngân sách; hệ thống production cần cơ chế đặt trước ngân sách nguyên tử.

## Part 5 — Scaling

Liveness cho biết process còn sống; readiness cho biết instance sẵn sàng nhận traffic. State trong RAM bị chia cắt giữa các instance và mất khi restart; Redis giúp các instance chia sẻ state. Đã chạy stack 3 instance và test_stateless.py: 5 request được phục vụ bởi cả 3 instance, history giữ đủ 10 message qua Redis. Script không tự tắt instance, nên kết quả này chưa kiểm tra failover khi một instance chết.

## Part 6 — Kiểm tra

Đã chạy script đầy đủ trong Ubuntu WSL2 với Python 3.11, Redis tạm thời và Docker Desktop:

```text
Checklist Deliverable
✅ Dockerfile (multi-stage, < 500 MB)
✅ docker-compose.yml (agent + redis)
✅ .dockerignore
✅ Health check endpoint (GET /health)
✅ Readiness endpoint (GET /ready)
✅ API Key authentication
✅ Rate limiting
✅ Cost guard
✅ Config từ environment variables
✅ Structured logging
✅ Graceful shutdown
✅ Public URL ready (Railway / Render config)
Result: 12/12 tiêu chí đạt · 43/43 checks passed
🎉 PASS 12/12 — PRODUCTION READY!
```

Docker image đo được 238 MB; Docker stop exit code 0 sau 0,9 giây. SIGTERM trong lúc xử lý request: request trả 200, process thoát code 0. Kiểm tra cấu hình deploy không chứng minh có URL public.

## AI log

- Yêu cầu: đọc hướng dẫn và hoàn thành bài tập. Codex đã viết phần triển khai Part 6, bổ sung metric, knowledge base và CI; các ghi chú này cũng do Codex soạn.
- Sau yêu cầu tiếp tục, Codex chuẩn bị Python và Redis tạm thời, chạy kiểm tra --skip-docker, TestClient, curl, eval và load test; số liệu được ghi từ output và JSON. Người nộp cần đọc, hiểu, kiểm tra lại và bổ sung bằng chứng Docker/cloud trước khi nộp.
- Lần tiếp theo Codex cài WSL2, Docker Desktop, Ubuntu và Redis; sửa Dockerfile của stack quan sát để Python tìm được thư viện; chạy script chấm đầy đủ, Locust, Prometheus và Jaeger. Các số đo, ảnh và trạng thái đều lấy từ lần chạy thực tế.
- Codex kết nối Render, sửa root directory của service, cấu hình Redis và key, deploy và kiểm tra HTTP; người nộp cần tự đọc, hiểu và kiểm tra kết quả, bổ sung phần tự sửa/tự kiểm tra cá nhân nếu có.
