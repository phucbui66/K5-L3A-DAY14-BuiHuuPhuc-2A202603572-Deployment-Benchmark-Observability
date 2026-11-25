# Deployment — Day 14

## Dịch vụ

- **Public URL:** https://k5-l3a-day14-buihuuphuc-2a202603572.onrender.com
- **Nền tảng:** Render Web Service, Docker, gói Free, region Oregon.
- **Build:** thư mục gốc `06-lab-complete`, Dockerfile của thư mục đó, nhánh `main`.
- **Redis:** Render Key Value (Valkey), gói Free, cùng region và mạng nội bộ. Gói miễn phí không bật persistence.
- **Health check:** `/health`.

## Kiểm tra thực tế

Ngày 26/11/2026, kiểm tra URL public:

| Phép kiểm | Kết quả HTTP |
|---|---:|
| GET /health | 200 |
| GET /ready | 200 |
| POST /ask không có API key | 401 |
| POST /ask với API key đúng | 200 |

Có thể kiểm tra lại bằng các lệnh sau; đặt API key lấy từ mục Environment trên Render vào biến môi trường cục bộ, không commit giá trị:

```bash
BASE=https://k5-l3a-day14-buihuuphuc-2a202603572.onrender.com
curl -sS -o /dev/null -w '%{http_code}\n' "$BASE/health"
curl -sS -o /dev/null -w '%{http_code}\n' "$BASE/ready"
curl -sS -o /dev/null -w '%{http_code}\n' -X POST "$BASE/ask" -H 'Content-Type: application/json' -d '{"question":"Hello"}'
curl -sS -o /dev/null -w '%{http_code}\n' -X POST "$BASE/ask" -H 'Content-Type: application/json' -H "X-API-Key: $AGENT_API_KEY" -d '{"question":"Hello"}'
```

## Cấu hình

Render đặt `REDIS_URL` tới Key Value nội bộ và tạo `AGENT_API_KEY` trong Environment. `PORT` do Render cung cấp; `ENVIRONMENT`, `RATE_LIMIT_PER_MINUTE` và `DAILY_BUDGET_USD` dùng giá trị mặc định trong ứng dụng. Secret không được ghi vào repo.

[Dashboard dự án](screenshots/dashboard.png) · [Trạng thái deploy](screenshots/running.png) · [Kiểm tra health](screenshots/test.png).

Gói Free có thể ngủ khi không sử dụng và cần thời gian khởi động lại. Redis Free không có persistence, nên rate limit và cost có thể mất khi Redis khởi động lại; đây là giới hạn của cấu hình lab, không phù hợp khi cần bảo đảm ngân sách lâu dài.
